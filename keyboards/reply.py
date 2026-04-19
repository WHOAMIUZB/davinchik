from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from utils.regions import REGIONS

def make_row_keyboard(items: list) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    for item in items:
        builder.add(KeyboardButton(text=item))
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

start_kb = make_row_keyboard(["👌 boshlaymiz"])
ok_kb = make_row_keyboard(["👌 Ok"])
gender_kb = make_row_keyboard(["men yigitman", "men qizman"])
target_kb = make_row_keyboard(["Qizlar", "Yigitlar", "farqi yo`q"])
photo_kb = make_row_keyboard(["Profilimdan olish"])
confirm_kb = make_row_keyboard(["ha", "tahrirlash"])

phone_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="📱 Mening telefon raqamimni yuborish", request_contact=True)]
], resize_keyboard=True)

def get_regions_kb():
    return make_row_keyboard(list(REGIONS.keys()))

def get_districts_kb(region):
    return make_row_keyboard(REGIONS.get(region, []))

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔍 Qidirish")],
        [KeyboardButton(text="❤️ Yoqtirganlar"), KeyboardButton(text="👤 Mening anketam")]
    ],
    resize_keyboard=True
)