import logging
import sqlite3
import sys
import asyncio
from datetime import datetime, timedelta, timezone
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, ChatPermissions

TOKEN = "ТВОЙ_ТОКЕН_БОТА"
CODER_ID = 123456789  # Твой Telegram ID

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Названия рангов для вывода в тексте
ROLES = {
    0: "💀 Скаммер",
    1: "👤 Обычный участник",
    2: "🤝 Гарант",
    3: "🛡️ Admin",
    4: "💼 Директор",
    5: "👑 Президент",
    6: "💎 Владелец",
    7: "👨‍💻 Кодер (Создатель)"
}

# file_id для главного меню
START_IMG = "AgACAgIAAxkBAAN7ah9hK8nBps-WHP4so0zeKt0D6YQAAhokaxsyz_lIN4kQDaeDugcBAAMCAAN5AAM7BA"

ROLE_IMAGES = {
    0: "AgACAgIAAxkBAANTah9X_y70zoGN7N3JK3lfkitCmUoAAgokaxsyz_lI5tvp7bhRiNsBAAMCAAN5AAM7BA",
    1: "AgACAgIAAxkBAANRah9XryUb-9AJhOyjODAoDkuFrYsAAgkkaxsyz_lIRrIvIBStxq8BAAMCAAN5AAM7BA",
    2: "AgACAgIAAxkBAANVah9YL5R7l-zxY5RDgRpKM5Ralk8AAgwkaxsyz_lIc_l2bZ0f3I8BAAMCAAN5AAM7BA",
    3: "AgACAgIAAxkBAANXah9YYwkEuIAttD6liYWSOiew-PUAAg0kaxsyz_lI_WibXKEMT-IBAAMCAAN5AAM7BA",
    4: "AgACAgIAAxkBAANZah9Yv1pW_EJlvTgrDbVCb0IVL9gAAg4kaxsyz_lIvzbLsldoAhABAAMCAAN5AAM7BA",
    5: "AgACAgIAAxkBAANcah9ZG5TSFiGFes_86ZCOT6sGw0wAAhEkaxsyz_lIzLTI7TOtFhYBAAMCAAN5AAM7BA",
    6: "AgACAgIAAxkBAANhah9ZqdzeS8LTbfk0TlCelBjgvs4AAhMkaxsyz_lI-Ho_bfHRo4UBAAMCAAN5AAM7BA",
    7: "AgACAgIAAxkBAANjah9Z7rnn9mB7CIJ0doyFYhn7OwADFSRrGzLP-Uj9o_mfN4adLQEAAwIAA3kAAzsE"
}

# Правила нормальным шрифтом
RULES_TEXT = (
    "📜 <b>Правила Чата | Quality Chat Rules</b> 📜\n"
    "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    "📑 Спам — мут 30 минут ⏳\n\n"
    "🔞 Отправка 18+ контента — мут 45 минут 𝄎\n\n"
    "🤬 Оскорбление участников — мут 1 час ⏰\n\n"
    "🚨 Спам 18+ контентом — мут 2 часа 🔥\n\n"
    "💔 Оскорбление родных — БАН 𝄵\n\n"
    "💬 Оскорбление чата — БАН 💥\n\n"
    "🥷 Скам или попытка обмана — БАН 🏴‍☠️\n\n"
    "☁️ Скам-ссылки, фишинг или вредоносные сайты — БАН ☣️\n\n"
    "👨‍⚖️ Оскорбление администрации — БАН 𝄩\n\n"
    "🚫 Неуважение к админке — мут 1 час 🛑\n\n"
    "📢 Флуд капсом (БОЛЬШИМИ БУКВАМИ) — мут 30 минут 𝄪\n\n"
    "🎭 Выдача себя за администрацию — БАН 𝄡\n\n"
    "📨 Реклама сторонних ресурсов/чатов — БАН 𝄢\n\n"
    "⚔️ Разжигание конфликтов — мут или БАН 💣\n\n"
    "🔊 Спам стикерами, GIF или ГС — мут 30 минут 𝄠\n\n"
    "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    "⚠️ Администрация вправе изменить решение — правила актуальны!\n"
    "👨‍⚖️ Правила для администрации одинаковы.\n"
    "📌 Незнание правил не освобождает от ответственности!"
)

