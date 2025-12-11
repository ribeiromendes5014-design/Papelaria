from django import forms


class CheckoutForm(forms.Form):
    nome = forms.CharField(
        label="Nome completo",
        max_length=120,
        widget=forms.TextInput(attrs={"placeholder": "Nome do solicitante", "class": "form-input"}),
    )
    telefone = forms.CharField(
        label="Telefone ou WhatsApp",
        max_length=30,
        widget=forms.TextInput(attrs={"placeholder": "(11) 99999-1234", "class": "form-input"}),
    )
    capa = forms.ImageField(
        label="Upload da capa",
        required=False,
        widget=forms.ClearableFileInput(attrs={"accept": "image/*", "class": "form-input"}),
    )
    contra_capa = forms.ImageField(
        label="Upload da contra capa",
        required=False,
        widget=forms.ClearableFileInput(attrs={"accept": "image/*", "class": "form-input"}),
    )
    nome_capa = forms.CharField(
        label="Nome ou frase na capa",
        required=False,
        widget=forms.Textarea(
            attrs={
                "rows": 3,
                "placeholder": "Ex: Meu porto seguro",
                "class": "form-input",
            }
        ),
    )
