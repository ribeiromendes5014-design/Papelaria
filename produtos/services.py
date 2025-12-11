import base64
import logging

import requests
from django.conf import settings
from django.core.exceptions import ValidationError

LOGGER = logging.getLogger(__name__)
IMGBB_UPLOAD_URL = "https://api.imgbb.com/1/upload"


def upload_image_to_imgbb(image_file):
    api_key = getattr(settings, "IMGBB_API_KEY", None)
    if not api_key:
        raise ValidationError("Chave do IMGBB não está configurada.")

    try:
        image_file.seek(0)
        payload = {
            "key": api_key,
            "image": base64.b64encode(image_file.read()).decode("ascii"),
        }

        response = requests.post(IMGBB_UPLOAD_URL, data=payload, timeout=15)
        response.raise_for_status()
        data = response.json()
        if LOGGER.isEnabledFor(logging.DEBUG):
            LOGGER.debug("IMGBB response: %s", data)

        if data.get("status") != 200 or not data.get("data"):
            raise ValidationError("Não foi possível concluir o upload da imagem.")

        url = data["data"].get("url")
        if not url:
            raise ValidationError("O serviço de imagens retornou uma resposta inválida.")

        return url
    except requests.RequestException as exc:
        LOGGER.exception("Erro ao enviar imagem para o IMGBB")
        raise ValidationError("Falha ao enviar a imagem; tente novamente mais tarde.") from exc
    except (ValueError, KeyError) as exc:
        LOGGER.exception("Resposta inválida do IMGBB")
        raise ValidationError("Resposta inesperada do serviço de imagens.") from exc
