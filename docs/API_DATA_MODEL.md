# Data Model (MongoDB)

Loyiha MongoDB’da 3 ta asosiy collection ishlatadi:

- `users`
- `candidates`
- `admins`

> `notification_jobs` repo fayli hozircha bo‘sh (0 bytes) — ishlatilmaydi.

---

## 1) `users` collection

**Maqsad:** user tilini va /start statistikani saqlash.

### Field’lar

| Field | Type | Izoh |
|---|---|---|
| `telegram_id` | int | Telegram user ID |
| `language` | str | `uz` / `ru` / `en` |
| `start_count` | int | /start bosilgan soni |
| `created_at` | datetime (UTC) | yaratilgan vaqt |
| `updated_at` | datetime (UTC) | oxirgi yangilanish |

### Example

```json
{
  "telegram_id": 123456789,
  "language": "uz",
  "start_count": 3,
  "created_at": "2026-03-02T10:00:00Z",
  "updated_at": "2026-03-02T10:05:00Z"
}
```

Tavsiya indeks:
- `telegram_id` unique

---

## 2) `admins` collection

**Maqsad:** admin va super admin rollarini boshqarish.

### Field’lar

| Field | Type | Izoh |
|---|---|---|
| `telegram_id` | int | Telegram ID |
| `role` | str | `admin` yoki `super` |
| `created_at` | datetime (UTC) | yaratilgan |
| `updated_at` | datetime (UTC) | yangilangan |

### Example

```json
{
  "telegram_id": 5899057322,
  "role": "super",
  "created_at": "2026-03-02T10:00:00Z",
  "updated_at": "2026-03-02T10:00:00Z"
}
```

Tavsiya indeks:
- `telegram_id` unique

---

## 3) `candidates` collection

**Maqsad:** ro‘yxatdan o‘tgan abituriyentning barcha progress va admin tomonidan beriladigan imtihon ma’lumotlarini saqlash.

### Status’lar

- `draft` — WebApp’dan ism/telefon kelgan, lekin yakuniy ro‘yxatdan o‘tish tugamagan
- `registered` — faculty/exam_type tanlangan, user ro‘yxatdan o‘tgan

### Field’lar (asosiy)

| Field | Type | Izoh |
|---|---|---|
| `telegram_id` | int | Telegram ID |
| `full_name` | str | F.I.Sh |
| `phone` | str | Telefon (string) |
| `language` | str | user tili (draft paytida) |
| `status` | str | `draft` / `registered` |
| `faculty` | str | `BBA`, `BSC`, `BAAE`, `BTECH` |
| `btech_track` | str\|null | `CSE` / `AIML` / `CYBER` |
| `exam_type` | str | `ONLINE` / `OFFLINE` |
| `exam_date_time` | str\|null | admin kiritadigan matn (lokal format) |
| `exam_datetime_utc` | datetime\|null | parse qilingan UTC datetime (reminder uchun) |
| `online_link` | str\|null | online imtihon havolasi |
| `exam_login` | str\|null | login |
| `exam_password` | str\|null | password |
| `address` | str\|null | offline manzil |
| `location` | object\|null | `{lat, lng}` offline location |
| `updated_by_admin_id` | int\|null | oxirgi edit qilgan admin |
| `why_choose_sharda_sent` | bool | “Why choose” post yuborilganmi |
| `reminder_30m_sent` | bool | reminder yuborilganmi |
| `reminder_30m_sent_at` | datetime\|null | yuborilgan vaqt |
| `created_at` | datetime (UTC) | yaratilgan |
| `updated_at` | datetime (UTC) | yangilangan |

### Example (ONLINE)

```json
{
  "telegram_id": 111222333,
  "full_name": "John Doe",
  "phone": "+998901234567",
  "language": "en",
  "status": "registered",
  "faculty": "BTECH",
  "btech_track": "AIML",
  "exam_type": "ONLINE",
  "exam_date_time": "2026-03-05 10:00",
  "exam_datetime_utc": "2026-03-05T05:00:00Z",
  "online_link": "https://meet.example.com/...",
  "exam_login": "john",
  "exam_password": "secret",
  "reminder_30m_sent": false,
  "created_at": "2026-03-02T10:00:00Z",
  "updated_at": "2026-03-02T10:30:00Z"
}
```

### Example (OFFLINE)

```json
{
  "telegram_id": 444555666,
  "full_name": "Ali Valiyev",
  "phone": "901112233",
  "status": "registered",
  "faculty": "BBA",
  "exam_type": "OFFLINE",
  "exam_date_time": "2026-03-06 14:00",
  "address": "Toshkent sh., ...",
  "location": {"lat": 41.2995, "lng": 69.2401},
  "reminder_30m_sent": true,
  "reminder_30m_sent_at": "2026-03-06T08:30:00Z",
  "created_at": "2026-03-02T10:00:00Z",
  "updated_at": "2026-03-02T10:30:00Z"
}
```

### Pending (yetishmayotgan) logikasi

Repo ichida:

- `TIME` — `exam_date_time` yo‘q
- `CREDS` — ONLINE bo‘lsa `online_link/login/password` dan biri yo‘q
- `ADDR` — OFFLINE bo‘lsa `address` yo‘q
- `ALL` — yuqoridagilarning istalgan biri

### Tavsiya indekslar

- `telegram_id` unique
- `updated_at` index (admin list sort)
- (opsional) `status`, `exam_type`, `faculty` indexlar (stats va list uchun)

---

## Callback Data conventions (qisqacha)

- `setlang:<lang>`
- `faculty:<code>`
- `btech:<track|BACK>`
- `exam:ONLINE|OFFLINE`
- `menu:*` — user menu
- `adm:*` — admin menu
- `au:*` — admin users list/detail
- `ae:*` — admin edit field
- `am:*` — admin messaging/broadcast

Bu pattern’lar router’lar ichida ishlatiladi va UI flow’ni boshqaradi.
