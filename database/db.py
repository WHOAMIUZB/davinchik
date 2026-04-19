import sqlite3
from datetime import datetime
from typing import List, Optional, Tuple, Any, Union

class Database:
    def __init__(self, db_file: str):
        # check_same_thread=False - Telegram botlar (Aiogram) kabi asinxron 
        # muhitda SQLite xato bermasligi uchun juda muhim!
        self.connection = sqlite3.connect(db_file, check_same_thread=False)
        self.cursor = self.connection.cursor()
        self.create_table()

    def create_table(self) -> None:
        with self.connection:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    name TEXT, age INTEGER, gender TEXT, target TEXT,
                    region TEXT, district TEXT, bio TEXT, photo TEXT,
                    phone TEXT, status TEXT DEFAULT 'new',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS likes (
                    from_user INTEGER, to_user INTEGER,
                    status TEXT DEFAULT 'pending',
                    PRIMARY KEY (from_user, to_user)
                )
            """)
            self.cursor.execute("PRAGMA table_info(users)")
            existing_columns = [col[1] for col in self.cursor.fetchall()]
            new_columns = ['name', 'age', 'gender', 'target', 'region', 'district', 'bio', 'photo', 'phone', 'status', 'created_at']
            
            for col in new_columns:
                if col not in existing_columns:
                    if col == 'created_at':
                        # XATOLIK TUZATILDI: DEFAULT CURRENT_TIMESTAMP olib tashlandi
                        self.cursor.execute(f"ALTER TABLE users ADD COLUMN {col} TIMESTAMP")
                        # Bazada avvaldan bor foydalanuvchilarning vaqtini hozirgi vaqtga to'ldirib qo'yamiz
                        self.cursor.execute("UPDATE users SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL")
                    else:
                        self.cursor.execute(f"ALTER TABLE users ADD COLUMN {col} TEXT")
            self.connection.commit()

    def user_exists(self, user_id: int) -> bool:
        with self.connection:
            return bool(self.cursor.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,)).fetchone())

    def add_user(self, user_id: int):
        with self.connection:
            # YANGI: Foydalanuvchi qo'shilayotganda vaqtni ham kiritib ketamiz
            res = self.cursor.execute(
                "INSERT OR IGNORE INTO users (user_id, created_at) VALUES (?, CURRENT_TIMESTAMP)", 
                (user_id,)
            )
            self.connection.commit()
            return res

    def get_status(self, user_id: int) -> Optional[str]:
        with self.connection:
            res = self.cursor.execute("SELECT status FROM users WHERE user_id = ?", (user_id,)).fetchone()
            return res[0] if res else None

    def set_status(self, user_id: int, status: str):
        with self.connection:
            res = self.cursor.execute("UPDATE users SET status = ? WHERE user_id = ?", (status, user_id))
            self.connection.commit()
            return res

    def update_user_data(self, user_id: int, data: dict):
        with self.connection:
            res = self.cursor.execute("""
                UPDATE users SET name=?, age=?, gender=?, target=?, region=?, district=?, bio=?, photo=?, phone=?
                WHERE user_id=?
            """, (data.get('name'), data.get('age'), data.get('gender'), data.get('target'),
                  data.get('region'), data.get('district'), data.get('bio'), data.get('photo'), 
                  data.get('phone'), user_id))
            self.connection.commit()
            return res

    def get_user_data(self, user_id: int) -> Optional[sqlite3.Row]:
        with self.connection:
            self.cursor.row_factory = sqlite3.Row
            return self.cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()

    def get_search_results(self, user_id: int, region: str, district: str) -> List[sqlite3.Row]:
        """Eski qidiruv metodi (zaxira uchun saqlandi)"""
        with self.connection:
            self.cursor.row_factory = sqlite3.Row
            res = self.cursor.execute("SELECT * FROM users WHERE status='active' AND user_id!=? AND district=?", (user_id, district)).fetchall()
            if res: return res
            res = self.cursor.execute("SELECT * FROM users WHERE status='active' AND user_id!=? AND region=?", (user_id, region)).fetchall()
            if res: return res
            return self.cursor.execute("SELECT * FROM users WHERE status='active' AND user_id!=?", (user_id,)).fetchall()

    def add_like(self, from_user: int, to_user: int):
        with self.connection:
            res = self.cursor.execute("INSERT OR REPLACE INTO likes (from_user, to_user) VALUES (?, ?)", (from_user, to_user))
            self.connection.commit()
            return res

    def get_who_liked_me(self, user_id: int) -> List[sqlite3.Row]:
        with self.connection:
            self.cursor.row_factory = sqlite3.Row
            return self.cursor.execute("""
                SELECT users.* FROM users 
                JOIN likes ON users.user_id = likes.from_user 
                WHERE likes.to_user = ? AND likes.status = 'pending'
            """, (user_id,)).fetchall()

    def update_like_status(self, from_user: int, to_user: int, status: str):
        with self.connection:
            res = self.cursor.execute(
                "UPDATE likes SET status = ? WHERE from_user = ? AND to_user = ?",
                (status, from_user, to_user)
            )
            self.connection.commit()
            return res

    def get_all_users(self) -> List[Tuple]:
        with self.connection:
            return self.cursor.execute("SELECT user_id FROM users").fetchall()

    def get_stats(self) -> Tuple[Union[int, str], Union[int, str]]:
        with self.connection:
            total_users = self.cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            today = datetime.now().strftime('%Y-%m-%d')
            try:
                today_users = self.cursor.execute(
                    "SELECT COUNT(*) FROM users WHERE date(created_at) = ?", (today,)
                ).fetchone()[0]
            except Exception as e:
                today_users = "0 (ustun yo'q)"
            return total_users, today_users

    def delete_user_profile(self, user_id: int) -> bool:
        with self.connection:
            self.cursor.execute("""
                UPDATE users 
                SET status = 'new', name = NULL, age = NULL, region = NULL, 
                    district = NULL, bio = NULL, photo = NULL, phone = NULL 
                WHERE user_id = ?
            """, (user_id,))
            self.connection.commit()
            return self.cursor.rowcount > 0

    def get_user_stats(self, user_id: int) -> Tuple[int, int]:
        with self.connection:
            likes = self.cursor.execute(
                "SELECT COUNT(*) FROM likes WHERE to_user = ? AND status = 'accepted'", 
                (user_id,)
            ).fetchone()[0]
            dislikes = self.cursor.execute(
                "SELECT COUNT(*) FROM likes WHERE to_user = ? AND status = 'rejected'", 
                (user_id,)
            ).fetchone()[0]
            return likes, dislikes

    def get_users_for_search(self, viewer_id: int, target_gender: str, region: str, district: str) -> List[sqlite3.Row]:
        self.cursor.row_factory = sqlite3.Row
        
        # DEBUG uchun konsolga chiqarish (bot ishlayotgan terminalda ko'rasiz)
        print(f"Qidirilmoqda: Viewer:{viewer_id}, Jins:{target_gender}, Region:{region}")

        # Agar jins "Farqi yo'q" (all) bo'lsa
        if target_gender == "all":
            query = "SELECT * FROM users WHERE user_id != ?"
            params = [viewer_id]
        else:
            # target_gender bu yerda "men qizman" yoki "men yigitman" qiymatlarini oladi
            query = "SELECT * FROM users WHERE user_id != ? AND gender = ?"
            params = [viewer_id, target_gender]

        # 1. Tuman bo'yicha qidiruv
        res = self.cursor.execute(query + " AND region = ? AND district = ?", tuple(params + [region, district])).fetchall()
        if res: return res

        # 2. Viloyat bo'yicha qidiruv
        res = self.cursor.execute(query + " AND region = ?", tuple(params + [region])).fetchall()
        if res: return res

        # 3. Hamma joydan qidiruv
        return self.cursor.execute(query, tuple(params)).fetchall()

    def get_random_users(self, viewer_id: int, target_gender: str, region: str) -> List[sqlite3.Row]:
        """Random qidiruv uchun bazadan ma'lumot olish"""
        self.cursor.row_factory = sqlite3.Row
        
        if target_gender == "all":
            query = "SELECT * FROM users WHERE user_id != ? AND status = 'active' AND region = ?"
            params: List[Union[int, str]] = [viewer_id, region]
        else:
            query = "SELECT * FROM users WHERE user_id != ? AND status = 'active' AND gender = ? AND region = ?"
            params = [viewer_id, target_gender, region]
            
        res = self.cursor.execute(query, tuple(params)).fetchall()
        
        # Agar viloyatda topilmasa, respublika miqyosida qidirish
        if not res:
            if target_gender == "all":
                query = "SELECT * FROM users WHERE user_id != ? AND status = 'active'"
                params = [viewer_id]
            else:
                query = "SELECT * FROM users WHERE user_id != ? AND status = 'active' AND gender = ?"
                params = [viewer_id, target_gender]
            res = self.cursor.execute(query, tuple(params)).fetchall()
            
        return res

# Asosiy baza obyekti
db = Database("bot_database.db")