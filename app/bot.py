from __future__ import annotations

import asyncio
import contextlib
import logging
import os
import socket

import aiohttp
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
import google.genai as genai

from app.config import settings
from app.db.mongo import mongo
from app.db.repos.admins_repo import AdminsRepo
from app.db.repos.candidates_repo import CandidatesRepo
from app.db.repos.users_repo import UsersRepo
from app.db.repos.exam_configs_repo import ExamConfigsRepo
from app.i18n.loader import load_translations
from app.middlewares.i18n import I18nMiddleware
from app.middlewares.role import RoleMiddleware
from app.routers.admin import router as admin_router
from app.routers.registration import router as registration_router
from app.routers.start import router as start_router
from app.routers.user import router as user_router
from app.scheduler.scheduler import reminder_loop


def build_bot() -> Bot:
    session = AiohttpSession(timeout=60)
    session._connector_init["family"] = socket.AF_INET
    session._connector_init["ttl_dns_cache"] = 300

    return Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        session=session,
    )


def build_dispatcher(
    admins_repo: AdminsRepo,
    users_repo: UsersRepo,
    candidates_repo: CandidatesRepo,
    exam_configs_repo: ExamConfigsRepo,
    translations: dict,
) -> Dispatcher:
    dp = Dispatcher()

    dp["users_repo"] = users_repo
    dp["candidates_repo"] = candidates_repo
    dp["admins_repo"] = admins_repo
    dp["exam_configs_repo"] = exam_configs_repo
    dp["translations"] = translations

    dp.message.middleware(RoleMiddleware(admins_repo))
    dp.callback_query.middleware(RoleMiddleware(admins_repo))

    dp.message.middleware(I18nMiddleware(users_repo, translations))
    dp.callback_query.middleware(I18nMiddleware(users_repo, translations))

    dp.include_router(registration_router)
    dp.include_router(start_router)
    dp.include_router(user_router)
    dp.include_router(admin_router)

    return dp


async def healthcheck(_: web.Request) -> web.Response:
    return web.json_response({"status": "ok"})


async def handle_ai_chat(request: web.Request) -> web.Response:
    if not settings.GEMINI_API_KEY:
        return web.json_response({"error": "AI not configured"}, status=500)

    try:
        data = await request.json()
        user_message = data.get("message")
        history = data.get("history", [])
        user_id = data.get("user_id", "unknown")
    except Exception:
        return web.json_response({"error": "Invalid request"}, status=400)

    if not user_message:
        return web.json_response({"error": "Message required"}, status=400)

    # Use cached Knowledge Base
    kb_content = request.app.get("kb_content", "")
    
    system_instruction = (
        "Siz Sharda University Uzbekistan (SUUZ) ning rasmiy virtual yordamchisi - 'Suuz agent'siz. "
        "Sizning vazifangiz universitet haqidagi ma'lumotlar bazasi asosida aniq javob berish. "
        "Suhbatni professional va juda xushmuomala tarzda olib boring. "
        "Faqat taqdim etilgan ma'lumotlar asosida javob bering. Noma'lum ma'lumotlar uchun rasmiy saytni tavsiya qiling.\n\n"
        f"MA'LUMOTLAR BAZASI:\n{kb_content}"
    )

    try:
        # Configure Google Genai SDK
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel(
            model_name="gemini-3.1-flash-lite",
            system_instruction=system_instruction
        )
        
        # Truncate history to last 6 messages (3 turns) to save tokens and stay within TPM limits
        if len(history) > 6:
            history = history[-6:]

        # Build chat history for the model
        chat_history = []
        for h in history:
            role = "user" if h["role"] == "user" else "model"
            text = h["parts"][0]["text"]
            chat_history.append({"role": role, "parts": [{"text": text}]})

        # Start chat session with history
        chat_session = model.start_chat(history=chat_history)
        
        # Send user message and get response
        response = chat_session.send_message(user_message)
        ai_text = response.text
        
        return web.json_response({"reply": ai_text})
        
    except Exception as e:
        logging.error("Gemini API error (User: %s): %s", user_id, str(e))
        return web.json_response({"error": "AI error"}, status=500)


