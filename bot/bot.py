import os
import telebot
from telebot import types
import requests
import jwt
import time
import threading
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import boto3
from botocore.client import Config
import uuid
import psycopg2
from psycopg2 import sql
from yookassa import Configuration
from io import BytesIO
from datetime import datetime, timedelta, timezone

LOCAL_TZ = timezone(timedelta(hours=5))  # Сургут UTC+5

def _env(name, default=''):
    return os.environ.get(name, default)


def _env_int(name, default=0):
    value = os.environ.get(name)
    return int(value) if value else default


Configuration.account_id = _env('YOOKASSA_ACCOUNT_ID')
Configuration.secret_key = _env('YOOKASSA_SECRET_KEY')

BUCKET_NAME = _env('S3_BUCKET_NAME')

session = boto3.session.Session()
s3 = session.client(
    service_name='s3',
    endpoint_url=_env('S3_ENDPOINT_URL', 'https://storage.yandexcloud.net'),
    aws_access_key_id=_env('S3_ACCESS_KEY_ID'),
    aws_secret_access_key=_env('S3_SECRET_ACCESS_KEY'),
    config=Config(signature_version='s3')
)

API_TOKEN = _env('TELEGRAM_BOT_TOKEN')
OWNER_ID = _env_int('OWNER_ID')
DATABASE_URL = _env('DATABASE_URL', "dbname='postgres' user='postgres' password='' host='localhost'")
CHAT_ID = _env_int('CHAT_ID')
PRIVATE_CHANNEL_ID = _env_int('PRIVATE_CHANNEL_ID')
OPEN_CHANNEL_URL = _env('OPEN_CHANNEL_URL')
PRIVATE_CHANNEL_URL = _env('PRIVATE_CHANNEL_URL')
SITE_URL = _env('SITE_URL')
VK_URL = _env('VK_URL')
INSTAGRAM_URL = _env('INSTAGRAM_URL')
MAX_URL = _env('MAX_URL')
MANAGER_CONTACT = _env('MANAGER_CONTACT')
SUPPORT_CONTACT = _env('SUPPORT_CONTACT')
DEV_CONTACT_URL = _env('DEV_CONTACT_URL')

bot = telebot.TeleBot(API_TOKEN)

user_data = {}

YOOMONEY_WALLET = _env('YOOMONEY_WALLET')
YOOMONEY_TOKEN = _env('YOOMONEY_TOKEN')
CRYPTOPAY_TOKEN = _env('CRYPTOPAY_TOKEN')
CRYPTOPAY_TESTNET = _env('CRYPTOPAY_TESTNET', '1') == '1'

# SMTP для отправки чеков на email
SMTP_HOST = _env('SMTP_HOST', 'smtp.yandex.ru')
SMTP_PORT = _env_int('SMTP_PORT', 465)
SMTP_USER = _env('SMTP_USER')
SMTP_PASSWORD = _env('SMTP_PASSWORD')
SMTP_FROM_NAME = _env('SMTP_FROM_NAME', 'PRODAYAUTO86')

SUBSCRIPTION_PLANS = [
    {'name': '1 месяц', 'months': 1, 'price': 200, 'days': 30},
    {'name': '2 месяца', 'months': 2, 'price': 378, 'days': 60},
    {'name': '3 месяца', 'months': 3, 'price': 537, 'days': 90},
    {'name': '6 месяцев', 'months': 6, 'price': 964, 'days': 180},
    {'name': '12 месяцев', 'months': 12, 'price': 1671, 'days': 365},
]

BTN_PROPOSE = 'Предложить автомобиль 🚗'
BTN_SUBSCRIBE = 'Оформить подписку 👑'
BTN_RENEW = 'Продлить подписку 🔄'
BTN_SUB_STATUS = 'Статус подписки 📊'
BTN_APPLICATION_STATUS = 'Посмотреть статус заявки 📄'
BTN_ACTIVE_APPLICATIONS = 'Посмотреть активные заявки 📌'
BTN_ABOUT = 'Почитать о нас ℹ️'
BTN_MANAGER = 'Связаться с менеджером 👨‍💼'
BTN_SUPPORT = 'Связаться с поддержкой 🛠️'
BTN_SITE = 'Посмотреть сайт 🌐'
BTN_OPEN_CHANNEL = 'Посмотреть открытый канал 🔓'
BTN_PRIVATE_CHANNEL = 'Посмотреть закрытый канал 🔒'
BTN_ADMIN = 'Управление заявками ⚙️'

APPLICATION_STATUS_PENDING = 'pending'
APPLICATION_STATUS_REJECTED = 'rejected'
APPLICATION_STATUS_PUBLISHED_OPEN = 'published_open'
APPLICATION_STATUS_PUBLISHED_CLOSED = 'published_closed'
APPLICATION_STATUS_PUBLISHED_BOTH = 'published_both'

SUBSCRIPTION_STATUS_ACTIVE = 'active'
SUBSCRIPTION_STATUS_PENDING = 'pending'
SUBSCRIPTION_STATUS_EXPIRED = 'expired'

APPLICATION_STATUS_LABELS = {
    APPLICATION_STATUS_PENDING: 'На проверке ⏳',
    APPLICATION_STATUS_REJECTED: 'Отклонено ❌',
    APPLICATION_STATUS_PUBLISHED_OPEN: 'Опубликовано в открытом канале 🔓',
    APPLICATION_STATUS_PUBLISHED_CLOSED: 'Опубликовано в закрытом канале 🔒',
    APPLICATION_STATUS_PUBLISHED_BOTH: 'Опубликовано в обоих каналах 📢',
}

SUBSCRIPTION_STATUS_LABELS = {
    SUBSCRIPTION_STATUS_ACTIVE: 'Активна ✅',
    SUBSCRIPTION_STATUS_PENDING: 'Ожидает оплаты ⏳',
    SUBSCRIPTION_STATUS_EXPIRED: 'Истекла ❌',
}


def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn


