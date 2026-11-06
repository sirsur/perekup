# Admin Review Flow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace direct channel publishing with admin moderation — user submits car proposal, admin reviews via conveyor panel, then decides where to publish.

**Architecture:** Single-file modification of `bot.py`. Rewrite DB functions from non-existent `applications` table to existing `objects` table. Remove channel publishing from user flow, add `input_contact` step. New admin conveyor: fetch oldest pending, show full details, action buttons, auto-advance to next.

**Tech Stack:** Python, pyTelegramBotAPI (telebot), PostgreSQL (psycopg2), boto3 (S3)

---

### Task 1: Add new status constant and rewrite DB functions to use `objects` table

**Files:**
- Modify: `bot.py:71-78` (status constants)
- Modify: `bot.py:194-251` (DB functions)

- [ ] **Step 1: Add `APPLICATION_STATUS_PUBLISHED_BOTH` constant**

In `bot.py`, after line 74, add the new status:

```python
APPLICATION_STATUS_PUBLISHED_BOTH = 'published_both'
```

- [ ] **Step 2: Rewrite `save_application` → `finalize_object`**

Replace the `save_application` function (lines 194-203) with a function that UPDATEs the existing `objects` row (created during `input_description`):

```python
def finalize_object(object_id, user_id, price, contact, photo_file_ids):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE objects SET user_id = %s, price = %s, contact = %s, photo_file_ids = %s, status = %s WHERE id = %s",
        (user_id, price, contact, photo_file_ids, APPLICATION_STATUS_PENDING, object_id)
    )
    conn.commit()
    cursor.close()
    conn.close()
```

- [ ] **Step 3: Rewrite `update_application_status` → `update_object_status`**

Replace lines 206-215:

```python
def update_object_status(obj_uuid, status):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE objects SET status = %s WHERE uuid = %s",
        (status, obj_uuid)
    )
    conn.commit()
    cursor.close()
    conn.close()
```

- [ ] **Step 4: Rewrite `get_application_by_uuid` → `get_object_by_uuid`**

Replace lines 218-238:

```python
def get_object_by_uuid(obj_uuid):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, user_id, description, price, contact, status, photo_file_ids, autotekaId, uuid FROM objects WHERE uuid = %s",
        (obj_uuid,)
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if not row:
        return None
    return {
        'id': row[0],
        'user_id': row[1],
        'description': row[2],
        'price': row[3],
        'contact': row[4],
        'status': row[5],
        'photos': row[6] or [],
        'autoteka_id': row[7],
        'uuid': row[8],
    }
```

- [ ] **Step 5: Rewrite `get_user_applications` → `get_user_objects`**

Replace lines 241-251:

```python
def get_user_objects(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT uuid, description, price, contact, status, created_at FROM objects WHERE user_id = %s ORDER BY created_at DESC",
        (user_id,)
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows
```

- [ ] **Step 6: Commit**

```bash
git add bot.py
git commit -m "refactor: rewrite DB functions from applications to objects table, add published_both status"
```

---

### Task 2: Rewrite `input_photos` — remove channel publishing

**Files:**
- Modify: `bot.py:433-490` (`input_photos` function)

- [ ] **Step 1: Replace the `'готово'` branch in `input_photos`**

Replace lines 446-473 (the entire `if message.text ... == 'готово':` block) with:

```python
    if message.text is not None and message.text.lower() == 'готово':
        if 'photos' not in user_data[user_id] or len(user_data[user_id]['photos']) == 0:
            bot.send_message(message.chat.id, "Вы не добавили ни одной фотографии. Добавьте хотя бы одну 📷")
            bot.register_next_step_handler(message, input_photos)
            return
        bot.send_message(message.chat.id, "Все фотографии сохранены ✅")
        bot.send_message(message.chat.id, "Добавьте автотеку 📄")
        bot.register_next_step_handler(message, input_autoteka)
        return
```

This removes: `create_payment()` calls, `bot.send_media_group(chat_id=CHAT_ID, ...)`, `bot.send_message(chat_id=CHAT_ID, ...)`, payment button generation, `group_message_id` / `media_group_message_ids` storage.

- [ ] **Step 2: Commit**

