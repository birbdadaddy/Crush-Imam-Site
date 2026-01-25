from django.urls import re_path
from . import consumers
from social.routing import websocket_urlpatterns as social_websocket_patterns


websocket_urlpatterns = [
    # WebSocket endpoint for anonymous random chat
    re_path(r'ws/chat/$', consumers.ChatConsumer.as_asgi()),
] + social_websocket_patterns
