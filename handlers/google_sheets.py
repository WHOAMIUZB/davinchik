import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
JSON_FILE = "credentials.json" 
SHEET_NAME = "davinchik" # Jadvalingiz nomi 'Новая таблица' bo'lsa, shunga o'zgartiring

class GoogleSheetsManager:
    def __init__(self):
        try:
            creds = Credentials.from_service_account_file(JSON_FILE, scopes=SCOPE)
            client = gspread.authorize(creds)
            self.sheet = client.open(SHEET_NAME).sheet1
            
            # Birinchi qatorni tekshirish
            first_row = self.sheet.row_values(1)
            if not first_row:
                # Agar birinchi qator bo'sh bo'lsa, sarlavhalarni yozamiz
                headers = [
                    "Ism", "Yosh", "Viloyat", "Tuman", "Telefon raqami", 
                    "O'zi haqida ta'rif", "Telegram nomi", "Telegram ID", 
                    "Username", "Yoqtirganlar soni", "Yoqmaganlar soni", "Qo'shilgan sana"
                ]
                self.sheet.insert_row(headers, 1) # 1-qatorga sarlavhalarni qo'shish
        except Exception as e:
            print(f"Sheets ulanishda xato: {e}")

    def add_user_row(self, data):
        """Ma'lumotlarni sarlavhalar ostidan qo'shish"""
        try:
            row = [
                data.get('name'), 
                data.get('age'), 
                data.get('region'),
                data.get('district'), 
                data.get('phone'), 
                data.get('bio'),
                data.get('full_name'), 
                data.get('user_id'), 
                data.get('username'),
                0, 0, 
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ]
            self.sheet.append_row(row)
        except Exception as e:
            print(f"Yozishda xato: {e}")

gs_db = GoogleSheetsManager()