def format_datetime(dt):
    if not dt:
        return '—'
    # Даты хранятся в UTC (naive), переводим в UTC+5 для отображения
    dt_local = dt.replace(tzinfo=timezone.utc).astimezone(LOCAL_TZ)
    return dt_local.strftime('%d.%m.%Y %H:%M')


def is_cancel(message):
    return message.text and message.text.strip().lower() == 'отмена'


def is_skip_receipt(message):
    return message.text and message.text.strip().lower() in ['отказаться от чека', 'нет чека']


def send_main_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    if message.from_user.id == OWNER_ID:
        markup.add(BTN_ADMIN)
    else:
        markup.add(BTN_PROPOSE, BTN_SUB_STATUS)
        markup.add(BTN_SUBSCRIBE, BTN_RENEW)
        markup.add(BTN_APPLICATION_STATUS, BTN_ACTIVE_APPLICATIONS)
        markup.add(BTN_ABOUT, BTN_MANAGER)
        markup.add(BTN_SUPPORT, BTN_SITE)
        markup.add(BTN_OPEN_CHANNEL, BTN_PRIVATE_CHANNEL)
    bot.send_message(message.chat.id, 'Выберите действие:', reply_markup=markup)


def check_subscription_notifications(user_id, chat_id):
    subscription = get_subscription(user_id)
    if not subscription:
        return
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if subscription['end_date'] and subscription['end_date'] < now:
        if subscription['status'] != SUBSCRIPTION_STATUS_EXPIRED:
            update_subscription_status(user_id, SUBSCRIPTION_STATUS_EXPIRED)
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton('Продлить подписку 🔄', callback_data='renew_subscription'))
        bot.send_message(chat_id, 'Ваша подписка закончилась. Продлите подписку, чтобы снова получить доступ к закрытому каналу.', reply_markup=keyboard)
    elif subscription['end_date'] and subscription['end_date'] - now <= timedelta(days=3):
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton('Продлить подписку 🔄', callback_data='renew_subscription'))
        bot.send_message(chat_id, f'Ваша подписка истекает {format_datetime(subscription["end_date"])}. Хотите продлить её?', reply_markup=keyboard)


def remove_from_private_channel(user_id):
    try:
        member = bot.get_chat_member(PRIVATE_CHANNEL_ID, user_id)

        if member.status in ['member', 'restricted']:
            bot.ban_chat_member(PRIVATE_CHANNEL_ID, user_id)
            bot.unban_chat_member(PRIVATE_CHANNEL_ID, user_id)
            print(f"Пользователь {user_id} удалён из канала")
        else:
            print(f"Пользователь {user_id} не в канале")
    except Exception as e:
        print(f'Ошибка удаления пользователя {user_id}: {e}')

@bot.chat_member_handler()
def handle_user_join(update):
    try:
        if update.chat.id != PRIVATE_CHANNEL_ID:
            return
        new_status = update.new_chat_member.status
        user_id = update.new_chat_member.user.id  # кто вступил, не кто добавил

        if new_status == 'member':
            subscription = get_subscription(user_id)
            if (
                not subscription or
                subscription['status'] != SUBSCRIPTION_STATUS_ACTIVE or
                not subscription['end_date'] or
                subscription['end_date'] < datetime.now(timezone.utc).replace(tzinfo=None)
            ):
                remove_from_private_channel(user_id)
                print(f"Удалён при входе (нет подписки): {user_id}")

    except Exception as e:
        print(f'Ошибка при входе пользователя: {e}')

def allow_in_private_channel(user_id):
    try:
        member = bot.get_chat_member(PRIVATE_CHANNEL_ID, user_id)
        if member.status == 'kicked':
            bot.unban_chat_member(PRIVATE_CHANNEL_ID, user_id)
            print(f'Пользователь {user_id} разблокирован в канале')
        # иначе — не был заблокирован, ничего не делаем
    except Exception as e:
        print(f'Не удалось разблокировать пользователя в закрытом канале: {e}')


def send_receipt_email(to_email, amount, plan_name, end_date):
    if not SMTP_USER or not SMTP_PASSWORD:
        print('SMTP не настроен, чек не отправлен')
        return
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'Чек об оплате подписки — PRODAYAUTO86'
        msg['From'] = f'{SMTP_FROM_NAME} <{SMTP_USER}>'
        msg['To'] = to_email
        end_str = end_date.replace(tzinfo=timezone.utc).astimezone(LOCAL_TZ).strftime('%d.%m.%Y') if end_date else '—'
        body = (
            f'Спасибо за оплату!\n\n'
            f'Услуга: Подписка {plan_name}\n'
            f'Сумма: {amount} ₽\n'
            f'Действует до: {end_str}\n\n'
            f'С уважением,\nPRODAYAUTO86'
        )
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, to_email, msg.as_string())
        print(f'Чек отправлен на {to_email}')
    except Exception as e:
        print(f'Ошибка отправки чека на {to_email}: {e}')


def generate_one_time_invite(user_id):
    try:
        expire = datetime.now(timezone.utc) + timedelta(hours=24)
        link = bot.create_chat_invite_link(
            PRIVATE_CHANNEL_ID,
            name=f'user_{user_id}',
            expire_date=expire,
            member_limit=1,
        )
        return link.invite_link
    except Exception as e:
        print(f'Не удалось создать ссылку-приглашение для {user_id}: {e}')
        return None
    
def give_access_after_payment(user_id):
    link = generate_one_time_invite(user_id)

    if link:
        bot.send_message(
            user_id,
            f"✅ Оплата прошла!\n\n"
            f"Вот ссылка в закрытый канал:\n{link}\n\n"
            f"⚠️ Ссылка одноразовая и действует 24 часа"
        )
    else:
        bot.send_message(user_id, "Ошибка выдачи доступа, напишите менеджеру")

