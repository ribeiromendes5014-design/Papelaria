from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pedidos", "0002_pedido_tenant"),
    ]

    operations = [
        migrations.AddField(
            model_name="pedido",
            name="capa",
            field=models.ImageField(blank=True, null=True, upload_to="pedidos/"),
        ),
        migrations.AddField(
            model_name="pedido",
            name="contra_capa",
            field=models.ImageField(blank=True, null=True, upload_to="pedidos/"),
        ),
        migrations.AddField(
            model_name="pedido",
            name="nome_capa",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="pedido",
            name="telefone",
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AddField(
            model_name="itempedido",
            name="imagem",
            field=models.URLField(blank=True, max_length=500, null=True),
        ),
        migrations.AddField(
            model_name="itempedido",
            name="produto_id",
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
