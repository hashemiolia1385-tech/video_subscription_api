import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone


class WatchPartyConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope.get("user")

        if not self.user or not self.user.is_authenticated:
            await self.close(code=4001)
            return

        self.video_id = self.scope["url_route"]["kwargs"]["video_id"]
        self.room_group_name = f"watch_party_{self.video_id}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "system_message",
                "message": f"کاربر {self.user.username} به اتاق پیوست.",
                "user": self.user.username,
            },
        )

    async def disconnect(self, close_code):
        if hasattr(self, "room_group_name"):
            if self.user and self.user.is_authenticated:
                try:
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            "type": "system_message",
                            "message": f"کاربر {self.user.username} از اتاق خارج شد.",
                            "user": self.user.username,
                        },
                    )
                except Exception:
                    pass

            await self.channel_layer.group_discard(
                self.room_group_name, self.channel_name
            )

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return

        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        action = data.get("action")

        # هندل کردن پینگ برای زنده نگه داشتن ارتباط ردیس
        if action == "ping":
            await self.send(text_data=json.dumps({"event_type": "pong"}))
            return

        if action == "chat_message":
            message = data.get("message", "").strip()
            if not message:
                return

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_broadcast",
                    "message": message,
                    "sender": self.user.username,
                    "timestamp": timezone.now().isoformat(),
                },
            )

    async def chat_broadcast(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "event_type": "chat_message",
                    "message": event["message"],
                    "sender": event["sender"],
                    "timestamp": event["timestamp"],
                }
            )
        )

    async def system_message(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "event_type": "system",
                    "message": event["message"],
                    "user": event["user"],
                }
            )
        )