async def load_kb(app: web.Application) -> None:
    kb_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "about_suuz.txt")
    content = ""
    if os.path.exists(kb_path):
        try:
            with open(kb_path, "r", encoding="utf-8") as f:
                content = f.read()
            logging.info("Knowledge Base loaded into memory (%d chars)", len(content))
        except Exception as e:
            logging.error("Error loading Knowledge Base: %s", e)
    app["kb_content"] = content


async def safe_reminder_loop(app: web.Application) -> None:
    bot: Bot = app["bot"]
    candidates_repo: CandidatesRepo = app["candidates_repo"]
    users_repo: UsersRepo = app["users_repo"]
    translations: dict = app["translations"]

    while True:
        try:
            await reminder_loop(
                bot=bot,
                candidates_repo=candidates_repo,
                users_repo=users_repo,
                translations=translations,
                tz_name=settings.TZ,
                interval_seconds=60,
            )
        except asyncio.CancelledError:
            raise
        except Exception:
            logging.exception("Reminder loop crashed. Restarting in 5 seconds...")
            await asyncio.sleep(5)


async def on_startup(app: web.Application) -> None:
    logging.info("Application startup...")

    # Load Knowledge Base into memory once
    await load_kb(app)

    bot: Bot = app["bot"]
    admins_repo: AdminsRepo = app["admins_repo"]

    await admins_repo.ensure_super_admin(settings.SUPER_ADMIN_TG_ID)

    webhook_url = f"{settings.WEBHOOK_BASE_URL.rstrip('/')}{app['webhook_path']}"

    await bot.set_webhook(
        url=webhook_url,
        drop_pending_updates=True,
        allowed_updates=["message", "callback_query"],
    )

    app["reminder_task"] = asyncio.create_task(safe_reminder_loop(app))

    logging.info("Webhook set successfully.")


async def on_shutdown(app: web.Application) -> None:
    logging.info("Application shutdown...")

    reminder_task = app.get("reminder_task")
    if reminder_task:
        reminder_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await reminder_task

    bot: Bot = app["bot"]

    with contextlib.suppress(Exception):
        await bot.delete_webhook()

    await bot.session.close()
    mongo.close()


def create_app() -> web.Application:
    mongo.connect()
    db = mongo.db

    users_repo = UsersRepo(db)
    candidates_repo = CandidatesRepo(db)
    admins_repo = AdminsRepo(db)
    exam_configs_repo = ExamConfigsRepo(db)
    translations = load_translations()

    bot = build_bot()
    dp = build_dispatcher(
        admins_repo=admins_repo,
        users_repo=users_repo,
        candidates_repo=candidates_repo,
        exam_configs_repo=exam_configs_repo,
        translations=translations,
    )

    app = web.Application()

    app.router.add_get("/", healthcheck)
    app.router.add_get("/health", healthcheck)
    app.router.add_post("/api/ai_chat", handle_ai_chat)

    webhook_path = f"/webhook/{settings.WEBHOOK_SECRET}"

    app["bot"] = bot
    app["dp"] = dp
    app["users_repo"] = users_repo
    app["candidates_repo"] = candidates_repo
    app["admins_repo"] = admins_repo
    app["exam_configs_repo"] = exam_configs_repo
    app["translations"] = translations
    app["webhook_path"] = webhook_path
    app["reminder_task"] = None

    webapp_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "webapp")
    if os.path.exists(webapp_dir):
        app.router.add_static("/webapp/", path=webapp_dir, name="webapp")
        logging.info("Serving WebApp from %s at /webapp/", webapp_dir)
    else:
        logging.warning("WebApp directory not found at %s", webapp_dir)

    SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
    ).register(app, path=webhook_path)

    setup_application(app, dp)

    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    return app


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )

    port = int(os.getenv("PORT", "10000"))
    logging.info("Starting server on 0.0.0.0:%s", port)

    web.run_app(
        create_app(),
        host="0.0.0.0",
        port=port,
    )
