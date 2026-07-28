from sqlalchemy import create_engine, text
from werkzeug.security import generate_password_hash

# Render External Database URL
RENDER_PG_URL = "postgresql://brotherhood_foodie_db_user:Vstop5q6S7J6AlKA9W33FTjdAiS53xg8@dpg-d9i7hgt8nd3s739dnpv0-a.ohio-postgres.render.com/brotherhood_foodie_db"

if RENDER_PG_URL.startswith("postgres://"):
    RENDER_PG_URL = RENDER_PG_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(RENDER_PG_URL)

admin_email = "pardeepkumarcse.ai@gmail.com"
admin_pass = "12345678abc"
hashed_pass = generate_password_hash(admin_pass)

with engine.begin() as conn:
    # 1. Check karo ki user exist karta hai ya nahi
    user = conn.execute(
        text("SELECT id, name FROM users WHERE email = :e"), 
        {"e": admin_email}
    ).fetchone()

    if user:
        # Delete nahi karenge (orders crash bachane ke liye), direct UPDATE karenge
        print(f"🔍 User found (ID: {user[0]}, Name: {user[1]}). Updating password and setting role='admin'...")
        conn.execute(
            text("UPDATE users SET password = :p, role = 'admin' WHERE email = :e"),
            {"p": hashed_pass, "e": admin_email}
        )
        print("✅ Password and Admin role successfully updated!")
    else:
        # User exist nahi karta toh naya Admin insert karo
        print("👤 User not found. Inserting new Admin record...")
        conn.execute(
            text("INSERT INTO users (name, email, password, role) VALUES ('Admin', :e, :p, 'admin')"),
            {"e": admin_email, "p": hashed_pass}
        )
        print("✅ New Admin created!")

print(f"\n🎉 ALL DONE! Live site par ab isse login karo:")
print(f"Email: {admin_email}")
print(f"Password: {admin_pass}")















