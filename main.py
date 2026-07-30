import asyncio
import json
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.types import (
    ReplyKeyboardMarkup, 
    KeyboardButton, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    WebAppInfo
)
from database import (
    init_db, 
    is_user_registered, 
    register_user, 
    can_spin, 
    update_spin_time, 
    save_promocode
)

BOT_TOKEN = "8606797635:AAGhDiB9oAxkP5ozPPWKE2WFMYQQo4XwBcY"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# 🌐 Інлайн-кнопка для відкриття WebApp з GitHub Pages
kb_inline_wheel = InlineKeyboardMarkup(
    inline_keyboard=[[
        InlineKeyboardButton(
            text="🎰 Відкрити Рулетку", 
            web_app=WebAppInfo(url="https://candy-storm.github.io/sushi_bot/index.html?v=5")
        )
    ]]
)

# Кнопка для запиту номера телефону
kb_phone = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="📱 Поділитися номером", request_contact=True)]],
    resize_keyboard=True,
    one_time_keyboard=True
)

# Головне меню
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

# 1. При натисканні "🎰 Крутити колесо!" надсилаємо кнопку з WebApp
@dp.message(F.text == "🎰 Крутити колесо!")
async def spin_wheel(message: types.Message):
    user_id = message.from_user.id
    
    # Перевірка таймера на 24 години (розкоментуй для продакшену)
    # if not can_spin(user_id):
    #     await message.answer(
    #         "⏳ Ви вже крутили колесо сьогодні!\n"
    #         "Наступна спроба буде доступна через 24 години."
    #     )
    #     return

    await message.answer(
        "Натисни кнопку нижче, щоб відкрити анімоване колесо рулетки! 👇",
        reply_markup=kb_inline_wheel
    )

# 2. Обробка результату, який повертає index.html після прокрутки
@dp.message(F.web_app_data)
async def handle_web_app_data(message: types.Message):
    user_id = message.from_user.id
    
    # Зчитуємо дані з JSON, який відправив WebApp (tg.sendData)
    data = json.loads(message.web_app_data.data)
    win_prize = data.get("prize", "Знижка 10%")
    
    # Фіксуємо час спіну в БД
    update_spin_time(user_id)
    
    # Перевіряємо виграш
    if win_prize in ["🌀 Ще раз", "🌀 Спробуйте ще"]:
        await message.answer("😔 На жаль, цього разу сектор порожній. Спробуйте ще раз завтра!")
    elif win_prize in ["🎲 +1 спін", "🎲 Спробуй завтра! (+1 спін)"]:
        await message.answer("🎲 Вам випав бонусний спін на завтра! Повертайтеся завтра за призом!")
    else:
        # Генеруємо промокод і зберігаємо в БД
        code, expires_str = save_promocode(user_id, win_prize)
        
        await message.answer(
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