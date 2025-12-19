from django.urls import path
from . import consumers


websocket_urlpatterns = [
    # WebSocket endpoint for anonymous random chat
    path('ws/chat/', consumers.ChatConsumer.as_asgi()),
]
