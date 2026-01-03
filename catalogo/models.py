from django.db import models

from tenants.models import TenantProfile


class CatalogProfile(models.Model):
    tenant = models.OneToOneField(
        TenantProfile,
        on_delete=models.CASCADE,
        related_name="catalog_profile",
    )
    title = models.CharField(max_length=120, blank=True)
    message = models.TextField(blank=True)
    cta = models.CharField(max_length=80, blank=True)
    image = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Perfil do catálogo"
        verbose_name_plural = "Perfis do catálogo"

    def __str__(self):
        return self.title or f"Perfil de catálogo de {self.tenant}"
