from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("produtos", "0006_variacaocategoria"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="produto",
            index=models.Index(fields=["tenant", "ativo"], name="prod_tenant_ativo"),
        ),
        migrations.AddIndex(
            model_name="produto",
            index=models.Index(fields=["categoria"], name="prod_categoria"),
        ),
        migrations.AddIndex(
            model_name="produto",
            index=models.Index(fields=["subcategoria"], name="prod_subcategoria"),
        ),
        migrations.AddIndex(
            model_name="variacao",
            index=models.Index(fields=["produto"], name="var_produto"),
        ),
        migrations.AddIndex(
            model_name="categoria",
            index=models.Index(fields=["tenant"], name="categoria_tenant"),
        ),
        migrations.AddIndex(
            model_name="subcategoria",
            index=models.Index(fields=["tenant"], name="subcat_tenant"),
        ),
    ]
