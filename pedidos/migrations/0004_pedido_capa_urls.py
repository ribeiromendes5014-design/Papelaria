from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pedidos", "0003_add_checkout_media_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="pedido",
            name="capa_url",
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="pedido",
            name="contra_capa_url",
            field=models.URLField(blank=True, null=True),
        ),
    ]
