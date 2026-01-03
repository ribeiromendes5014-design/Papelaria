from django.contrib.auth import views as auth_views
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
# django imports
from django.contrib import messages
from django.utils.text import slugify
from django.views.generic import FormView

from django.views.generic import TemplateView

from catalogo.models import CatalogProfile
from catalogo.profile import get_default_catalog_profile

from .forms import FirstAccessForm, TenantAuthenticationForm, TenantProfileForm
from tenants.models import TenantProfile


class TenantLoginView(auth_views.LoginView):
    authentication_form = TenantAuthenticationForm
    template_name = "registration/login.html"
    redirect_authenticated_user = True
    success_url = reverse_lazy("core:configuracao")

    def form_valid(self, form):
        remember = form.cleaned_data.get("remember_me")
        if remember:
            self.request.session.set_expiry(60 * 60 * 24 * 30)
        else:
            self.request.session.set_expiry(0)
        self.request.session["tenant_id"] = getattr(form.get_user(), "tenant_profile", None).pk if getattr(form.get_user(), "tenant_profile", None) else None
        return super().form_valid(form)


class FirstAccessView(LoginRequiredMixin, FormView):
    template_name = "core/welcome.html"
    form_class = FirstAccessForm
    success_url = reverse_lazy("pedidos:lista")

    def dispatch(self, request, *args, **kwargs):
        tenant = getattr(request, "tenant", None)
        if tenant and tenant.nome_negocio and tenant.whatsapp:
            return redirect(self.success_url)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        tenant = getattr(self.request, "tenant", None)
        if tenant:
            form.save(tenant)
        return super().form_valid(form)


class ConfiguracaoView(LoginRequiredMixin, TemplateView):
    template_name = "core/configuracao.html"


class PerfilCatalogoView(LoginRequiredMixin, TemplateView):
    template_name = "core/perfil_catalogo.html"

    def _get_catalog_profile(self, tenant):
        if not tenant:
            return None
        return CatalogProfile.objects.filter(tenant=tenant).first()

    def _build_profile_data(self, tenant):
        profile_data = get_default_catalog_profile()
        profile = self._get_catalog_profile(tenant)
        if not profile:
            return profile_data
        if profile.title:
            profile_data["title"] = profile.title
        if profile.message:
            profile_data["message"] = profile.message
        if profile.cta:
            profile_data["cta"] = profile.cta
        if profile.desktop_image:
            profile_data["desktop_image"] = profile.desktop_image
            profile_data["image"] = profile.desktop_image
        elif profile.image:
            profile_data["desktop_image"] = profile.image
            profile_data["image"] = profile.image
        if profile.mobile_image:
            profile_data["mobile_image"] = profile.mobile_image
        elif profile.desktop_image:
            profile_data["mobile_image"] = profile.desktop_image
        elif profile.image:
            profile_data["mobile_image"] = profile.image
        return profile_data

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = getattr(self.request, "tenant", None)
        error = self.request.session.pop("catalog_profile_error", None)
        if error:
            context["profile_error"] = error
        context["profile_data"] = self._build_profile_data(tenant)
        return context

    def post(self, request, *args, **kwargs):
        tenant = getattr(request, "tenant", None)
        if not tenant:
            return redirect("core:configuracao")

        profile = self._get_catalog_profile(tenant)
        if not profile:
            profile = CatalogProfile(tenant=tenant)

        profile.title = request.POST.get("title", profile.title)
        profile.message = request.POST.get("message", profile.message)
        profile.cta = request.POST.get("cta", profile.cta)
        desktop_file = request.FILES.get("banner_desktop")
        mobile_file = request.FILES.get("banner_mobile")
        uploader = None
        if desktop_file or mobile_file:
            from produtos.services import upload_image_to_imgbb

            uploader = upload_image_to_imgbb

        if desktop_file and uploader:
            try:
                profile.desktop_image = uploader(desktop_file)
                profile.image = profile.desktop_image
            except Exception:
                request.session["catalog_profile_error"] = "Não foi possível enviar a imagem agora."
                request.session.modified = True
        if mobile_file and uploader:
            try:
                profile.mobile_image = uploader(mobile_file)
            except Exception:
                request.session["catalog_profile_error"] = "Não foi possível enviar a imagem agora."
                request.session.modified = True

        profile.save()
        return redirect("core:perfil_catalogo")


class PapelariaPerfilView(LoginRequiredMixin, FormView):
    template_name = "core/papelaria_perfil.html"
    form_class = TenantProfileForm
    tenant_selector_param = "tenant"

    def _resolve_target_tenant(self):
        if hasattr(self, "_resolved_tenant"):
            return self._resolved_tenant
        identifier = (
            self.request.POST.get(self.tenant_selector_param)
            or self.request.GET.get(self.tenant_selector_param)
        )
        tenant = None
        if self.request.user.is_superuser:
            if identifier:
                tenant = self._lookup_tenant(identifier)
            options = self._tenant_options
            if not tenant and options.count() == 1:
                tenant = options.first()
        if not tenant:
            tenant = getattr(self.request, "tenant", None) or getattr(
                self.request.user, "tenant_profile", None
            )
        self._resolved_tenant = tenant
        return tenant

    def _lookup_tenant(self, identifier):
        if not identifier:
            return None
        if identifier.isdigit():
            return TenantProfile.objects.filter(pk=int(identifier)).first()
        return TenantProfile.objects.filter(slug=identifier).first()

    def _generate_slug(self, name, pk):
        base = slugify(name or "")
        if not base:
            base = f"tenant-{pk}"
        candidate = base
        counter = 1
        while TenantProfile.objects.filter(slug=candidate).exclude(pk=pk).exists():
            candidate = f"{base}-{counter}"
            counter += 1
        return candidate
    @property
    def _tenant_options(self):
        if not self.request.user.is_superuser:
            return TenantProfile.objects.none()
        if not hasattr(self, "_tenant_options_qs"):
            self._tenant_options_qs = TenantProfile.objects.select_related("user").all()
        return self._tenant_options_qs

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        tenant = self._resolve_target_tenant()
        if not tenant:
            return kwargs
        kwargs["instance"] = tenant
        return kwargs

    def form_valid(self, form):
        tenant = self._resolve_target_tenant()
        if not tenant:
            messages.error(self.request, "Perfil indisponível sem tenant definido.")
            return redirect("core:configuracao")
        form.instance = tenant
        tenant_instance = form.save(commit=False)
        tenant_instance.slug = self._generate_slug(tenant_instance.nome_negocio, tenant.pk)
        tenant_instance.save()
        tenant = tenant_instance
        tenant.refresh_from_db()
        self.request.tenant = tenant
        self._resolved_tenant = tenant
        messages.success(self.request, "Perfil atualizado com sucesso.")
        identifier = tenant.slug or tenant.pk
        success_url = self.get_success_url()
        return redirect(f"{success_url}?tenant={identifier}")

    def get_success_url(self):
        return reverse("core:papelaria_perfil")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tenant_selector_options"] = self._tenant_options
        tenant = self._resolve_target_tenant()
        context["selected_tenant"] = tenant
        if not tenant:
            return context
        tenant = TenantProfile.objects.select_related("user").get(pk=tenant.pk)
        context["tenant_name"] = tenant.nome_negocio or tenant.user.get_full_name() or tenant.user.username
        context["tenant_whatsapp"] = tenant.whatsapp
        identifier = tenant.slug or tenant.pk
        context["catalog_url"] = self.request.build_absolute_uri(
            reverse("catalogo:publico", kwargs={"tenant_identifier": identifier})
        )
        return context
