from django.utils.deprecation import MiddlewareMixin

from tenants.models import TenantProfile


class TenantMiddleware(MiddlewareMixin):
    """
    Attach the tenant profile to every request. If the user is authenticated and has a
    profile we reuse it, otherwise we leave tenant unset.
    """

    def process_request(self, request):
        tenant = None
        if request.user.is_authenticated:
            tenant = getattr(request.user, "tenant_profile", None)
        request.tenant = tenant
