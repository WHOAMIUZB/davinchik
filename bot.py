import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

# Routerlarni to'g'ri va turli nomlar bilan import qilish
from handlers.admin_panel import admin_router as panel_router
from handlers.admin_moderation import admin_router as moderation_router
from handlers.registration import router as reg_router 
from handlers.search import search_router
from database.db import db

TOKEN = "8757536170:AAGd6mICLU1GAFBiGdg-O0uaegdthl6Aacw"

async def on_startup():
    """Bot ishga tushganda ma'lumotlar bazasini tayyorlash"""
    try:
        db.create_table()
        print("Ma'lumotlar bazasi tayyor ✅")
    except Exception as e:
        print(f"Baza bilan bog'liq xatolik: {e}")

async def main():
    # Bot obyektini yaratish
    bot = Bot(
        token=TOKEN, 
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    # Dispatcher yaratish
    dp = Dispatcher()
    
    # Bazani tekshirish
    await on_startup()
    
    # TUZATILDI: Routerlarni ulash tartibi va nomlari aniqlashtirildi
    # Admin routerlari har doim birinchi bo'lishi kerak
    dp.include_router(panel_router)      # Admin panel buyruqlari
    dp.include_router(moderation_router) # Tasdiqlash/Rad etish tugmalari
    dp.include_router(reg_router)   
    dp.include_router(search_router)
    
    # Eski xabarlarni o'chirib yuborish
    await bot.delete_webhook(drop_pending_updates=True)
    
    print("Bot ishga tushdi... 🚀")
    
    # Pollingni boshlash
    await dp.start_polling(bot)

if __name__ == "__main__":
    # Loglarni sozlash
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot to'xtatildi 🛑")