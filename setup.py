"""
What this script does:
  1. Checks that required packages are installed
  2. Creates the .env file with your database credentials
  3. Tests the database connection
  4. Creates all required tables
  5. Creates a default admin account

"""

import subprocess
import sys
import os
import re

# ─────────────────────────────────────────────
#  STEP 0 — Install required packages
# ─────────────────────────────────────────────

REQUIRED_PACKAGES = {
    "mysql-connector-python": "mysql.connector",
    "python-dotenv":          "dotenv",
    "bcrypt":                 "bcrypt",
}

def check_and_install_packages():
    print("\n[1/5] Checking required packages...")
    missing = []
    for pip_name, import_name in REQUIRED_PACKAGES.items():
        try:
            __import__(import_name)
            print(f"  ✓  {pip_name}")
        except ImportError:
            print(f"  ✗  {pip_name} — not found, will install")
            missing.append(pip_name)

    if missing:
        print("\n  Installing missing packages...")
        for pkg in missing:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", pkg],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                print(f"  ✓  {pkg} installed")
            else:
                print(f"  ✗  Failed to install {pkg}:")
                print(result.stderr)
                sys.exit(1)
    print("  All packages ready.\n")

check_and_install_packages()

# Now safe to import
import mysql.connector
import bcrypt
import random
import time

#  STEP 1 — Collect database credentials

def prompt(label, default=None, secret=False):
    if default:
        display = f"{label} [{default}]: "
    else:
        display = f"{label}: "
    if secret:
        import getpass
        val = getpass.getpass(display)
    else:
        val = input(display).strip()
    return val if val else default

def collect_credentials():
    print("[2/5] Database Configuration")
    print("  Enter your MySQL connection details.\n")
    host     = prompt("  DB Host",     default="localhost")
    user     = prompt("  DB User",     default="root")
    password = prompt("  DB Password", secret=True)
    db_name  = prompt("  DB Name",     default="inventrack")
    return host, user, password, db_name

#  STEP 2 — Write .env file

def write_env(host, user, password, db_name):
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    with open(env_path, "w") as f:
        f.write(f"DB_HOST={host}\n")
        f.write(f"DB_USER={user}\n")
        f.write(f"DB_PASSWORD={password}\n")
        f.write(f"DB_NAME={db_name}\n")
    print(f"\n  .env file written → {env_path}")

#  STEP 3 — Connect & create database if needed

def get_connection(host, user, password, db_name=None):
    kwargs = dict(host=host, username=user, password=password)
    if db_name:
        kwargs["database"] = db_name
    return mysql.connector.connect(**kwargs)

def setup_database(host, user, password, db_name):
    print("\n[3/5] Testing database connection...")
    try:
        # Connect without selecting a DB first so we can create it if needed
        conn = get_connection(host, user, password)
        cur = conn.cursor()
        cur.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        conn.commit()
        cur.close()
        conn.close()
        print(f"  ✓  Connected. Database '{db_name}' is ready.")
    except mysql.connector.Error as e:
        print(f"  ✗  Connection failed: {e}")
        sys.exit(1)

#  STEP 4 — Create all tables

TABLES = {
    "users": """
        CREATE TABLE IF NOT EXISTS users (
            user_id     VARCHAR(20)  PRIMARY KEY,
            name        VARCHAR(50)  NOT NULL,
            email       VARCHAR(100) UNIQUE NOT NULL,
            password    VARCHAR(255) NOT NULL,
            role        ENUM('admin','user') NOT NULL DEFAULT 'user',
            is_deleted  TINYINT(1) DEFAULT 0,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """,
    "categories": """
        CREATE TABLE IF NOT EXISTS categories (
            category_id   INT AUTO_INCREMENT PRIMARY KEY,
            category_name VARCHAR(100) UNIQUE NOT NULL,
            description   VARCHAR(255)
        )
    """,
    "suppliers": """
        CREATE TABLE IF NOT EXISTS suppliers (
            supplier_id   INT AUTO_INCREMENT PRIMARY KEY,
            supplier_name VARCHAR(100) NOT NULL,
            contact_name  VARCHAR(100),
            phone         VARCHAR(20),
            email         VARCHAR(100),
            address       VARCHAR(255),
            is_deleted    TINYINT(1) DEFAULT 0,
            created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """,
    "product": """
        CREATE TABLE IF NOT EXISTS product (
            product_id    VARCHAR(20)  PRIMARY KEY,
            product_name  VARCHAR(100) NOT NULL,
            sku           VARCHAR(50)  UNIQUE,
            price         FLOAT        NOT NULL,
            cost_price    FLOAT        DEFAULT 0,
            stock         INT          NOT NULL DEFAULT 0,
            reorder_level INT          DEFAULT 5,
            category_id   INT,
            supplier_id   INT,
            is_deleted    TINYINT(1) DEFAULT 0,
            created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories(category_id),
            FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id)
        )
    """,
    "orders": """
        CREATE TABLE IF NOT EXISTS orders (
            order_id     INT AUTO_INCREMENT PRIMARY KEY,
            user_id      VARCHAR(20),
            product_id   VARCHAR(20),
            quantity     INT NOT NULL,
            order_status ENUM('placed','shipped','delivered','cancelled','refunded') NOT NULL DEFAULT 'placed',
            created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id)    REFERENCES users(user_id),
            FOREIGN KEY (product_id) REFERENCES product(product_id)
        )
    """,
    "payment": """
        CREATE TABLE IF NOT EXISTS payment (
            payment_id     INT AUTO_INCREMENT PRIMARY KEY,
            order_id       INT UNIQUE,
            amount         FLOAT NOT NULL,
            payment_status ENUM('pending','completed','failed','refunded') DEFAULT 'pending',
            paid_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (order_id) REFERENCES orders(order_id)
        )
    """,
}

