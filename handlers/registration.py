from aiogram import Router, types, F, Bot
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from states.register_state import RegisterSteps
from keyboards import reply
from utils.regions import REGIONS
from keyboards.inline import get_admin_kb
from database.db import db 
from keyboards.reply import main_menu, start_kb
from .google_sheets import gs_db

# Routerni e'lon qilamiz
router = Router()
registration_router = router 


ADMIN_ID = 7861165622

@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    if not message.from_user:
        return
        
    user_id = message.from_user.id
    if not db.user_exists(user_id):
        db.add_user(user_id)
    
    user_data = db.get_user_data(user_id)
    
    # TUZATILDI: statusni xavfsiz olish mantiqi
    status = "new"
    if user_data:
        if isinstance(user_data, dict):
            status = user_data.get('status', 'new')
        else:
            try:
                status = user_data.status
            except AttributeError:
                status = "new"

    if status == 'active':
        return await message.answer(
            "Siz allaqachon ro'yxatdan o'tgansiz! Qidiruvni boshlashingiz mumkin.",
            reply_markup=main_menu
        )
    elif status == "pending":
        return await message.answer(
            "Anketangiz moderatsiyada ⏳, lekin botdan foydalanishingiz mumkin:",
            reply_markup=main_menu
        )

    await message.answer("Dayvinchikda tanishuvni boshlaymiz! 😍", reply_markup=start_kb)

@router.message(F.text == "👌 boshlaymiz")
async def start_reg(message: types.Message, state: FSMContext):
    await message.answer(
        "❗️ Internetda odamlar o'zini boshqasi sifatida ko'rsatishi mumkinligini unutma.\n\n"
        "Bot shaxsiy ma'lumotlarni so'ramaydi va foydalanuvchilarni identifikatsiya qilmaydi.",
        reply_markup=reply.ok_kb
    )
    await state.set_state(RegisterSteps.agreement)

