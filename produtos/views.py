from django.core.cache import cache
import logging

from django.core.exceptions import ValidationError
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import DeleteView, FormView, ListView, UpdateView

from .forms import CategoriaForm, ProdutoForm, VariacaoFormSet
from .models import Categoria, Produto, ProdutoImagem, Subcategoria, VariacaoCategoria
from .services import upload_image_to_imgbb

LOGGER = logging.getLogger(__name__)

CATEGORY_CACHE_TIMEOUT = 30
SUBCATEGORY_CACHE_TIMEOUT = 30


def _cached_categories(tenant):
    if not tenant:
        return Categoria.objects.none()
    cache_key = f"produtos:categorias:{tenant.pk}"
    categorias = cache.get(cache_key)
    if categorias is None:
        categorias = list(Categoria.objects.filter(tenant=tenant))
        cache.set(cache_key, categorias, CATEGORY_CACHE_TIMEOUT)
    return categorias


def _cached_subcategories(tenant):
    if not tenant:
        return Subcategoria.objects.none()
    cache_key = f"produtos:subcategorias:{tenant.pk}"
    subcategorias = cache.get(cache_key)
    if subcategorias is None:
        subcategorias = list(Subcategoria.objects.filter(tenant=tenant))
        cache.set(cache_key, subcategorias, SUBCATEGORY_CACHE_TIMEOUT)
    return subcategorias


class ProdutoListView(ListView):
    model = Produto
    template_name = "produtos/produto_list.html"
    context_object_name = "produtos"
    paginate_by = 15
    ordering = ["nome"]

    def _get_variacao_formset(self, data=None, instance=None):
        return VariacaoFormSet(
            data=data,
            instance=instance or Produto(),
            prefix="variacoes",
        )

    def get_queryset(self):
        tenant = getattr(self.request, "tenant", None)
        qs = super().get_queryset()
        if tenant:
            return (
                qs.filter(tenant=tenant)
                .select_related("categoria", "subcategoria")
                .prefetch_related("variacoes__categoria", "variacoes", "imagens")
            )
        return qs.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = getattr(self.request, "tenant", None)
        if tenant:
            context["categorias"] = _cached_categories(tenant)
            context["subcategorias"] = _cached_subcategories(tenant)
        else:
            context["categorias"] = Categoria.objects.none()
            context["subcategorias"] = Subcategoria.objects.none()
        if "produto_form" not in context:
            context["produto_form"] = ProdutoForm(tenant=tenant)
        if "variacao_formset" not in context:
            context["variacao_formset"] = getattr(
                self, "variacao_formset", self._get_variacao_formset()
            )
        return context

    def post(self, request, *args, **kwargs):
        tenant = getattr(request, "tenant", None)
        form = ProdutoForm(request.POST, request.FILES, tenant=tenant)
        variacao_formset = self._get_variacao_formset(request.POST)
        self.variacao_formset = variacao_formset
        if tenant:
            form.instance.tenant = tenant
        if request.FILES:
            LOGGER.warning("Received uploaded files: %s", list(request.FILES.keys()))
        if not form.is_valid():
            LOGGER.warning("ProdutoForm invalid: %s", form.errors)
        if not variacao_formset.is_valid():
            LOGGER.warning("VariacaoFormSet invalid: %s", variacao_formset.errors)
        if form.is_valid() and variacao_formset.is_valid():
            if not _handle_image_upload(form):
                if not hasattr(self, "object_list"):
                    self.object_list = self.get_queryset()
                return self.render_to_response(self.get_context_data(produto_form=form))
            produto = form.save()
            _save_variacoes(variacao_formset, produto)
            extra_files = form.cleaned_data.get("imagens_upload") or []
            LOGGER.warning("Received %s extra files for %s (create)", len(extra_files or []), produto)
            if not _save_extra_images(produto, extra_files):
                LOGGER.error("Não foi possível salvar imagens extras para %s", produto)
                form.add_error(
                    None,
                    "As imagens extras não puderam ser enviadas. Tente novamente.",
                )
                produto.delete()
            else:
                return redirect("produtos:lista")
        if not hasattr(self, "object_list"):
            self.object_list = self.get_queryset()
        return self.render_to_response(
            self.get_context_data(produto_form=form, variacao_formset=variacao_formset)
        )


def _handle_image_upload(form):
    image_file = form.cleaned_data.get("imagem_upload")
    if not image_file:
        LOGGER.warning("No image file attached for %s", form.instance)
        return True

    try:
        file_name = getattr(image_file, "name", "unknown")
        LOGGER.warning(
            "Uploading image %s (%s bytes) for %s",
            file_name,
            getattr(image_file, "size", "unknown"),
            form.instance,
        )
        form.instance.imagem = upload_image_to_imgbb(image_file)
        form.cleaned_data["imagem"] = form.instance.imagem
        LOGGER.warning("Image upload saved to %s for %s", form.instance.imagem, form.instance)
        return True
    except ValidationError as exc:
        LOGGER.error("Image upload failed: %s", exc)
        form.add_error("imagem", exc)
        return False


