"""
ASGI config for dashboard project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

import os
# from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
# from channels.routing import ProtocolTypeRouter, URLRouter

import megacellcnc

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dashboard.settings')

# application = ProtocolTypeRouter(
#     {
#         "http": get_asgi_application(),
#         "websocket": AuthMiddlewareStack(
#             URLRouter(
#                 megacellcnc.routing.websocket_urlpatterns
#             )
#         ),
#     }
# )