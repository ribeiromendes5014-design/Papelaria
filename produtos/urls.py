from django.urls import path
from django.views.generic import RedirectView

from .views import CategoriaCreateView, ProdutoDeleteView, ProdutoListView, ProdutoUpdateView

app_name = "produtos"

urlpatterns = [
    path("", ProdutoListView.as_view(), name="lista"),
    path(
        "novo/",
        RedirectView.as_view(pattern_name="produtos:lista", permanent=False),
        name="novo",
    ),
    path("<int:pk>/editar/", ProdutoUpdateView.as_view(), name="editar"),
    path("<int:pk>/deletar/", ProdutoDeleteView.as_view(), name="excluir"),
    path("categorias/novo/", CategoriaCreateView.as_view(), name="categoria_nova"),
]
