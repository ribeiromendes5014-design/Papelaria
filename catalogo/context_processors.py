from catalogo.services import normalize_cart


def cart_summary(request):
    cart = request.session.get("cart", {})
    summary = normalize_cart(cart)
    return {
        "cart_total_items": summary["total_items"],
        "cart_total_value": summary["total"],
        "cart_items": summary["items"],
    }
