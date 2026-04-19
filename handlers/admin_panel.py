from aiogram import Router, F, types, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from database.db import db
import asyncio

admin_router = Router()
ADMIN_ID = 7861165622  # Sizning ID raqamingiz

class AdminStates(StatesGroup):
    waiting_for_post = State()
    waiting_for_delete_id = State()

def get_admin_main_kb():
    builder = ReplyKeyboardBuilder()
    builder.row(types.KeyboardButton(text="📢 Post yuborish"))
    builder.row(types.KeyboardButton(text="📊 Statistika"), types.KeyboardButton(text="🗑 Anketani o'chirish"))
    builder.row(types.KeyboardButton(text="🔙 Chiqish"))
    return builder.as_markup(resize_keyboard=True)

@admin_router.message(Command("admin"), F.from_user.id == ADMIN_ID)
async def admin_start(message: types.Message):
    await message.answer("Xush kelibsiz, Admin! Panelga kirdingiz:", reply_markup=get_admin_main_kb())

# --- STATISTIKA ---
@admin_router.message(F.text == "📊 Statistika", F.from_user.id == ADMIN_ID)
async def show_stats(message: types.Message):
    total, today = db.get_stats()
    text = (
        f"📊 **Bot statistikasi:**\n\n"
        f"👥 Jami foydalanuvchilar: {total}\n"
        f"📅 Bugun qo'shilganlar: {today}"
    )
    await message.answer(text, parse_mode="Markdown")

# --- POST YUBORISH ---
@admin_router.message(F.text == "📢 Post yuborish", F.from_user.id == ADMIN_ID)
async def start_broadcasting(message: types.Message, state: FSMContext):
    await message.answer("Barcha foydalanuvchilarga yubormoqchi bo'lgan xabaringizni yozing (rasm, matn, video bo'lishi mumkin):")
    await state.set_state(AdminStates.waiting_for_post)

@admin_router.message(AdminStates.waiting_for_post, F.from_user.id == ADMIN_ID)
async def send_post_to_all(message: types.Message, state: FSMContext, bot: Bot):
    users = db.get_all_users()
    count = 0
    await message.answer("Yuborish boshlandi, kuting...")

    for user in users:
        try:
            # Xabarni nusxalab yuborish (shunda rasm va matn birga ketadi)
            await bot.copy_message(
                chat_id=user[0],
                from_chat_id=message.chat.id,
                message_id=message.message_id
            )
            count += 1
            await asyncio.sleep(0.05) # Spamga tushmaslik uchun kichik kechikish
        except Exception:
            continue

    await message.answer(f"✅ Yuborish yakunlandi!\nJami {count} ta foydalanuvchiga yuborildi.")
    await state.clear()

# --- ANKETANI O'CHIRISH ---
@admin_router.message(F.text == "🗑 Anketani o'chirish", F.from_user.id == ADMIN_ID)
async def ask_delete_id(message: types.Message, state: FSMContext):
    await message.answer("O'chirmoqchi bo'lgan foydalanuvchining ID raqamini kiriting:")
    await state.set_state(AdminStates.waiting_for_delete_id)

@admin_router.message(AdminStates.waiting_for_delete_id, F.from_user.id == ADMIN_ID)
async def delete_user_id(message: types.Message, state: FSMContext, bot: Bot):
    if not message.text.isdigit():
        return await message.answer("Iltimos, faqat raqamlardan iborat ID kiriting!")

    target_id = int(message.text)
    success = db.delete_user_profile(target_id)

    if success:
        await message.answer(f"✅ Foydalanuvchi {target_id} anketasi o'chirildi. Endi u qaytadan ro'yxatdan o'ta oladi.")
        try:
            await bot.send_message(target_id, "Sizning anketangiz admin tomonidan o'chirildi. Qaytadan ro'yxatdan o'tishingiz mumkin.")
        except:
            pass
    else:
        await message.answer("❌ Bunday ID ga ega foydalanuvchi topilmadi.")
    
    await state.clear()

@admin_router.message(F.text == "🔙 Chiqish", F.from_user.id == ADMIN_ID)
async def exit_admin(message: types.Message):
    from keyboards.reply import main_menu # Asosiy menyu importi
    await message.answer("Admin paneldan chiqdingiz.", reply_markup=main_menu)