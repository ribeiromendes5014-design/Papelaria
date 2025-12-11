from django.contrib import admin
from django.urls import include, path

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
]
