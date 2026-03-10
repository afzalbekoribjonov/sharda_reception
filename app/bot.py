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
    translations: dict,
) -> Dispatcher:
    dp = Dispatcher()

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


async def on_startup(app: web.Application) -> None:
    logging.warning("Application startup...")

    bot: Bot = app["bot"]
    reminder_task = asyncio.create_task(
        reminder_loop(
            bot=bot,
            candidates_repo=app["candidates_repo"],
            users_repo=app["users_repo"],
            translations=app["translations"],
            tz_name=settings.TZ,
            interval_seconds=60,
        )
    )
    app["reminder_task"] = reminder_task

    webhook_path = app["webhook_path"]
    webhook_url = f"{settings.WEBHOOK_BASE_URL.rstrip('/')}{webhook_path}"

    await bot.set_webhook(
        url=webhook_url,
        drop_pending_updates=True,
    )

    logging.warning("Webhook set to: %s", webhook_url)


async def on_shutdown(app: web.Application) -> None:
    logging.warning("Application shutdown...")

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
    logging.warning("Creating application...")

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

    SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
    ).register(app, path=webhook_path)

    setup_application(
        app,
        dp,
        bot=bot,
        users_repo=users_repo,
        candidates_repo=candidates_repo,
        admins_repo=admins_repo,
        translations=translations,
    )

    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    return app


async def ensure_super_admin(app: web.Application) -> None:
    admins_repo: AdminsRepo = app["admins_repo"]
    await admins_repo.ensure_super_admin(settings.SUPER_ADMIN_TG_ID)


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)

    app = create_app()

    async def startup_wrapper(app_: web.Application) -> None:
        await ensure_super_admin(app_)
        await on_startup(app_)

    app.on_startup.clear()
    app.on_startup.append(startup_wrapper)
    app.on_shutdown.append(on_shutdown)

    port = int(os.getenv("PORT", "10000"))
    logging.warning("Starting aiohttp on 0.0.0.0:%s", port)

    web.run_app(app, host="0.0.0.0", port=port)