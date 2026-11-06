# Admin Review Flow for Car Proposals

## Problem

Currently the car proposal flow in `bot.py` publishes directly to the Telegram channel after the user uploads photos (in `input_photos`), with no admin moderation. The owner has no control over what gets published.

## Database (actual schema)

```sql
-- Main table for car listings
CREATE TABLE objects (
    id INT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    uuid VARCHAR(255) NOT NULL UNIQUE,
    description TEXT NOT NULL,
    messageId INT UNIQUE,
    isSold BOOLEAN NOT NULL DEFAULT FALSE,
    isReserved BOOLEAN NOT NULL DEFAULT FALSE,
    userReserved VARCHAR(255) DEFAULT NULL,
    autotekaId INTEGER REFERENCES autoteka(id) ON DELETE SET NULL,
    -- Added columns:
    user_id BIGINT,
    contact TEXT,
    status VARCHAR(32) DEFAULT 'pending',
    photo_file_ids TEXT[],
    price TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE autoteka (
    id INT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    uuid VARCHAR(255) NOT NULL UNIQUE
);

CREATE TABLE autoteka_user (
    userUuid VARCHAR(255) NOT NULL,
    autotekaId INTEGER REFERENCES autoteka(id) ON DELETE CASCADE,
    PRIMARY KEY (userUuid, autotekaId)
);

CREATE TABLE subscriptions (
    user_id BIGINT PRIMARY KEY,
    email TEXT,
    status VARCHAR(32),
    plan TEXT,
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    payment_id TEXT,
    amount INTEGER,
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Important:** The code in `bot.py` references an `applications` table that does not exist. All queries must use the `objects` table instead. Functions like `save_application`, `get_application_by_uuid`, `get_user_applications`, `update_application_status` must be rewritten to use `objects`.

## New Flow

### User Submission (changed)

```
описание → цена → фото → автотека → контактные данные → сохранение (status=pending) → тихое уведомление админу
```

Steps:
1. `input_description` — user enters car description. Inserts row into `objects` (uuid, description) as before.
2. `input_price` — user enters price (unchanged in UX, but saved to `user_data`)
3. `input_photos` — user uploads photos one by one, types "Готово" when done. **Remove direct channel publishing from this step.** After "Готово", proceed to autoteka.
4. `input_autoteka` — user uploads autoteka document to S3, links via `autoteka` table (unchanged)
5. **NEW: `input_contact`** — bot asks for contact info, user sends text
6. All collected data (price, contact, photo_file_ids, user_id) saved to `objects` row via UPDATE (row already exists from step 1)
7. Admin receives a short notification

### Admin Notification

When a new application is saved:
- Admin (OWNER_ID) receives message: `"Новая заявка от @username. Ожидает проверки: N"` where N = total pending count
- No photos, no details in the notification — just the alert
- Message includes inline button: "Посмотреть заявки"

### Admin Panel (conveyor)

Triggered by:
- The "Посмотреть заявки" button on notification
- The existing "Управление заявками" button in admin's main menu

Behavior:
1. Bot fetches the oldest `pending` object from `objects` table
2. Sends full details to admin:
   - All photos (media group from `photo_file_ids`)
   - Description, price, contact info
   - Autoteka document (fetched via `autotekaId` → `autoteka.uuid` → S3 key `files/{uuid}.{ext}`)
   - Inline keyboard with action buttons
3. Action buttons:
   - "В открытый канал" — publish to CHAT_ID, set status `published_open`
   - "В закрытый канал" — publish to PRIVATE_CHANNEL_ID, set status `published_closed`
   - "В оба канала" — publish to both, set status `published_both`
   - "Отклонить" — set status `rejected`
   - "Пропустить" — move to next without changing status
4. After any action (except skip which just advances), status is updated in `objects` table
5. Next pending object is shown automatically
6. If no more pending objects: "Нет заявок на проверку"

### User Notifications

None. User checks status via existing "Посмотреть статус заявки" button.

## What Changes in Code

### Remove from `input_photos` (lines ~408-434)
- Remove `create_payment()` calls
- Remove `bot.send_media_group(chat_id=CHAT_ID, ...)`
- Remove `bot.send_message(chat_id=CHAT_ID, ...)`
- Remove payment button generation (reserve, buy, engine)
- After "Готово", just proceed to `input_autoteka` prompt

### Modify `input_autoteka`
- After successful upload, ask for contact: `bot.send_message(... "Введите контактные данные")` and register `input_contact`

### New: `input_contact(message)`
- Save contact to `user_data[user_id]['contact']`
- UPDATE the existing `objects` row (created in `input_description`) with: `user_id`, `contact`, `status='pending'`, `photo_file_ids`, `price`
- Call `notify_admin_new_application(user_id)`
- Send confirmation: "Ваша заявка отправлена на проверку"

### New: `notify_admin_new_application(user_id)`
- Count pending objects: `SELECT COUNT(*) FROM objects WHERE status = 'pending'`
- Send to OWNER_ID: `"Новая заявка от @{username}. Ожидает проверки: {N}"`
- Include inline button: `callback_data='admin_review_apps'`

### New: `show_next_pending(chat_id)`
- `SELECT * FROM objects WHERE status = 'pending' ORDER BY created_at ASC LIMIT 1`
- If none: send "Нет заявок на проверку"
- If found: send photos as media group, then description/price/contact message with action buttons

### Rewrite DB functions to use `objects` table
- `save_application` → replaced by UPDATE on existing `objects` row
- `get_application_by_uuid` → `SELECT ... FROM objects WHERE uuid = %s`
- `get_user_applications` → `SELECT ... FROM objects WHERE user_id = %s ORDER BY created_at DESC`
- `update_application_status` → `UPDATE objects SET status = %s WHERE uuid = %s`

### Modified: `callback_inline` handler
- Add handlers for new callback data:
  - `admin_review_apps` — triggers `show_next_pending`
  - `admin_publish_open_{uuid}` — publish to open channel, show next
  - `admin_publish_closed_{uuid}` — publish to closed channel, show next
  - `admin_publish_both_{uuid}` — publish to both, show next
  - `admin_reject_{uuid}` — reject, show next
  - `admin_skip_{uuid}` — show next without action
- Remove old handlers: `publish_open_`, `publish_closed_`, `contact_seller_`, `reject_app_`

### Modify `publish_application_to_channel`
- Update to read from `objects` table instead of `applications`
- Same publishing logic: photos + caption + inline buttons to target channel

### New status constant
- `APPLICATION_STATUS_PUBLISHED_BOTH = 'published_both'`

### Modified: admin menu button handler
- "Управление заявками" (`BTN_ADMIN` / `handle_admin`) calls `show_next_pending` instead of showing a text message

## What Does NOT Change

- Subscription system (plans, payments, YooKassa, private channel access)
- "О нас", "Поддержка", "Менеджер" handlers
- `build_start_inline_markup`, `build_main_menu_markup`
- User-facing status check buttons
- S3 upload logic for autoteka
- `autoteka` / `autoteka_user` tables
- Database schema (no migrations needed)