def _expire_subscriptions(catch_up=False):
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    # Активные с истёкшей датой → перевести в expired и выкинуть
    cursor.execute(
        "SELECT user_id FROM subscriptions WHERE status = %s AND end_date < %s",
        (SUBSCRIPTION_STATUS_ACTIVE, now)
    )
    to_expire = [row[0] for row in cursor.fetchall()]
    # При catch_up (старт бота) — также выкинуть уже expired,
    # на случай если бот был перезапущен и не успел их удалить
    if catch_up:
        cursor.execute(
            "SELECT user_id FROM subscriptions WHERE status = %s",
            (SUBSCRIPTION_STATUS_EXPIRED,)
        )
        already_expired = [row[0] for row in cursor.fetchall()]
    else:
        already_expired = []
    cursor.close()
    conn.close()

    for user_id in to_expire:
        update_subscription_status(user_id, SUBSCRIPTION_STATUS_EXPIRED)
        remove_from_private_channel(user_id)
        try:
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton('Продлить подписку 🔄', callback_data='renew_subscription'))
            bot.send_message(
                user_id,
                'Ваша подписка закончилась. Вы удалены из закрытого канала.\n'
                'Продлите подписку для восстановления доступа.',
                reply_markup=keyboard
            )
        except Exception as e:
            print(f'Не удалось уведомить пользователя {user_id} об истечении подписки: {e}')

    for user_id in already_expired:
        remove_from_private_channel(user_id)  # без уведомления — уже получили


def _run_subscription_checker():
    # Сразу при старте — выкидываем всех с просроченной/истёкшей подпиской
    try:
        _expire_subscriptions(catch_up=True)
    except Exception as e:
        print(f'Ошибка первичной проверки подписок: {e}')
    while True:
        time.sleep(300)  # каждые 5 минут
        try:
            _expire_subscriptions()
        except Exception as e:
            print(f'Ошибка планировщика подписок: {e}')


def get_subscription(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT email, status, plan, start_date, end_date, payment_id, amount FROM subscriptions WHERE user_id = %s",
        (user_id,)
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if not row:
        return None
    return {
        'email': row[0],
        'status': row[1],
        'plan': row[2],
        'start_date': row[3],
        'end_date': row[4],
        'payment_id': row[5],
        'amount': row[6],
    }


def update_subscription_status(user_id, status):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE subscriptions SET status = %s, updated_at = NOW() WHERE user_id = %s",
        (status, user_id)
    )
    conn.commit()
    cursor.close()
    conn.close()


def create_or_update_subscription(user_id, email, plan, start_date, end_date, amount, payment_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO subscriptions (user_id, email, status, plan, start_date, end_date, amount, payment_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        " ON CONFLICT (user_id) DO UPDATE SET email = EXCLUDED.email, status = EXCLUDED.status, plan = EXCLUDED.plan, start_date = EXCLUDED.start_date, end_date = EXCLUDED.end_date, amount = EXCLUDED.amount, payment_id = EXCLUDED.payment_id, updated_at = NOW()",
        (user_id, email, SUBSCRIPTION_STATUS_PENDING, plan, start_date, end_date, amount, payment_id)
    )
    conn.commit()
    cursor.close()
    conn.close()


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


def get_pending_count():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM objects WHERE status = %s", (APPLICATION_STATUS_PENDING,))
    count = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return count


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


def build_main_menu_markup(user_id):
    if user_id == OWNER_ID:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False, row_width=1)
        markup.add(BTN_ADMIN)
        return markup
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False, row_width=2)
    subscription = get_subscription(user_id)
    has_active_subscription = subscription and subscription['status'] == SUBSCRIPTION_STATUS_ACTIVE and subscription['end_date'] and subscription['end_date'] > datetime.now(timezone.utc).replace(tzinfo=None)
    markup.add(BTN_PROPOSE, BTN_SUB_STATUS)
    if has_active_subscription:
        markup.add(BTN_RENEW, BTN_APPLICATION_STATUS)
    else:
        markup.add(BTN_SUBSCRIBE, BTN_APPLICATION_STATUS)
    markup.add(BTN_ABOUT, BTN_MANAGER)
    markup.add(BTN_SUPPORT)
    return markup


def build_start_inline_markup(user_id):
    if user_id == OWNER_ID:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('Управление заявками ⚙️', callback_data='admin'))
    markup = types.InlineKeyboardMarkup(row_width=2)
    subscription = get_subscription(user_id)
    has_active_subscription = subscription and subscription['status'] == SUBSCRIPTION_STATUS_ACTIVE and subscription['end_date'] and subscription['end_date'] > datetime.now(timezone.utc).replace(tzinfo=None)
    markup.add(
        types.InlineKeyboardButton('Предложить автомобиль 🚗', callback_data='propose_car'),
        types.InlineKeyboardButton('Статус подписки 📊', callback_data='sub_status')
    )
    if has_active_subscription:
        markup.add(
            types.InlineKeyboardButton('Продлить подписку 🔄', callback_data='renew_subscription'),
            types.InlineKeyboardButton('Статус заявки 📄', callback_data='app_status')
        )
    else:
        markup.add(
            types.InlineKeyboardButton('Оформить подписку 👑', callback_data='subscribe'),
            types.InlineKeyboardButton('Статус заявки 📄', callback_data='app_status')
        )
    markup.add(
        types.InlineKeyboardButton('О нас ℹ️', callback_data='about'),
        types.InlineKeyboardButton('Связь с менеджером 👨‍💼', callback_data='manager')
    )
    markup.add(types.InlineKeyboardButton('Поддержка 🛠️', callback_data='support'))
    return markup


