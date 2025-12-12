from django.urls import path

from .views import PedidoDeleteView, PedidoListView, PedidoStatusUpdateView

app_name = "pedidos"

urlpatterns = [
    path("", PedidoListView.as_view(), name="lista"),
    path("status/<int:pk>/", PedidoStatusUpdateView.as_view(), name="status"),
    path("excluir/<int:pk>/", PedidoDeleteView.as_view(), name="excluir"),
]