def create_tables(host, user, password, db_name):
    print("\n[4/5] Creating database tables...")
    try:
        conn = get_connection(host, user, password, db_name)
        cur = conn.cursor()
        for table_name, ddl in TABLES.items():
            cur.execute(ddl)
            conn.commit()
            print(f"  ✓  {table_name}")
        cur.close()
        conn.close()
    except mysql.connector.Error as e:
        print(f"  ✗  Error creating tables: {e}")
        sys.exit(1)

#  STEP 5 — Create default admin

def is_valid_email(email):
    return re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,}$', email)

def generate_user_id(name, cur):
    prefix = name[0:3].upper()
    for _ in range(10):
        uid = f"{prefix}{random.randint(1000, 9999)}"
        cur.execute("SELECT user_id FROM users WHERE user_id=%s", (uid,))
        if not cur.fetchone():
            return uid
    return f"{prefix}{str(int(time.time()))[-4:]}"

def create_default_admin(host, user, password, db_name):
    print("\n[5/5] Default Admin Account")

    try:
        conn = get_connection(host, user, password, db_name)
        cur = conn.cursor()

        # Check if any admin already exists
        cur.execute("SELECT COUNT(*) FROM users WHERE role='admin' AND is_deleted=0")
        if cur.fetchone()[0] > 0:
            print("  ℹ  An admin account already exists — skipping creation.")
            cur.close()
            conn.close()
            return

        print("  Set up your default admin credentials.\n")

        # Admin name
        admin_name = prompt("  Admin name", default="Admin")

        # Admin email
        while True:
            admin_email = prompt("  Admin email", default="admin@inventrack.com")
            if is_valid_email(admin_email):
                break
            print("  ✗  Invalid email format. Try again.")

        # Admin password
        import getpass
        while True:
            admin_pass  = getpass.getpass("  Admin password (min 6 chars): ")
            if len(admin_pass) >= 6:
                confirm = getpass.getpass("  Confirm password: ")
                if admin_pass == confirm:
                    break
                print("  ✗  Passwords do not match. Try again.")
            else:
                print("  ✗  Password must be at least 6 characters.")

        user_id = generate_user_id(admin_name, cur)
        hashed  = bcrypt.hashpw(admin_pass.encode('utf-8'), bcrypt.gensalt())

        cur.execute(
            "INSERT INTO users (user_id, name, email, password, role) VALUES (%s,%s,%s,%s,'admin')",
            (user_id, admin_name, admin_email, hashed)
        )
        conn.commit()
        cur.close()
        conn.close()

        print(f"\n  ✓  Admin created successfully!")
        print(f"     User ID : {user_id}")
        print(f"     Name    : {admin_name}")
        print(f"     Email   : {admin_email}")
        print(f"     Role    : admin")

    except mysql.connector.Error as e:
        print(f"  ✗  Error creating admin: {e}")
        sys.exit(1)

#  MAIN

def main():
    print("=" * 52)
    print("      InvenTrack — First-Time Setup")
    print("=" * 52)

    host, user, password, db_name = collect_credentials()
    write_env(host, user, password, db_name)
    setup_database(host, user, password, db_name)
    create_tables(host, user, password, db_name)
    create_default_admin(host, user, password, db_name)

    print("\n" + "=" * 52)
    print("  ✅  Setup complete!")
    print()
    print("  To launch the app:")
    print("    UI version   →  python InvenTrackUI.py")
    print("    CLI version  →  python InvenTrack.py")
    print("=" * 52 + "\n")

if __name__ == "__main__":
    main()