from aiogram.fsm.state import State, StatesGroup

# Xatoni tuzatish: O'z-o'ziga ishora qiluvchi import olib tashlandi.
# Klas nomi RegistrationState bo'lishi kerak, chunki boshqa fayllarda shu nom bilan chaqirilmoqda.

class RegistrationState(StatesGroup):
    agreement = State()
    age = State()
    gender = State()
    target_gender = State()
    region = State()
    district = State()
    name = State()
    bio = State()
    photo = State()
    phone = State()
    confirm = State()

# Agar kodingizning boshqa joyida RegisterSteps nomi ham kerak bo'lsa, 
# shunchaki ikkinchi nom sifatida bog'lab qo'yamiz:
RegisterSteps = RegistrationState