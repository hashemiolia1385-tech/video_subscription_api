import json
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from config.asgi import application

User = get_user_model()


@database_sync_to_async
def create_test_user_and_token(username):
    user = User.objects.create_user(username=username, password="Password123!")
    refresh = RefreshToken.for_user(user)
    return user, str(refresh.access_token)


class WatchPartyWebSocketTests(TestCase):
    async def test_websocket_rejects_unauthenticated_connection(self):
        communicator = WebsocketCommunicator(application, "/ws/watch/1/")
        connected, close_code = await communicator.connect()
        self.assertFalse(connected)
        self.assertEqual(close_code, 4001)
        await communicator.disconnect()

    async def test_websocket_accepts_valid_jwt(self):
        user, token = await create_test_user_and_token("ws_auth_single_user")

        communicator = WebsocketCommunicator(application, f"/ws/watch/1/?token={token}")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        await communicator.disconnect()

    async def test_video_sync_play_pause_and_seek(self):
        _, token1 = await create_test_user_and_token("alice_watcher")
        _, token2 = await create_test_user_and_token("bob_watcher")

        comm1 = WebsocketCommunicator(application, f"/ws/watch/10/?token={token1}")
        connected1, _ = await comm1.connect()
        self.assertTrue(connected1)
        _ = await comm1.receive_json_from()

        comm2 = WebsocketCommunicator(application, f"/ws/watch/10/?token={token2}")
        connected2, _ = await comm2.connect()
        self.assertTrue(connected2)
        _ = await comm1.receive_json_from()
        _ = await comm2.receive_json_from()

        await comm1.send_json_to({"action": "play", "current_time": 45.5})

        msg1 = await comm1.receive_json_from()
        msg2 = await comm2.receive_json_from()

        self.assertEqual(msg2["event_type"], "video_sync")
        self.assertEqual(msg2["action"], "play")
        self.assertEqual(msg2["current_time"], 45.5)
        self.assertEqual(msg2["sender"], "alice_watcher")

        await comm2.send_json_to({"action": "pause", "current_time": 60.0})

        pause_msg = await comm1.receive_json_from()
        self.assertEqual(pause_msg["action"], "pause")
        self.assertEqual(pause_msg["current_time"], 60.0)
        self.assertEqual(pause_msg["sender"], "bob_watcher")

        await comm1.disconnect()
        await comm2.disconnect()

    async def test_live_chat_broadcast(self):
        _, token1 = await create_test_user_and_token("chat_user_1")
        _, token2 = await create_test_user_and_token("chat_user_2")

        comm1 = WebsocketCommunicator(application, f"/ws/watch/5/?token={token1}")
        await comm1.connect()
        _ = await comm1.receive_json_from()

        comm2 = WebsocketCommunicator(application, f"/ws/watch/5/?token={token2}")
        await comm2.connect()
        _ = await comm1.receive_json_from()
        _ = await comm2.receive_json_from()

        await comm1.send_json_to(
            {"action": "chat_message", "message": "این سکانس فوق‌العاده بود!"}
        )

        chat_response = await comm2.receive_json_from()
        self.assertEqual(chat_response["event_type"], "chat_message")
        self.assertEqual(chat_response["message"], "این سکانس فوق‌العاده بود!")
        self.assertEqual(chat_response["sender"], "chat_user_1")
        self.assertIn("timestamp", chat_response)

        await comm1.disconnect()
        await comm2.disconnect()
