from django.contrib import admin

from .models import TenantProfile


@admin.register(TenantProfile)
class TenantProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "nome_negocio", "slug", "is_active", "access_end_date")
    search_fields = ("user__username", "user__email", "nome_negocio", "slug")
    list_filter = ("is_active",)
