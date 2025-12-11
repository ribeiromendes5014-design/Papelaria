from django import forms
from django.forms import inlineformset_factory

from .models import Categoria, Produto, Subcategoria, Variacao, VariacaoCategoria



class MultiFileInput(forms.FileInput):
    allow_multiple_selected = True

class CategoriaForm(forms.Form):
    TIPO_CHOICES = (
        ("categoria", "Categoria pai"),
        ("subcategoria", "Subcategoria"),
    )

    nome = forms.CharField(max_length=120)
    descricao = forms.CharField(widget=forms.Textarea, required=False)
    tipo = forms.ChoiceField(
        choices=TIPO_CHOICES,
        initial="categoria",
        widget=forms.RadioSelect(attrs={"class": "tipo-radio"}),
    )
    parent = forms.ModelChoiceField(queryset=Categoria.objects.none(), required=False)

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields["parent"].queryset = Categoria.objects.filter(tenant=tenant)

class ProdutoForm(forms.ModelForm):
    imagem_upload = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(attrs={"class": "form-input"}),
        help_text="Envie JPG/PNG até 5 MB para manter a paleta do site.",
    )
    imagens_upload = forms.FileField(
        required=False,
        widget=MultiFileInput(attrs={"class": "form-input", "multiple": True}),
    help_text="Envie quantas fotos extras desejar para o produto.",
    )

    class Meta:
        model = Produto
        fields = [
            "nome",
            "descricao",
            "preco",
            "estoque",
            "ativo",
            "categoria",
            "subcategoria",
        ]
        widgets = {
            "nome": forms.TextInput(
                attrs={"placeholder": "Agenda 2026", "class": "form-input"}
            ),
            "descricao": forms.Textarea(
                attrs={
                    "placeholder": "Descrição breve do produto",
                    "rows": 4,
                    "class": "form-input",
                }
            ),
            "preco": forms.NumberInput(
                attrs={"placeholder": "75,00", "step": "0.01", "class": "form-input"}
            ),
            "estoque": forms.NumberInput(
                attrs={"placeholder": "100", "class": "form-input"}
            ),
            "ativo": forms.CheckboxInput(attrs={"class": "form-checkbox"}),
            "categoria": forms.Select(attrs={"class": "form-input"}),
            "subcategoria": forms.Select(attrs={"class": "form-input"}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields["categoria"].queryset = Categoria.objects.filter(tenant=tenant)
            self.fields["subcategoria"].queryset = Subcategoria.objects.filter(
                tenant=tenant
            )


class VariacaoForm(forms.ModelForm):
    categoria_nome = forms.CharField(
        required=False,
        label="Categoria",
        widget=forms.TextInput(attrs={"placeholder": "Ex: Tamanho ou Cor", "class": "form-input"}),
    )
    categoria_max_escolhas = forms.IntegerField(
        required=False,
        min_value=1,
        label="Limite por categoria",
        widget=forms.NumberInput(
            attrs={"placeholder": "1", "class": "form-input", "style": "width:120px;"}
        ),
    )

    class Meta:
        model = Variacao
        fields = ["nome", "tamanho", "preco_adicional"]
        widgets = {
            "nome": forms.TextInput(
                attrs={"placeholder": "Tamanho P / Azul / 500ml", "class": "form-input"}
            ),
            "tamanho": forms.TextInput(
                attrs={"placeholder": "Opcional: P, M, G", "class": "form-input"}
            ),
            "preco_adicional": forms.NumberInput(
                attrs={
                    "placeholder": "0,00",
                    "step": "0.01",
                    "class": "form-input",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        categoria = getattr(self.instance, "categoria", None)
        if categoria:
            self.fields["categoria_nome"].initial = categoria.nome
            self.fields["categoria_max_escolhas"].initial = categoria.max_escolhas

    def clean(self):
        cleaned = super().clean()
        cat_name = (cleaned.get("categoria_nome") or "").strip()
        if cat_name and not cleaned.get("categoria_max_escolhas"):
            cleaned["categoria_max_escolhas"] = 1
        return cleaned

VariacaoFormSet = inlineformset_factory(
    Produto,
    Variacao,
    form=VariacaoForm,
    fields=["nome", "tamanho", "preco_adicional"],
    extra=1,
    can_delete=True,
    validate_min=False,
    min_num=0,
)
