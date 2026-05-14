import mysql.connector
import random
import mysql.connector.errors
from dotenv import load_dotenv
import os
import bcrypt
import time
import re

load_dotenv()

try:
    connect = mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        username=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )
    if connect.is_connected():
        print('Connected successfully')
except mysql.connector.Error as e:
    print("Error while connecting to MySQL", e)
    exit()

cursor = connect.cursor()
current_user_id = None  # Global variable to store the logged-in user's ID


# ─────────────────────────────────────────────
#  TABLE CREATION
# ─────────────────────────────────────────────

def create_user_table():
    try:
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id VARCHAR(20) PRIMARY KEY,
            name VARCHAR(50) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            role ENUM('admin','user') NOT NULL DEFAULT 'user',
            is_deleted TINYINT(1) DEFAULT 0
        )
        ''')
        connect.commit()
        print("User table ready.")
    except mysql.connector.Error as e:
        print("Error while creating user table", e)
create_user_table()


def create_categories_table():
    try:
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            category_id INT AUTO_INCREMENT PRIMARY KEY,
            category_name VARCHAR(100) UNIQUE NOT NULL,
            description VARCHAR(255)
        )
        ''')
        connect.commit()
        print("Categories table ready.")
    except mysql.connector.Error as e:
        print("Error while creating categories table", e)
create_categories_table()


def create_suppliers_table():
    try:
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS suppliers (
            supplier_id INT AUTO_INCREMENT PRIMARY KEY,
            supplier_name VARCHAR(100) NOT NULL,
            contact_name VARCHAR(100),
            phone VARCHAR(20),
            email VARCHAR(100),
            address VARCHAR(255),
            is_deleted TINYINT(1) DEFAULT 0
        )
        ''')
        connect.commit()
        print("Suppliers table ready.")
    except mysql.connector.Error as e:
        print("Error while creating suppliers table", e)
create_suppliers_table()


def create_product_table():
    try:
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS product (
            product_id VARCHAR(20) PRIMARY KEY,
            product_name VARCHAR(100) NOT NULL,
            sku VARCHAR(50) UNIQUE,
            price FLOAT NOT NULL,
            cost_price FLOAT DEFAULT 0,
            stock INT NOT NULL DEFAULT 0,
            reorder_level INT DEFAULT 5,
            category_id INT,
            supplier_id INT,
            is_deleted TINYINT(1) DEFAULT 0,
            FOREIGN KEY (category_id) REFERENCES categories(category_id),
            FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id)
        )
        ''')
        connect.commit()
        print("Product table ready.")
    except mysql.connector.Error as e:
        print("Error while creating product table", e)
create_product_table()


def create_orders_table():
    try:
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            order_id INT AUTO_INCREMENT PRIMARY KEY,
            user_id VARCHAR(20),
            product_id VARCHAR(20),
            quantity INT NOT NULL,
            order_status ENUM('placed', 'shipped', 'delivered', 'cancelled', 'refunded') NOT NULL DEFAULT 'placed',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (product_id) REFERENCES product(product_id)
        )
        ''')
        connect.commit()
        print("Orders table ready.")
    except mysql.connector.Error as e:
        print("Error while creating orders table", e)
create_orders_table()


def create_payment_table():
    try:
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS payment (
            payment_id INT AUTO_INCREMENT PRIMARY KEY,
            order_id INT UNIQUE,
            amount FLOAT NOT NULL,
            payment_status ENUM('pending','completed','failed','refunded') DEFAULT 'pending',
            paid_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(order_id) REFERENCES orders(order_id)
        )
        ''')
        connect.commit()
        print("Payment table ready.")
    except mysql.connector.Error as e:
        print("Error while creating payment table", e)
create_payment_table()


# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────

def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email)


def generate_user_id(name):
    prefix = name[0:3].upper()
    for _ in range(10):
        uid = f"{prefix}{random.randint(1000, 9999)}"
        cursor.execute("SELECT user_id FROM users WHERE user_id=%s", (uid,))
        if not cursor.fetchone():
            return uid
    return f"{prefix}{str(int(time.time()))[-4:]}"


def generate_product_id(product_name):
    prefix = product_name[0:2].upper()
    for _ in range(10):
        pid = f"{prefix}{random.randint(1000, 9999)}"
        cursor.execute("SELECT product_id FROM product WHERE product_id=%s", (pid,))
        if not cursor.fetchone():
            return pid
    return f"{prefix}{str(int(time.time()))[-4:]}"


