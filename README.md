# perekup

Telegram-бот для подачи заявок и подписок на закрытый канал (`bot/`) и сайт-лендинг выкупа автомобилей на Next.js (`site/`).

Все ключи и контакты передаются через переменные окружения, см. `bot/.env.example` и `site/.env.example`.

## Бот

```bash
cd bot
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # заполнить и экспортировать переменные
python bot.py
```

## Сайт

```bash
cd site
npm install
cp .env.example .env.local
npm run dev
```

Телефон и ссылки на соцсети в `site/src` заменены заглушками (`+7 (000) 000-00-00`, `your_channel`, `your_account`, `your_group`).
