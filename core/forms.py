from django import forms
from django.contrib.auth.forms import AuthenticationForm

from tenants.models import TenantProfile


class TenantAuthenticationForm(AuthenticationForm):
    remember_me = forms.BooleanField(
        required=False,
        initial=True,
        label="Salva-me",
    )


class FirstAccessForm(forms.Form):
    name = forms.CharField(label="Nome do negócio", max_length=120)
    whatsapp = forms.CharField(label="WhatsApp", max_length=20)

    def save(self, tenant):
        tenant.nome_negocio = self.cleaned_data["name"]
        tenant.whatsapp = self.cleaned_data["whatsapp"]
        tenant.save()


class TenantProfileForm(forms.ModelForm):
    class Meta:
        model = TenantProfile
        fields = ["nome_negocio", "whatsapp"]
        widgets = {
            "nome_negocio": forms.TextInput(attrs={"placeholder": "Nome do seu negócio"}),
            "whatsapp": forms.TextInput(attrs={"placeholder": "WhatsApp com DDD"}),
        }
