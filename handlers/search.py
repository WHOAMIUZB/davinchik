import random
from aiogram import Router, F, types, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.db import db
from keyboards import reply, inline
from typing import cast, Union, Optional

# Holatlarni boshqarish
class MessageState(StatesGroup):
    waiting_for_text = State()

search_router = Router()

# --- QIDIRUVNI BOSHLASH ---

@search_router.message(F.text == "🔍 Qidirish")
async def start_search_handler(message: types.Message, state: FSMContext):
    """Qidiruv tugmasi bosilganda jinsni tanlash menyusini chiqarish"""
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="👩 Qizlar", callback_data="filter_men qizman"),
        types.InlineKeyboardButton(text="👨 Yigitlar", callback_data="filter_men yigitman")
    )
    builder.row(types.InlineKeyboardButton(text="🌐 Farqi yo'q", callback_data="filter_all"))
    
    await message.answer("Kimni qidiramiz? Tanlang:", reply_markup=builder.as_markup())

@search_router.callback_query(F.data.startswith("filter_"))
async def process_filter(call: types.CallbackQuery, state: FSMContext):
    """Filtr tanlanganda qidiruvni boshlash va tarixni tozalash"""
    if not call.data: return
    
    gender_filter = call.data.split("_")[1]
    # Yangi qidiruvda ko'rilgan anketalar ro'yxatini bo'shatamiz
    await state.update_data(current_filter=gender_filter, viewed_ids=[])
    
    if call.message:
        await call.message.delete()
    
    await start_search(call, state)

async def start_search(event: Union[types.Message, types.CallbackQuery], state: FSMContext):
    """Uzluksiz va takrorlanmas qidiruv mantiqi"""
    user_id = event.from_user.id if event.from_user else None
    if not user_id: return

    user_data = db.get_user_data(user_id)
    state_data = await state.get_data()
    
    target_gender = state_data.get('current_filter', 'all')
    viewed_ids = state_data.get('viewed_ids', []) # Oldin ko'rilgan ID'lar

    if not user_data: 
        return await (event.answer("Avval ro'yxatdan o'ting!") if isinstance(event, types.Message) else event.answer())

    # Bazadan barcha mos anketalarni olamiz
    all_results = db.get_users_for_search(
        user_id, target_gender, user_data['region'], user_data['district']
    )
    
    if not all_results:
        msg = "Hozircha hech qanday anketa topilmadi. 😊"
        return await (event.answer(msg) if isinstance(event, types.Message) else event.message.answer(msg))

    # Hali ko'rilmagan anketalarni filtrlash (Siz so'ragan takrorlanmaslik qismi)
    available_results = [u for u in all_results if u['user_id'] not in viewed_ids]

    # Agar hamma anketa ko'rilgan bo'lsa
    if not available_results:
        msg = "Hamma anketalarni ko'rib bo'ldingiz. Yangidan boshlash uchun qayta '🔍 Qidirish'ni bosing."
        if isinstance(event, types.CallbackQuery) and event.message:
            await event.message.answer(msg)
        else:
            await event.answer(msg)
        return

    # Tasodifiy bitta anketa tanlash
    target = random.choice(available_results)
    
    # Ko'rilganlar ro'yxatiga qo'shish
    viewed_ids.append(target['user_id'])
    await state.update_data(viewed_ids=viewed_ids)
    
    caption = (
        f"👤 {target['name']}, {target['age']}\n"
        f"📍 {target['region']}, {target['district']}\n\n"
        f"📝 {target['bio']}"
    )
    
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="❤️ Yoqdi", callback_data=f"like_{target['user_id']}"),
        types.InlineKeyboardButton(text="👎 Yoqmadi", callback_data="next_profile")
    )
    builder.row(types.InlineKeyboardButton(text="✍️ Yozish", callback_data=f"write_{target['user_id']}"))
    
    photo = target['photo'] if target['photo'] else "https://via.placeholder.com/300"

    try:
        if isinstance(event, types.Message):
            await event.answer_photo(photo=photo, caption=caption, reply_markup=builder.as_markup())
        else:
            await event.message.answer_photo(photo=photo, caption=caption, reply_markup=builder.as_markup())
    except Exception:
        if isinstance(event, types.Message):
            await event.answer(caption, reply_markup=builder.as_markup())
        else:
            await event.message.answer(caption, reply_markup=builder.as_markup())

# --- LIKE VA YOQMADI HANDLERLARI ---

@search_router.callback_query(F.data == "next_profile")
async def handle_next(call: types.CallbackQuery, state: FSMContext):
    """Yoqmadi bosilganda keyingi anketaga o'tish"""
    await call.answer()
    if call.message:
        await call.message.delete()
    await start_search(call, state)

@search_router.callback_query(F.data.startswith("like_"))
async def handle_like(call: types.CallbackQuery, state: FSMContext, bot: Bot):
    """Yoqdi bosilganda like qo'shish va AVTOMATIK keyingisiga o'tish"""
    if not call.data: return
    to_user_id = int(call.data.split("_")[1])
    db.add_like(call.from_user.id, to_user_id) 
    
    try:
        await bot.send_message(to_user_id, "Sizni kimdir yoqtirdi! ❤️\n'❤️ Yoqtirganlar' bo'limini tekshiring.")
    except: pass
        
    await call.answer("Yoqdi! ❤️")
    if call.message:
        await call.message.delete()
    
    # Darhol keyingi anketani ko'rsatish
    await start_search(call, state)

# --- YOQTIRGANLAR BO'LIMI ---