def start(message):
    check_subscription_notifications(message.from_user.id, message.chat.id)
    markup = build_start_inline_markup(message.from_user.id)
    welcome_text = (
        'Привет! 👋\n'
        'Я бот сервиса PRODAYAUTO86 🚗\n\n'
        'Помогу быстро продать автомобиль и получить доступ к закрытым предложениям.\n\n'
        '🔧 Что я умею:\n\n'
        '1️⃣ Предложить автомобиль\n'
        'Отправь информацию — мы разместим заявку и поможем с дальнейшей продажей.\n\n'
        '2️⃣ Статус подписки\n'
        'Проверь, активен ли доступ к закрытому каналу.\n\n'
        '3️⃣ Оформить подписку\n'
        'Получай эксклюзивные авто и специальные предложения.\n\n'
        '4️⃣ О нас\n'
        'Узнай, как работает сервис и где найти каналы.\n\n'
        '5️⃣ Связь с менеджером\n'
        'Задай любой вопрос напрямую.\n\n'
        '6️⃣ Статус заявки\n'
        'Отслеживай этап обработки твоей продажи.\n\n'
        '⚡ Быстро • Просто • Выгодно'
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)


def menu(message):
    markup = build_main_menu_markup(message.from_user.id)
    bot.send_message(message.chat.id, 'Выберите действие:', reply_markup=markup)


@bot.message_handler(commands=['start'])
def handle_start(message):
    start(message)


@bot.message_handler(commands=['activate'])
def handle_activate(message):
    if message.from_user.id != OWNER_ID:
        return
    parts = message.text.strip().split()
    if len(parts) != 2 or not parts[1].isdigit():
        bot.send_message(message.chat.id, 'Использование: /activate {user_id}\nНапример: /activate 123456789')
        return
    target_id = int(parts[1])
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    end_date = now + timedelta(days=30)
    create_or_update_subscription(
        user_id=target_id,
        email=None,
        plan='Тест (1 месяц)',
        start_date=now,
        end_date=end_date,
        amount=0,
        payment_id='manual_test',
    )
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE subscriptions SET status = %s WHERE user_id = %s', (SUBSCRIPTION_STATUS_ACTIVE, target_id))
    conn.commit()
    cursor.close()
    conn.close()
    bot.send_message(message.chat.id, f'Подписка активирована для {target_id} до {end_date.replace(tzinfo=timezone.utc).astimezone(LOCAL_TZ).strftime("%d.%m.%Y")} ✅')
    try:
        bot.send_message(target_id, 'Ваша подписка активирована! ✅')
    except Exception:
        pass


@bot.message_handler(commands=['kickexpired'])
def handle_kick_expired(message):
    if message.from_user.id != OWNER_ID:
        return
    bot.send_message(message.chat.id, 'Запускаю проверку просроченных подписок...')
    try:
        _expire_subscriptions(catch_up=True)
        bot.send_message(message.chat.id, 'Готово ✅')
    except Exception as e:
        bot.send_message(message.chat.id, f'Ошибка: {e}')


@bot.message_handler(commands=['testchannel'])
def handle_test_channel(message):
    if message.from_user.id != OWNER_ID:
        return
    lines = [f'PRIVATE_CHANNEL_ID: <code>{PRIVATE_CHANNEL_ID}</code>\n']
    # Проверяем, что бот является администратором канала
    try:
        member = bot.get_chat_member(PRIVATE_CHANNEL_ID, bot.get_me().id)
        lines.append(f'✅ Бот в канале. Статус: <b>{member.status}</b>')
        if member.status not in ('administrator', 'creator'):
            lines.append('⚠️ Бот не администратор — нужны права администратора!')
    except Exception as e:
        lines.append(f'❌ Бот не может получить доступ к каналу: {e}')
        lines.append('\nКак исправить:')
        lines.append('1. Откройте канал → Управление каналом → Администраторы')
        lines.append('2. Добавьте бота как администратора')
        lines.append('3. Выдайте права: Добавлять участников, Блокировать участников')
        lines.append('\nЕсли канал правильный, но ошибка — проверьте ID канала.')
        lines.append('Перешлите любое сообщение из канала боту @userinfobot чтобы узнать ID.')
    # Проверяем тестовую генерацию ссылки
    try:
        expire = datetime.now(timezone.utc) + timedelta(minutes=1)
        test_link = bot.create_chat_invite_link(PRIVATE_CHANNEL_ID, name='test', expire_date=expire, member_limit=1)
        lines.append(f'\n✅ Тестовая ссылка создана: {test_link.invite_link}')
        bot.revoke_chat_invite_link(PRIVATE_CHANNEL_ID, test_link.invite_link)
        lines.append('(ссылка сразу отозвана)')
    except Exception as e:
        lines.append(f'\n❌ Не удалось создать ссылку: {e}')
    bot.send_message(message.chat.id, '\n'.join(lines), parse_mode='HTML')


@bot.message_handler(commands=['menu'])
def handle_menu(message):
    menu(message)


def get_subscription_button_keyboard(text, callback):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text, callback_data=callback))
    return markup


@bot.message_handler(func=lambda message: message.text == BTN_PROPOSE)
def propose_car(message):
    bot.send_message(message.chat.id, "Вы нажали на кнопку добавления автомобиля. Для добавления автомобиля Вам необходимо добавить описание, фотографии и автотеку. Фотографии можно отправить одним альбомом или по одной. Если хотите отменить добавление, напишите в чат 'Отмена'")
    bot.send_message(message.chat.id, "Добавьте описание 📝")
    bot.register_next_step_handler(message, input_description)

def cancel_add(message, user_id):
    bot.send_message(message.chat.id, "Операция отменена, дождитесь окончания транзакции ❌")
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        sql.SQL("DELETE FROM Objects WHERE uuid = %s"),
        [user_data[user_id]['uuid']]
    )
    conn.commit()
    cursor.close()
    conn.close()
    bot.send_message(message.chat.id, f"Запись в базе данных успешно удалена 🗑")

def input_description(message):
    if message.text is not None and message.text.lower() == 'отмена':
        bot.send_message(message.chat.id, "Операция отменена ❌")
        return

    user_input = message.text
    user_id = message.from_user.id
    car_uuid = str(uuid.uuid4())
    user_data[user_id] = {'description': user_input, 'uuid': car_uuid}

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        sql.SQL("INSERT INTO objects (uuid, description) VALUES (%s, %s) RETURNING id"),
        (car_uuid, user_data[user_id]['description'])
    )
    user_data[user_id]['object_id'] = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()
    
    bot.send_message(message.chat.id, "Введите цену 💵")
    bot.register_next_step_handler(message, input_price)


