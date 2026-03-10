from __future__ import annotations

import asyncio
import contextlib
import logging
import os
import socket

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from app.config import settings
from app.db.mongo import mongo
from app.db.repos.admins_repo import AdminsRepo
from app.db.repos.candidates_repo import CandidatesRepo
from app.db.repos.users_repo import UsersRepo
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
    translations: dict,
) -> Dispatcher:
    dp = Dispatcher()

    # Handlerlarga dependency uzatish
    dp["users_repo"] = users_repo
    dp["candidates_repo"] = candidates_repo
    dp["admins_repo"] = admins_repo
    dp["translations"] = translations

    # Middlewares
    dp.message.middleware(RoleMiddleware(admins_repo))
    dp.callback_query.middleware(RoleMiddleware(admins_repo))

    dp.message.middleware(I18nMiddleware(users_repo, translations))
    dp.callback_query.middleware(I18nMiddleware(users_repo, translations))

    # Routers
    dp.include_router(registration_router)
    dp.include_router(start_router)
    dp.include_router(user_router)
    dp.include_router(admin_router)

    return dp


async def healthcheck(_: web.Request) -> web.Response:
    return web.json_response({"status": "ok"})


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
    translations = load_translations()

    bot = build_bot()
    dp = build_dispatcher(
        admins_repo=admins_repo,
        users_repo=users_repo,
        candidates_repo=candidates_repo,
        translations=translations,
    )

    app = web.Application()

    app.router.add_get("/", healthcheck)
    app.router.add_get("/health", healthcheck)

    webhook_path = f"/webhook/{settings.WEBHOOK_SECRET}"

    app["bot"] = bot
    app["dp"] = dp
    app["users_repo"] = users_repo
    app["candidates_repo"] = candidates_repo
    app["admins_repo"] = admins_repo
    app["translations"] = translations
    app["webhook_path"] = webhook_path
    app["reminder_task"] = None

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