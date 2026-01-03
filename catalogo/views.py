import hashlib
from io import BytesIO

from PIL import Image, UnidentifiedImageError
import requests
from requests.exceptions import RequestException

from itertools import groupby

from django.contrib import messages
from django.core.cache import cache
from django.db import transaction
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_GET
from django.views.generic import DetailView, FormView, ListView, TemplateView

from django.core.exceptions import ValidationError

from catalogo.forms import CheckoutForm
from catalogo.models import CatalogProfile
from catalogo.profile import get_default_catalog_profile
from catalogo.services import normalize_cart, serialize_cart
from pedidos.models import ItemPedido, Pedido
from produtos.models import Produto, ProdutoImagem
from produtos.services import upload_image_to_imgbb
from tenants.models import TenantProfile


IMAGE_CACHE_TIMEOUT = 60 * 60 * 24  # one day
IMAGE_MAX_DIMENSION = 900
IMAGE_QUALITY = 78


def _get_cached_image(url):
    if not url:
        return None
    cache_key = f"catalogo:image:{hashlib.sha256(url.encode('utf-8')).hexdigest()}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    try:
        response = requests.get(url, timeout=8)
        response.raise_for_status()
        payload = response.content
        image = Image.open(BytesIO(payload))
        image = image.convert("RGB")
        image.thumbnail((IMAGE_MAX_DIMENSION, IMAGE_MAX_DIMENSION), Image.LANCZOS)
        output = BytesIO()
        image.save(output, format="JPEG", quality=IMAGE_QUALITY, optimize=True)
        data = output.getvalue()
    except (RequestException, UnidentifiedImageError, OSError):
        return None
    cache.set(cache_key, data, IMAGE_CACHE_TIMEOUT)
    return data


def _build_image_response(data):
    response = HttpResponse(data, content_type="image/jpeg")
    response["Cache-Control"] = f"public, max-age={IMAGE_CACHE_TIMEOUT}"
    return response


@require_GET
@cache_page(IMAGE_CACHE_TIMEOUT)
def produto_imagem_cache(request, produto_pk):
    produto = get_object_or_404(Produto, pk=produto_pk, ativo=True)
    image_data = _get_cached_image(produto.imagem)
    if not image_data:
        raise Http404("Imagem indisponível")
    return _build_image_response(image_data)


@require_GET
@cache_page(IMAGE_CACHE_TIMEOUT)
def produto_imagem_extra_cache(request, imagem_pk):
    imagem = get_object_or_404(ProdutoImagem, pk=imagem_pk)
    image_data = _get_cached_image(imagem.url)
    if not image_data:
        raise Http404("Imagem indisponível")
    return _build_image_response(image_data)


def _get_cart(request):
    return request.session.setdefault("cart", {})


def _maybe_cart_json_response(request, cart):
    if request.headers.get("x-requested-with") != "XMLHttpRequest":
        return None
    summary = normalize_cart(cart)
    return JsonResponse(serialize_cart(summary))


def _get_tenant_by_identifier(identifier):
    if not identifier:
        return None
    if identifier.isdigit():
        return TenantProfile.objects.filter(pk=int(identifier), is_active=True).first()
    return TenantProfile.objects.filter(slug=identifier, is_active=True).first()


def _resolve_shared_tenant(request):
    cached = request.session.get("public_catalog_identifier")
    return _get_tenant_by_identifier(cached)


def _get_request_tenant(request):
    return getattr(request, "tenant", None) or _resolve_shared_tenant(request)


def _get_catalog_profile_for_tenant(tenant):
    if not tenant:
        return None
    return CatalogProfile.objects.filter(tenant=tenant).first()


class TenantAwareMixin:
    """
    Helper mixin that centralizes how the catalog identifies which tenant should
    back a request, supporting both authenticated tenants and the public sharing
    link identified by the tenant slug.
    """

    identifier_kwarg = "tenant_identifier"

    def dispatch(self, request, *args, **kwargs):
        self.public_tenant_identifier = kwargs.get(self.identifier_kwarg) or request.GET.get("tenant")
        session_identifier = request.session.get("public_catalog_identifier")
        request_tenant = getattr(request, "tenant", None)
        self.effective_tenant = request_tenant

        if request_tenant:
            request.session.pop("public_catalog_identifier", None)
        elif self.public_tenant_identifier:
            tenant = _get_tenant_by_identifier(self.public_tenant_identifier)
            if tenant:
                self.effective_tenant = tenant
                request.session["public_catalog_identifier"] = self.public_tenant_identifier
        elif session_identifier:
            tenant = _get_tenant_by_identifier(session_identifier)
            if tenant:
                self.effective_tenant = tenant
                self.public_tenant_identifier = session_identifier

        return super().dispatch(request, *args, **kwargs)

    def get_effective_tenant(self):
        return self.effective_tenant