```bash
git add bot.py
git commit -m "feat: remove direct channel publishing from input_photos"
```

---

### Task 3: Modify `input_autoteka` — remove channel refs, add contact step

**Files:**
- Modify: `bot.py:493-534` (`input_autoteka` function)

- [ ] **Step 1: Rewrite `input_autoteka`**

Replace the entire `input_autoteka` function (lines 493-534) with:

```python
def input_autoteka(message):
    try:
        user_id = message.from_user.id

        if message.text is not None and message.text.lower() == 'отмена':
            cancel_add(message, user_id)
            bot.send_message(message.chat.id, "Готово! ✅")
            return

        file_id = message.document.file_id
        file_info = bot.get_file(file_id)
        name, extension = message.document.file_name.rsplit('.', 1)

        file_url = f"https://api.telegram.org/file/bot{bot.token}/{file_info.file_path}"
        object_key = f"files/{user_data[user_id]['uuid']}.{extension}"

        with requests.get(file_url, stream=True) as r:
            r.raise_for_status()
            s3.upload_fileobj(r.raw, BUCKET_NAME, object_key)
        bot.reply_to(message, "Автотека успешно загружена в Облако! ✅")

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            sql.SQL("INSERT INTO autoteka (uuid) VALUES (%s) RETURNING id"),
            (str(user_data[user_id]['uuid']),)
        )
        autoteka_id = cursor.fetchone()[0]
        cursor.execute(
            sql.SQL("UPDATE objects SET autotekaId = %s WHERE id = %s"),
            (autoteka_id, str(user_data[user_id]['object_id']))
        )
        conn.commit()
        cursor.close()
        conn.close()

        bot.send_message(message.chat.id, "Введите контактные данные (телефон или ссылка на Telegram) 📱")
        bot.register_next_step_handler(message, input_contact)
    except Exception as e:
        print(f"Ошибка: {e}")
```

Changes from original:
- Removed `delete_message(message, user_id)` from cancel branch (no channel messages to delete anymore)
- Removed `messageId` from the UPDATE query (no channel message to track)
- Replaced final success message with contact prompt + `register_next_step_handler(message, input_contact)`

- [ ] **Step 2: Commit**

```bash
git add bot.py
git commit -m "feat: modify input_autoteka to ask for contact instead of finishing"
```

---

### Task 4: Add `input_contact` function and admin notification

**Files:**
- Modify: `bot.py` — add new functions after `input_autoteka`

- [ ] **Step 1: Add `get_pending_count` helper**

Add after the DB functions section (after `get_user_objects`):

```python
def get_pending_count():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM objects WHERE status = %s", (APPLICATION_STATUS_PENDING,))
    count = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return count
```

- [ ] **Step 2: Add `notify_admin_new_application` function**

Add after `get_pending_count`:

```python
def notify_admin_new_application(username):
    count = get_pending_count()
    display_name = f'@{username}' if username else 'пользователь'
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton('Посмотреть заявки 📋', callback_data='admin_review_apps'))
    bot.send_message(
        OWNER_ID,
        f'Новая заявка от {display_name}. Ожидает проверки: {count}',
        reply_markup=keyboard
    )
```

- [ ] **Step 3: Add `input_contact` function**

Replace the existing `get_contact` function (lines 537-541) with:

```python
def input_contact(message):
    user_id = message.from_user.id

    if message.text is not None and message.text.lower() == 'отмена':
        cancel_add(message, user_id)
        bot.send_message(message.chat.id, "Готово! ✅")
        return

    user_data[user_id]['contact'] = message.text

    finalize_object(
        object_id=user_data[user_id]['object_id'],
        user_id=user_id,
        price=user_data[user_id].get('price'),
        contact=user_data[user_id]['contact'],
        photo_file_ids=user_data[user_id].get('photos', []),
    )

    username = message.from_user.username
    notify_admin_new_application(username)

    bot.send_message(message.chat.id, 'Ваша заявка отправлена на проверку ✅')
    user_data.pop(user_id, None)
```

- [ ] **Step 4: Remove old `send_application_to_admin` function**

Delete the `send_application_to_admin` function (lines 544-538) entirely — it references the non-existent `applications` table and sends full details to admin (we now use terse notifications instead).

