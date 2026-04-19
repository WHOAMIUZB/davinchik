from aiogram import Router, F, types, Bot
from keyboards.reply import start_kb
from database.db import db
from typing import cast 

admin_router = Router()
# handlers/admin_moderation.py (yoki mos fayl)

@admin_router.callback_query(F.data.startswith("accept_"))
async def accept_anketa(call: types.CallbackQuery, bot: Bot):
    # ... mavjud kodlar ...
    
    # XATONI TUZATISH: Markdown o'rniga HTML ishlatish xavfsizroq
    # yoki maxsus belgilarni tozalash kerak
    status_text = "\n\n✅ <b>HOLAT: Tasdiqlandi</b>"
    
    current_caption = call.message.caption or ""
    
    try:
        await call.message.edit_caption(
            caption=f"{current_caption}{status_text}",
            parse_mode="HTML" # Markdown o'rniga HTML ishlating
        )
    except Exception as e:
        # Agar xato bersa, formatlashsiz yuborish
        await call.message.edit_caption(
            caption=f"{current_caption}\n\n✅ HOLAT: Tasdiqlandi",
            parse_mode=None 
        )
    # ...
@admin_router.callback_query(F.data.startswith("reject_"))
async def reject_anketa(call: types.CallbackQuery, bot: Bot):
    if not call.data or not isinstance(call.message, types.Message):
        return

    try:
        user_id = int(call.data.split("_")[1])
        # TUZATILDI: Rad etilganda statusni 'new' qilib, foydalanuvchiga qayta to'ldirish imkonini berish
        db.set_status(user_id, "new") 
        
        await bot.send_message(
            chat_id=user_id,
            text="Anketangiz yaroqsiz deb topildi. ⚠️ Iltimos, ma'lumotlarni tekshirib qaytadan to'ldiring.",
            reply_markup=start_kb
        )
        
        msg = cast(types.Message, call.message)
        current_caption = msg.caption or ""
        
        await msg.edit_caption(
            caption=f"{current_caption}\n\n❌ **HOLAT: Rad etildi**",
            parse_mode="Markdown",
            reply_markup=None
        )
        await call.answer("Anketa rad etildi ❌")
        
    except Exception as e:
        await call.answer(f"Xatolik: {e}", show_alert=True)