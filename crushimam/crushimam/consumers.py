import asyncio
import random
import uuid
import base64
import os

from channels.generic.websocket import AsyncJsonWebsocketConsumer
from asgiref.sync import sync_to_async
from django.core.files.base import ContentFile
from django.utils.dateparse import parse_datetime
from django.utils import timezone


# Simple in-memory matchmaking structures (development only)
# - waiting: list of channel_names waiting to be paired
# - channel_to_room: mapping channel_name -> room_name
# - rooms: mapping room_name -> [channel_name_a, channel_name_b]
waiting = []
waiting_lock = asyncio.Lock()
channel_to_room = {}
rooms = {}
channel_to_user = {}


class ChatConsumer(AsyncJsonWebsocketConsumer):
    """WebSocket consumer handling matchmaking and WebRTC signaling.

    Flow:
    - Client sends `find` action to enter the waiting queue.
    - If another user is waiting, server pairs them into a unique room and
      notifies both with `matched` (includes `initiator` boolean).
    - Signaling messages (`offer`, `answer`, `ice`) are sent with action
      `signal` and forwarded to the partner using channel layer group_send.
    - Text chat messages use action `chat` and are broadcast to the room.
    - `next` disconnects both peers in the room (partner receives
      `partner_left`) and the clients may start searching again.
    - On disconnect the consumer removes the user from waiting or notifies
      the partner and cleans up room state.
    """

    async def connect(self):
        await self.accept()
        self.room_name = None
        # record authenticated username for this channel if available
        try:
            user = self.scope.get('user')
            if user and getattr(user, 'is_authenticated', False):
                channel_to_user[self.channel_name] = getattr(user, 'username', None)
        except Exception:
            pass

    async def disconnect(self, code):
        # Remove from waiting if present
        async with waiting_lock:
            if self.channel_name in waiting:
                try:
                    waiting.remove(self.channel_name)
                except ValueError:
                    pass

        # If in a room, notify partner and clean up
        room = channel_to_room.get(self.channel_name)
        if room:
            peers = rooms.get(room, [])
            for ch in peers:
                if ch != self.channel_name:
                    # notify partner that this user disconnected
                    await self.channel_layer.send(ch, {
                        'type': 'chat.partner_left',
                    })
            # cleanup
            for ch in peers:
                channel_to_room.pop(ch, None)
            rooms.pop(room, None)
            try:
                await self.channel_layer.group_discard(room, self.channel_name)
            except Exception:
                pass
        # remove from channel->user map
        try:
            channel_to_user.pop(self.channel_name, None)
        except Exception:
            pass

    async def receive_json(self, content, **kwargs):
        action = content.get('action')

        if action == 'find':
            # Try to match with a waiting user; otherwise enqueue
            async with waiting_lock:
                # remove duplicates
                if self.channel_name in waiting:
                    await self.send_json({'action': 'waiting'})
                    return

                if waiting:
                    # pick a random waiting partner
                    idx = random.randrange(len(waiting))
                    partner = waiting.pop(idx)
                    room = 'room_' + uuid.uuid4().hex
                    rooms[room] = [partner, self.channel_name]
                    channel_to_room[partner] = room
                    channel_to_room[self.channel_name] = room

                    # add both channels to the group so we can broadcast
                    await self.channel_layer.group_add(room, partner)
                    await self.channel_layer.group_add(room, self.channel_name)

                    # randomly choose an initiator for SDP offer
                    initiator_for_self = bool(random.getrandbits(1))

                    # notify both peers individually (so we can set different initiator flags)
                    await self.channel_layer.send(partner, {
                        'type': 'chat.matched',
                        'room': room,
                        'initiator': not initiator_for_self,
                    })
                    await self.channel_layer.send(self.channel_name, {
                        'type': 'chat.matched',
                        'room': room,
                        'initiator': initiator_for_self,
                    })
                else:
                    waiting.append(self.channel_name)
                    await self.send_json({'action': 'waiting'})

        elif action == 'signal':
            # Forward signaling payloads (offer/answer/ice) to room peers
            data = content.get('data')
            room = channel_to_room.get(self.channel_name)
            if room:
                await self.channel_layer.group_send(room, {
                    'type': 'chat.signal',
                    'sender': self.channel_name,
                    'data': data,
                })

        elif action == 'chat':
            # Text chat message — broadcast to the room
            message = content.get('message')
            room = channel_to_room.get(self.channel_name)
            if room and message:
                await self.channel_layer.group_send(room, {
                    'type': 'chat.message',
                    'sender': self.channel_name,
                    'message': message,
                })

        elif action == 'next':
            # User wants to skip and find a new partner: notify partner and cleanup
            room = channel_to_room.get(self.channel_name)
            if room:
                peers = rooms.get(room, [])
                for ch in peers:
                    if ch != self.channel_name:
                        await self.channel_layer.send(ch, {'type': 'chat.partner_left'})
                # cleanup room state
                for ch in peers:
                    channel_to_room.pop(ch, None)
                rooms.pop(room, None)
                try:
                    await self.channel_layer.group_discard(room, self.channel_name)
                except Exception:
                    pass

        elif action == 'report':
            from confessions.models import Report
            # Handle incoming report payload: contains base64 images and metadata
            if Report is None:
                # reports app not available
                await self.send_json({'action': 'report_result', 'status': 'error', 'message': 'reports not configured'})
                return

            local_b64 = content.get('local_image')
            remote_b64 = content.get('remote_image')
            room_name = content.get('room')
            ts = content.get('timestamp')
            # prefer server-side mapping of channel->user if client did not provide
            reporter_username = content.get('reporter') or channel_to_user.get(self.channel_name)
            reported_username = content.get('reported_user')
            # if reported not provided try to infer from room peers
            if not reported_username and room_name:
                peers = rooms.get(room_name, [])
                for ch in peers:
                    if ch != self.channel_name:
                        reported_username = channel_to_user.get(ch)
                        break

            # parse timestamp if provided
            dt = parse_datetime(ts) if ts else None
            if dt is None:
                dt = timezone.now()

            # synchronous save helper
            @sync_to_async
            def _save_report():
                rpt = Report(room=room_name, timestamp=dt)
                # attach reporter/reported if usernames provided
                try:
                    from django.contrib.auth import get_user_model
                    User = get_user_model()
                    if reporter_username:
                        try:
                            rpt.reporter = User.objects.filter(username=reporter_username).first()
                        except Exception as e:
                            pass
                    if reported_username:
                        try:
                            rpt.reported_user = User.objects.filter(username=reported_username).first()
                        except Exception as e:
                            pass
                except Exception:
                    pass
                rpt.save()
                # save local image
                if local_b64:
                    try:
                        header, data = local_b64.split(',', 1) if ',' in local_b64 else (None, local_b64)
                        img_data = base64.b64decode(data)
                        fname = f'local_{rpt.id}.jpg'
                        rpt.local_image.save(fname, ContentFile(img_data), save=True)
                    except Exception:
                        pass
                if remote_b64:
                    try:
                        header, data = remote_b64.split(',', 1) if ',' in remote_b64 else (None, remote_b64)
                        img_data = base64.b64decode(data)
                        fname = f'remote_{rpt.id}.jpg'
                        rpt.remote_image.save(fname, ContentFile(img_data), save=True)
                    except Exception:
                        pass
                return str(rpt.id)

            try:
                report_id = await _save_report()
                await self.send_json({'action': 'report_result', 'status': 'ok', 'report_id': report_id})
            except Exception as e:
                await self.send_json({'action': 'report_result', 'status': 'error', 'message': str(e)})

    # Handlers for channel-layer messages -> translate into WebSocket JSON
    async def chat_matched(self, event):
        # Received when a match is made. Notify client and set local room state.
        self.room_name = event.get('room')
        await self.send_json({
            'action': 'matched',
            'room': event.get('room'),
            'initiator': event.get('initiator', False),
        })

    async def chat_signal(self, event):
        # Forward signaling payloads to the other peer only
        if event.get('sender') == self.channel_name:
            return
        await self.send_json({'action': 'signal', 'data': event.get('data')})

    async def chat_message(self, event):
        # Forward text chat messages
        if event.get('sender') == self.channel_name:
            return
        await self.send_json({'action': 'chat', 'message': event.get('message')})

    async def chat_partner_left(self, event):
        # Partner left (or was skipped). Client should reset and optionally search again.
        # Clear local room state
        if self.room_name:
            try:
                await self.channel_layer.group_discard(self.room_name, self.channel_name)
            except Exception:
                pass
        self.room_name = None
        channel_to_room.pop(self.channel_name, None)
        await self.send_json({'action': 'partner_left'})
