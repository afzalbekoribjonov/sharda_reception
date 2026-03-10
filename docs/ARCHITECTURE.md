# Architecture

## Umumiy ko‘rinish

Loyiha 4 ta asosiy komponentdan iborat:

1. **Telegram Client** (abituriyent va admin)
2. **Telegram Bot (Aiogram 3)** — `app/bot.py`
3. **MongoDB (Motor async)** — `app/db/...`
4. **Telegram WebApp (Static)** — `app/webapp/`

## Komponentlar diagrammasi

```mermaid
flowchart LR
  U[User/Admin<br/>Telegram App] -->|messages/callbacks| B[Bot: Aiogram 3]
  U -->|WebApp open| W[WebApp: Static HTML/JS/CSS]
  W -->|tg.sendData(payload)| B
  B -->|Motor| M[(MongoDB)]
```

## User ro‘yxatdan o‘tish flow

```mermaid
sequenceDiagram
  participant U as User (Telegram)
  participant B as Bot (Aiogram)
  participant W as WebApp (Static)
  participant M as MongoDB

  U->>B: /start
  B->>U: Lang tanlash (inline)
  U->>B: setlang:uz/ru/en
  B->>U: WebApp ochish (ReplyKeyboard WebApp)
  U->>W: Form (F.I.Sh + telefon)
  W->>B: sendData({full_name, phone, lang})
  B->>M: candidates.upsert_draft(status=draft)
  B->>U: Faculty tanlash
  U->>B: faculty:...
  B->>M: candidates.set_faculty()
  B->>U: (BTECH bo‘lsa track) yoki exam type
  U->>B: exam:ONLINE/OFFLINE
  B->>M: candidates.set_exam_type(status=registered)
  B->>U: Menu + info post
```

## Admin flow (Telegram ichida)

Admin router’lar `app/routers/admin/*` ichida.

### Admin menyu (entry)
- `/admin` → admin menu
- `adm:USERS` → filter + paginated list (10 ta)
- `adm:PENDING` → TIME/CREDS/ADDR/ALL bo‘yicha “yetishmayotgan”lar
- `adm:EXPORT` → Excel export filterlari
- `adm:MSG` → telefon/target bo‘yicha xabar
- `adm:BCAST` → broadcast post
- `adm:ADMINS` → super admin uchun admin management

### Admin user detail + edit

```mermaid
sequenceDiagram
  participant A as Admin
  participant B as Bot
  participant M as MongoDB

  A->>B: adm:USERS (filter)
  B->>M: candidates.admin_list_page(...)
  B->>A: List (page)
  A->>B: au:detail:<tid>:...
  B->>M: candidates.get_progress(tid)
  B->>A: Detail card + edit buttons
  A->>B: ae:<FIELD>:<tid>:...
  B->>A: "Qiymat kiriting" (FSM AdminEdit)
  A->>B: (message) value
  B->>M: candidates.set_*_admin(...)
  B->>A: Updated detail + return button
```

## Reminder scheduler (30 daqiqa oldin)

Bot ishga tushganda `reminder_loop()` fon task sifatida ishlaydi:

- `exam_date_time` matnidan `exam_datetime_utc` ni **backfill** qiladi
- Har 60 soniyada:
  - imtihongacha 30 daqiqa qolgan userlarni topadi
  - `reminder_30m` xabarini yuboradi
  - `reminder_30m_sent=true` qilib belgilaydi

```mermaid
flowchart TD
  S[Bot start] --> BF[Backfill exam_datetime_utc]
  BF --> L{Loop каждый 60s}
  L --> Q[find_due_reminders(now_utc..+30m)]
  Q -->|docs| SEND[send_message]
  SEND --> MARK[mark_reminder_sent]
  MARK --> L
```

## Kod tuzilmasi

- `app/bot.py` — entrypoint, dispatcher, middlewares, routers, scheduler loop
- `app/config.py` — `.env` settings (Pydantic Settings)
- `app/db/mongo.py` — Mongo connection
- `app/db/repos/*` — repository layer
- `app/routers/*` — handlers (user + admin)
- `app/keyboards/*` — inline/reply keyboards
- `app/i18n/*.json` — tarjimalar
- `app/webapp/*` — WebApp static UI

## Middleware’lar

- `RoleMiddleware` — `is_admin`, `is_super_admin` flag’larini data context’ga qo‘shadi
- `I18nMiddleware` — `lang` va `t` (translations) ni data context’ga qo‘shadi

## Data injection (Aiogram)

`dp.start_polling(..., users_repo=..., candidates_repo=..., admins_repo=..., translations=...)`

Handler’larda shu argumentlar dependency sifatida olinadi.
