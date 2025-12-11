from django.urls import path

from .views import (
    AdicionarAoCarrinhoView,
    AtualizarCarrinhoView,
    CarrinhoView,
    CatalogoHomeView,
    CheckoutView,
    ProdutoDetailView,
)

app_name = "catalogo"

urlpatterns = [
    path("", CatalogoHomeView.as_view(), name="home"),
    path("produto/<int:pk>/", ProdutoDetailView.as_view(), name="produto"),
    path("carrinho/", CarrinhoView.as_view(), name="carrinho"),
    path(
        "carrinho/adicionar/<int:pk>/",
        AdicionarAoCarrinhoView.as_view(),
        name="carrinho_adicionar",
    ),
    path(
        "carrinho/item/<str:pk>/atualizar/",
        AtualizarCarrinhoView.as_view(),
        name="carrinho_atualizar",
    ),
    path("checkout/", CheckoutView.as_view(), name="checkout"),
    path("<slug:tenant_identifier>/", CatalogoHomeView.as_view(), name="publico"),
]
