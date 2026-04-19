from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

def get_admin_kb(user_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"accept_{user_id}"),
            InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_{user_id}")
        ]
    ])

def get_retry_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🔄 Qayta anketa yaratish")]
    ], resize_keyboard=True)

def get_search_inline(target_user_id):
    """Qidiruv paytida chiqadigan tugmalar"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="❤️ Yoqdi", callback_data=f"like_{target_user_id}"),
            InlineKeyboardButton(text="✍️ Yozish", callback_query_data=f"write_{target_user_id}"),
            InlineKeyboardButton(text="👎 Yoqmadi", callback_data="next_profile")
        ]
    ])

def get_message_kb(sender_id):
    """Xabar kelganda chiqadigan tugmalar"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="↩️ Javob yozish", callback_data=f"write_{sender_id}"),
            InlineKeyboardButton(text="👤 Anketasini ko'rish", callback_data=f"view_{sender_id}")
        ],
        [InlineKeyboardButton(text="🗑 O'chirish", callback_data="delete_msg")]
    ])