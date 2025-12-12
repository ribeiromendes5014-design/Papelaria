from decimal import Decimal


def normalize_cart(session_cart):
    total = Decimal("0")
    items = []
    total_items = 0

    for item_key, payload in session_cart.items():
        quantidade = payload.get("quantidade", 0)
        preco = Decimal(str(payload.get("preco", "0")))
        total += preco * quantidade
        total_items += quantidade
        base_nome = payload.get("nome")
        variacao_label = payload.get("variacao_label") or payload.get("variacao")
        variacoes_labels = payload.get("variacoes_labels") or []
        nome_exibicao = base_nome
        label_composta = variacao_label
        if not label_composta and variacoes_labels:
            label_composta = ", ".join([str(v) for v in variacoes_labels if v])
        if base_nome and label_composta:
            nome_exibicao = f"{base_nome} - {label_composta}"
        items.append(
            {
                "produto_id": payload.get("produto_id") or item_key,
                "item_key": item_key,
                "nome": nome_exibicao,
                "quantidade": quantidade,
                "preco": preco,
                "imagem": payload.get("imagem"),
                "variacao_label": label_composta,
                "variacao_id": payload.get("variacao_id"),
                "variacoes_labels": variacoes_labels,
            }
        )

    return {
        "items": items,
        "total": total,
        "total_items": total_items,
    }


def serialize_cart(summary):
    return {
        "items": [
            {
                "produto_id": item["produto_id"],
                "item_key": item.get("item_key") or item["produto_id"],
                "nome": item["nome"],
                "quantidade": item["quantidade"],
                "preco": str(item["preco"]),
                "imagem": item["imagem"],
                "variacao_label": item.get("variacao_label"),
                "variacao_id": item.get("variacao_id"),
            }
            for item in summary["items"]
        ],
        "total_items": summary["total_items"],
        "total": str(summary["total"]),
    }
