from __future__ import annotations

from dataclasses import dataclass

from aiogram.fsm.state import State, StatesGroup


class AdminEdit(StatesGroup):
    waiting_value = State()


class AdminAdd(StatesGroup):
    waiting_tid = State()


class AdminMsg(StatesGroup):
    choosing_target = State()
    waiting_phone = State()
    waiting_text = State()
    confirm = State()


class AdminBcast(StatesGroup):
    waiting_post = State()
    confirm = State()


@dataclass
class EditCtx:
    field: str
    candidate_id: int
    return_kind: str
    return_page: int
    origin_chat_id: int
    origin_message_id: int
    return_fac: str | None = None
    return_ex: str | None = None
    return_st: str | None = None
