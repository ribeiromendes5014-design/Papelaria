from django.db import models
from django.urls import reverse


class Categoria(models.Model):
    nome = models.CharField(max_length=120)
    descricao = models.TextField(blank=True)
    tenant = models.ForeignKey(
        "tenants.TenantProfile",
        on_delete=models.CASCADE,
        related_name="categorias",
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.nome


class Produto(models.Model):
    tenant = models.ForeignKey(
        "tenants.TenantProfile",
        on_delete=models.CASCADE,
        related_name="produtos",
        null=True,
        blank=True,
    )
    nome = models.CharField(max_length=120)
    descricao = models.TextField(blank=True)
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    estoque = models.PositiveIntegerField(default=0)
    imagem = models.URLField(max_length=500, blank=True, null=True)
    ativo = models.BooleanField(default=True)
    categoria = models.ForeignKey(
        Categoria, related_name="produtos", on_delete=models.SET_NULL, null=True, blank=True
    )
    subcategoria = models.ForeignKey(
        "Subcategoria",
        related_name="produtos",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.nome

    class Meta:
        ordering = ["nome"]

    def get_cached_image_url(self):
        if not self.imagem:
            return ""
        return reverse("catalogo:produto_imagem_principal", args=[self.pk])

    def get_gallery_cached_urls(self):
        urls = []
        main_url = self.get_cached_image_url()
        if main_url:
            urls.append(main_url)
        for foto in self.imagens.all():
            cached = foto.get_cached_image_url()
            if cached:
                urls.append(cached)
        return urls

class ProdutoImagem(models.Model):
    produto = models.ForeignKey(
        Produto, on_delete=models.CASCADE, related_name="imagens"
    )
    url = models.URLField(max_length=500)
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Imagem de {self.produto}"

    class Meta:
        ordering = ["-criado_em"]

    def get_cached_image_url(self):
        return reverse("catalogo:produto_imagem_extra", args=[self.pk])

class Subcategoria(models.Model):
    categoria = models.ForeignKey(
        Categoria, on_delete=models.CASCADE, related_name="subcategorias"
    )
    nome = models.CharField(max_length=120)
    tenant = models.ForeignKey(
        "tenants.TenantProfile",
        on_delete=models.CASCADE,
        related_name="subcategorias",
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"{self.categoria.nome} / {self.nome}"


class Variacao(models.Model):
    produto = models.ForeignKey(
        Produto, on_delete=models.CASCADE, related_name="variacoes"
    )
    categoria = models.ForeignKey(
        "VariacaoCategoria",
        on_delete=models.SET_NULL,
        related_name="opcoes",
        null=True,
        blank=True,
    )
    nome = models.CharField(max_length=120)
    tamanho = models.CharField(max_length=60, blank=True)
    preco_adicional = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )

    def __str__(self):
        return f"{self.nome} ({self.tamanho})"


class VariacaoCategoria(models.Model):
    produto = models.ForeignKey(
        Produto, on_delete=models.CASCADE, related_name="categorias_variacao"
    )
    nome = models.CharField(max_length=120)
    max_escolhas = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = "Categoria de variação"
        verbose_name_plural = "Categorias de variação"
        ordering = ["nome"]

    def __str__(self):
        return f"{self.nome} (máx {self.max_escolhas})"