class CatalogoHomeView(TenantAwareMixin, ListView):
    model = Produto
    template_name = "catalogo/home.html"
    context_object_name = "produtos"
    cache_timeout = 30

    def get_queryset(self):
        tenant = self.get_effective_tenant()
        if tenant:
            cache_key = f"catalogo:home:{tenant.pk}"
            cached = cache.get(cache_key)
            if cached is not None:
                return cached
            qs = (
                Produto.objects.filter(ativo=True, tenant=tenant)
                .select_related("categoria")
                .prefetch_related("variacoes__categoria", "variacoes", "imagens")
                .order_by("categoria__nome", "nome")
            )
            cache.set(cache_key, qs, self.cache_timeout)
            return qs
        return Produto.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = self.get_effective_tenant()
        profile_data = get_default_catalog_profile()
        profile_record = _get_catalog_profile_for_tenant(tenant)
        if profile_record:
            if profile_record.title:
                profile_data["title"] = profile_record.title
            if profile_record.message:
                profile_data["message"] = profile_record.message
            if profile_record.cta:
                profile_data["cta"] = profile_record.cta
            desktop_source = profile_record.desktop_image or profile_record.image
            if desktop_source:
                profile_data["desktop_image"] = desktop_source
                profile_data["image"] = desktop_source
            if profile_record.mobile_image:
                profile_data["mobile_image"] = profile_record.mobile_image
            elif profile_record.desktop_image:
                profile_data["mobile_image"] = profile_record.desktop_image
            elif profile_record.image:
                profile_data["mobile_image"] = profile_record.image
        context["profile_data"] = profile_data
        context["banner_image"] = profile_data["desktop_image"]

        produtos = list(context.get("produtos", []))
        grouped = []
        for categoria, items in groupby(produtos, key=lambda prod: getattr(prod, "categoria", None)):
            grouped.append({"categoria": categoria, "produtos": list(items)})
        context["produtos_por_categoria"] = grouped

        return context


class AdicionarAoCarrinhoView(View):
    def post(self, request, pk, *args, **kwargs):
        tenant = _get_request_tenant(request)
        produto = get_object_or_404(Produto, pk=pk, ativo=True, tenant=tenant)
        cart = _get_cart(request)
        variacao_ids = request.POST.getlist("variacoes") or []
        try:
            quantity = int(request.POST.get("quantity") or 1)
        except (TypeError, ValueError):
            quantity = 1
        quantity = max(1, min(quantity, 999))
        single_variacao = request.POST.get("variacao_id")
        if single_variacao and single_variacao not in variacao_ids:
            variacao_ids.append(single_variacao)
        if not variacao_ids:
            variacao_ids = [None]

        variacoes_map = {
            str(v.pk): v for v in produto.variacoes.select_related("categoria").all()
        }

        selecionadas = []
        for raw_id in variacao_ids:
            if raw_id and str(raw_id) not in variacoes_map:
                continue
            variacao = variacoes_map.get(str(raw_id)) if raw_id else None
            if variacao:
                selecionadas.append(variacao)
        if not selecionadas and variacao_ids == [None]:
            selecionadas = [None]

        # valida limite por categoria
        cat_contagem = {}
        violacao_msg = ""
        for variacao in selecionadas:
            if variacao is None:
                continue
            cat_key = variacao.categoria_id or "none"
            limite = variacao.categoria.max_escolhas if variacao.categoria else 99
            atual = cat_contagem.get(cat_key, 0) + 1
            cat_contagem[cat_key] = atual
            if atual > limite:
                nome_cat = variacao.categoria.nome if variacao.categoria else "variações"
                violacao_msg = f"Selecione no máximo {limite} opção(ões) em {nome_cat}."
                break

        if violacao_msg:
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({"error": violacao_msg}, status=400)
            messages.error(request, violacao_msg)
            fallback = request.POST.get("next") or request.META.get("HTTP_REFERER")
            return redirect(fallback or reverse("catalogo:home"))

        def _build_label(variacao):
            if not variacao:
                return ""
            parts = [variacao.nome]
            if variacao.tamanho:
                parts.append(variacao.tamanho)
            return " / ".join(parts)

        variacao_ids_sorted = sorted(str(v.pk) for v in selecionadas if v)
        item_key = str(produto.pk)
        if variacao_ids_sorted:
            item_key = f"{produto.pk}:{'-'.join(variacao_ids_sorted)}"

        preco = produto.preco
        labels = []
        variacao_id = None
        if selecionadas != [None]:
            for variacao in selecionadas:
                preco += variacao.preco_adicional
                labels.append(_build_label(variacao))
            if selecionadas:
                variacao_id = selecionadas[0].pk

        if item_key not in cart:
            cart[item_key] = {
                "produto_id": produto.pk,
                "nome": produto.nome,
                "preco": str(preco),
                "imagem": produto.imagem or "",
                "quantidade": 0,
                "variacao_id": variacao_id,
                "variacao_label": ", ".join(labels) if labels else "",
                "variacoes_ids": variacao_ids_sorted,
                "variacoes_labels": labels,
            }
        cart[item_key]["quantidade"] += quantity
        request.session.modified = True

        destination = request.POST.get("destination")
        if destination == "cart":
            return redirect(reverse("catalogo:carrinho"))
        if destination == "checkout":
            return redirect(reverse("catalogo:checkout"))

        ajax_response = _maybe_cart_json_response(request, cart)
        if ajax_response:
            return ajax_response

        fallback = request.POST.get("next") or request.META.get("HTTP_REFERER")
        return redirect(fallback or reverse("catalogo:home"))


