from django.conf import settings
from django.db import models
from django.utils import timezone


class TenantProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tenant_profile",
    )
    nome_negocio = models.CharField("Nome do negócio", max_length=120, blank=True)
    slug = models.SlugField(
        "Slug público",
        max_length=80,
        unique=True,
        help_text="Usado na URL pública da papelaria.",
        null=True,
        blank=True,
    )
    whatsapp = models.CharField("WhatsApp", max_length=30, blank=True)
    access_end_date = models.DateField("Expiração da assinatura", null=True, blank=True)
    is_active = models.BooleanField("Conta ativa", default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Perfil de papelaria"
        verbose_name_plural = "Perfis de papelaria"
        ordering = ["-created_at"]

    def __str__(self):
        return self.nome_negocio or self.user.get_full_name() or self.user.username

    @property
    def active(self):
        if self.access_end_date and self.access_end_date < timezone.now().date():
            return False
        return self.is_active