def generate_sku(product_name, category_id=None):
    """Auto-generate a SKU like CAT-PRD-0001"""
    prefix = product_name[0:3].upper()
    cat_prefix = "GEN"
    if category_id:
        cursor.execute("SELECT category_name FROM categories WHERE category_id=%s", (category_id,))
        cat = cursor.fetchone()
        if cat:
            cat_prefix = cat[0][0:3].upper()
    suffix = str(random.randint(1000, 9999))
    return f"{cat_prefix}-{prefix}-{suffix}"


# ─────────────────────────────────────────────
#  USER MANAGEMENT
# ─────────────────────────────────────────────

def add_user():
    try:
        name = input("Enter name: ").strip()
        if not name:
            print("Name cannot be empty.")
            return
        user_id = generate_user_id(name)

        while True:
            email = input("Enter email: ").strip()
            if is_valid_email(email):
                break
            print("Invalid email format. Please enter a valid email (e.g. abc@gmail.com)")

        password = input("Enter password: ")
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        while True:
            role = input("Enter role (admin/user): ").strip().lower()
            if role in ['admin', 'user']:
                break
            print("Invalid role. Please enter 'admin' or 'user'.")

        cursor.execute(
            "INSERT INTO users (user_id, name, email, password, role) VALUES (%s,%s,%s,%s,%s)",
            (user_id, name, email, hashed_password, role)
        )
        connect.commit()
        print(f"User added! ID: {user_id}")

    except mysql.connector.IntegrityError:
        print("Email already exists.")
    except mysql.connector.Error as e:
        print("Error adding user:", e)


def view_users():
    try:
        cursor.execute("SELECT user_id, name, email, role FROM users WHERE is_deleted=0")
        result = cursor.fetchall()
        if not result:
            print("No users found.")
            return
        print(f"\n{'User ID':<12} {'Name':<20} {'Email':<30} {'Role':<8}")
        print("-" * 72)
        for r in result:
            print(f"{r[0]:<12} {r[1]:<20} {r[2]:<30} {r[3]:<8}")
    except mysql.connector.Error as e:
        print("Error fetching users:", e)


def delete_user():
    try:
        user_id = input("Enter user ID to delete: ").strip()
        cursor.execute("SELECT user_id FROM users WHERE user_id=%s AND is_deleted=0", (user_id,))
        if not cursor.fetchone():
            print("User not found.")
            return
        cursor.execute("""SELECT order_id FROM orders WHERE user_id=%s
                          AND order_status NOT IN ('cancelled','delivered')""", (user_id,))
        if cursor.fetchall():
            print("Cannot delete. User has active orders. Cancel them first.")
            return
        cursor.execute("UPDATE users SET is_deleted=1 WHERE user_id=%s", (user_id,))
        connect.commit()
        print("User deleted (soft delete).")
    except mysql.connector.Error as e:
        print("Error deleting user:", e)


def update_email():
    try:
        user_id = input("Enter user ID to update email: ").strip()
        while True:
            new_email = input("Enter new email: ").strip()
            if is_valid_email(new_email):
                break
            print("Invalid email format.")
        cursor.execute("UPDATE users SET email=%s WHERE user_id=%s", (new_email, user_id))
        connect.commit()
        print("Email updated.")
    except mysql.connector.Error as e:
        print("Error updating email:", e)


def update_user_email():
    """Update own email (user action)."""
    try:
        while True:
            new_email = input("Enter new email: ").strip()
            if is_valid_email(new_email):
                break
            print("Invalid email format.")
        cursor.execute("UPDATE users SET email=%s WHERE user_id=%s", (new_email, current_user_id))
        connect.commit()
        print("Email updated.")
    except mysql.connector.Error as e:
        print("Error updating email:", e)


# ─────────────────────────────────────────────
#  CATEGORY MANAGEMENT
# ─────────────────────────────────────────────

def add_category():
    name = input("Enter category name: ").strip()
    description = input("Enter description (optional): ").strip()
    try:
        cursor.execute("INSERT INTO categories (category_name, description) VALUES (%s,%s)",
                       (name, description or None))
        connect.commit()
        print(f"Category '{name}' added. ID: {cursor.lastrowid}")
    except mysql.connector.IntegrityError:
        print("Category name already exists.")
    except mysql.connector.Error as e:
        print("Error adding category:", e)


def view_categories():
    try:
        cursor.execute("SELECT category_id, category_name, description FROM categories ORDER BY category_id")
        result = cursor.fetchall()
        if not result:
            print("No categories found.")
            return
        print(f"\n{'ID':<6} {'Name':<30} {'Description'}")
        print("-" * 60)
        for r in result:
            print(f"{r[0]:<6} {r[1]:<30} {r[2] or ''}")
    except mysql.connector.Error as e:
        print("Error fetching categories:", e)


