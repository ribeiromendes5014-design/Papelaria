import base64
import io
import logging

from PIL import Image
import requests
from django.conf import settings
from django.core.exceptions import ValidationError

LOGGER = logging.getLogger(__name__)
IMGBB_UPLOAD_URL = "https://api.imgbb.com/1/upload"


def _compress_image(image_file, max_size=1600, quality=82):
    """
    Compacta a imagem para JPEG, limitando dimensoes e qualidade para economizar banda.
    Caso algo falhe, devolve os bytes originais como fallback.
    """
    try:
        image_file.seek(0)
        with Image.open(image_file) as img:
            img = img.convert("RGB")
            img.thumbnail((max_size, max_size))
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", optimize=True, quality=quality)
            buffer.seek(0)
            return buffer.read()
    except Exception:
        LOGGER.warning("Falha ao comprimir imagem; enviando original.", exc_info=True)
        image_file.seek(0)
        return image_file.read()


def upload_image_to_imgbb(image_file):
    api_key = getattr(settings, "IMGBB_API_KEY", None)
    if not api_key:
        raise ValidationError("Chave do IMGBB não está configurada.")

    try:
        image_file.seek(0)
        payload = {
            "key": api_key,
            "image": base64.b64encode(_compress_image(image_file)).decode("ascii"),
        }

        response = requests.post(IMGBB_UPLOAD_URL, data=payload, timeout=15)
        response.raise_for_status()
        data = response.json()
        if LOGGER.isEnabledFor(logging.DEBUG):
            LOGGER.debug("IMGBB response: %s", data)

        if data.get("status") != 200 or not data.get("data"):
            raise ValidationError("Não foi possível concluir o upload da imagem.")

        url = data["data"].get("url")
        if url:
            LOGGER.warning("IMGBB uploaded: %s", url)

        if not url:
            raise ValidationError("O serviço de imagens retornou uma resposta inválida.")

        return url
    except requests.RequestException as exc:
        LOGGER.exception("Erro ao enviar imagem para o IMGBB")
        raise ValidationError("Falha ao enviar a imagem; tente novamente mais tarde.") from exc
    except (ValueError, KeyError) as exc:
        LOGGER.exception("Resposta inválida do IMGBB")
        raise ValidationError("Resposta inesperada do serviço de imagens.") from exc