@search_router.message(F.text == "❤️ Yoqtirganlar")
async def show_who_liked_me(message: types.Message):
    user_id = message.from_user.id
    likers = db.get_who_liked_me(user_id)
    
    if not likers:
        return await message.answer("Hozircha sizni hech kim yoqtirmadi. 😊")

    target = likers[0]
    caption = (
        f"Sizni yoqtirishdi! ❤️\n\n"
        f"👤 {target['name']}, {target['age']}\n"
        f"📍 {target['region']}, {target['district']}\n"
        f"📝 {target['bio']}"
    )

    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="✅ Qabul qilish", callback_data=f"accept_{target['user_id']}"),
        types.InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_{target['user_id']}")
    )
    
    if target['photo']:
        await message.answer_photo(photo=target['photo'], caption=caption, reply_markup=builder.as_markup())
    else:
        await message.answer(caption, reply_markup=builder.as_markup())

# --- YOZISH TUGMASI VA XABAR YUBORISH ---

@search_router.callback_query(F.data.startswith("write_"))
async def start_writing(call: types.CallbackQuery, state: FSMContext):
    """Yozish tugmasi bosilganda ishlashini ta'minlash"""
    if not call.data: return
    target_id = int(call.data.split("_")[1])
    
    await state.update_data(target_id=target_id)
    await state.set_state(MessageState.waiting_for_text)
    
    if call.message:
        await call.message.answer("Xabaringizni yozing (bu xabar anketa egasiga yuboriladi):")
    await call.answer()

@search_router.message(MessageState.waiting_for_text)
async def send_user_message(message: types.Message, state: FSMContext, bot: Bot):
    """Xabar yuborish mantiqi"""
    data = await state.get_data()
    target_id = data.get('target_id')
    sender_data = db.get_user_data(message.from_user.id)

    if not sender_data or not target_id: 
        await state.clear()
        return

    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="↩️ Javob yozish", callback_data=f"write_{message.from_user.id}"),
        types.InlineKeyboardButton(text="👤 Anketasini ko'rish", callback_data=f"view_{message.from_user.id}")
    )

    try:
        await bot.send_message(
            target_id, 
            f"Yangi xabar! 📩\n\nKimdan: {sender_data['name']}\nXabar: {message.text}",
            reply_markup=builder.as_markup()
        )
        await message.answer("Xabaringiz yuborildi! ✅")
    except:
        await message.answer("Xabar yuborishda xatolik yuz berdi. ❌")

    await state.clear()
    await start_search(message, state)

# --- MENING ANKETAM VA TAHRIRLASH ---

@search_router.message(F.text == "👤 Mening anketam")
async def show_my_profile(message: types.Message):
    user_data = db.get_user_data(message.from_user.id)
    if not user_data: return

    caption = f"Sizning anketangiz:\n\n👤 {user_data['name']}, {user_data['age']}\n📍 {user_data['region']}\n📝 {user_data['bio']}"
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="⚙️ Tahrirlash", callback_data="edit_profile"))
    
    if user_data['photo']:
        await message.answer_photo(photo=user_data['photo'], caption=caption, reply_markup=builder.as_markup())
    else:
        await message.answer(caption, reply_markup=builder.as_markup())

@search_router.callback_query(F.data == "edit_profile")
async def ask_edit_confirmation(call: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="✅ Ha", callback_data="confirm_edit"),
        types.InlineKeyboardButton(text="❌ Yo'q", callback_data="cancel_edit")
    )
    if call.message:
        await call.message.answer("Anketangizni tahrirlashni istaysizmi?", reply_markup=builder.as_markup())
    await call.answer()

@search_router.callback_query(F.data == "confirm_edit")
async def process_edit_confirm(call: types.CallbackQuery, state: FSMContext):
    warning_text = "❗️ Bot shaxsiy ma'lumotlarni so'ramaydi va foydalanuvchilarni identifikatsiya qilmaydi."
    await call.message.answer(warning_text)
    await state.clear()
    
    try:
        from handlers.registration import RegistrationState 
        await state.set_state(RegistrationState.waiting_for_name)
        await call.message.answer("Anketangizni yangilaymiz.\n\nIsmingizni kiriting:")
    except ImportError:
        await call.message.answer("Xatolik: Ro'yxatdan o'tish moduli topilmadi.")
    await call.answer()

# --- QOLGAN CALLBACKLAR ---

@search_router.callback_query(F.data.startswith("accept_"))
async def handle_accept(call: types.CallbackQuery, bot: Bot):
    target_id = int(call.data.split("_")[1])
    db.update_like_status(target_id, call.from_user.id, 'accepted')
    try:
        await bot.send_message(target_id, "Anketangiz qabul qilindi! 😍")
    except: pass
    await call.answer("Qabul qilindi! ✅")
    await call.message.delete()

@search_router.callback_query(F.data.startswith("reject_"))
async def handle_reject(call: types.CallbackQuery):
    target_id = int(call.data.split("_")[1])
    db.update_like_status(target_id, call.from_user.id, 'rejected')
    await call.answer("Rad etildi.")
    await call.message.delete()

@search_router.callback_query(F.data.startswith("view_"))
async def view_profile(call: types.CallbackQuery):
    target_id = int(call.data.split("_")[1])
    target = db.get_user_data(target_id)
    if target and call.message:
        caption = f"👤 {target['name']}, {target['age']}\n📍 {target['region']}\n\n📝 {target['bio']}"
        await call.message.answer_photo(photo=target['photo'], caption=caption)
    await call.answer()

@search_router.callback_query(F.data == "cancel_edit")
async def process_edit_cancel(call: types.CallbackQuery):
    await call.message.answer("Amal bekor qilindi.", reply_markup=reply.main_menu)
    await call.answer()