def input_price(message):
    user_id = message.from_user.id

    if message.text is not None and message.text.lower() == 'отмена':
        cancel_add(message, user_id)

        bot.send_message(message.chat.id, "Готово! ✅")
        return

    user_input = message.text
    user_data[user_id]['price'] = user_input
    
    bot.send_message(message.chat.id, "Отправляйте фотографии по одной. Когда все добавите — напишите 'Готово' 📷")
    bot.register_next_step_handler(message, input_photos)


def input_photos(message):
    user_id = message.from_user.id

    if message.text is not None and message.text.lower() == 'отмена':
        cancel_add(message, user_id)
        bot.send_message(message.chat.id, "Готово! ✅")
        return

    if message.text is not None and message.text.lower() != 'готово':
        bot.send_message(message.chat.id, "Упс, вы ввели неправильное значение! Повторите 😅")
        bot.register_next_step_handler(message, input_photos)
        return

    if message.text is not None and message.text.lower() == 'готово':
        if not user_data[user_id].get('photos'):
            bot.send_message(message.chat.id, "Вы не добавили ни одной фотографии. Добавьте хотя бы одну 📷")
            bot.register_next_step_handler(message, input_photos)
            return
        bot.send_message(message.chat.id, "Все фотографии сохранены ✅")
        bot.send_message(message.chat.id, "Добавьте автотеку 📄")
        bot.register_next_step_handler(message, input_autoteka)
        return

    if message.photo:
        if 'photos' not in user_data[user_id]:
            user_data[user_id]['photos'] = []
        photo_id = message.photo[-1].file_id
        user_data[user_id]['photos'].append(photo_id)
        total = len(user_data[user_id]['photos'])
        if total == 1:
            bot.send_message(message.chat.id, "Фото сохранено! Отправьте ещё или напишите 'Готово'.")
        else:
            bot.send_message(message.chat.id, f"Сохранено {total} фото. Отправьте ещё или напишите 'Готово'.")
        bot.register_next_step_handler(message, input_photos)


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

        bot.send_message(message.chat.id, "Введите ваше имя 👤")
        bot.register_next_step_handler(message, input_name)
    except Exception as e:
        print(f"Ошибка: {e}")


def notify_admin_new_application():
    count = get_pending_count()
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton('Посмотреть заявки 📋', callback_data='admin_review_apps'))
    bot.send_message(
        OWNER_ID,
        f'Новая заявка. Ожидает проверки: {count}',
        reply_markup=keyboard
    )


def input_name(message):
    user_id = message.from_user.id
    if is_cancel(message):
        cancel_add(message, user_id)
        bot.send_message(message.chat.id, "Готово! ✅")
        return
    user_data[user_id]['name'] = message.text.strip() if message.text else ''
    bot.send_message(message.chat.id, "Введите номер телефона 📞")
    bot.register_next_step_handler(message, input_phone)


def input_phone(message):
    user_id = message.from_user.id
    if is_cancel(message):
        cancel_add(message, user_id)
        bot.send_message(message.chat.id, "Готово! ✅")
        return
    user_data[user_id]['phone'] = message.text.strip() if message.text else ''
    bot.send_message(message.chat.id, "Введите ник в Telegram (например @username) или «-» если нет 📱")
    bot.register_next_step_handler(message, input_telegram_handle)


def input_telegram_handle(message):
    user_id = message.from_user.id
    if is_cancel(message):
        cancel_add(message, user_id)
        bot.send_message(message.chat.id, "Готово! ✅")
        return
    tg = message.text.strip() if message.text else ''
    if tg == '-':
        tg = ''

    name = user_data[user_id].get('name', '')
    phone = user_data[user_id].get('phone', '')
    contact_parts = [f'Имя: {name}', f'Телефон: {phone}']
    if tg:
        contact_parts.append(f'Telegram: {tg}')
    contact = '\n'.join(contact_parts)

    finalize_object(
        object_id=user_data[user_id]['object_id'],
        user_id=user_id,
        price=user_data[user_id].get('price'),
        contact=contact,
        photo_file_ids=user_data[user_id].get('photos', []),
    )

    notify_admin_new_application()

    bot.send_message(message.chat.id, 'Ваша заявка отправлена на проверку ✅')
    user_data.pop(user_id, None)


@bot.message_handler(func=lambda message: message.text == BTN_SUBSCRIBE)
def subscribe(message):
    subscription = get_subscription(message.from_user.id)
    if subscription and subscription['status'] == SUBSCRIPTION_STATUS_ACTIVE and subscription['end_date'] and subscription['end_date'] > datetime.now(timezone.utc).replace(tzinfo=None):
        bot.send_message(message.chat.id, f'У вас уже есть активная подписка до {format_datetime(subscription["end_date"])}. Мы сообщим вам за 3 дня до окончания.')
        return
    show_subscription_plans(message.chat.id, message.from_user.id, action='subscribe')


@bot.message_handler(func=lambda message: message.text == BTN_RENEW)
def renew(message):
    show_subscription_plans(message.chat.id, message.from_user.id, action='renew')


def show_subscription_plans(chat_id, user_id, action):
    markup = types.InlineKeyboardMarkup()
    for plan in SUBSCRIPTION_PLANS:
        markup.add(types.InlineKeyboardButton(
            f"{plan['name']} — {plan['price']}р", callback_data=f"select_plan_{plan['months']}_{action}"))
    markup.add(types.InlineKeyboardButton('Связь с разработчиком', url=DEV_CONTACT_URL))
    bot.send_message(chat_id, 'Выберите вариант подписки. После выбора вы получите инструкцию по оплате и оформлению.', reply_markup=markup)