class AtualizarCarrinhoView(View):
    def post(self, request, pk, *args, **kwargs):
        cart = _get_cart(request)
        item_key = request.POST.get("item_key") or str(pk)
        if item_key in cart:
            action = request.POST.get("cart_action") or request.POST.get("action")
            if action == "remove":
                cart.pop(item_key, None)
            elif action == "decrement":
                cart[item_key]["quantidade"] = max(0, cart[item_key]["quantidade"] - 1)
                if cart[item_key]["quantidade"] == 0:
                    cart.pop(item_key, None)
        request.session.modified = True
        ajax_response = _maybe_cart_json_response(request, cart)
        if ajax_response:
            return ajax_response
        return redirect(request.POST.get("next") or reverse("catalogo:carrinho"))


class ProdutoDetailView(DetailView):
    model = Produto
    template_name = "catalogo/produto_detail.html"

    def get_queryset(self):
        tenant = _get_request_tenant(self.request)
        qs = super().get_queryset()
        if tenant:
            return (
                qs.filter(tenant=tenant)
                .prefetch_related("variacoes__categoria", "variacoes", "imagens")
                .select_related("categoria", "subcategoria")
            )
        return qs.none()


class CarrinhoView(TemplateView):
    template_name = "catalogo/carrinho.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = _get_cart(self.request)
        summary = normalize_cart(cart)
        context["cart_items"] = summary["items"]
        context["cart_total"] = summary["total"]
        return context


class CheckoutView(FormView):
    template_name = "catalogo/checkout.html"
    form_class = CheckoutForm

    def _get_cart_summary(self):
        cart = _get_cart(self.request)
        return normalize_cart(cart)

    def _clear_cart(self):
        self.request.session["cart"] = {}
        self.request.session.modified = True

    def form_valid(self, form):
        tenant = _get_request_tenant(self.request)
        if not tenant:
            messages.error(self.request, "Nenhuma papelaria ativa para registrar o pedido.")
            return redirect(reverse("catalogo:home"))

        summary = self._get_cart_summary()
        if summary["total_items"] == 0:
            messages.error(self.request, "Seu carrinho está vazio. Adicione itens antes de finalizar.")
            return redirect(reverse("catalogo:home"))

        contato = form.cleaned_data.get("nome", "").strip()
        telefone = form.cleaned_data.get("telefone", "").strip()
        nome_capa = form.cleaned_data.get("nome_capa", "").strip()
        capa = form.cleaned_data.get("capa")
        contra_capa = form.cleaned_data.get("contra_capa")
        capa_url = ""
        contra_capa_url = ""
        if telefone:
            contato = f"{contato} ({telefone})" if contato else telefone

        # Upload para IMGBB quando o arquivo for enviado.
        try:
            if capa:
                capa_url = upload_image_to_imgbb(capa)
            if contra_capa:
                contra_capa_url = upload_image_to_imgbb(contra_capa)
        except ValidationError as exc:
            messages.error(self.request, exc.messages[0] if exc.messages else "Erro ao enviar imagens.")
            return redirect(reverse("catalogo:checkout"))

        with transaction.atomic():
            pedido = Pedido.objects.create(
                tenant=tenant,
                cliente=contato or "Cliente",
                telefone=telefone,
                total=summary["total"],
                nome_capa=nome_capa,
                capa_url=capa_url,
                contra_capa_url=contra_capa_url,
            )

            for item in summary["items"]:
                raw_id = item.get("produto_id")
                try:
                    produto_id = int(raw_id)
                except (TypeError, ValueError):
                    produto_id = None
                ItemPedido.objects.create(
                    pedido=pedido,
                    produto_id=produto_id,
                    produto=item["nome"] or f"Produto {item['produto_id']}",
                    quantidade=item["quantidade"],
                    preco_unitario=item["preco"],
                    imagem=item.get("imagem"),
                )

        self._clear_cart()
        messages.success(
            self.request,
            "Pedido recebido! Em breve entraremos em contato para concluir a produção.",
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("catalogo:checkout")
