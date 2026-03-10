# Deployment Guide (Production)

Ushbu hujjat **Sharda Registration** botini serverga (Linux VPS) chiqarish uchun amaliy qo‘llanma. Loyiha hozircha **polling** rejimida ishlaydi (webhook shart emas).

## Talablar

- **Ubuntu 22.04/24.04** (yoki boshqa Linux)
- **Python 3.11**
- **MongoDB** (Atlas yoki self-hosted)
- WebApp uchun **HTTPS** domen (Netlify/Vercel/Nginx static)
- Telegram bot token (BotFather)

## 0) Muhim xavfsizlik eslatmalari

- `.env` faylini **hech qachon gitga qo‘shmang** va **serverdan tashqariga ulashmang**.
- Agar `.env` ichida real `BOT_TOKEN` yoki `MONGO_URI` tarqalib ketgan bo‘lsa, darhol:
  - BotFather’da tokenni **revoke/rotate** qiling,
  - MongoDB user/password’ni **almashtiring** (yangi user yarating).

## 1) Serverda user va papka tayyorlash

```bash
sudo adduser --disabled-password --gecos "" sharda
sudo mkdir -p /opt/sharda_registration
sudo chown -R sharda:sharda /opt/sharda_registration
```

Repo’ni `/opt/sharda_registration` ichiga joylashtiring (git clone yoki zip orqali).

## 2) Python environment va dependency’lar

### Variant A — venv + pip (tavsiya)

```bash
cd /opt/sharda_registration
python3.11 -m venv .venv
source .venv/bin/activate

pip install -U pip wheel
# Agar requirements.txt bo‘lmasa, Pipfile’dan foydalanamiz:
pip install pipenv
pipenv requirements > requirements.txt
pip install -r requirements.txt
```

### Variant B — Pipenv (deploy)

```bash
cd /opt/sharda_registration
pip install pipenv
pipenv sync --deploy
```

## 3) .env sozlash

Serverda `.env.example` dan nusxa oling va to‘ldiring:

```bash
cd /opt/sharda_registration
cp .env.example .env
nano .env
```

Minimal `.env`:

```dotenv
BOT_TOKEN=123456:ABC...
MONGO_URI=mongodb+srv://<user>:<pass>@<cluster>/<db>?retryWrites=true&w=majority
MONGO_DB=suuz_bot
SUPER_ADMIN_TG_ID=5899057322
TZ=Asia/Tashkent
WEBAPP_URL=https://your-webapp-domain.tld/
INTRO_PHOTO_FILE_ID=
```

> `WEBAPP_URL` — WebApp (mini form) joylashgan **HTTPS** URL. Masalan: Netlify’dagi root `https://xxx.netlify.app/`.

Fayl permission:

```bash
chmod 600 .env
```

## 4) WebApp’ni host qilish (HTTPS)

WebApp fayllari: `app/webapp/` (`index.html`, `app.js`, `styles.css`).

### Netlify / Vercel
- `app/webapp` papkani publish qiling.
- URL’ni `.env` dagi `WEBAPP_URL` ga yozing.

### Nginx orqali serverda static
Misol: `https://example.com/webapp/`

1) Fayllarni joylashtiring:

```bash
sudo mkdir -p /var/www/sharda-webapp
sudo rsync -a /opt/sharda_registration/app/webapp/ /var/www/sharda-webapp/
```

2) Nginx server block:

```nginx
server {
    server_name example.com;

    location /webapp/ {
        alias /var/www/sharda-webapp/;
        try_files $uri $uri/ /webapp/index.html;
    }
}
```

So‘ng `WEBAPP_URL=https://example.com/webapp/` qilib qo‘ying.

## 5) BotFather sozlash (WebApp Domain)

Telegram WebApp ochilishi uchun BotFather’da domenni ruxsat qilish kerak:

- BotFather → **/setdomain**
- Botni tanlang
- Domen kiriting: `your-webapp-domain.tld` (protocolsiz)

> Domen `WEBAPP_URL` bilan mos bo‘lishi shart.

## 6) systemd service (botni doimiy ishlatish)

`/etc/systemd/system/sharda-bot.service`:

```ini
[Unit]
Description=Sharda Registration Telegram Bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=sharda
WorkingDirectory=/opt/sharda_registration

# venv ishlatsangiz:
Environment="PYTHONUNBUFFERED=1"
EnvironmentFile=/opt/sharda_registration/.env
ExecStart=/opt/sharda_registration/.venv/bin/python -m app.bot

Restart=always
RestartSec=3

# Resurs limitlari (xohlasangiz)
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
```

Aktivlashtirish:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now sharda-bot
sudo systemctl status sharda-bot
```

Loglar:

```bash
journalctl -u sharda-bot -f
```

## 7) MongoDB (production tavsiyalar)

Tavsiya etiladigan indekslar (opsional, performance uchun):

- `candidates.telegram_id` unique
- `admins.telegram_id` unique
- `users.telegram_id` unique
- `candidates.updated_at` index (admin list sort uchun)

Mongo shell misol:

```javascript
db.candidates.createIndex({ telegram_id: 1 }, { unique: true })
db.admins.createIndex({ telegram_id: 1 }, { unique: true })
db.users.createIndex({ telegram_id: 1 }, { unique: true })
db.candidates.createIndex({ updated_at: -1 })
```

## 8) Troubleshooting

### WebApp’dan data kelmayapti
- `WEBAPP_URL` HTTPS ekanini tekshiring
- BotFather’da `/setdomain` to‘g‘ri qo‘yilganmi
- WebApp URL domeni bilan `/setdomain` domeni bir xilmi (subdomain ham hisoblanadi)
- Browser console’da WebApp yuklanyaptimi (Netlify/Vercel deploy)

### Bot ishlamay qoldi
- `journalctl -u sharda-bot -f` loglarni ko‘ring
- `.env` ichida `BOT_TOKEN` to‘g‘rimi
- Mongo `MONGO_URI` ga server IP ruxsat etilganmi (Atlas IP allowlist)

### Excel export ishlamayapti
- `openpyxl` o‘rnatilganmi (`pip show openpyxl`)
- Serverda disk permission va temp folder muammosi yo‘qmi