def delete_category():
    view_categories()
    try:
        cid = int(input("Enter category ID to delete: "))
        cursor.execute("SELECT COUNT(*) FROM product WHERE category_id=%s AND is_deleted=0", (cid,))
        count = cursor.fetchone()[0]
        if count > 0:
            print(f"Cannot delete. {count} product(s) still use this category.")
            return
        cursor.execute("DELETE FROM categories WHERE category_id=%s", (cid,))
        connect.commit()
        print("Category deleted.")
    except ValueError:
        print("Invalid ID.")
    except mysql.connector.Error as e:
        print("Error deleting category:", e)


# ─────────────────────────────────────────────
#  SUPPLIER MANAGEMENT
# ─────────────────────────────────────────────

def add_supplier():
    name = input("Supplier/Company name: ").strip()
    contact = input("Contact person name: ").strip()
    phone = input("Phone: ").strip()
    email = input("Email: ").strip()
    address = input("Address: ").strip()
    try:
        cursor.execute(
            "INSERT INTO suppliers (supplier_name, contact_name, phone, email, address) VALUES (%s,%s,%s,%s,%s)",
            (name, contact or None, phone or None, email or None, address or None)
        )
        connect.commit()
        print(f"Supplier added. ID: {cursor.lastrowid}")
    except mysql.connector.Error as e:
        print("Error adding supplier:", e)


def view_suppliers():
    try:
        cursor.execute("""SELECT supplier_id, supplier_name, contact_name, phone, email
                          FROM suppliers WHERE is_deleted=0 ORDER BY supplier_id""")
        result = cursor.fetchall()
        if not result:
            print("No suppliers found.")
            return
        print(f"\n{'ID':<6} {'Company':<25} {'Contact':<20} {'Phone':<15} {'Email'}")
        print("-" * 80)
        for r in result:
            print(f"{r[0]:<6} {r[1]:<25} {r[2] or '':<20} {r[3] or '':<15} {r[4] or ''}")
    except mysql.connector.Error as e:
        print("Error fetching suppliers:", e)


def update_supplier():
    view_suppliers()
    try:
        sid = int(input("Enter supplier ID to update: "))
        cursor.execute("SELECT supplier_id FROM suppliers WHERE supplier_id=%s AND is_deleted=0", (sid,))
        if not cursor.fetchone():
            print("Supplier not found.")
            return
        print("Leave blank to keep current value.")
        name = input("New company name: ").strip()
        contact = input("New contact name: ").strip()
        phone = input("New phone: ").strip()
        email = input("New email: ").strip()
        address = input("New address: ").strip()

        updates, vals = [], []
        if name:    updates.append("supplier_name=%s");  vals.append(name)
        if contact: updates.append("contact_name=%s");   vals.append(contact)
        if phone:   updates.append("phone=%s");          vals.append(phone)
        if email:   updates.append("email=%s");          vals.append(email)
        if address: updates.append("address=%s");        vals.append(address)

        if not updates:
            print("Nothing to update.")
            return
        vals.append(sid)
        cursor.execute(f"UPDATE suppliers SET {', '.join(updates)} WHERE supplier_id=%s", vals)
        connect.commit()
        print("Supplier updated.")
    except ValueError:
        print("Invalid ID.")
    except mysql.connector.Error as e:
        print("Error updating supplier:", e)


def delete_supplier():
    view_suppliers()
    try:
        sid = int(input("Enter supplier ID to delete: "))
        cursor.execute("SELECT COUNT(*) FROM product WHERE supplier_id=%s AND is_deleted=0", (sid,))
        count = cursor.fetchone()[0]
        if count > 0:
            print(f"Cannot delete. {count} product(s) are linked to this supplier.")
            return
        cursor.execute("UPDATE suppliers SET is_deleted=1 WHERE supplier_id=%s", (sid,))
        connect.commit()
        print("Supplier deleted.")
    except ValueError:
        print("Invalid ID.")
    except mysql.connector.Error as e:
        print("Error deleting supplier:", e)


# ─────────────────────────────────────────────
#  PRODUCT MANAGEMENT
# ─────────────────────────────────────────────