@router.message(RegisterSteps.agreement, F.text == "👌 Ok")
async def ask_age(message: types.Message, state: FSMContext):
    await message.answer("Yoshingiz nechida?", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(RegisterSteps.age)

@router.message(RegisterSteps.age)
async def process_age(message: types.Message, state: FSMContext):
    if not message.text or not message.text.isdigit() or not (10 < int(message.text) < 100):
        return await message.answer("Iltimos, yoshingizni to'g'ri raqamlarda kiriting!")
    await state.update_data(age=message.text)
    await message.answer("Endi jinsingizni aniqlab olaylik:", reply_markup=reply.gender_kb)
    await state.set_state(RegisterSteps.gender)

@router.message(RegisterSteps.gender, F.text.in_(["men yigitman", "men qizman"]))
async def process_gender(message: types.Message, state: FSMContext):
    await state.update_data(gender=message.text)
    await message.answer("Senga kim qiziq?", reply_markup=reply.target_kb)
    await state.set_state(RegisterSteps.target_gender)

@router.message(RegisterSteps.target_gender, F.text.in_(["Qizlar", "Yigitlar", "farqi yo`q"]))
async def process_target(message: types.Message, state: FSMContext):
    await state.update_data(target=message.text)
    await message.answer("Qaysi viloyatdansiz?", reply_markup=reply.get_regions_kb())
    await state.set_state(RegisterSteps.region)

@router.message(RegisterSteps.region, F.text.in_(REGIONS.keys()))
async def process_region(message: types.Message, state: FSMContext):
    await state.update_data(region=message.text)
    await message.answer(f"{message.text}ning qaysi tumanidansiz?", reply_markup=reply.get_districts_kb(message.text))
    await state.set_state(RegisterSteps.district)

@router.message(RegisterSteps.district)
async def process_district(message: types.Message, state: FSMContext):
    await state.update_data(district=message.text)
    await message.answer("Seni qanday chaqiray?", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(RegisterSteps.name)

@router.message(RegisterSteps.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("O'zing va kimni topmoqchi ekaning haqida yoz.")
    await state.set_state(RegisterSteps.bio)

@router.message(RegisterSteps.bio)
async def process_bio(message: types.Message, state: FSMContext):
    await state.update_data(bio=message.text)
    await message.answer("Suratingni yubor.\n\nYuz ko'rinadigan anketalar ko'proq layk oladi ❤️", reply_markup=reply.photo_kb)
    await state.set_state(RegisterSteps.photo)

@router.message(RegisterSteps.photo, F.photo | (F.text == "Profilimdan olish"))
async def process_photo(message: types.Message, state: FSMContext, bot: Bot):
    if not message.from_user:
        return
        
    photo_id = None
    if message.photo:
        photo_id = message.photo[-1].file_id
    elif message.text == "Profilimdan olish":
        user_photos = await bot.get_user_profile_photos(message.from_user.id)
        if user_photos.total_count > 0:
            photo_id = user_photos.photos[0][-1].file_id
        else:
            return await message.answer("Profil rasmingiz topilmadi, iltimos rasm yuboring.")
    
    if not photo_id:
        return await message.answer("Iltimos, rasm yuboring yoki tugmani bosing.")
    
    await state.update_data(photo=photo_id)
    await message.answer("Telefon raqamingizni yuboring:", reply_markup=reply.phone_kb)
    await state.set_state(RegisterSteps.phone)

@router.message(RegisterSteps.phone, F.contact)
async def process_phone(message: types.Message, state: FSMContext):
    if not message.contact:
        return await message.answer("Iltimos, kontaktni yuboring!")
        
    await state.update_data(phone=message.contact.phone_number)
    data = await state.get_data()
    
    text = f"Anketangiz shunday ko'rinadi:\n\n{data.get('name')}, {data.get('age')}\n{data.get('region')}, {data.get('district')}\n{data.get('bio')}"
    await message.answer_photo(data['photo'], caption=text)
    await message.answer("Hammasi to'g'rimi?", reply_markup=reply.confirm_kb)
    await state.set_state(RegisterSteps.confirm)

@router.message(RegisterSteps.confirm, F.text == "ha")
async def finish(message: types.Message, state: FSMContext, bot: Bot):
    if not message.from_user:
        return
        
    data = await state.get_data()
    user_id = message.from_user.id
    
    # Google Sheets uchun qo'shimcha ma'lumotlarni tayyorlash
    data['user_id'] = user_id
    data['full_name'] = message.from_user.full_name
    data['username'] = f"@{message.from_user.username}" if message.from_user.username else "Mavjud emas"
    
    # 1. SQL bazani yangilash
    db.update_user_data(user_id, data)
    db.set_status(user_id, "pending")
    
    # 2. Google Sheetsga yozish
    gs_db.add_user_row(data)
    
    # 3. Adminga yuborish
    admin_text = (
        f"Yangi anketa! 📩\n\n"
        f"Ism: {data.get('name')}\n"
        f"Yosh: {data.get('age')}\n"
        f"Manzil: {data.get('region')}, {data.get('district')}\n"
        f"Tel: {data.get('phone')}\n"
        f"Username: {data['username']}\n"
        f"Bio: {data.get('bio')}"
    )
    
    await bot.send_photo(
        chat_id=ADMIN_ID,
        photo=data['photo'],
        caption=admin_text,
        reply_markup=get_admin_kb(user_id)
    )

    await message.answer(
        "Ajoyib! Anketangiz tasdiqlash uchun yuborildi va bazaga saqlandi. ⏳",
        reply_markup=main_menu 
    )
    await state.clear()
    
@router.message(F.text == "🔄 Qayta anketa yaratish")
@router.message(RegisterSteps.confirm, F.text == "tahrirlash")
async def retry(message: types.Message, state: FSMContext):
    if not message.from_user:
        return
        
    db.set_status(message.from_user.id, "new")
    await state.clear()
    await message.answer("Anketani qaytadan to'ldirishni boshlaymiz.")
    await cmd_start(message, state)

@router.callback_query(F.data == "confirm_edit")
async def process_edit_confirmed(call: types.CallbackQuery, state: FSMContext):
    if not call.from_user:
        return

    user_id = call.from_user.id
    db.set_status(user_id, "new")
    await state.clear()
    
    if call.message:
        await call.message.delete()
        await call.message.answer(
            "Anketangiz o'chirildi. Keling, hammasini noldan boshlaymiz! 😍", 
            reply_markup=start_kb
        )
    await call.answer()