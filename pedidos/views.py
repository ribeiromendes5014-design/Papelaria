from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views import View
from django.views.generic import ListView

from .models import Pedido


class PedidoListView(ListView):
    model = Pedido
    template_name = "pedidos/pedido_list.html"
    context_object_name = "pedidos"
    paginate_by = 10

    def get_queryset(self):
        tenant = getattr(self.request, "tenant", None)
        qs = super().get_queryset()
        self.base_queryset = qs.none()
        if tenant:
            self.base_queryset = qs.filter(tenant=tenant).order_by("-created_on")
            return self.base_queryset
        return qs.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = getattr(self.request, "tenant", None)
        if tenant:
            pedidos = Pedido.objects.filter(tenant=tenant)
            stats = []
            for value, label in Pedido.STATUS_CHOICES:
                stats.append(
                    {
                        "value": value,
                        "label": label,
                        "count": pedidos.filter(status=value).count(),
                    }
                )
            context["status_counts"] = stats
        else:
            context["status_counts"] = []
        return context


class PedidoStatusUpdateView(View):
    def post(self, request, pk):
        tenant = getattr(request, "tenant", None)
        if not tenant:
            return JsonResponse({"error": "Tenant não encontrado"}, status=403)

        pedido = get_object_or_404(Pedido, pk=pk, tenant=tenant)
        new_status = request.POST.get("status")
        valid_status = dict(Pedido.STATUS_CHOICES).keys()
        if new_status not in valid_status:
            return JsonResponse({"error": "Status inválido"}, status=400)

        pedido.status = new_status
        pedido.save(update_fields=["status"])

        return JsonResponse(
            {
                "ok": True,
                "status": pedido.status,
                "status_label": pedido.get_status_display(),
                "id": pedido.id,
            }
        )


class PedidoDeleteView(View):
    def post(self, request, pk):
        tenant = getattr(request, "tenant", None)
        if not tenant:
            return JsonResponse({"error": "Tenant não encontrado"}, status=403)

        pedido = get_object_or_404(Pedido, pk=pk, tenant=tenant)
        pedido.delete()

        return JsonResponse({"ok": True, "id": pk})