- [ ] **Step 5: Commit**

```bash
git add bot.py
git commit -m "feat: add input_contact step and admin notification"
```

---

### Task 5: Add admin conveyor — `show_next_pending` and `get_next_pending_object`

**Files:**
- Modify: `bot.py` — add new functions before `callback_inline`

- [ ] **Step 1: Add `get_next_pending_object` DB function**

Add after `get_pending_count`:

```python
def get_next_pending_object():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, uuid, user_id, description, price, contact, photo_file_ids, autotekaId, created_at FROM objects WHERE status = %s ORDER BY created_at ASC LIMIT 1",
        (APPLICATION_STATUS_PENDING,)
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if not row:
        return None
    return {
        'id': row[0],
        'uuid': row[1],
        'user_id': row[2],
        'description': row[3],
        'price': row[4],
        'contact': row[5],
        'photos': row[6] or [],
        'autoteka_id': row[7],
        'created_at': row[8],
    }
```

- [ ] **Step 2: Add `get_autoteka_s3_url` helper**

Add after `get_next_pending_object`:

```python
def get_autoteka_s3_url(autoteka_id):
    if not autoteka_id:
        return None
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT uuid FROM autoteka WHERE id = %s", (autoteka_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if not row:
        return None
    return row[0]
```

- [ ] **Step 3: Add `show_next_pending` function**

Add after `get_autoteka_s3_url`:

```python
def show_next_pending(chat_id):
    obj = get_next_pending_object()
    if not obj:
        bot.send_message(chat_id, 'Нет заявок на проверку ✅')
        return

    obj_uuid = obj['uuid']
    pending_count = get_pending_count()

    if obj['photos']:
        media = [types.InputMediaPhoto(photo) for photo in obj['photos']]
        bot.send_media_group(chat_id, media)

    text = (
        f"Заявка ({pending_count} в очереди)\n\n"
        f"Описание: {obj['description']}\n"
        f"Цена: {obj['price']}\n"
        f"Контакт: {obj['contact']}\n"
        f"Дата: {format_datetime(obj['created_at'])}"
    )

    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        types.InlineKeyboardButton('В открытый канал 🔓', callback_data=f'admin_publish_open_{obj_uuid}'),
        types.InlineKeyboardButton('В закрытый канал 🔒', callback_data=f'admin_publish_closed_{obj_uuid}'),
        types.InlineKeyboardButton('В оба канала 📢', callback_data=f'admin_publish_both_{obj_uuid}'),
        types.InlineKeyboardButton('Отклонить ❌', callback_data=f'admin_reject_{obj_uuid}'),
        types.InlineKeyboardButton('Пропустить ⏭️', callback_data=f'admin_skip_{obj_uuid}'),
    )
    bot.send_message(chat_id, text, reply_markup=keyboard)

    autoteka_uuid = get_autoteka_s3_url(obj['autoteka_id'])
    if autoteka_uuid:
        try:
            url = s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': BUCKET_NAME, 'Key': f'files/{autoteka_uuid}.pdf'},
                ExpiresIn=3600
            )
            keyboard_doc = types.InlineKeyboardMarkup()
            keyboard_doc.add(types.InlineKeyboardButton('Скачать автотеку 📄', url=url))
            bot.send_message(chat_id, 'Автотека:', reply_markup=keyboard_doc)
        except Exception as e:
            print(f'Ошибка при генерации ссылки на автотеку: {e}')
```

- [ ] **Step 4: Commit**

```bash
git add bot.py
git commit -m "feat: add admin conveyor - show_next_pending with full details and action buttons"
```

---

### Task 6: Rewrite `publish_application_to_channel` to use `objects` table

**Files:**
- Modify: `bot.py:779-797` (`publish_application_to_channel`)

- [ ] **Step 1: Rewrite the function**

Replace `publish_application_to_channel` (lines 779-797) with:

