from django.db import models


class Pedido(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pendente"),
        ("processing", "Em processamento"),
        ("finished", "Finalizado"),
    ]

    tenant = models.ForeignKey(
        "tenants.TenantProfile",
        on_delete=models.CASCADE,
        related_name="pedidos",
        null=True,
        blank=True,
    )

    cliente = models.CharField(max_length=120)
    created_on = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="pending")
    total = models.DecimalField(max_digits=10, decimal_places=2)
    telefone = models.CharField(max_length=30, blank=True)
    nome_capa = models.TextField(blank=True)
    capa = models.ImageField(upload_to="pedidos/", null=True, blank=True)
    contra_capa = models.ImageField(upload_to="pedidos/", null=True, blank=True)
    capa_url = models.URLField(blank=True, null=True)
    contra_capa_url = models.URLField(blank=True, null=True)

    class Meta:
        ordering = ["-created_on"]

    def __str__(self):
        return f"{self.cliente} ({self.created_on:%d/%m/%Y})"


class ItemPedido(models.Model):
    pedido = models.ForeignKey(Pedido, related_name="itens", on_delete=models.CASCADE)
    produto = models.CharField(max_length=120)
    produto_id = models.IntegerField(null=True, blank=True)
    imagem = models.URLField(max_length=500, null=True, blank=True)
    quantidade = models.PositiveIntegerField(default=1)
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.produto} x {self.quantidade}"
