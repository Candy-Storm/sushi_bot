import asyncio
import json
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.types import (
    ReplyKeyboardMarkup, 
    KeyboardButton, 
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

# 🌐 ПРАВИЛЬНО: Reply-кнопка внизу екрана для запуску WebApp
kb_wheel = ReplyKeyboardMarkup(
    keyboard=[[
        KeyboardButton(
            text="🎰 Відкрити Рулетку", 
            web_app=WebAppInfo(url="https://candy-storm.github.io/sushi_bot/index.html?v=16")
        )
    ]],
    resize_keyboard=True
)

# Кнопка для запиту номера телефону
kb_phone = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="📱 Поділитися номером", request_contact=True)]],
    resize_keyboard=True,
    one_time_keyboard=True
)

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    
    if is_user_registered(user_id):
        await message.answer(
            f"З поверненням, {message.from_user.first_name}! 🍣\n"
            "Натискай кнопку нижче, щоб відкрити рулетку! 👇",
            reply_markup=kb_wheel
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
        "✅ Дякуємо! Авторизація успішна.\n"
        "Тепер ти можеш крутити колесо!",
        reply_markup=kb_wheel
    )

# Обробка призу з WebApp (працює 100% при Reply-клавіатурі)
@dp.message(F.web_app_data)
async def handle_web_app_data(message: types.Message):
    user_id = message.from_user.id
    
    data = json.loads(message.web_app_data.data)
    win_prize = data.get("prize", "Знижка 10%")
    
    # 🌀 Сектор "Ще раз"
    if win_prize in ["🌀 Ще раз", "🌀 Спробуйте ще"]:
        update_spin_time(user_id)
        await message.answer(
            "😔 На жаль, цього разу сектор порожній. Спробуйте ще раз завтра!",
            reply_markup=kb_wheel
        )

    # 🎲 Сектор "+1 спін на ЗАРАЗ"
    elif win_prize in ["🎲 +1 спін", "🎲 Спробуй завтра! (+1 спін)"]:
        await message.answer(
            "🎉 **Вітаємо! Ви виграли додатковий спін просто зараз!** 🎲\n\n"
            "Твоя спроба збереглася! Відкривай рулетку та крути ще раз! 👇",
            reply_markup=kb_wheel,
            parse_mode="Markdown"
        )

    # 🎁 Звичайний виграш призу
    else:
        update_spin_time(user_id)
        code, expires_str = save_promocode(user_id, win_prize)
        
        await message.answer(
            f"🎉 **ВІТАЄМО! Ви виграли:**\n\n"
            f"🎁 **{win_prize}**\n"
            f"🔑 Ваш промокод: `{code}`\n\n"
            f"⏰ Дійсний до: **{expires_str}** (24 години)\n"
            f"Покажіть цей код або назвіть його при замовленні!",
            reply_markup=kb_wheel,
            parse_mode="Markdown"
        )

async def main():
    logging.basicConfig(level=logging.INFO)
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())