```python
def publish_to_channel(obj_uuid, target_channel):
    obj = get_object_by_uuid(obj_uuid)
    if not obj:
        return
    caption = (
        f'{obj["description"]}\n'
        f'Цена: {obj["price"]}\n'
        f'Контакты: {obj["contact"]}'
    )
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton('Предложить собственный автомобиль 🚗', callback_data='propose_car'))
    keyboard.add(types.InlineKeyboardButton('Подписаться на закрытый канал 🔒', callback_data='subscribe_now'))

    if obj['photos']:
        media = [types.InputMediaPhoto(photo) for photo in obj['photos']]
        if media:
            media[0] = types.InputMediaPhoto(obj['photos'][0], caption=caption)
        bot.send_media_group(target_channel, media)
    else:
        bot.send_message(target_channel, caption)

    bot.send_message(target_channel, 'Действия:', reply_markup=keyboard)
```

- [ ] **Step 2: Commit**

```bash
git add bot.py
git commit -m "feat: rewrite publish_to_channel to use objects table"
```

---

### Task 7: Rewrite `callback_inline` — replace old admin handlers with new conveyor handlers

**Files:**
- Modify: `bot.py:800-919` (`callback_inline`)

- [ ] **Step 1: Replace the `admin` callback handler**

Replace lines 808-811:

```python
    if data == 'admin':
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, 'Управление заявками: используйте уведомления от бота для публикации и отклонения заявок.')
        return
```

with:

```python
    if data == 'admin':
        bot.answer_callback_query(call.id)
        show_next_pending(call.message.chat.id)
        return
```

- [ ] **Step 2: Add new admin conveyor handlers**

Add these handlers inside `callback_inline`, after the `subscribe_now` handler (after line 891) and before the old `publish_open_` handler:

```python
    if data == 'admin_review_apps':
        bot.answer_callback_query(call.id)
        show_next_pending(call.message.chat.id)
        return
    if data.startswith('admin_publish_open_'):
        obj_uuid = data.replace('admin_publish_open_', '')
        publish_to_channel(obj_uuid, CHAT_ID)
        update_object_status(obj_uuid, APPLICATION_STATUS_PUBLISHED_OPEN)
        bot.answer_callback_query(call.id, 'Опубликовано в открытом канале')
        show_next_pending(call.message.chat.id)
        return
    if data.startswith('admin_publish_closed_'):
        obj_uuid = data.replace('admin_publish_closed_', '')
        publish_to_channel(obj_uuid, PRIVATE_CHANNEL_ID)
        update_object_status(obj_uuid, APPLICATION_STATUS_PUBLISHED_CLOSED)
        bot.answer_callback_query(call.id, 'Опубликовано в закрытом канале')
        show_next_pending(call.message.chat.id)
        return
    if data.startswith('admin_publish_both_'):
        obj_uuid = data.replace('admin_publish_both_', '')
        publish_to_channel(obj_uuid, CHAT_ID)
        publish_to_channel(obj_uuid, PRIVATE_CHANNEL_ID)
        update_object_status(obj_uuid, APPLICATION_STATUS_PUBLISHED_BOTH)
        bot.answer_callback_query(call.id, 'Опубликовано в оба канала')
        show_next_pending(call.message.chat.id)
        return
    if data.startswith('admin_reject_'):
        obj_uuid = data.replace('admin_reject_', '')
        update_object_status(obj_uuid, APPLICATION_STATUS_REJECTED)
        bot.answer_callback_query(call.id, 'Заявка отклонена')
        show_next_pending(call.message.chat.id)
        return
    if data.startswith('admin_skip_'):
        bot.answer_callback_query(call.id)
        show_next_pending(call.message.chat.id)
        return
```

- [ ] **Step 3: Remove old admin callback handlers**

Delete these blocks (lines 892-918):

```python
    if data.startswith('publish_open_'):
        ...
    if data.startswith('publish_closed_'):
        ...
    if data.startswith('contact_seller_'):
        ...
    if data.startswith('reject_app_'):
        ...
```

- [ ] **Step 4: Commit**

```bash
git add bot.py
git commit -m "feat: replace old admin handlers with conveyor review system"
```

---

### Task 8: Update user-facing status functions to use `objects` table

**Files:**
- Modify: `bot.py:752-776` (`application_status`, `active_applications`)

- [ ] **Step 1: Update `application_status` function**

Replace lines 752-762:

