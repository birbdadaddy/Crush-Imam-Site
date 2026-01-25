"""
Django Channels routing configuration for WebSocket endpoints
"""
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/notifications/$', consumers.NotificationConsumer.as_asgi()),
    re_path(r'ws/chat/(?P<conversation_id>[a-f0-9-]+)/$', consumers.ChatConsumer.as_asgi()),
    re_path(r'ws/feed/$', consumers.FeedConsumer.as_asgi()),
]
