from django.contrib import admin
from django.urls import include, path, re_path
from django.views.decorators.cache import never_cache
from django.views.generic import TemplateView

from core.views import FirstAccessView, TenantLoginView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("accounts/profile/", FirstAccessView.as_view(), name="profile"),
    path("login/", TenantLoginView.as_view(), name="login"),
    path("pedidos/", include(("pedidos.urls", "pedidos"), namespace="pedidos")),
    path("produtos/", include(("produtos.urls", "produtos"), namespace="produtos")),
    path("catalogo/", include(("catalogo.urls", "catalogo"), namespace="catalogo")),
    path("", include(("core.urls", "core"), namespace="core")),
    re_path(
        r"^service-worker\.js$",
        never_cache(
            TemplateView.as_view(
                template_name="service-worker.js",
                content_type="application/javascript",
            )
        ),
        name="service-worker",
    ),
]
