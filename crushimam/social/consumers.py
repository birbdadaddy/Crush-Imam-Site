"""
Django Channels consumers for real-time features: Messaging, Notifications, Typing Indicators
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone


class NotificationConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time notifications"""

    async def connect(self):
        """Handle WebSocket connection"""
        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            await self.close()
            return

        # Create a notification room for each user
        self.notification_group_name = f"notifications_{self.user.id}"
        await self.channel_layer.group_add(
            self.notification_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        if hasattr(self, 'notification_group_name'):
            await self.channel_layer.group_discard(
                self.notification_group_name,
                self.channel_name
            )

    async def send_notification(self, event):
        """Send notification to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'notification_id': event['notification_id'],
            'notification_type': event['notification_type'],
            'actor': event['actor'],
            'text': event['text'],
            'timestamp': event['timestamp'],
            'read': event.get('read', False),
        }))


class ChatConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for direct messaging and typing indicators"""

    async def connect(self):
        """Handle WebSocket connection for chat"""
        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            await self.close()
            return

        # Extract conversation ID from URL route
        self.conversation_id = self.scope['url_route']['kwargs'].get('conversation_id')
        if not self.conversation_id:
            await self.close()
            return

        # Verify user is part of this conversation
        is_participant = await self.verify_conversation_participant()
        if not is_participant:
            await self.close()
            return

        self.chat_group_name = f"chat_{self.conversation_id}"
        await self.channel_layer.group_add(
            self.chat_group_name,
            self.channel_name
        )
        await self.accept()

        # Notify that user is online
        await self.channel_layer.group_send(
            self.chat_group_name,
            {
                'type': 'user_status',
                'user_id': self.user.id,
                'username': self.user.username,
                'status': 'online'
            }
        )

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection from chat"""
        if hasattr(self, 'chat_group_name'):
            # Notify user is offline
            await self.channel_layer.group_send(
                self.chat_group_name,
                {
                    'type': 'user_status',
                    'user_id': self.user.id,
                    'username': self.user.username,
                    'status': 'offline'
                }
            )
            await self.channel_layer.group_discard(
                self.chat_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')

            if message_type == 'message':
                await self.handle_message(data)
            elif message_type == 'typing':
                await self.handle_typing(data)
            elif message_type == 'read_receipt':
                await self.handle_read_receipt(data)
        except json.JSONDecodeError:
            pass

    async def handle_message(self, data):
        """Handle incoming chat message"""
        text = data.get('text', '').strip()
        if not text:
            return

        # Save message to database
        message = await self.save_message(text)
        if message:
            await self.channel_layer.group_send(
                self.chat_group_name,
                {
                    'type': 'chat_message',
                    'message_id': str(message['id']),
                    'sender_id': message['sender_id'],
                    'sender_username': message['sender_username'],
                    'text': message['text'],
                    'timestamp': message['timestamp'],
                    'is_read': message['is_read'],
                }
            )

    async def handle_typing(self, data):
        """Handle typing indicator"""
        is_typing = data.get('is_typing', False)
        await self.channel_layer.group_send(
            self.chat_group_name,
            {
                'type': 'user_typing',
                'user_id': self.user.id,
                'username': self.user.username,
                'is_typing': is_typing
            }
        )

    async def handle_read_receipt(self, data):
        """Handle message read receipt"""
        message_id = data.get('message_id')
        await self.mark_message_as_read(message_id)
        await self.channel_layer.group_send(
            self.chat_group_name,
            {
                'type': 'message_read',
                'message_id': message_id,
                'user_id': self.user.id,
            }
        )

    async def chat_message(self, event):
        """Send chat message to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message_id': event['message_id'],
            'sender_id': event['sender_id'],
            'sender_username': event['sender_username'],
            'text': event['text'],
            'timestamp': event['timestamp'],
            'is_read': event['is_read'],
        }))

    async def user_typing(self, event):
        """Send typing indicator to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'user_id': event['user_id'],
            'username': event['username'],
            'is_typing': event['is_typing']
        }))

    async def user_status(self, event):
        """Send user status (online/offline) to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'status',
            'user_id': event['user_id'],
            'username': event['username'],
            'status': event['status']
        }))

    async def message_read(self, event):
        """Send message read status to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'read_receipt',
            'message_id': event['message_id'],
            'user_id': event['user_id']
        }))

    @database_sync_to_async
    def verify_conversation_participant(self):
        """Verify user is part of this conversation"""
        from .models import Conversation
        try:
            conversation = Conversation.objects.get(id=self.conversation_id)
            return conversation.participants.filter(id=self.user.id).exists()
        except Conversation.DoesNotExist:
            return False

    @database_sync_to_async
    def save_message(self, text):
        """Save message to database"""
        try:
            from .models import DirectMessage, Conversation
            conversation = Conversation.objects.get(id=self.conversation_id)

            # Get recipient (other participant)
            recipient = conversation.participants.exclude(id=self.user.id).first()
            if not recipient:
                return None

            message = DirectMessage.objects.create(
                sender=self.user,
                recipient=recipient,
                text=text,
                message_type='text'
            )

            # Update conversation's last_message
            conversation.last_message = message
            conversation.save(update_fields=['last_message', 'updated_at'])

            return {
                'id': message.id,
                'sender_id': message.sender.id,
                'sender_username': message.sender.username,
                'text': message.text,
                'timestamp': message.created_at.isoformat(),
                'is_read': message.is_read,
            }
        except Exception as e:
            print(f"Error saving message: {e}")
            return None

    @database_sync_to_async
    def mark_message_as_read(self, message_id):
        """Mark message as read"""
        from .models import DirectMessage
        try:
            message = DirectMessage.objects.get(id=message_id)
            if message.recipient == self.user and not message.is_read:
                message.is_read = True
                message.read_at = timezone.now()
                message.save(update_fields=['is_read', 'read_at'])
        except DirectMessage.DoesNotExist:
            pass


class FeedConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time feed updates (new posts, likes, comments)"""

    async def connect(self):
        """Handle WebSocket connection for feed"""
        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            await self.close()
            return

        self.feed_group_name = f"feed_{self.user.id}"
        await self.channel_layer.group_add(
            self.feed_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection from feed"""
        if hasattr(self, 'feed_group_name'):
            await self.channel_layer.group_discard(
                self.feed_group_name,
                self.channel_name
            )

    async def feed_update(self, event):
        """Send feed update to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'update',
            'event_type': event['event_type'],
            'post_id': event.get('post_id'),
            'action': event.get('action'),
            'timestamp': event.get('timestamp'),
        }))