def ask_for_email(message, user_id, action, plan_name, plan_days, plan_price):
    user_data[user_id] = {
        'flow': 'subscription',
        'action': action,
        'plan_name': plan_name,
        'plan_days': plan_days,
        'plan_price': plan_price,
    }
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton('Отказаться от чека ❌', callback_data='skip_receipt'))
    bot.send_message(message.chat.id, 'Введите email для чека или нажмите кнопку, если чек не нужен.', reply_markup=keyboard)
    bot.register_next_step_handler(message, handle_subscription_email)


def handle_subscription_email(message):
    user_id = message.from_user.id
    if is_cancel(message):
        bot.send_message(message.chat.id, 'Операция отменена ❌')
        user_data.pop(user_id, None)
        return
    if is_skip_receipt(message):
        if user_id not in user_data:
            return  # обработчик устарел, платёж уже запущен
        user_data[user_id]['email'] = None
        send_payment_options(message.chat.id, user_id)
        return
    if user_id not in user_data:
        return  # обработчик устарел, игнорируем
    email = message.text.strip() if message.text else ''
    if '@' not in email:
        bot.send_message(message.chat.id, 'Пожалуйста, введите корректный email или напишите Отказаться от чека.')
        bot.register_next_step_handler(message, handle_subscription_email)
        return
    user_data[user_id]['email'] = email
    send_payment_options(message.chat.id, user_id)


def send_payment_options(chat_id, user_id):
    if user_id not in user_data:
        bot.send_message(chat_id, 'Ошибка. Начните оформление подписки заново.')
        return
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton('Оплатить через ЮMoney 💳', callback_data='payment_method_yoomoney'))
    keyboard.add(types.InlineKeyboardButton('Оплатить через CryptoBot 🔗', callback_data='payment_method_crypto'))
    bot.send_message(chat_id, 'Выберите способ оплаты:', reply_markup=keyboard)


def create_yoomoney_link(amount, label):
    return (
        f"https://yoomoney.ru/quickpay/confirm.xml"
        f"?receiver={YOOMONEY_WALLET}"
        f"&quickpay-form=button"
        f"&targets=Подписка"
        f"&sum={amount:.2f}"
        f"&label={label}"
    )


def check_yoomoney_payment(label):
    try:
        resp = requests.post(
            'https://yoomoney.ru/api/operation-history',
            headers={
                'Authorization': f'Bearer {YOOMONEY_TOKEN}',
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            data={'label': label},
        )
        ops = resp.json().get('operations', [])
        return any(op.get('status') == 'success' for op in ops)
    except Exception as e:
        print(f'YooMoney check error: {e}')
        return False


def _cryptopay_url(path):
    base = 'https://testnet-pay.crypt.bot/api' if CRYPTOPAY_TESTNET else 'https://pay.crypt.bot/api'
    return f'{base}/{path}'


def create_cryptopay_invoice(amount_rub, description):
    resp = requests.post(
        _cryptopay_url('createInvoice'),
        headers={'Crypto-Pay-API-Token': CRYPTOPAY_TOKEN},
        json={
            'currency_type': 'fiat',
            'fiat': 'RUB',
            'accepted_assets': 'USDT,TON,BTC,ETH',
            'amount': str(int(amount_rub)),
            'description': description,
            'expires_in': 3600,
        },
    )
    data = resp.json()
    if data.get('ok'):
        inv = data['result']
        return inv['pay_url'], str(inv['invoice_id'])
    raise Exception(f"CryptoPay error: {data}")


def check_cryptopay_payment(invoice_id):
    try:
        resp = requests.get(
            _cryptopay_url('getInvoices'),
            headers={'Crypto-Pay-API-Token': CRYPTOPAY_TOKEN},
            params={'invoice_ids': invoice_id},
        )
        data = resp.json()
        if data.get('ok'):
            items = data['result'].get('items', [])
            if items:
                return items[0].get('status') == 'paid'
    except Exception as e:
        print(f'CryptoPay check error: {e}')
    return False


def _activate_subscription(call):
    user_id = call.from_user.id
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE subscriptions SET status = %s, updated_at = NOW() WHERE user_id = %s',
        (SUBSCRIPTION_STATUS_ACTIVE, user_id)
    )
    conn.commit()
    cursor.close()
    conn.close()
    sub = get_subscription(user_id)
    if sub and sub.get('email'):
        send_receipt_email(sub['email'], sub['amount'], sub['plan'], sub['end_date'])
    allow_in_private_channel(user_id)  # снимаем бан, если был
    invite = generate_one_time_invite(user_id)
    if invite:
        bot.send_message(
            user_id,
            f'Платеж подтверждён. Ваша подписка активирована! ✅\n\n'
            f'Ваша персональная ссылка для входа в закрытый канал '
            f'(одноразовая, действует 24 часа):\n{invite}'
        )
    else:
        bot.send_message(user_id, 'Платеж подтверждён. Ваша подписка активирована! ✅\nОбратитесь в поддержку для получения ссылки на закрытый канал.')
    bot.answer_callback_query(call.id, 'Оплата подтверждена ✅')


def _payment_not_found(call):
    bot.send_message(call.from_user.id, 'Оплата пока не поступила. Попробуйте через несколько минут.')
    bot.answer_callback_query(call.id, 'Оплата не найдена')


