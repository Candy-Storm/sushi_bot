import asyncio
import logging
import random
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from database import init_db, is_user_registered, register_user, can_spin, update_spin_time
from database import init_db, is_user_registered, register_user, can_spin, update_spin_time, save_promocode

BOT_TOKEN = "8606797635:AAGhDiB9oAxkP5ozPPWKE2WFMYQQo4XwBcY"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# 🎲 Наші 6 секторів та їхні ваги (шанси виграшу)
PRIZES = [
    {"name": "🥤 Соус / Напій у подарунок", "weight": 40},
    {"name": "💸 Знижка 10%", "weight": 15},
    {"name": "💰 Знижка 15%", "weight": 10},
    {"name": "🌀 Спробуйте ще", "weight": 15},
    {"name": "🎲 Спробуй завтра! (+1 спін)", "weight": 15},
    {"name": "🍣 Рол «Філадельфія» за 1 грн (від 500 грн)", "weight": 5},
]

from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton

# Створюємо інлайн-кнопку з відкриттям WebApp
# (Для тестування можна використати хостинг GitHub Pages або ngrok URL)
kb_inline_wheel = InlineKeyboardMarkup(
    inline_keyboard=[[
        InlineKeyboardButton(
            text="🎰 Відкрити Рулетку", 
            web_app=WebAppInfo(url="https://твій-домен.com/index.html") # URL вашого HTML
        )
    ]]
)

# Кнопка для запиту номера телефону
kb_phone = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="📱 Поділитися номером", request_contact=True)]],
    resize_keyboard=True,
    one_time_keyboard=True
)

# Головне меню з кнопкою гри
kb_main = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="🎰 Крутити колесо!")]],
    resize_keyboard=True
)

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    
    if is_user_registered(user_id):
        await message.answer(
            f"З поверненням, {message.from_user.first_name}! 🍣\nГотовий випробувати удачу?",
            reply_markup=kb_main
        )
    else:
        await message.answer(
            f"Привіт, {message.from_user.first_name}! 🍣\n\n"
            "Щоб брати участь у розіграші та отримувати смачні призи, "
            "будь ласка, підтвердь свій номер телефону.",
            reply_markup=kb_phone
        )

# Обробка отримання контакту
@dp.message(F.contact)
async def get_contact(message: types.Message):
    user_id = message.from_user.id
    phone = message.contact.phone_number
    username = message.from_user.username or ""
    
    register_user(user_id, username, phone)
    
    await message.answer(
        "✅ Дякуємо! Авторизація успішна.\nТепер ти можеш крутити колесо!",
        reply_markup=kb_main
    )

# Обробка прокручування рулетки
@dp.message(F.text == "🎰 Крутити колесо!")
async def spin_wheel(message: types.Message):
    user_id = message.from_user.id
    
    # 1. Перевірка таймера на 24 години
    #if not can_spin(user_id):
     #   await message.answer(
      #      "⏳ Ви вже крутили колесо сьогодні!\n"
       #     "Наступна спроба буде доступна через 24 години з моменту останнього спіну."
        #)
        #return

    # 2. Анімація прокрутки
    msg = await message.answer("🌀 Колесо крутиться... 🎰")
    await asyncio.sleep(2)
    
    # 3. Визначення призу за вагами (шансами)
    prizes_list = [p["name"] for p in PRIZES]
    weights_list = [p["weight"] for p in PRIZES]
    win_prize = random.choices(prizes_list, weights=weights_list, k=1)[0]
    
    # 4. Фіксація часу спіну
    update_spin_time(user_id)
    
    # 5. Вивід результату
    if win_prize == "🌀 Спробуйте ще":
        await msg.edit_text("😔 На жаль, цього разу сектор порожній. Спробуйте ще раз завтра!")
    elif win_prize == "🎲 Спробуй завтра! (+1 спін)":
        await msg.edit_text("🎲 Вам випав бонусний спін на завтра! Повертайтеся завтра за призом!")
    else:
    # Генеруємо промокод і зберігаємо в БД
        code, expires_str = save_promocode(user_id, win_prize)

    await msg.edit_text(
        f"🎉 **ВІТАЄМО! Ви виграли:**\n\n"
        f"🎁 **{win_prize}**\n"
        f"🔑 Ваш промокод: `{code}`\n\n"
        f"⏰ Дійсний до: **{expires_str}** (24 години)\n"
        f"Покажіть цей код або назвіть його при замовленні!",
        parse_mode="Markdown"
       )

async def main():
    logging.basicConfig(level=logging.INFO)
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())