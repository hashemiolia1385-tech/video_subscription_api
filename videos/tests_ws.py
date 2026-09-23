import pytest
import json
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from config.asgi import application

User = get_user_model()


@database_sync_to_async
def create_test_user_and_token(username):
    user = User.objects.create_user(
        username=username,
        password="Password123!"
    )
    refresh = RefreshToken.for_user(user)
    return user, str(refresh.access_token)


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_websocket_rejects_unauthenticated_connection():
    communicator = WebsocketCommunicator(application, "/ws/watch/1/")
    connected, close_code = await communicator.connect()
    assert not connected
    assert close_code == 4001
    await communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_websocket_accepts_valid_jwt():
    user, token = await create_test_user_and_token("ws_auth_single_user")

    communicator = WebsocketCommunicator(application, f"/ws/watch/1/?token={token}")
    connected, _ = await communicator.connect()
    assert connected
    await communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_video_sync_play_pause_and_seek():
    # ساخت دو کاربر مجزا برای سناریوی Watch Party
    _, token1 = await create_test_user_and_token("alice_watcher")
    _, token2 = await create_test_user_and_token("bob_watcher")

    comm1 = WebsocketCommunicator(application, f"/ws/watch/10/?token={token1}")
    connected1, _ = await comm1.connect()
    assert connected1
    # پیام سیستم برای پیوستن کاربر اول
    _ = await comm1.receive_json_from()

    comm2 = WebsocketCommunicator(application, f"/ws/watch/10/?token={token2}")
    connected2, _ = await comm2.connect()
    assert connected2
    # اعلان ورود کاربر دوم به کاربر اول
    _ = await comm1.receive_json_from()
    # پیام خوش‌آمدگویی برای کاربر دوم
    _ = await comm2.receive_json_from()

    # ارسال اکشن play از طرف کاربر اول روی ثانیه ۴۵.۵
    await comm1.send_json_to({
        "action": "play",
        "current_time": 45.5
    })

    # دریافت ایونت همگام‌سازی توسط هر دو کلاینت
    msg1 = await comm1.receive_json_from()
    msg2 = await comm2.receive_json_from()

    assert msg2["event_type"] == "video_sync"
    assert msg2["action"] == "play"
    assert msg2["current_time"] == 45.5
    assert msg2["sender"] == "alice_watcher"

    # ارسال اکشن pause از طرف کاربر دوم روی ثانیه ۶۰.۰
    await comm2.send_json_to({
        "action": "pause",
        "current_time": 60.0
    })

    pause_msg = await comm1.receive_json_from()
    assert pause_msg["action"] == "pause"
    assert pause_msg["current_time"] == 60.0
    assert pause_msg["sender"] == "bob_watcher"

    await comm1.disconnect()
    await comm2.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_live_chat_broadcast():
    _, token1 = await create_test_user_and_token("chat_user_1")
    _, token2 = await create_test_user_and_token("chat_user_2")

    comm1 = WebsocketCommunicator(application, f"/ws/watch/5/?token={token1}")
    await comm1.connect()
    _ = await comm1.receive_json_from()

    comm2 = WebsocketCommunicator(application, f"/ws/watch/5/?token={token2}")
    await comm2.connect()
    _ = await comm1.receive_json_from()
    _ = await comm2.receive_json_from()

    # ارسال پیام متنی چت توسط کاربر اول
    await comm1.send_json_to({
        "action": "chat_message",
        "message": "این سکانس فوق‌العاده بود!"
    })

    # دریافت پیام به صورت همزمان توسط کاربر دوم
    chat_response = await comm2.receive_json_from()
    assert chat_response["event_type"] == "chat_message"
    assert chat_response["message"] == "این سکانس فوق‌العاده بود!"
    assert chat_response["sender"] == "chat_user_1"
    assert "timestamp" in chat_response

    await comm1.disconnect()
    await comm2.disconnect()