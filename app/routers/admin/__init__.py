from __future__ import annotations

from aiogram import Router

from . import admins, broadcast, cancel, edit, export, menu, messaging, pending, users

router = Router()
router.include_router(menu.router)
router.include_router(users.router)
router.include_router(pending.router)
router.include_router(edit.router)
router.include_router(export.router)
router.include_router(admins.router)
router.include_router(messaging.router)
router.include_router(broadcast.router)
router.include_router(cancel.router)
