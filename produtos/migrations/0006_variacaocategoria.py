from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("produtos", "0005_alter_produto_options_produtoimagem"),
    ]

    operations = [
        migrations.CreateModel(
            name="VariacaoCategoria",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("nome", models.CharField(max_length=120)),
                ("max_escolhas", models.PositiveIntegerField(default=1)),
                (
                    "produto",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="categorias_variacao",
                        to="produtos.produto",
                    ),
                ),
            ],
            options={
                "ordering": ["nome"],
                "verbose_name": "Categoria de variação",
                "verbose_name_plural": "Categorias de variação",
            },
        ),
        migrations.AddField(
            model_name="variacao",
            name="categoria",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="opcoes",
                to="produtos.variacaocategoria",
            ),
        ),
    ]
