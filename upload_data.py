import sqlite3
from sqlalchemy import create_engine, text


SQLITE_PATH = r"D:\Brotherhood_Foodie\restaurant.db"


RENDER_PG_URL = "postgresql://brotherhood_foodie_db_user:Vstop5q6S7J6AlKA9W33FTjdAiS53xg8@dpg-d9i7hgt8nd3s739dnpv0-a.ohio-postgres.render.com/brotherhood_foodie_db"

if RENDER_PG_URL.startswith("postgres://"):
    RENDER_PG_URL = RENDER_PG_URL.replace("postgres://", "postgresql://", 1)

print("🔌 Connecting to Local SQLite and Render PostgreSQL...")

sqlite_conn = sqlite3.connect(SQLITE_PATH)
sqlite_conn.row_factory = sqlite3.Row
sqlite_cursor = sqlite_conn.cursor()

pg_engine = create_engine(RENDER_PG_URL)

# Local SQLite se saari tables fetch karo
sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
tables = [r[0] for r in sqlite_cursor.fetchall()]

print(f"📋 Found tables: {tables}")

with pg_engine.begin() as pg_conn:
    for table in tables:
        print(f"⏳ Copying data for table: {table}...")
        sqlite_cursor.execute(f"SELECT * FROM {table}")
        rows = sqlite_cursor.fetchall()
        
        if not rows:
            print(f"   (Table {table} is empty, skipping)")
            continue
            
        columns = rows[0].keys()
        cols_str = ", ".join(columns)
        placeholders = ", ".join([f":{col}" for col in columns])
        
        insert_query = text(f"INSERT INTO {table} ({cols_str}) VALUES ({placeholders}) ON CONFLICT DO NOTHING")
        
        count = 0
        for row in rows:
            row_dict = dict(row)
            
            # FIX: SQLite 1 / 0 ko Postgres BOOLEAN (True / False) me convert karo
            for key, val in row_dict.items():
                if key in ['available', 'is_admin', 'is_active', 'is_staff', 'active', 'status']:
                    if val == 1:
                        row_dict[key] = True
                    elif val == 0:
                        row_dict[key] = False

            pg_conn.execute(insert_query, row_dict)
            count += 1
        print(f"   ✅ Migrated {count} rows in '{table}'")

print("\n🎉 Success! Saara data Render PostgreSQL me upload ho gaya hai!")