def add_product():
    try:
        product_name = input("Product name: ").strip()
        if not product_name:
            print("Product name cannot be empty.")
            return

        try:
            price = float(input("Selling price: "))
            if price <= 0:
                print("Price must be > 0.")
                return
        except ValueError:
            print("Invalid price.")
            return

        try:
            cost_price = float(input("Cost price (0 if unknown): "))
        except ValueError:
            cost_price = 0

        try:
            stock = int(input("Initial stock quantity: "))
            if stock < 0:
                print("Stock cannot be negative.")
                return
        except ValueError:
            print("Invalid stock.")
            return

        try:
            reorder_level = int(input("Reorder alert level (default 5): ") or "5")
        except ValueError:
            reorder_level = 5

        # Show & pick category
        view_categories()
        try:
            category_id = input("Category ID (leave blank to skip): ").strip()
            category_id = int(category_id) if category_id else None
        except ValueError:
            category_id = None

        # Show & pick supplier
        view_suppliers()
        try:
            supplier_id = input("Supplier ID (leave blank to skip): ").strip()
            supplier_id = int(supplier_id) if supplier_id else None
        except ValueError:
            supplier_id = None

        product_id = generate_product_id(product_name)
        sku = generate_sku(product_name, category_id)

        cursor.execute(
            """INSERT INTO product
               (product_id, product_name, sku, price, cost_price, stock, reorder_level, category_id, supplier_id)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (product_id, product_name, sku, price, cost_price, stock, reorder_level, category_id, supplier_id)
        )
        connect.commit()
        print(f"Product added! ID: {product_id} | SKU: {sku}")

    except mysql.connector.IntegrityError as e:
        print("Error adding product:", e)
    except mysql.connector.Error as e:
        print("Error adding product:", e)


def update_product():
    product_id = input("Enter product ID to update: ").strip()
    cursor.execute("SELECT product_id FROM product WHERE product_id=%s AND is_deleted=0", (product_id,))
    if not cursor.fetchone():
        print("Product not found.")
        return

    print("""
    1. Update Price
    2. Update Stock
    3. Update Reorder Level
    4. Update Price & Stock
    """)
    choice = input("Choice: ").strip()

    try:
        if choice == '1':
            price = float(input("New price: "))
            cursor.execute("UPDATE product SET price=%s WHERE product_id=%s", (price, product_id))
        elif choice == '2':
            stock = int(input("New stock: "))
            cursor.execute("UPDATE product SET stock=%s WHERE product_id=%s", (stock, product_id))
        elif choice == '3':
            level = int(input("New reorder level: "))
            cursor.execute("UPDATE product SET reorder_level=%s WHERE product_id=%s", (level, product_id))
        elif choice == '4':
            price = float(input("New price: "))
            stock = int(input("New stock: "))
            cursor.execute("UPDATE product SET price=%s, stock=%s WHERE product_id=%s",
                           (price, stock, product_id))
        else:
            print("Invalid choice.")
            return
        connect.commit()
        print("Product updated.")
    except ValueError:
        print("Invalid input.")
    except mysql.connector.Error as e:
        print("Error updating product:", e)


def delete_product():
    try:
        product_id = input("Enter product ID to delete: ").strip()
        cursor.execute("SELECT product_id FROM product WHERE product_id=%s AND is_deleted=0", (product_id,))
        if not cursor.fetchone():
            print("Product not found.")
            return
        cursor.execute("""SELECT order_id FROM orders
                          WHERE product_id=%s AND order_status NOT IN ('cancelled','delivered')""",
                       (product_id,))
        if cursor.fetchall():
            print("Cannot delete. Product has active orders.")
            return
        cursor.execute("UPDATE product SET is_deleted=1 WHERE product_id=%s", (product_id,))
        connect.commit()
        print("Product deleted.")
    except mysql.connector.Error as e:
        print("Error deleting product:", e)


def view_products():
    try:
        cursor.execute("""
            SELECT p.product_id, p.product_name, p.sku, p.price, p.stock,
                   p.reorder_level, c.category_name, s.supplier_name
            FROM product p
            LEFT JOIN categories c ON p.category_id = c.category_id
            LEFT JOIN suppliers s ON p.supplier_id = s.supplier_id
            WHERE p.is_deleted = 0
            ORDER BY p.product_name
        """)
        result = cursor.fetchall()
        if not result:
            print("No products found.")
            return
        print(f"\n{'ID':<10} {'Name':<22} {'SKU':<18} {'Price':>8} {'Stock':>6} {'Reorder':>8} {'Category':<15} {'Supplier'}")
        print("-" * 100)
        for r in result:
            stock_flag = " ⚠" if r[4] <= r[5] else (" ❌" if r[4] == 0 else "")
            print(f"{r[0]:<10} {r[1]:<22} {r[2] or '':<18} {r[3]:>8.2f} {r[4]:>6}{stock_flag:<2} {r[5]:>8} {r[6] or 'N/A':<15} {r[7] or 'N/A'}")
    except mysql.connector.Error as e:
        print("Error fetching products:", e)


def search_product_by_name():
    name = input("Search product name: ").strip()
    try:
        cursor.execute("""
            SELECT p.product_id, p.product_name, p.sku, p.price, p.stock, c.category_name
            FROM product p
            LEFT JOIN categories c ON p.category_id=c.category_id
            WHERE p.product_name LIKE %s AND p.is_deleted=0
        """, (f"%{name}%",))
        result = cursor.fetchall()
        if not result:
            print("No products found.")
            return
        for r in result:
            print(f"{r[0]} | {r[1]} | SKU: {r[2]} | ₹{r[3]} | Stock: {r[4]} | {r[5] or 'No Category'}")
    except mysql.connector.Error as e:
        print("Error searching:", e)


def low_stock_products():
    try:
        cursor.execute("""
            SELECT p.product_id, p.product_name, p.sku, p.stock, p.reorder_level,
                   s.supplier_name, s.phone
            FROM product p
            LEFT JOIN suppliers s ON p.supplier_id=s.supplier_id
            WHERE p.stock <= p.reorder_level AND p.stock > 0 AND p.is_deleted=0
            ORDER BY p.stock ASC
        """)
        result = cursor.fetchall()
        if not result:
            print("No low-stock products.")
            return
        print(f"\n⚠ LOW STOCK ALERT")
        print(f"{'ID':<10} {'Name':<22} {'SKU':<18} {'Stock':>6} {'Reorder':>8} {'Supplier':<20} {'Phone'}")
        print("-" * 95)
        for r in result:
            print(f"{r[0]:<10} {r[1]:<22} {r[2] or '':<18} {r[3]:>6} {r[4]:>8} {r[5] or 'N/A':<20} {r[6] or 'N/A'}")
    except mysql.connector.Error as e:
        print("Error:", e)


def out_of_stock_products():
    try:
        cursor.execute("""
            SELECT p.product_id, p.product_name, p.sku, s.supplier_name, s.phone
            FROM product p
            LEFT JOIN suppliers s ON p.supplier_id=s.supplier_id
            WHERE p.stock=0 AND p.is_deleted=0
        """)
        result = cursor.fetchall()
        if not result:
            print("No out-of-stock products.")
            return
        print(f"\n❌ OUT OF STOCK")
        print(f"{'ID':<10} {'Name':<22} {'SKU':<18} {'Supplier':<20} {'Phone'}")
        print("-" * 80)
        for r in result:
            print(f"{r[0]:<10} {r[1]:<22} {r[2] or '':<18} {r[3] or 'N/A':<20} {r[4] or 'N/A'}")
    except mysql.connector.Error as e:
        print("Error:", e)


# ─────────────────────────────────────────────
#  REPORTS & ANALYTICS
# ─────────────────────────────────────────────

def view_revenue():
    try:
        cursor.execute("SELECT COALESCE(SUM(amount),0) FROM payment WHERE payment_status='completed'")
        revenue = cursor.fetchone()[0]
        cursor.execute("SELECT COALESCE(SUM(amount),0) FROM payment WHERE payment_status='pending'")
        pending = cursor.fetchone()[0]
        cursor.execute("SELECT COALESCE(SUM(amount),0) FROM payment WHERE payment_status='refunded'")
        refunded = cursor.fetchone()[0]
        print(f"\n📈 REVENUE SUMMARY")
        print(f"  Total Revenue  : ₹{revenue:.2f}")
        print(f"  Pending        : ₹{pending:.2f}")
        print(f"  Refunded       : ₹{refunded:.2f}")
    except mysql.connector.Error as e:
        print("Error fetching revenue:", e)


def sales_report_by_product():
    """Show total quantity sold and revenue per product."""
    try:
        cursor.execute("""
            SELECT p.product_id, p.product_name,
                   COALESCE(SUM(o.quantity), 0) AS total_sold,
                   COALESCE(SUM(o.quantity * p.price), 0) AS total_revenue
            FROM product p
            LEFT JOIN orders o ON p.product_id=o.product_id
                              AND o.order_status NOT IN ('cancelled','refunded')
            WHERE p.is_deleted=0
            GROUP BY p.product_id, p.product_name
            ORDER BY total_revenue DESC
        """)
        result = cursor.fetchall()
        if not result:
            print("No data.")
            return
        print(f"\n📊 SALES REPORT BY PRODUCT")
        print(f"{'ID':<10} {'Name':<25} {'Qty Sold':>10} {'Revenue':>12}")
        print("-" * 60)
        for r in result:
            print(f"{r[0]:<10} {r[1]:<25} {r[2]:>10} {'₹'+str(round(r[3],2)):>12}")
    except mysql.connector.Error as e:
        print("Error:", e)


def sales_report_by_category():
    """Show total revenue per category."""
    try:
        cursor.execute("""
            SELECT c.category_name,
                   COUNT(DISTINCT p.product_id) AS products,
                   COALESCE(SUM(o.quantity), 0) AS total_sold,
                   COALESCE(SUM(o.quantity * p.price), 0) AS total_revenue
            FROM categories c
            LEFT JOIN product p ON c.category_id=p.category_id AND p.is_deleted=0
            LEFT JOIN orders o ON p.product_id=o.product_id
                              AND o.order_status NOT IN ('cancelled','refunded')
            GROUP BY c.category_id, c.category_name
            ORDER BY total_revenue DESC
        """)
        result = cursor.fetchall()
        if not result:
            print("No data.")
            return
        print(f"\n📊 SALES REPORT BY CATEGORY")
        print(f"{'Category':<25} {'Products':>10} {'Qty Sold':>10} {'Revenue':>12}")
        print("-" * 60)
        for r in result:
            print(f"{r[0]:<25} {r[1]:>10} {r[2]:>10} {'₹'+str(round(r[3],2)):>12}")
    except mysql.connector.Error as e:
        print("Error:", e)


def profit_report():
    """Show profit margin per product (price - cost_price)."""
    try:
        cursor.execute("""
            SELECT p.product_id, p.product_name, p.price, p.cost_price,
                   (p.price - p.cost_price) AS margin,
                   COALESCE(SUM(o.quantity),0) AS qty_sold,
                   COALESCE(SUM(o.quantity * (p.price - p.cost_price)),0) AS total_profit
            FROM product p
            LEFT JOIN orders o ON p.product_id=o.product_id
                              AND o.order_status NOT IN ('cancelled','refunded')
            WHERE p.is_deleted=0
            GROUP BY p.product_id, p.product_name, p.price, p.cost_price
            ORDER BY total_profit DESC
        """)
        result = cursor.fetchall()
        if not result:
            print("No data.")
            return
        print(f"\n💰 PROFIT REPORT")
        print(f"{'ID':<10} {'Name':<22} {'Price':>8} {'Cost':>8} {'Margin':>8} {'Sold':>6} {'Total Profit':>14}")
        print("-" * 85)
        for r in result:
            print(f"{r[0]:<10} {r[1]:<22} {r[2]:>8.2f} {r[3]:>8.2f} {r[4]:>8.2f} {r[5]:>6} {'₹'+str(round(r[6],2)):>14}")
    except mysql.connector.Error as e:
        print("Error:", e)


# ─────────────────────────────────────────────
#  ORDER MANAGEMENT
# ─────────────────────────────────────────────

def place_order():
    try:
        user_id = current_user_id
        product_id = input("Enter product ID to order: ").strip()

        try:
            quantity = int(input("Quantity: "))
            if quantity <= 0:
                print("Quantity must be > 0.")
                return
        except ValueError:
            print("Invalid quantity.")
            return

        cursor.execute("SELECT stock, price FROM product WHERE product_id=%s AND is_deleted=0", (product_id,))
        result = cursor.fetchone()
        if not result:
            print("Product not found.")
            return

        stock, price = result
        if stock < quantity:
            print(f"Insufficient stock. Only {stock} available.")
            return

        cursor.execute("INSERT INTO orders (user_id, product_id, quantity) VALUES (%s,%s,%s)",
                       (user_id, product_id, quantity))
        cursor.execute("UPDATE product SET stock=stock-%s WHERE product_id=%s", (quantity, product_id))
        connect.commit()
        order_id = cursor.lastrowid
        print(f"Order placed! ID: {order_id} | Total: ₹{quantity * float(price):.2f}")
        make_payment(order_id)

    except mysql.connector.Error as e:
        connect.rollback()
        print("Error placing order:", e)


def make_payment(order_id):
    try:
        user_id = current_user_id
        cursor.execute("SELECT payment_status FROM payment WHERE order_id=%s", (order_id,))
        existing = cursor.fetchone()
        if existing:
            print("Payment already exists.")
            return

        cursor.execute("""
            SELECT o.quantity, p.price FROM orders o
            JOIN product p ON o.product_id=p.product_id
            WHERE o.order_id=%s AND o.user_id=%s
        """, (order_id, user_id))
        result = cursor.fetchone()
        if not result:
            print("Invalid order.")
            return

        quantity, price = result
        total = quantity * float(price)
        print(f"Total: ₹{total:.2f}")

        try:
            amount = float(input("Enter payment amount: "))
            if amount <= 0:
                print("Amount must be > 0.")
                return
        except ValueError:
            print("Invalid amount.")
            return

        status = "completed" if amount >= total else "pending"
        cursor.execute("INSERT INTO payment (order_id, amount, payment_status) VALUES (%s,%s,%s)",
                       (order_id, amount, status))
        if status == "completed":
            cursor.execute("UPDATE orders SET order_status='shipped' WHERE order_id=%s", (order_id,))
        connect.commit()
        print(f"Payment {'completed' if status=='completed' else 'saved as pending (₹'+str(round(total-amount,2))+' remaining)'}.")

    except mysql.connector.Error as e:
        connect.rollback()
        print("Error processing payment:", e)


def view_my_orders():
    try:
        cursor.execute("""
            SELECT o.order_id, p.product_name, o.quantity, o.order_status, o.created_at
            FROM orders o JOIN product p ON o.product_id=p.product_id
            WHERE o.user_id=%s ORDER BY o.order_id DESC
        """, (current_user_id,))
        result = cursor.fetchall()
        if not result:
            print("No orders found.")
            return
        print(f"\n{'Order ID':>10} {'Product':<22} {'Qty':>5} {'Status':<12} {'Date'}")
        print("-" * 65)
        for r in result:
            print(f"{r[0]:>10} {r[1]:<22} {r[2]:>5} {r[3]:<12} {str(r[4])[:16]}")
    except mysql.connector.Error as e:
        print("Error fetching orders:", e)


def cancel_order():
    try:
        user_id = current_user_id
        cursor.execute("""SELECT order_id, product_id, quantity, order_status
                          FROM orders WHERE user_id=%s""", (user_id,))
        orders = cursor.fetchall()
        if not orders:
            print("No orders found.")
            return

        try:
            order_id = int(input("Enter order ID to cancel: "))
        except ValueError:
            print("Invalid order ID.")
            return

        for order in orders:
            if order[0] == order_id:
                product_id, quantity, status = order[1], order[2], order[3]
                if status != "placed":
                    print("Only 'placed' orders can be cancelled.")
                    return

                cursor.execute("SELECT payment_status FROM payment WHERE order_id=%s", (order_id,))
                payment = cursor.fetchone()

                if payment and payment[0] == "completed":
                    confirm = input("This order was paid. Cancel and refund? (yes/no): ")
                    if confirm.lower() != "yes":
                        print("Cancellation aborted.")
                        return
                    cursor.execute("UPDATE payment SET payment_status='refunded' WHERE order_id=%s", (order_id,))
                elif payment and payment[0] == "pending":
                    cursor.execute("UPDATE payment SET payment_status='failed' WHERE order_id=%s", (order_id,))

                cursor.execute("UPDATE orders SET order_status='cancelled' WHERE order_id=%s", (order_id,))
                cursor.execute("UPDATE product SET stock=stock+%s WHERE product_id=%s", (quantity, product_id))
                connect.commit()
                print("Order cancelled. Stock restored.")
                return

        print("Order ID not found.")
    except mysql.connector.Error as e:
        connect.rollback()
        print("Error cancelling order:", e)


def change_order_status():
    try:
        try:
            order_id = int(input("Order ID: "))
        except ValueError:
            print("Invalid order ID.")
            return

        cursor.execute("SELECT order_id FROM orders WHERE order_id=%s", (order_id,))
        if not cursor.fetchone():
            print("Order not found.")
            return

        new_status = input("New status (placed/shipped/delivered/cancelled): ").strip()
        if new_status not in ['placed', 'shipped', 'delivered', 'cancelled']:
            print("Invalid status.")
            return

        cursor.execute("UPDATE orders SET order_status=%s WHERE order_id=%s", (new_status, order_id))
        connect.commit()
        print("Order status updated.")
    except mysql.connector.Error as e:
        print("Error:", e)


def view_payments():
    try:
        if current_user_id:
            cursor.execute("""SELECT p.payment_id, p.order_id, p.amount, p.payment_status, p.paid_at
                              FROM payment p JOIN orders o ON p.order_id=o.order_id
                              WHERE o.user_id=%s ORDER BY p.payment_id DESC""", (current_user_id,))
        else:
            cursor.execute("SELECT payment_id, order_id, amount, payment_status, paid_at FROM payment ORDER BY payment_id DESC")
        result = cursor.fetchall()
        if not result:
            print("No payments found.")
            return
        print(f"\n{'Pay ID':>8} {'Order ID':>9} {'Amount':>10} {'Status':<12} {'Date'}")
        print("-" * 55)
        for r in result:
            print(f"{r[0]:>8} {r[1]:>9} {'₹'+str(round(r[2],2)):>10} {r[3]:<12} {str(r[4])[:16]}")
    except mysql.connector.Error as e:
        print("Error:", e)


# ─────────────────────────────────────────────
#  MENUS
# ─────────────────────────────────────────────

def admin_menu():
    while True:
        print("""
╔══════════════════════════════╗
║      InvenTrack — Admin      ║
╠══════════════════════════════╣
║  PRODUCTS                    ║
║  1.  Add Product             ║
║  2.  Update Product          ║
║  3.  Delete Product          ║
║  4.  View All Products       ║
║  5.  Search Product          ║
║  6.  Low Stock Alerts        ║
║  7.  Out of Stock            ║
║                              ║
║  CATEGORIES                  ║
║  8.  Add Category            ║
║  9.  View Categories         ║
║  10. Delete Category         ║
║                              ║
║  SUPPLIERS                   ║
║  11. Add Supplier            ║
║  12. View Suppliers          ║
║  13. Update Supplier         ║
║  14. Delete Supplier         ║
║                              ║
║  USERS                       ║
║  15. View Users              ║
║  16. Add User                ║
║  17. Delete User             ║
║  18. Update User Email       ║
║                              ║
║  ORDERS & PAYMENTS           ║
║  19. Change Order Status     ║
║  20. View All Payments       ║
║                              ║
║  REPORTS                     ║
║  21. Revenue Summary         ║
║  22. Sales by Product        ║
║  23. Sales by Category       ║
║  24. Profit Report           ║
║                              ║
║  0.  Exit                    ║
╚══════════════════════════════╝
        """)
        choice = input("Enter choice: ").strip()
        actions = {
            '1': add_product, '2': update_product, '3': delete_product,
            '4': view_products, '5': search_product_by_name,
            '6': low_stock_products, '7': out_of_stock_products,
            '8': add_category, '9': view_categories, '10': delete_category,
            '11': add_supplier, '12': view_suppliers, '13': update_supplier, '14': delete_supplier,
            '15': view_users, '16': add_user, '17': delete_user, '18': update_email,
            '19': change_order_status, '20': view_payments,
            '21': view_revenue, '22': sales_report_by_product,
            '23': sales_report_by_category, '24': profit_report,
        }
        if choice == '0':
            print("Goodbye!")
            break
        elif choice in actions:
            actions[choice]()
        else:
            print("Invalid choice.")


def user_menu():
    while True:
        print("""
╔══════════════════════════════╗
║    InvenTrack — My Account   ║
╠══════════════════════════════╣
║  1. Browse Products          ║
║  2. Search Product           ║
║  3. Place Order              ║
║  4. View My Orders           ║
║  5. Cancel Order             ║
║  6. View My Payments         ║
║  7. Update My Email          ║
║  0. Exit                     ║
╚══════════════════════════════╝
        """)
        choice = input("Enter choice: ").strip()
        actions = {
            '1': view_products, '2': search_product_by_name,
            '3': place_order, '4': view_my_orders,
            '5': cancel_order, '6': view_payments,
            '7': update_user_email,
        }
        if choice == '0':
            print("Goodbye!")
            break
        elif choice in actions:
            actions[choice]()
        else:
            print("Invalid choice.")


# ─────────────────────────────────────────────
#  LOGIN
# ─────────────────────────────────────────────

def login():
    global current_user_id
    print("\n========== InvenTrack ==========")
    print("  Small Business Inventory System")
    print("=================================\n")

    for attempt in range(3):
        email = input("Email: ").strip()
        password = input("Password: ")

        try:
            cursor.execute("SELECT user_id, role, password FROM users WHERE email=%s AND is_deleted=0", (email,))
            result = cursor.fetchone()
            if result:
                uid, role, hashed = result
                if bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8')):
                    current_user_id = uid
                    print(f"\nWelcome, {uid}! Role: {role.upper()}")
                    if role == "admin":
                        admin_menu()
                    else:
                        user_menu()
                    return

            remaining = 2 - attempt
            if remaining > 0:
                print(f"Invalid credentials. {remaining} attempt(s) remaining.")
            else:
                print("Too many failed attempts. Access blocked.")
                exit()
        except mysql.connector.Error as e:
            print("Login error:", e)
            return


login()

try:
    connect.close()
    print("Database connection closed.")
except mysql.connector.Error as e:
    print("Error closing connection:", e)
