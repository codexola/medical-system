import hashlib
import hmac
import base64

import httpx

from app.config import get_settings

settings = get_settings()


class LineClient:
    def __init__(self):
        self.channel_access_token = settings.LINE_CHANNEL_ACCESS_TOKEN
        self.channel_secret = settings.LINE_CHANNEL_SECRET
        self.api_base = "https://api.line.me/v2/bot"

    def verify_signature(self, body: bytes, signature: str) -> bool:
        if not self.channel_secret:
            return False
        hash_value = hmac.new(
            self.channel_secret.encode("utf-8"), body, hashlib.sha256
        ).digest()
        expected = base64.b64encode(hash_value).decode("utf-8")
        return hmac.compare_digest(expected, signature)

    async def reply_message(self, reply_token: str, text: str) -> bool:
        headers = {
            "Authorization": f"Bearer {self.channel_access_token}",
            "Content-Type": "application/json",
        }
        payload = {"replyToken": reply_token, "messages": [{"type": "text", "text": text[:5000]}]}
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{self.api_base}/message/reply", json=payload, headers=headers)
            return response.status_code == 200

    async def push_message(self, user_id: str, text: str) -> bool:
        headers = {
            "Authorization": f"Bearer {self.channel_access_token}",
            "Content-Type": "application/json",
        }
        payload = {"to": user_id, "messages": [{"type": "text", "text": text[:5000]}]}
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{self.api_base}/message/push", json=payload, headers=headers)
            return response.status_code == 200

    async def get_profile(self, user_id: str) -> dict:
        headers = {"Authorization": f"Bearer {self.channel_access_token}"}
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.api_base}/profile/{user_id}", headers=headers)
            if response.status_code == 200:
                return response.json()
            return {}
