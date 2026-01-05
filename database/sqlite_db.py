import aiosqlite
from pathlib import Path


path = Path("database") / "calories_counter.sqlite3"


class Database:
    def __init__(self, db_path=path):
        self.db_path = db_path
        
    async def init_db(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("PRAGMA foreign_keys = 1")
            
            await db.execute('''
                            CREATE TABLE IF NOT EXISTS users (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            telegram_id INTEGER UNIQUE NOT NULL,
                            full_name TEXT,
                            goal TEXT
                            )
                             ''')
   
            await db.execute('''
                            CREATE TABLE IF NOT EXISTS indicators (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER UNIQUE NOT NULL,
                            height REAL,
                            weight REAL,
                            calories_goal REAL,
                            belki REAL,
                            jiri REAL,
                            uglevodi REAL,
                            
                            FOREIGN KEY (user_id) REFERENCES users(telegram_id) ON DELETE CASCADE
                            )
                             ''')
                            
            await db.execute('''
                            CREATE TABLE IF NOT EXISTS history (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER NOT NULL,
                            weight REAL,
                            calories REAL DEFAULT 0,
                            belki REAL DEFAULT 0,
                            jiri REAL DEFAULT 0,
                            uglevodi REAL DEFAULT 0,
                            days_date DATE DEFAULT CURRENT_DATE,
                            
                            FOREIGN KEY (user_id) REFERENCES users(telegram_id) ON DELETE CASCADE,
                            UNIQUE(user_id, days_date)
                            )
                             ''')
            
            await db.execute('''
                             CREATE INDEX IF NOT EXISTS idx_history_user_date ON history(user_id, days_date)
                             ''')
            
            await db.execute('''
                             CREATE INDEX IF NOT EXISTS idx_indicators_user ON indicators(user_id)
                             ''')
            
            await db.execute('''
                             CREATE INDEX IF NOT EXISTS idx_users_telegram ON users(telegram_id)
                             ''')
            
            await db.commit()
            print("Бд инициализирована!")
            
            
    async def create_day_by_product(self, user_id, 
                                          calories, belki,
                                          jiri, uglevodi, date):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                             INSERT INTO history
                             (user_id, weight, calories, belki, jiri, uglevodi, days_date)
                             VALUES (?, (SELECT weight FROM indicators WHERE user_id = ?), ?, ?, ?, ?, ?)
                             ''', (user_id, user_id, calories, belki, jiri, uglevodi, date))
            await db.commit()
            
            
    async def add_product_to_progress(self, user_id, 
                                          calories, belki,
                                          jiri, uglevodi, date):
        async with aiosqlite.connect(self.db_path) as db:
            #умная функция от дипсика но я бы до такого не догадался бы никогда хоть и понял принцип работы, не хочу использовать
            #по факту я сам подал идею не заполнять нулями тк это лишние операции и что можно сразу добавлять первый продукт
            #но все равно код написал не я и я бы его так сделать не смог
            
            # await db.execute('''
            # INSERT INTO history 
            # (user_id, days_date, weight, today_calories, belki, jiri, uglevodi)
            # VALUES (
            #     ?, 
            #     DATE('now'), 
            #     (SELECT weight FROM indicators WHERE user_id = ?),
            #     ?,
            #     ?,
            #     ?,
            #     ?
            # )
            # ON CONFLICT(user_id, days_date) DO UPDATE SET
            #     today_calories = today_calories + excluded.today_calories,
            #     belki = belki + excluded.belki,
            #     jiri = jiri + excluded.jiri,
            #     uglevodi = uglevodi + excluded.uglevodi
            #                  ''', (user_id, user_id, calories, belki, jiri, uglevodi))
            
            await db.execute('''
                             UPDATE history
                             SET
                                calories = calories + ?,
                                belki = belki + ?,
                                jiri = jiri + ?,
                                uglevodi = uglevodi + ?
                             WHERE user_id = ? AND days_date = ?
                             ''', (calories, belki, jiri, uglevodi, user_id, date))
            
            await db.commit()
    
    
    async def save_data(self, telegram_id: int, full_name: str, goal: str,
                              height: float, weight: float, calories_goal: float,
                              belki: float, jiri: float, uglevodi: float):
        async with aiosqlite.connect(self.db_path) as db:
            #in users
            await db.execute('''
                             INSERT INTO users (telegram_id, full_name, goal)
                             VALUES (?, ?, ?)
                             ON CONFLICT(telegram_id) DO UPDATE SET
                                full_name = excluded.full_name,
                                goal = excluded.goal
                             ''', (telegram_id, full_name, goal)
                             )
            await db.commit()
            
            #in indicators
            await db.execute('''
                             INSERT INTO indicators (user_id, height, weight, calories_goal, belki, jiri, uglevodi)
                             VALUES (?, ?, ?, ?, ?, ?, ?)
                             ON CONFLICT(user_id) DO UPDATE SET
                                height = excluded.height,
                                weight = excluded.weight,
                                calories_goal = excluded.calories_goal,
                                belki = excluded.belki,
                                jiri = excluded.jiri,
                                uglevodi = excluded.uglevodi
                             ''', (telegram_id, height, weight, calories_goal, belki, jiri, uglevodi)
                             )
            await db.commit()
    
    
    async def update_data(self, user_id, goal=None, height=None,
                                weight=None, calories_goal=None, belki=None,
                                jiri=None, uglevodi=None):
        async with aiosqlite.connect(self.db_path) as db:
            if goal is not None:
                await db.execute('''
                                UPDATE users
                                SET 
                                    goal = ?
                                WHERE telegram_id = ?
                                ''', (goal, user_id))
                await db.commit()
                
            if height is not None:
                await db.execute('''
                                UPDATE indicators
                                SET 
                                    height = ?
                                WHERE user_id = ?
                                ''', (height, user_id))
                await db.commit()
                
            if weight is not None:
                await db.execute('''
                                UPDATE indicators
                                SET 
                                    weight = ?
                                WHERE user_id = ?
                                ''', (weight, user_id))
                await db.commit()    
            
            if ((calories_goal is not None) and 
                (belki is not None) and 
                (jiri is not None) and 
                (uglevodi is not None)):
                await db.execute('''
                                UPDATE indicators
                                SET 
                                    calories_goal = ?,
                                    belki = ?,
                                    jiri = ?,
                                    uglevodi = ?
                                WHERE user_id = ?
                                ''', (calories_goal, belki, jiri, uglevodi, user_id))
                await db.commit()
            
        
    async def show_daily_progress(self, user_id, today_date):
        async with aiosqlite.connect(self.db_path) as db:
            curr_day = await db.execute('''
                             SELECT calories, belki, jiri, uglevodi
                             FROM history
                             WHERE user_id = ? AND days_date = ?
                             ''', (user_id, today_date))

            result = await curr_day.fetchone()
            
            if result:
                return result
            return None
            
    
    async def show_week_history(self, user_id):
        async with aiosqlite.connect(self.db_path) as db:
            weekly_data = await db.execute('''
                                           SELECT calories, belki, jiri, uglevodi, days_date
                                           FROM history
                                           WHERE user_id = ? AND days_date >= date('now', '-7 days')
                                           ORDER BY days_date DESC
                                           ''', (user_id,))
            
            result = await weekly_data.fetchall()
            
            if result:
                return result
            return None
    
    
    async def get_profile(self, telegram_id):
        async with aiosqlite.connect(self.db_path) as db:
            from_users_and_indicators = await db.execute('''
                                                         SELECT
                                                            u.full_name, 
                                                            u.goal,
                                                            i.height,
                                                            i.weight,
                                                            i.calories_goal,
                                                            i.belki,
                                                            i.jiri,
                                                            i.uglevodi
                                                         FROM users u
                                                         LEFT JOIN indicators i ON u.telegram_id = i.user_id
                                                         WHERE u.telegram_id = ?
                                                         ''', (telegram_id,))

            result = await from_users_and_indicators.fetchone()
            
            if result:
                return result
            return None
        
        
    async def get_progress_goal(self, telegram_id):
        async with aiosqlite.connect(self.db_path) as db:
            from_indicators = await db.execute('''
                                               SELECT calories_goal, belki, jiri, uglevodi
                                               FROM indicators
                                               WHERE user_id = ?
                                               ''', (telegram_id,))

            result = await from_indicators.fetchone()
            
            if result:
                return result
            return None
        
        
db = Database()