"""
QZ Tray: öffentliches Zertifikat + SHA512-Signatur (Private Key nur serverseitig).
Nur für localhost / geschlossenes Setup gedacht.
"""
import base64
from pathlib import Path

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotAllowed
from django.views.decorators.csrf import csrf_exempt


def _paths():
    base = Path(settings.BASE_DIR) / 'certificate'
    return base / 'qz-tray-public.pem', base / 'qz-tray-private.pem'


def qz_certificate(request):
    """Liefert das PEM-Zertifikat für setCertificatePromise (text/plain)."""
    pub, _ = _paths()
    if not pub.is_file():
        return HttpResponse(
            'QZ-Zertifikat fehlt (certificate/qz-tray-public.pem).',
            status=503,
            content_type='text/plain; charset=utf-8',
        )
    return HttpResponse(
        pub.read_text(encoding='utf-8'),
        content_type='text/plain; charset=utf-8',
    )


@csrf_exempt
def qz_sign(request):
    """
    Signiert den von QZ Tray übergebenen String (SHA512, RSA PKCS#1 v1.5).
    POST: application/x-www-form-urlencoded, Feld 'request'.
    """
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    to_sign = request.POST.get('request')
    if not to_sign:
        return HttpResponseBadRequest('Missing "request" in POST body.')

    _, priv = _paths()
    if not priv.is_file():
        return HttpResponse(
            'QZ Private Key fehlt (certificate/qz-tray-private.pem).',
            status=503,
            content_type='text/plain; charset=utf-8',
        )

    try:
        pem = priv.read_bytes()
        private_key = serialization.load_pem_private_key(
            pem, password=None, backend=default_backend()
        )
        signature = private_key.sign(
            to_sign.encode('utf-8'),
            padding.PKCS1v15(),
            hashes.SHA512(),
        )
    except Exception as exc:
        return HttpResponse(
            f'Signatur fehlgeschlagen: {exc}',
            status=500,
            content_type='text/plain; charset=utf-8',
        )

    b64 = base64.b64encode(signature).decode('ascii')
    return HttpResponse(b64, content_type='text/plain; charset=utf-8')
