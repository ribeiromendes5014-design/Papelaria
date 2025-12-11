from catalogo.banners import BANNER_OPTIONS


def get_default_catalog_profile():
    banner_image = BANNER_OPTIONS[0]["image"]
    return {
        "title": "Nossos Produtos",
        "message": "Explore os lançamentos com a mesma paleta vibrante do sistema e clique em um produto para ver detalhes.",
        "cta": "Ver coleção",
        "image": banner_image,
    }
