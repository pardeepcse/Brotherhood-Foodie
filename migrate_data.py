from app import app, db
from sqlalchemy import create_engine, inspect

# 1. Local SQLite connection
local_sqlite_uri = "sqlite:///D:/Brotherhood_Foodie/restaurant.db"

# 2. Render PostgreSQL External Connection (Isme apni URL paste karo)
# Note: 'postgres://' ho toh use 'postgresql://' kar dena
render_pg_uri = "postgresql://brotherhood_foodie_db_user:Vstop5q6S7J6AlKA9W33FTjdAiS53xg8@dpg-d9i7hgt8nd3s739dnpv0-a.ohio-postgres.render.com/brotherhood_foodie_db"
if render_pg_uri.startswith("postgres://"):
    render_pg_uri = render_pg_uri.replace("postgres://", "postgresql://", 1)

print("Creating tables on Render PostgreSQL...")
app.config['SQLALCHEMY_DATABASE_URI'] = render_pg_uri
with app.app_context():
    db.create_all() # Pehle Render par blank tables banao

print("Starting data transfer from SQLite to PostgreSQL...")
sqlite_engine = create_engine(local_sqlite_uri)
pg_engine = create_engine(render_pg_uri)

inspector = inspect(sqlite_engine)
tables = inspector.get_table_names()

with sqlite_engine.connect() as sqlite_conn, pg_engine.connect() as pg_conn:
    for table in tables:
        print(f"Migrating table: {table}")
        data = sqlite_conn.execute(db.text(f"SELECT * FROM {table}")).fetchall()
        if data:
            # Get column names
            columns = sqlite_conn.execute(db.text(f"SELECT * FROM {table}")).keys()
            
            # Insert each row into Postgres
            for row in data:
                row_dict = dict(zip(columns, row))
                cols = ", ".join(row_dict.keys())
                vals = ", ".join([f":{k}" for k in row_dict.keys()])
                insert_stmt = db.text(f"INSERT INTO {table} ({cols}) VALUES ({vals}) ON CONFLICT DO NOTHING")
                pg_conn.execute(insert_stmt, row_dict)
            pg_conn.commit()

print("✅ Success! Saara data Render PostgreSQL me migrate ho chuka hai.")