def _save_extra_images(instance, images):
    if not images:
        LOGGER.warning("No extra images received for %s", instance)
        return True
    for image_file in images:
        if not image_file:
            continue
        try:
            url = upload_image_to_imgbb(image_file)
            ProdutoImagem.objects.create(produto=instance, url=url)
            LOGGER.warning("Extra image uploaded for %s: %s", instance, url)
        except ValidationError as exc:
            LOGGER.error("Extra image upload failed for %s: %s", instance, exc)
            return False
    return True


def _save_variacoes(formset, produto):
    """
    Persiste variações e cria/atualiza categorias de variação com limite.
    """
    categorias_cache = {
        c.nome.lower(): c for c in VariacaoCategoria.objects.filter(produto=produto)
    }
    for form in formset.forms:
        if not getattr(form, "cleaned_data", None):
            continue
        if form.cleaned_data.get("DELETE"):
            if form.instance.pk:
                form.instance.delete()
            continue
        instance = form.save(commit=False)
        instance.produto = produto
        cat_name = (form.cleaned_data.get("categoria_nome") or "").strip()
        max_escolhas = form.cleaned_data.get("categoria_max_escolhas") or 1
        categoria_obj = None
        if cat_name:
            key = cat_name.lower()
            categoria_obj = categorias_cache.get(key)
            if not categoria_obj:
                categoria_obj = VariacaoCategoria.objects.create(
                    produto=produto,
                    nome=cat_name,
                    max_escolhas=max_escolhas,
                )
                categorias_cache[key] = categoria_obj
            else:
                if categoria_obj.max_escolhas != max_escolhas:
                    categoria_obj.max_escolhas = max_escolhas
                    categoria_obj.save(update_fields=["max_escolhas"])
        instance.categoria = categoria_obj
        instance.save()
    return True


class ProdutoUpdateView(UpdateView):
    model = Produto
    form_class = ProdutoForm
    template_name = "produtos/produto_form.html"
    success_url = reverse_lazy("produtos:lista")

    def get_queryset(self):
        tenant = getattr(self.request, "tenant", None)
        qs = super().get_queryset()
        if tenant:
            return qs.filter(tenant=tenant)
        return qs.none()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["tenant"] = getattr(self.request, "tenant", None)
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if "variacao_formset" not in context:
            context["variacao_formset"] = getattr(
                self,
                "variacao_formset",
                VariacaoFormSet(
                    instance=self.object,
                    prefix="variacoes",
                ),
            )
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = ProdutoForm(
            request.POST,
            request.FILES,
            instance=self.object,
            tenant=getattr(self.request, "tenant", None),
        )
        self.variacao_formset = VariacaoFormSet(
            request.POST,
            instance=self.object,
            prefix="variacoes",
        )
        if not form.is_valid():
            LOGGER.warning("ProdutoForm invalid (update): %s", form.errors)
        if not self.variacao_formset.is_valid():
            LOGGER.warning("VariacaoFormSet invalid (update): %s", self.variacao_formset.errors)
        LOGGER.warning("Update request.FILES keys: %s", list(request.FILES.keys()))
        if form.is_valid() and self.variacao_formset.is_valid():
            return self.form_valid(form)
        return self.form_invalid(form)

    def form_valid(self, form):
        if not _handle_image_upload(form):
            return self.form_invalid(form)
        produto = form.save()
        _save_variacoes(self.variacao_formset, produto)
        extra_files = form.cleaned_data.get("imagens_upload") or []
        LOGGER.warning("Received %s extra files for %s (update)", len(extra_files or []), produto)
        if not _save_extra_images(produto, extra_files):
            LOGGER.error("Não foi possível salvar imagens extras para %s", produto)
            form.add_error(
                None,
                "As imagens extras não puderam ser enviadas. Tente novamente.",
            )
            return self.form_invalid(form)
        self.object = produto
        return redirect(self.get_success_url())


class ProdutoDeleteView(DeleteView):
    model = Produto
    template_name = "produtos/produto_confirm_delete.html"
    success_url = reverse_lazy("produtos:lista")

    def get_queryset(self):
        tenant = getattr(self.request, "tenant", None)
        qs = super().get_queryset()
        if tenant:
            return qs.filter(tenant=tenant)
        return qs.none()

class CategoriaCreateView(FormView):
    template_name = "produtos/categoria_form.html"
    form_class = CategoriaForm
    success_url = reverse_lazy("produtos:lista")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["tenant"] = getattr(self.request, "tenant", None)
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        tipo = self.request.GET.get("tipo")
        if tipo in dict(self.form_class.TIPO_CHOICES):
            initial["tipo"] = tipo
        return initial

    def form_valid(self, form):
        tenant = getattr(self.request, "tenant", None)
        tipo = form.cleaned_data["tipo"]
        nome = form.cleaned_data["nome"]
        descricao = form.cleaned_data["descricao"]
        parent = form.cleaned_data["parent"]
        if tipo == "categoria":
            Categoria.objects.create(tenant=tenant, nome=nome, descricao=descricao)
        elif parent:
            Subcategoria.objects.create(
                categoria=parent,
                tenant=tenant,
                nome=nome,
            )
        return super().form_valid(form)
