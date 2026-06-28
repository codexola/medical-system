from datetime import date

from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.agents import AgentOrchestrator
from app.database.session import get_db
from app.line.client import LineClient
from app.services.auth import AuthService

router = APIRouter(prefix="/line", tags=["line"])


@router.post("/webhook")
async def line_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    body = await request.body()
    signature = request.headers.get("X-Line-Signature", "")

    client = LineClient()
    if client.channel_secret and not client.verify_signature(body, signature):
        raise HTTPException(status_code=403, detail="Invalid signature")

    import json

    payload = json.loads(body)
    events = payload.get("events", [])

    for event in events:
        if event.get("type") != "message" or event["message"]["type"] != "text":
            continue

        line_user_id = event["source"]["userId"]
        message_text = event["message"]["text"]
        reply_token = event["replyToken"]

        profile = await client.get_profile(line_user_id)
        auth = AuthService(db)
        user = await auth.get_or_create_line_user(line_user_id, profile.get("displayName"))

        orchestrator = AgentOrchestrator(db)
        reply = await orchestrator.process_message(user, message_text, "line")
        await client.reply_message(reply_token, reply)

    return {"status": "ok"}
