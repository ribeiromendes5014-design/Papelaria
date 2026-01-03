from django.urls import path

from .views import ConfiguracaoView, FirstAccessView, PapelariaPerfilView, PerfilCatalogoView

app_name = "core"

urlpatterns = [
    path("", FirstAccessView.as_view(), name="first_access"),
    path("configuracao/", ConfiguracaoView.as_view(), name="configuracao"),
    path("configuracao/perfil/", PerfilCatalogoView.as_view(), name="perfil_catalogo"),
    path("papelaria/perfil/", PapelariaPerfilView.as_view(), name="papelaria_perfil"),
]