def handle_payment_callback(call, method):
    user_id = call.from_user.id
    data = user_data.get(user_id)
    if not data or data.get('flow') != 'subscription':
        bot.answer_callback_query(call.id, 'Сначала выберите подписку.')
        return
    plan_name = data['plan_name']
    plan_days = data['plan_days']
    plan_price = data['plan_price']
    subscription = get_subscription(user_id)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    start_date = subscription['end_date'] if subscription and subscription['end_date'] and subscription['end_date'] > now else now
    end_date = start_date + timedelta(days=plan_days)

    try:
        if method == 'yoomoney':
            label = str(uuid.uuid4())
            pay_url = create_yoomoney_link(plan_price, label)
            payment_ref = f'ym_{label}'
            check_data = f'check_yoomoney_{label}'
            method_name = 'ЮMoney'
        elif method == 'crypto':
            pay_url, invoice_id = create_cryptopay_invoice(plan_price, f'Подписка {plan_name}')
            payment_ref = f'cp_{invoice_id}'
            check_data = f'check_cryptopay_{invoice_id}'
            method_name = 'CryptoBot'
        else:
            bot.answer_callback_query(call.id, 'Неизвестный метод оплаты.')
            return
    except Exception as e:
        print(f'Payment creation error: {e}')
        bot.answer_callback_query(call.id, 'Ошибка создания платежа. Попробуйте позже.')
        return

    create_or_update_subscription(
        user_id=user_id,
        email=data.get('email'),
        plan=plan_name,
        start_date=start_date,
        end_date=end_date,
        amount=plan_price,
        payment_id=payment_ref,
    )
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(f'Оплатить через {method_name}', url=pay_url))
    keyboard.add(types.InlineKeyboardButton('Проверить оплату ✅', callback_data=check_data))
    bot.send_message(
        call.message.chat.id,
        f'Платеж на {plan_price}₽ через {method_name}. Ожидает оплаты ⏳\nПосле оплаты нажмите «Проверить оплату».',
        reply_markup=keyboard
    )
    bot.answer_callback_query(call.id)
    user_data.pop(user_id, None)
    bot.clear_step_handler_by_chat_id(call.message.chat.id)


def subscription_status(message):
    subscription = get_subscription(message.from_user.id)
    if not subscription:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton('Оформить подписку 👑', callback_data='subscribe_now'))
        bot.send_message(message.chat.id, 'У вас нет подписки. Оформите её через меню.', reply_markup=keyboard)
        return
    status_label = SUBSCRIPTION_STATUS_LABELS.get(subscription['status'], subscription['status'])
    status_text = (
        f'Статус подписки: {status_label}\n'
        f'Тип: {subscription["plan"]}\n'
        f'Дата начала: {format_datetime(subscription["start_date"])}\n'
        f'Дата окончания: {format_datetime(subscription["end_date"])}'
    )
    keyboard = types.InlineKeyboardMarkup()
    if subscription['status'] == SUBSCRIPTION_STATUS_EXPIRED:
        keyboard.add(types.InlineKeyboardButton('Продлить подписку 🔄', callback_data='renew_subscription'))
    elif subscription['status'] == SUBSCRIPTION_STATUS_ACTIVE:
        keyboard.add(types.InlineKeyboardButton('Посмотреть закрытый канал 🔒', callback_data='private_channel_access'))
    bot.send_message(message.chat.id, status_text, reply_markup=keyboard)


def about_company(message):
    text = 'Я бот сервиса PRODAYAUTO86 🚗 Помогу продать авто или получить доступ к закрытым предложениям. Здесь ты можешь предложить автомобиль и получить оценку, проверить или оформить подписку, узнать о сервисе, перейти в открытый канал с авто, связаться с менеджером и отслеживать статус своей заявки. Также ниже вы можете найти ссылки на наши ресурсы:'
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton('Посмотреть открытый канал', url=OPEN_CHANNEL_URL))
    keyboard.add(types.InlineKeyboardButton('Посмотреть закрытый канал', callback_data='private_channel_access'))
    keyboard.add(types.InlineKeyboardButton('Посмотреть сайт', url=SITE_URL))
    keyboard.add(types.InlineKeyboardButton('Посмотреть VK', url=VK_URL))
    keyboard.add(types.InlineKeyboardButton('Посмотреть MAX', url=MAX_URL))
    keyboard.add(types.InlineKeyboardButton('Посмотреть Instagram', url=INSTAGRAM_URL))
    bot.send_message(message.chat.id, text, reply_markup=keyboard)


def contact_manager(message):
    bot.send_message(message.chat.id, f'Связаться с менеджером: {MANAGER_CONTACT}')


def contact_support(message):
    bot.send_message(message.chat.id, f'Связаться с поддержкой: {SUPPORT_CONTACT}')


def application_status(message):
    applications = get_user_objects(message.from_user.id)
    if not applications:
        bot.send_message(message.chat.id, 'У вас пока нет заявок.')
        return
    parts = []
    for i, row in enumerate(applications[:5], 1):
        description, price, status, created_at = row[1], row[2], row[4], row[5]
        status_label = APPLICATION_STATUS_LABELS.get(status, status)
        parts.append(
            f'Заявка #{i}\n'
            f'Статус: {status_label}\n'
            f'Описание: {description}\n'
            f'Цена: {price}\n'
            f'Дата: {format_datetime(created_at)}'
        )
    bot.send_message(message.chat.id, '\n\n'.join(parts))


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


def parse_contact(contact_str):
    result = {'phone': '', 'telegram': ''}
    for line in (contact_str or '').split('\n'):
        if line.startswith('Телефон: '):
            result['phone'] = line[9:].strip()
        elif line.startswith('Telegram: '):
            result['telegram'] = line[10:].strip()
    return result


