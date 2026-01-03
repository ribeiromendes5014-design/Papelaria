def current_tenant(request):
    return {"tenant": getattr(request, "tenant", None)}