# Инициализация базы данных
conn = sqlite3.connect("simple_roles.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, role_id INTEGER, username TEXT, first_name TEXT)")
conn.commit()

def get_role(user_id: int) -> int:
    cursor.execute("SELECT role_id FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    return row[0] if row else 1

def set_role(user_id: int, role_id: int, username: str = None, first_name: str = None):
    # При любом обновлении роли также сохраняем имя/юзернейм для команды /admin
    cursor.execute("""
        INSERT INTO users (user_id, role_id, username, first_name) 
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET 
            role_id=excluded.role_id,
            username=coalesce(excluded.username, users.username),
            first_name=coalesce(excluded.first_name, users.first_name)
    """, (user_id, role_id, username, first_name))
    conn.commit()

def get_target_id(message: Message) -> int:
    if message.reply_to_message:
        return message.reply_to_message.from_user.id
    parts = message.text.split()
    if len(parts) > 1 and parts[-1].isdigit() and len(parts[-1]) > 5:
        return int(parts[-1])
    return None

# Функция автоматического обновления данных пользователя при сообщениях (чтобы /admin работал точнее)
@dp.message(F.text, F.chat.type.in_({"group", "supergroup"}))
async def update_user_info_handler(message: Message):
    # Записываем текущее имя, чтобы бот знал, как зовут пользователя
    uid = message.from_user.id
    role = get_role(uid)
    set_role(uid, role, message.from_user.username, message.from_user.first_name)

@dp.message(F.photo)
async def get_photo_file_id(message: Message):
    file_id = message.photo[-1].file_id
    await message.reply(f"<code>{file_id}</code>", parse_mode="HTML")

# --- КОМАНДЫ БОТА ---

@dp.message(Command("rules", "правила"))
async def rules_cmd(message: Message):
    await message.reply(RULES_TEXT, parse_mode="HTML")

@dp.message(Command("roles", "ранги"))
async def roles_cmd(message: Message):
    """Показывает иерархию ролей чата"""
    text = "👑 <b>Иерархия рангов в чате:</b>\n━━━━━━━━━━━━━━━━━━━━\n"
    for r_id, r_name in sorted(ROLES.items(), reverse=True):
        text += f"{r_id} ➔ {r_name}\n"
    text += "━━━━━━━━━━━━━━━━━━━━\n💡 Повысить/понизить роль: <code>/promote</code> или <code>/demote</code>"
    await message.reply(text, parse_mode="HTML")

@dp.message(Command("admin", "админы"))
async def admin_cmd(message: Message):
    """Выводит список администрации, зарегистрированной в боте"""
    cursor.execute("SELECT user_id, role_id, username, first_name FROM users WHERE role_id >= 3 ORDER BY role_id DESC")
    admins = cursor.fetchall()
    
    if not admins:
        return await message.reply("🛡️ В базе данных бота пока нет зарегистрированной администрации.")
    
    text = "🛡️ <b>Список администрации чата (в боте):</b>\n━━━━━━━━━━━━━━━━━━━━\n"
    for uid, rid, username, first_name in admins:
        name = first_name if first_name else f"ID: {uid}"
        user_link = f"@{username}" if username else f"<a href='tg://user?id={uid}'>{name}</a>"
        text += f"{ROLES.get(rid, 'Админ')} — {user_link} <code>({uid})</code>\n"
    
    await message.reply(text, parse_mode="HTML", disable_web_page_preview=True)

@dp.message(Command("help", "помощь"))
async def help_cmd(message: Message):
    """Динамическое меню помощи для администрации"""
    user_role = get_role(message.from_user.id)
    if message.from_user.id == CODER_ID:
        user_role = 7

    text = f"⚙️ <b>Панель помощи бота (Ваш ранг: {ROLES.get(user_role, 'Участник')})</b>\n"
    text += "━━━━━━━━━━━━━━━━━━━━\n"
    text += "👤 <b>Общие команды:</b>\n"
    text += "➔ <code>/profile</code> (или <code>/me</code>) — Посмотреть ранг\n"
    text += "➔ <code>/rules</code> — Посмотреть правила чата\n"
    text += "➔ <code>/roles</code> — Посмотреть иерархию рангов\n"
    text += "➔ <code>/admin</code> — Список администрации чата\n"

    if user_role >= 4:
        text += "\n💼 <b>Команды от Директора (4) и выше:</b>\n"
        text += "➔ <code>/promote [номер]</code> — Выдать роль (реплаем или по ID)\n"
        text += "➔ <code>/demote [номер]</code> — Снять роль/понизить\n"
        text += "➔ <code>/mute</code> — Мут нарушителя на 15 минут (реплаем)\n"
        text += "➔ <code>/scam</code> — Объявить пользователя скаммером (ранг 0)\n"

    if user_role >= 5:
        text += "\n👑 <b>Команды от Президента (5) и выше:</b>\n"
        text += "➔ <code>/ban</code> — Забанить нарушителя навсегда (реплаем)\n"

    if user_role == 7:
        text += "\n👨‍💻 <b>Команды Создателя:</b>\n"
        text += "➔ <code>/setcoder</code> — Авторизоваться как Создатель бота\n"

    text += "━━━━━━━━━━━━━━━━━━━━"
    await message.reply(text, parse_mode="HTML")

@dp.message(Command("start"))
async def start_cmd(message: Message):
    start_text = (
        f"👋 <b>Привет, {message.from_user.first_name}!</b>\n\n"
        f"Я простой бот управления рангами в чате. Регистрация не нужна!\n"
        f"Узнать ранг и список команд можно через: <code>/profile</code> \n"
        f"Посмотреть правила чата: <code>/rules</code>\n"
        f"Открыть меню помощи: <code>/help</code>"
    )
    try:
        await message.answer_photo(photo=START_IMG, caption=start_text, parse_mode="HTML")
    except Exception:
        await message.answer(start_text, parse_mode="HTML")

@dp.message(Command("profile", "me"))
async def profile_cmd(message: Message):
    target_id = get_target_id(message)
    
    if target_id:
        user_id = target_id
        title_text = "👤 <b>ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ</b>"
    else:
        user_id = message.from_user.id
        title_text = "👤 <b>ТВОЙ ЛИЧНЫЙ ПРОФИЛЬ</b>"
        
    role_id = get_role(user_id)
    
    profile_text = (
        f"{title_text}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 ID человека: <code>{user_id}</code>\n"
        f"🎭 Ранг в системе: <b>{ROLES.get(role_id, 'Участник')}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📈 <code>/promote [ранг]</code> — Выдать роль\n"
        f"📉 <code>/demote [ранг]</code> — Понизить роль"
    )
    
    img_id = ROLE_IMAGES.get(role_id, None)
    try:
        await message.answer_photo(photo=img_id, caption=profile_text, parse_mode="HTML")
    except Exception:
        await message.answer(profile_text, parse_mode="HTML")

@dp.message(Command("setcoder"))
async def set_coder_cmd(message: Message):
    if message.from_user.id == CODER_ID:
        set_role(CODER_ID, 7, message.from_user.username, message.from_user.first_name)
        await message.reply("👨‍💻 <b>Вы успешно вошли как Создатель бота!</b>", parse_mode="HTML")
    else:
        await message.reply("🚫 Доступ заблокирован.")

# --- УПРАВЛЕНИЕ РАНГАМИ ---

@dp.message(Command("promote"))
async def promote_cmd(message: Message):
    admin_role = get_role(message.from_user.id)
    if admin_role < 4 and message.from_user.id != CODER_ID:
        return await message.reply("🔒 Нужен ранг Директор (4) или выше!")

    parts = message.text.split()
    if len(parts) < 2:
        return await message.reply("📝 Пиши так: <code>/promote [номер_роли]</code>", parse_mode="HTML")

    try:
        new_role = int(parts[1])
    except ValueError:
        return await message.reply("❌ Номер роли должен быть числом!")

    if new_role not in ROLES:
        return await message.reply("❌ Такого ранга не существует!")
        
    target_id = get_target_id(message)
    if not target_id:
        return await message.reply("⚠️ Ответь командой на сообщение пользователя или допиши его ID.")

    target_role = get_role(target_id)

    if message.from_user.id != CODER_ID and admin_role != 7:
        if admin_role <= target_role:
            return await message.reply("⚠️ Вы не можете управлять пользователями с равным или высшим рангом!")
        if new_role >= admin_role:
            return await message.reply("⚠️ Вы не можете выдать ранг выше или равный вашему!")

    # При выдаче роли сохраняем ник цели, если команда была реплаем
    t_username = message.reply_to_message.from_user.username if message.reply_to_message else None
    t_firstname = message.reply_to_message.from_user.first_name if message.reply_to_message else None

    set_role(target_id, new_role, t_username, t_firstname)
    await message.reply(f"📈 Пользователю выдана роль: <b>{ROLES[new_role]}</b>!", parse_mode="HTML")

@dp.message(Command("demote"))
async def demote_cmd(message: Message):
    admin_role = get_role(message.from_user.id)
    if admin_role < 4 and message.from_user.id != CODER_ID:
        return await message.reply("🔒 Нужен ранг Директор (4) или выше!")

    target_id = get_target_id(message)
    if not target_id:
        return await message.reply("⚠️ Ответь командой на сообщение пользователя или укажи его ID.")

    target_role = get_role(target_id)
    parts = message.text.split()
    
    new_role = 1
    if len(parts) > 1:
        try:
            new_role = int(parts[1])
        except ValueError:
            return await message.reply("❌ Номер роли должен быть числом!")

    if new_role not in ROLES:
        return await message.reply("❌ Такого ранга не существует!")

    if message.from_user.id != CODER_ID and admin_role != 7:
        if admin_role <= target_role:
            return await message.reply("⚠️ Вы не можете понижать администраторов с равным или высшим рангом!")
        if new_role >= admin_role:
            return await message.reply("⚠️ Вы не можете установить ранг выше или равный вашему!")

    t_username = message.reply_to_message.from_user.username if message.reply_to_message else None
    t_firstname = message.reply_to_message.from_user.first_name if message.reply_to_message else None

    set_role(target_id, new_role, t_username, t_firstname)
    await message.reply(f"📉 Пользователь понижен до ранга: <b>{ROLES[new_role]}</b>!", parse_mode="HTML")

# --- СЛИВ, МУТ, БАН ---

@dp.message(Command("scam", "слив"))
async def scam_cmd(message: Message):
    if get_role(message.from_user.id) < 4 and message.from_user.id != CODER_ID: 
        return await message.reply("🔒 Нужен ранг Директор и выше!")
    target_id = get_target_id(message)
    if not target_id: return
    
    t_username = message.reply_to_message.from_user.username if message.reply_to_message else None
    t_firstname = message.reply_to_message.from_user.first_name if message.reply_to_message else None
    
    set_role(target_id, 0, t_username, t_firstname)
    try:
        await message.answer_photo(photo=ROLE_IMAGES[0], caption="🚨 Внимание! Этот пользователь официально объявлен <b>Скаммером</b>! 💀", parse_mode="HTML")
    except Exception:
        await message.reply("🚨 Этот пользователь объявлен <b>Скаммером</b>! 💀", parse_mode="HTML")

@dp.message(Command("mute"))
async def mute_cmd(message: Message):
    if get_role(message.from_user.id) < 4 and message.from_user.id != CODER_ID: 
        return await message.reply("🔒 Доступно от Директора!")
    target_id = get_target_id(message)
    if not target_id: return
    
    try:
        until_timestamp = int((datetime.now(timezone.utc) + timedelta(minutes=15)).timestamp())
        await message.chat.restrict(
            user_id=target_id, 
            permissions=ChatPermissions(can_send_messages=False), 
            until_date=until_timestamp
        )
        await message.reply("🤫 Нарушитель отправлен в мут на 15 минут.")
    except Exception as e:
        logging.error(f"Ошибка мута: {e}")
        await message.reply("❌ Не удалось выдать мут. Проверь права бота.")

@dp.message(Command("ban"))
async def ban_cmd(message: Message):
    if get_role(message.from_user.id) < 5 and message.from_user.id != CODER_ID: 
        return await message.reply("🔒 Доступно от Президента!")
    target_id = get_target_id(message)
    if not target_id: return
    
    try:
        await message.chat.ban(user_id=target_id)
        await message.reply("💥 Нарушитель забанен!")
    except Exception as e:
        logging.error(f"Ошибка бана: {e}")
        await message.reply("❌ Ошибка при бане.")

# Запуск бота
async def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    print("🤖 Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())