def publish_to_channel(obj_uuid, target_channel):
    obj = get_object_by_uuid(obj_uuid)
    if not obj:
        return
    caption = (
        f'{obj["description"]}\n'
        f'Цена: {obj["price"]}\n'
        f'{obj["contact"] or ""}'
    )
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton('Предложить собственный автомобиль 🚗', callback_data='propose_car'))
    keyboard.add(types.InlineKeyboardButton('Подписаться на закрытый канал 🔒', callback_data='subscribe_now'))

    if obj['photos']:
        if len(obj['photos']) == 1:
            bot.send_photo(target_channel, obj['photos'][0], caption=caption, reply_markup=keyboard)
        else:
            media = [types.InputMediaPhoto(photo) for photo in obj['photos']]
            bot.send_media_group(target_channel, media)
            bot.send_message(target_channel, caption, reply_markup=keyboard)
    else:
        bot.send_message(target_channel, caption, reply_markup=keyboard)


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
        f"{obj['contact'] or '—'}\n"
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

    autoteka_uuid = get_autoteka_s3_url(obj['autoteka_id'])
    if autoteka_uuid:
        try:
            url = s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': BUCKET_NAME, 'Key': f'files/{autoteka_uuid}.pdf'},
                ExpiresIn=3600
            )
            keyboard.add(types.InlineKeyboardButton('Посмотреть автотеку 📄', url=url))
        except Exception as e:
            print(f'Ошибка при генерации ссылки на автотеку: {e}')

    contact_parsed = parse_contact(obj['contact'])
    if contact_parsed['telegram']:
        tg_handle = contact_parsed['telegram'].lstrip('@')
        keyboard.add(types.InlineKeyboardButton('Написать в Telegram 💬', url=f'https://t.me/{tg_handle}'))
    if contact_parsed['phone']:
        phone = contact_parsed['phone'].strip()
        if phone.startswith('8') and len(phone) == 11:
            phone = '+7' + phone[1:]
        elif not phone.startswith('+'):
            phone = '+' + phone
        text += f'\n📞 {phone}'  # номер в тексте — кликабелен на мобильном

    bot.send_message(chat_id, text, reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    data = call.data
    user_id = call.from_user.id
    if data == 'menu':
        bot.answer_callback_query(call.id)
        menu(call.message)
        return
    if data == 'admin':
        bot.answer_callback_query(call.id)
        show_next_pending(call.message.chat.id)
        return
    if data == 'propose_car':
        bot.answer_callback_query(call.id)
        propose_car(call.message)
        return
    if data == 'sub_status':
        bot.answer_callback_query(call.id)
        subscription_status(call.message)
        return
    if data == 'subscribe':
        bot.answer_callback_query(call.id)
        show_subscription_plans(call.message.chat.id, user_id, action='subscribe')
        return
    if data == 'app_status':
        bot.answer_callback_query(call.id)
        application_status(call.message)
        return
    if data == 'about':
        bot.answer_callback_query(call.id)
        about_company(call.message)
        return
    if data == 'manager':
        bot.answer_callback_query(call.id)
        contact_manager(call.message)
        return
    if data == 'support':
        bot.answer_callback_query(call.id)
        contact_support(call.message)
        return
    if data == 'renew_subscription':
        bot.answer_callback_query(call.id)
        show_subscription_plans(call.message.chat.id, user_id, action='renew')
        return
    if data.startswith('select_plan_'):
        _, _, months, action = data.split('_', 3)
        plan = next((p for p in SUBSCRIPTION_PLANS if str(p['months']) == months), None)
        if not plan:
            bot.answer_callback_query(call.id, 'План не найден.')
            return
        bot.answer_callback_query(call.id)
        ask_for_email(call.message, call.from_user.id, action, plan['name'], plan['days'], plan['price'])
        return
    if data == 'skip_receipt':
        bot.answer_callback_query(call.id)
        user_id = call.from_user.id
        bot.clear_step_handler_by_chat_id(call.message.chat.id)
        if user_id in user_data and user_data[user_id].get('flow') == 'subscription':
            user_data[user_id]['email'] = None
            send_payment_options(call.message.chat.id, user_id)
        return
    if data.startswith('payment_method_'):
        method = data.replace('payment_method_', '')
        handle_payment_callback(call, method)
        return
    if data.startswith('check_yoomoney_'):
        label = data.replace('check_yoomoney_', '')
        paid = check_yoomoney_payment(label)
        if paid:
            _activate_subscription(call)
        else:
            _payment_not_found(call)
        return
    if data.startswith('check_cryptopay_'):
        invoice_id = data.replace('check_cryptopay_', '')
        paid = check_cryptopay_payment(invoice_id)
        if paid:
            _activate_subscription(call)
        else:
            _payment_not_found(call)
        return
    if data == 'private_channel_access':
        bot.answer_callback_query(call.id)
        subscription = get_subscription(user_id)
        if subscription and subscription['status'] == SUBSCRIPTION_STATUS_ACTIVE and subscription['end_date'] and subscription['end_date'] > datetime.now(timezone.utc).replace(tzinfo=None):
            allow_in_private_channel(user_id)  # снимаем бан, если был
            invite = generate_one_time_invite(user_id)
            if invite:
                bot.send_message(
                    call.message.chat.id,
                    f'Ваша персональная ссылка для входа в закрытый канал '
                    f'(одноразовая, действует 24 часа):\n{invite}'
                )
            else:
                bot.send_message(call.message.chat.id, 'Не удалось создать ссылку. Обратитесь в поддержку.')
        else:
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton('Оформить подписку 👑', callback_data='subscribe_now'))
            bot.send_message(call.message.chat.id, 'У вас нет активной подписки. Оформите подписку, чтобы получить доступ.', reply_markup=keyboard)
        return
    if data == 'subscribe_now':
        bot.answer_callback_query(call.id)
        show_subscription_plans(call.message.chat.id, user_id, action='subscribe')
        return
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
    bot.answer_callback_query(call.id)


@bot.message_handler(func=lambda message: message.text == BTN_SUB_STATUS)
def handle_subscription_status(message):
    subscription_status(message)


@bot.message_handler(func=lambda message: message.text == BTN_APPLICATION_STATUS)
def handle_application_status(message):
    application_status(message)


@bot.message_handler(func=lambda message: message.text == BTN_ABOUT)
def handle_about(message):
    about_company(message)


@bot.message_handler(func=lambda message: message.text == BTN_MANAGER)
def handle_manager(message):
    contact_manager(message)


@bot.message_handler(func=lambda message: message.text == BTN_SUPPORT)
def handle_support(message):
    contact_support(message)


@bot.message_handler(func=lambda message: message.text == BTN_ADMIN and message.from_user.id == OWNER_ID)
def handle_admin(message):
    show_next_pending(message.chat.id)


if __name__ == '__main__':
    threading.Thread(target=_run_subscription_checker, daemon=True).start()
    try:
        bot.polling(none_stop=True, timeout=123, allowed_updates=['message', 'callback_query', 'chat_member'])
    except Exception as e:
        print(f'Ошибка: {e}')