```python
def application_status(message):
    applications = get_user_objects(message.from_user.id)
    if not applications:
        bot.send_message(message.chat.id, 'У вас пока нет заявок.')
        return
    parts = []
    for obj_uuid, description, price, contact, status, created_at in applications[:5]:
        parts.append(
            f'Заявка: {obj_uuid}\nСтатус: {status}\nЦена: {price}\nКонтакты: {contact}\nОписание: {description}\nДата: {format_datetime(created_at)}\n'
        )
    bot.send_message(message.chat.id, '\n\n'.join(parts))
```

- [ ] **Step 2: Update `active_applications` function**

Replace lines 765-776:

```python
def active_applications(message):
    applications = get_user_objects(message.from_user.id)
    active = [row for row in applications if row[4] in (APPLICATION_STATUS_PENDING, APPLICATION_STATUS_PUBLISHED_OPEN, APPLICATION_STATUS_PUBLISHED_CLOSED, APPLICATION_STATUS_PUBLISHED_BOTH)]
    if not active:
        bot.send_message(message.chat.id, 'Активных заявок нет.')
        return
    parts = []
    for obj_uuid, description, price, contact, status, created_at in active[:5]:
        parts.append(
            f'Заявка: {obj_uuid}\nСтатус: {status}\nЦена: {price}\nДата: {format_datetime(created_at)}'
        )
    bot.send_message(message.chat.id, '\n\n'.join(parts))
```

- [ ] **Step 3: Commit**

```bash
git add bot.py
git commit -m "feat: update user status functions to use objects table"
```

---

### Task 9: Update admin menu button handler and clean up dead code

**Files:**
- Modify: `bot.py:911-913` (`handle_admin`)
- Modify: `bot.py` — remove unused functions

- [ ] **Step 1: Update `handle_admin` handler**

Replace lines 911-913:

```python
@bot.message_handler(func=lambda message: message.text == BTN_ADMIN and message.from_user.id == OWNER_ID)
def handle_admin(message):
    bot.send_message(message.chat.id, 'Управление заявками: используйте уведомления от бота для публикации и отклонения заявок.')
```

with:

```python
@bot.message_handler(func=lambda message: message.text == BTN_ADMIN and message.from_user.id == OWNER_ID)
def handle_admin(message):
    show_next_pending(message.chat.id)
```

- [ ] **Step 2: Remove dead code**

Delete these functions that are no longer called:
- `delete_message` (lines 367-374) — referenced channel messages that no longer exist
- `create_payment` (lines 376-390) — was used for channel publishing buttons, no longer needed in this flow
- `send_application_to_admin` (lines 544-538) — replaced by `notify_admin_new_application`
- `get_contact` (lines 537-541) — replaced by `input_contact`

- [ ] **Step 3: Remove `delete_videos_with_substring` reference**

In `input_autoteka`'s cancel branch, if `delete_videos_with_substring` is still referenced, remove that call (it was already removed in Task 3).

- [ ] **Step 4: Commit**

```bash
git add bot.py
git commit -m "chore: clean up dead code - remove unused channel publishing and payment functions"
```

---

### Task 10: Manual smoke test

- [ ] **Step 1: Start the bot**

Run: `python bot.py`

Expected: Bot starts without import/syntax errors, begins polling.

- [ ] **Step 2: Test user flow**

In Telegram, send `/start` to the bot. Click "Предложить автомобиль". Go through:
1. Enter description → should ask for price
2. Enter price → should ask for photos
3. Upload 1-2 photos, type "Готово" → should ask for autoteka (NO channel publish)
4. Upload a PDF → should ask for contact info
5. Enter contact → should say "Ваша заявка отправлена на проверку"

Expected: No messages appear in the channel. Admin receives notification with pending count.

- [ ] **Step 3: Test admin conveyor**

As admin (OWNER_ID), click "Посмотреть заявки" on the notification (or use "Управление заявками" button).

Expected: Bot shows photos, description, price, contact, autoteka link, and 5 action buttons.

Click "В открытый канал" → listing should appear in the open channel, next pending shown automatically.

- [ ] **Step 4: Test edge cases**

- Submit a second application, then test "В оба канала"
- Test "Отклонить" — status should update, next application shown
- Test "Пропустить" — next application shown, skipped one stays pending
- When no pending applications left — should say "Нет заявок на проверку"
- Test "Статус заявки" as user — should show correct statuses
