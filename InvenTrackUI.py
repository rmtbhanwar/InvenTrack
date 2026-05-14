import sys
sys.dont_write_bytecode = True

import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector
from dotenv import load_dotenv
import os
import bcrypt
import random
import time
import re


load_dotenv()

# ─────────────────────────────────────────────
#  THEME COLORS
# ─────────────────────────────────────────────
THEMES = {
    "light": {
        "bg":           "#F8F5FF",
        "sidebar_bg":   "#1E3A5F",
        "sidebar_fg":   "#FFFFFF",
        "sidebar_hover":"#2E5F9E",
        "card_bg":      "#FFFFFF",
        "fg":           "#1A1A2E",
        "fg_sub":       "#6B7280",
        "accent":       "#1E3A5F",
        "accent_hover": "#2E5F9E",
        "entry_bg":     "#FFFFFF",
        "entry_border": "#CBD5E1",
        "tree_bg":      "#FFFFFF",
        "tree_fg":      "#1A1A2E",
        "tree_select":  "#DBEAFE",
        "tree_head":    "#F1F5F9",
        "btn_fg":       "#FFFFFF",
        "danger":       "#EF4444",
        "success":      "#10B981",
        "warning":      "#F59E0B",
        "border":       "#E2E8F0",
        "shadow":       "#E2E8F0",
        "topbar_bg":    "#FFFFFF",
        "input_fg":     "#1A1A2E",
        "low_stock":    "#F59E0B",
        "out_stock":    "#EF4444",
    },
    "dark": {
        "bg":           "#0D1117",
        "sidebar_bg":   "#161B22",
        "sidebar_fg":   "#C9D1D9",
        "sidebar_hover":"#1F6FEB",
        "card_bg":      "#1C2128",
        "fg":           "#E6EDF3",
        "fg_sub":       "#8B949E",
        "accent":       "#1F6FEB",
        "accent_hover": "#388BFD",
        "entry_bg":     "#21262D",
        "entry_border": "#30363D",
        "tree_bg":      "#1C2128",
        "tree_fg":      "#E6EDF3",
        "tree_select":  "#1F3251",
        "tree_head":    "#21262D",
        "btn_fg":       "#FFFFFF",
        "danger":       "#F85149",
        "success":      "#3FB950",
        "warning":      "#D29922",
        "border":       "#30363D",
        "shadow":       "#161B22",
        "topbar_bg":    "#161B22",
        "input_fg":     "#E6EDF3",
        "low_stock":    "#D29922",
        "out_stock":    "#F85149",
    }
}

current_theme = "light"
def T(): return THEMES[current_theme]

# ─────────────────────────────────────────────
#  DATABASE
# ─────────────────────────────────────────────
try:
    connect = mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        username=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )
    cursor = connect.cursor()
except mysql.connector.Error as e:
    print("DB Error:", e)
    exit()

current_user_id = None
current_user_role = None

#!  HELPER FUNCTIONS

def is_valid_email(email):
    return re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,}$', email)

def generate_user_id(name):
    prefix = name[0:3].upper()
    for _ in range(10):
        uid = f"{prefix}{random.randint(1000,9999)}"
        cursor.execute("SELECT user_id FROM users WHERE user_id=%s", (uid,))
        if not cursor.fetchone():
            return uid
    return f"{prefix}{str(int(time.time()))[-4:]}"

def generate_product_id(name):
    prefix = name[0:2].upper()
    for _ in range(10):
        pid = f"{prefix}{random.randint(1000,9999)}"
        cursor.execute("SELECT product_id FROM product WHERE product_id=%s", (pid,))
        if not cursor.fetchone():
            return pid
    return f"{prefix}{str(int(time.time()))[-4:]}"

def generate_sku(product_name, category_id=None):
    prefix = product_name[0:3].upper()
    cat_prefix = "GEN"
    if category_id:
        cursor.execute("SELECT category_name FROM categories WHERE category_id=%s", (category_id,))
        cat = cursor.fetchone()
        if cat:
            cat_prefix = cat[0][0:3].upper()
    return f"{cat_prefix}-{prefix}-{random.randint(1000,9999)}"

def styled_table(parent, columns, height=13):
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Custom.Treeview",
                    background=T()["tree_bg"], foreground=T()["tree_fg"],
                    fieldbackground=T()["tree_bg"], rowheight=30,
                    font=("Helvetica", 10))
    style.configure("Custom.Treeview.Heading",
                    background=T()["tree_head"], foreground=T()["accent"],
                    font=("Helvetica", 10, "bold"), relief="flat")
    style.map("Custom.Treeview",
              background=[("selected", T()["tree_select"])],
              foreground=[("selected", T()["accent"])])
    frame = tk.Frame(parent, bg=T()["border"], bd=1)
    frame.pack(fill="both", expand=True, padx=2, pady=2)
    tree = ttk.Treeview(frame, columns=columns, show="headings",
                        height=height, style="Custom.Treeview")
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, anchor="center", width=110)
    vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    vsb.pack(side="right", fill="y")
    tree.pack(fill="both", expand=True)
    return tree

def page_header(parent, title, subtitle=""):
    tk.Label(parent, text=title, font=("Georgia", 22, "bold"),
             bg=T()["bg"], fg=T()["fg"]).pack(anchor="w", pady=(0, 2))
    if subtitle:
        tk.Label(parent, text=subtitle, font=("Helvetica", 11),
                 bg=T()["bg"], fg=T()["fg_sub"]).pack(anchor="w", pady=(0, 14))

def action_btn(parent, text, command, color=None, width=16):
    c = color or T()["accent"]
    return tk.Button(parent, text=text, font=("Helvetica", 10, "bold"),
                     bg=c, fg="#FFFFFF", relief="flat", bd=0,
                     padx=12, pady=8, cursor="hand2", width=width,
                     activebackground=T()["accent_hover"], command=command)

def form_entry(parent, label, var, show=None):
    tk.Label(parent, text=label, font=("Helvetica", 10, "bold"),
             bg=T()["card_bg"], fg=T()["fg"]).pack(anchor="w", pady=(8, 2))
    f = tk.Frame(parent, bg=T()["entry_border"], bd=1)
    f.pack(fill="x", pady=(0, 4))
    e = tk.Entry(f, textvariable=var, font=("Helvetica", 11),
                 bg=T()["entry_bg"], fg=T()["input_fg"], relief="flat",
                 bd=6, insertbackground=T()["accent"], show=show or "")
    e.pack(fill="x")
    return e

def form_dropdown(parent, label, var, values):
    tk.Label(parent, text=label, font=("Helvetica", 10, "bold"),
             bg=T()["card_bg"], fg=T()["fg"]).pack(anchor="w", pady=(8, 2))
    cb = ttk.Combobox(parent, textvariable=var, values=values,
                      state="readonly", font=("Helvetica", 11))
    cb.pack(fill="x", pady=(0, 4))
    return cb

def stat_card(parent, title, value, color, col):
    card = tk.Frame(parent, bg=color, padx=20, pady=16)
    card.grid(row=0, column=col, padx=6, pady=4, sticky="ew")
    tk.Label(card, text=value, font=("Georgia", 24, "bold"),
             bg=color, fg="#FFFFFF").pack(anchor="w")
    tk.Label(card, text=title, font=("Helvetica", 10),
             bg=color, fg="#FFFFFF").pack(anchor="w")

#!  MAIN APP

class InvenTrackApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("InvenTrack — Inventory Management")
        self.geometry("1200x720")
        self.minsize(960, 620)
        self.configure(bg=T()["bg"])
        self.resizable(True, True)
        self._show_login()

    def _clear(self):
        for w in self.winfo_children():
            w.destroy()

    def _show_login(self):
        self._clear()
        self.configure(bg=T()["bg"])
        LoginPage(self)

    def _show_main(self, role):
        self._clear()
        self.configure(bg=T()["bg"])
        MainApp(self, role)

#!  LOGIN PAGE

class LoginPage(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg=T()["bg"])
        self.pack(fill="both", expand=True)
        self.attempts = 0
        self._build()

    def _build(self):
        left = tk.Frame(self, bg=T()["sidebar_bg"], width=420)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        canvas = tk.Canvas(left, bg=T()["sidebar_bg"], highlightthickness=0, width=420, height=720)
        canvas.place(x=0, y=0)
        canvas.create_oval(-60, 520, 180, 760, outline="#2E5F9E", width=2)
        canvas.create_oval(260, -60, 500, 180, outline="#2E5F9E", width=2)
        canvas.create_text(210, 190, text="📦 InvenTrack",
                           font=("Georgia", 36, "bold"), fill="#FFFFFF")
        canvas.create_text(210, 245, text="Small Business Inventory System",
                           font=("Georgia", 13, "italic"), fill="#90AAC8")
        canvas.create_text(210, 420, text="✓  Product & SKU Management",
                           font=("Helvetica", 11), fill="#90AAC8")
        canvas.create_text(210, 455, text="✓  Supplier Tracking",
                           font=("Helvetica", 11), fill="#90AAC8")
        canvas.create_text(210, 490, text="✓  Stock Alerts & Reorder Levels",
                           font=("Helvetica", 11), fill="#90AAC8")
        canvas.create_text(210, 525, text="✓  Sales & Profit Reports",
                           font=("Helvetica", 11), fill="#90AAC8")

        right = tk.Frame(self, bg=T()["bg"])
        right.pack(side="right", fill="both", expand=True)
        form = tk.Frame(right, bg=T()["bg"])
        form.place(relx=0.5, rely=0.5, anchor="center")

        self.theme_btn = tk.Button(right, text="🌙 Dark" if current_theme=="light" else "☀️ Light",
                                   font=("Helvetica", 10), bg=T()["card_bg"],
                                   fg=T()["accent"], relief="flat", bd=0,
                                   cursor="hand2", command=self._toggle_theme)
        self.theme_btn.place(relx=0.95, rely=0.05, anchor="ne")

        tk.Label(form, text="Welcome Back", font=("Georgia", 28, "bold"),
                 bg=T()["bg"], fg=T()["fg"]).pack(anchor="w", pady=(0, 4))
        tk.Label(form, text="Sign in to your inventory account",
                 font=("Helvetica", 12), bg=T()["bg"], fg=T()["fg_sub"]).pack(anchor="w", pady=(0, 28))

        tk.Label(form, text="Email Address", font=("Helvetica", 11, "bold"),
                 bg=T()["bg"], fg=T()["fg"]).pack(anchor="w")
        self.email_var = tk.StringVar()
        ef = tk.Frame(form, bg=T()["entry_border"], bd=1)
        ef.pack(fill="x", pady=(4, 16), ipady=1)
        self.email_entry = tk.Entry(ef, textvariable=self.email_var,
                                    font=("Helvetica", 12), bg=T()["entry_bg"],
                                    fg=T()["input_fg"], relief="flat", bd=8,
                                    insertbackground=T()["accent"], width=32)
        self.email_entry.pack(fill="x")

        tk.Label(form, text="Password", font=("Helvetica", 11, "bold"),
                 bg=T()["bg"], fg=T()["fg"]).pack(anchor="w")
        self.pass_var = tk.StringVar()
        pf = tk.Frame(form, bg=T()["entry_border"], bd=1)
        pf.pack(fill="x", pady=(4, 8), ipady=1)
        self.pass_entry = tk.Entry(pf, textvariable=self.pass_var,
                                   font=("Helvetica", 12), bg=T()["entry_bg"],
                                   fg=T()["input_fg"], relief="flat", bd=8,
                                   show="●", insertbackground=T()["accent"], width=32)
        self.pass_entry.pack(fill="x")

        self.msg_label = tk.Label(form, text="", font=("Helvetica", 10),
                                  bg=T()["bg"], fg=T()["danger"])
        self.msg_label.pack(pady=(0, 14))

        tk.Button(form, text="Sign In →", font=("Helvetica", 13, "bold"),
                  bg=T()["accent"], fg="#FFFFFF", relief="flat",
                  bd=0, padx=20, pady=12, cursor="hand2",
                  activebackground=T()["accent_hover"],
                  command=self._login).pack(fill="x")

        self.bind_all("<Return>", lambda e: self._login())
        self.email_entry.focus()

    def _toggle_theme(self):
        global current_theme
        current_theme = "dark" if current_theme == "light" else "light"
        self.master._show_login()

    def _login(self):
        email = self.email_var.get().strip()
        password = self.pass_var.get().strip()
        if not email or not password:
            self.msg_label.config(text="Please enter email and password.")
            return
        try:
            cursor.execute("SELECT user_id, role, password FROM users WHERE email=%s AND is_deleted=0", (email,))
            result = cursor.fetchone()
            if result:
                uid, role, hashed = result
                if bcrypt.checkpw(password.encode(), hashed.encode()):
                    global current_user_id, current_user_role
                    current_user_id = uid
                    current_user_role = role
                    self.master._show_main(role)
                    return
            self.attempts += 1
            remaining = 3 - self.attempts
            if remaining <= 0:
                messagebox.showerror("Blocked", "Too many failed attempts.")
                self.master.destroy()
            else:
                self.msg_label.config(text=f"Invalid credentials. {remaining} attempt(s) left.")
        except mysql.connector.Error as e:
            self.msg_label.config(text=f"DB Error: {e}")


#!  MAIN APP SHELL

class MainApp(tk.Frame):
    def __init__(self, master, role):
        super().__init__(master, bg=T()["bg"])
        self.pack(fill="both", expand=True)
        self.role = role
        self._build()

    def _build(self):
        topbar = tk.Frame(self, bg=T()["topbar_bg"], height=54)
        topbar.pack(fill="x", side="top")
        topbar.pack_propagate(False)
        tk.Label(topbar, text="📦 InvenTrack", font=("Georgia", 18, "bold"),
                 bg=T()["topbar_bg"], fg=T()["accent"]).pack(side="left", padx=20)
        tk.Button(topbar, text="🌙" if current_theme=="light" else "☀️",
                  font=("Helvetica", 14), bg=T()["topbar_bg"], fg=T()["accent"],
                  relief="flat", bd=0, cursor="hand2",
                  command=self._toggle_theme).pack(side="right", padx=10)
        tk.Label(topbar, text=f"👤 {current_user_id}  |  {self.role.upper()}",
                 font=("Helvetica", 10), bg=T()["topbar_bg"],
                 fg=T()["fg_sub"]).pack(side="right", padx=10)

        body = tk.Frame(self, bg=T()["bg"])
        body.pack(fill="both", expand=True)

        self.sidebar = tk.Frame(body, bg=T()["sidebar_bg"], width=220)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self.content = tk.Frame(body, bg=T()["bg"])
        self.content.pack(side="right", fill="both", expand=True)

        self._build_sidebar()
        self._load_page("Dashboard")

    def _toggle_theme(self):
        global current_theme
        current_theme = "dark" if current_theme == "light" else "light"
        self.master._show_main(self.role)

    def _build_sidebar(self):
        tk.Label(self.sidebar, text="MENU", font=("Helvetica", 9, "bold"),
                 bg=T()["sidebar_bg"], fg="#5A7FA8").pack(anchor="w", padx=20, pady=(20, 6))

        admin_sections = [
            ("OVERVIEW",    [("📊", "Dashboard")]),
            ("INVENTORY",   [("📦", "Products"), ("🏷", "Categories"), ("🚚", "Suppliers")]),
            ("PEOPLE",      [("👥", "Users")]),
            ("TRANSACTIONS",[("🛒", "Orders"), ("💳", "Payments")]),
            ("ANALYTICS",   [("📈", "Revenue"), ("📊", "Reports")]),
        ]
        user_sections = [
            ("OVERVIEW",    [("📊", "Dashboard")]),
            ("SHOP",        [("📦", "Products"), ("🛒", "My Orders"), ("💳", "My Payments")]),
        ]

        sections = admin_sections if self.role == "admin" else user_sections
        self.nav_buttons = {}

        for section_label, pages in sections:
            tk.Label(self.sidebar, text=section_label, font=("Helvetica", 8, "bold"),
                     bg=T()["sidebar_bg"], fg="#5A7FA8").pack(anchor="w", padx=20, pady=(12, 2))
            for icon, name in pages:
                btn = tk.Button(self.sidebar, text=f"  {icon}  {name}",
                                font=("Helvetica", 11), bg=T()["sidebar_bg"],
                                fg=T()["sidebar_fg"], relief="flat", bd=0,
                                anchor="w", padx=10, pady=9, cursor="hand2",
                                activebackground=T()["sidebar_hover"],
                                command=lambda n=name: self._load_page(n))
                btn.pack(fill="x", padx=8, pady=1)
                self.nav_buttons[name] = btn

        tk.Frame(self.sidebar, bg="#2E5F9E", height=1).pack(fill="x", padx=16, pady=14)
        tk.Button(self.sidebar, text="  🚪  Logout", font=("Helvetica", 11),
                  bg=T()["sidebar_bg"], fg=T()["danger"], relief="flat", bd=0,
                  anchor="w", padx=10, pady=9, cursor="hand2",
                  command=self._logout).pack(fill="x", padx=8)

    def _load_page(self, name):
        for w in self.content.winfo_children():
            w.destroy()
        for n, b in self.nav_buttons.items():
            b.config(bg=T()["sidebar_hover"] if n == name else T()["sidebar_bg"])
        pages = {
            "Dashboard":   DashboardPage,
            "Products":    ProductsPage,
            "Categories":  CategoriesPage,
            "Suppliers":   SuppliersPage,
            "Users":       UsersPage,
            "Orders":      OrdersPage,
            "My Orders":   MyOrdersPage,
            "Payments":    PaymentsPage,
            "My Payments": MyPaymentsPage,
            "Revenue":     RevenuePage,
            "Reports":     ReportsPage,
        }
        if name in pages:
            pages[name](self.content)

    def _logout(self):
        global current_user_id, current_user_role
        current_user_id = None
        current_user_role = None
        self.master._show_login()


#!  DASHBOARD

class DashboardPage(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg=T()["bg"], padx=28, pady=20)
        self.pack(fill="both", expand=True)
        if current_user_role == "admin":
            self._build_admin()
        else:
            self._build_user()

    def _build_admin(self):
        page_header(self, "Dashboard", f"Welcome back, {current_user_id} 👋")
        sf = tk.Frame(self, bg=T()["bg"])
        sf.pack(fill="x", pady=(0, 16))
        sf.columnconfigure((0,1,2,3,4), weight=1)

        try:
            cursor.execute("SELECT COUNT(*) FROM product WHERE is_deleted=0"); products = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM users WHERE is_deleted=0"); users = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM orders"); orders = cursor.fetchone()[0]
            cursor.execute("SELECT COALESCE(SUM(amount),0) FROM payment WHERE payment_status='completed'"); revenue = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM product WHERE stock <= reorder_level AND stock > 0 AND is_deleted=0"); low_stock = cursor.fetchone()[0]
        except:
            products = users = orders = revenue = low_stock = 0

        stat_card(sf, "Products", str(products), "#1E3A5F", 0)
        stat_card(sf, "Users", str(users), "#2E5F9E", 1)
        stat_card(sf, "Orders", str(orders), "#3A7CA5", 2)
        stat_card(sf, "Revenue (₹)", f"{revenue:.0f}", "#10B981", 3)
        stat_card(sf, "⚠ Low Stock", str(low_stock), T()["warning"], 4)

        # Low stock alert strip
        if low_stock > 0:
            alert = tk.Frame(self, bg="#FEF3C7", padx=14, pady=10)
            alert.pack(fill="x", pady=(0, 10))
            tk.Label(alert, text=f"⚠  {low_stock} product(s) are at or below reorder level — visit Products page to review.",
                     font=("Helvetica", 10), bg="#FEF3C7", fg="#92400E").pack(anchor="w")

        tk.Label(self, text="Recent Orders", font=("Georgia", 14, "bold"),
                 bg=T()["bg"], fg=T()["fg"]).pack(anchor="w", pady=(4, 6))
        try:
            cursor.execute("""SELECT o.order_id, o.user_id, p.product_name, o.quantity, o.order_status
                              FROM orders o JOIN product p ON o.product_id=p.product_id
                              ORDER BY o.order_id DESC LIMIT 8""")
            rows = cursor.fetchall()
        except:
            rows = []
        tree = styled_table(self, ["Order ID","User","Product","Qty","Status"], height=8)
        for r in rows:
            tree.insert("", "end", values=r)

    def _build_user(self):
        page_header(self, "My Dashboard", f"Welcome back, {current_user_id} 👋")
        sf = tk.Frame(self, bg=T()["bg"])
        sf.pack(fill="x", pady=(0, 16))
        sf.columnconfigure((0,1,2,3), weight=1)
        try:
            cursor.execute("SELECT COUNT(*) FROM orders WHERE user_id=%s", (current_user_id,)); my_orders = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM orders WHERE user_id=%s AND order_status IN ('placed','shipped')", (current_user_id,)); active = cursor.fetchone()[0]
            cursor.execute("""SELECT COUNT(*) FROM payment p JOIN orders o ON p.order_id=o.order_id
                              WHERE o.user_id=%s AND p.payment_status='pending'""", (current_user_id,)); pending = cursor.fetchone()[0]
            cursor.execute("""SELECT COALESCE(SUM(p.amount),0) FROM payment p JOIN orders o ON p.order_id=o.order_id
                              WHERE o.user_id=%s AND p.payment_status='completed'""", (current_user_id,)); spent = cursor.fetchone()[0]
        except:
            my_orders = active = pending = spent = 0
        stat_card(sf, "My Orders", str(my_orders), "#1E3A5F", 0)
        stat_card(sf, "Active Orders", str(active), "#2E5F9E", 1)
        stat_card(sf, "Pending Payments", str(pending), T()["warning"], 2)
        stat_card(sf, "Total Spent (₹)", f"{spent:.0f}", "#10B981", 3)

        tk.Label(self, text="My Recent Orders", font=("Georgia", 14, "bold"),
                 bg=T()["bg"], fg=T()["fg"]).pack(anchor="w", pady=(6, 6))
        try:
            cursor.execute("""SELECT o.order_id, p.product_name, o.quantity, o.order_status
                              FROM orders o JOIN product p ON o.product_id=p.product_id
                              WHERE o.user_id=%s ORDER BY o.order_id DESC LIMIT 8""", (current_user_id,))
            rows = cursor.fetchall()
        except:
            rows = []
        tree = styled_table(self, ["Order ID","Product","Qty","Status"], height=8)
        for r in rows:
            tree.insert("", "end", values=r)


#!  PRODUCTS PAGE

class ProductsPage(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg=T()["bg"], padx=28, pady=20)
        self.pack(fill="both", expand=True)
        self._build()

    def _build(self):
        page_header(self, "Products", "Manage your product inventory")
        bf = tk.Frame(self, bg=T()["bg"])
        bf.pack(fill="x", pady=(0, 10))
        if current_user_role == "admin":
            action_btn(bf, "＋ Add Product", self._add).pack(side="left", padx=(0,6))
            action_btn(bf, "✎ Update", self._update, "#2E5F9E").pack(side="left", padx=(0,6))
            action_btn(bf, "🗑 Delete", self._delete, T()["danger"]).pack(side="left", padx=(0,6))
        action_btn(bf, "🔍 Search", self._search, T()["warning"]).pack(side="left", padx=(0,6))
        action_btn(bf, "⚠ Low Stock", self._show_low, T()["warning"]).pack(side="left", padx=(0,6))
        action_btn(bf, "⟳ Refresh", self._load, T()["success"]).pack(side="right")

        self.tree = styled_table(self, ["Product ID","Name","SKU","Price","Stock","Reorder","Category","Supplier"])
        self.tree.column("Product ID", width=90)
        self.tree.column("SKU", width=130)
        self.tree.column("Price", width=70)
        self.tree.column("Stock", width=60)
        self.tree.column("Reorder", width=70)
        self._load()

    def _load(self, filter_name=None, low_only=False):
        for r in self.tree.get_children():
            self.tree.delete(r)
        try:
            where = "WHERE p.is_deleted=0"
            vals = []
            if filter_name:
                where += " AND p.product_name LIKE %s"
                vals.append(f"%{filter_name}%")
            if low_only:
                where += " AND p.stock <= p.reorder_level"
            cursor.execute(f"""
                SELECT p.product_id, p.product_name, p.sku, p.price, p.stock,
                       p.reorder_level, c.category_name, s.supplier_name
                FROM product p
                LEFT JOIN categories c ON p.category_id=c.category_id
                LEFT JOIN suppliers s ON p.supplier_id=s.supplier_id
                {where} ORDER BY p.product_name
            """, vals)
            for r in cursor.fetchall():
                stock, reorder = r[4], r[5]
                tag = "out" if stock == 0 else ("low" if stock <= reorder else "")
                self.tree.insert("", "end", values=(r[0], r[1], r[2] or "", r[3], r[4], r[5], r[6] or "", r[7] or ""), tags=(tag,))
            self.tree.tag_configure("out", foreground=T()["out_stock"])
            self.tree.tag_configure("low", foreground=T()["low_stock"])
        except mysql.connector.Error as e:
            messagebox.showerror("Error", str(e))

    def _get_categories(self):
        cursor.execute("SELECT category_id, category_name FROM categories ORDER BY category_name")
        return cursor.fetchall()

    def _get_suppliers(self):
        cursor.execute("SELECT supplier_id, supplier_name FROM suppliers WHERE is_deleted=0 ORDER BY supplier_name")
        return cursor.fetchall()

    def _add(self):
        win = FormWindow(self, "Add Product")
        parent = win.scroll_frame  # ✅ SINGLE PARENT SOURCE
        
        # TEST: Verify parent is working
        tk.Label(parent, text="✓ FORM ACTIVE", bg="yellow", fg="black", font=("Helvetica", 9, "bold")).pack(pady=5)
        
        name_v = tk.StringVar(); price_v = tk.StringVar(); cost_v = tk.StringVar()
        stock_v = tk.StringVar(); reorder_v = tk.StringVar(value="5")
        form_entry(parent, "Product Name", name_v)
        form_entry(parent, "Selling Price (₹)", price_v)
        form_entry(parent, "Cost Price (₹)", cost_v)
        form_entry(parent, "Stock Quantity", stock_v)
        form_entry(parent, "Reorder Alert Level", reorder_v)

        cats = self._get_categories()
        cat_map = {c[1]: c[0] for c in cats}
        cat_v = tk.StringVar()
        form_dropdown(parent, "Category", cat_v, [c[1] for c in cats] + ["— None —"])

        supps = self._get_suppliers()
        supp_map = {s[1]: s[0] for s in supps}
        supp_v = tk.StringVar()
        form_dropdown(parent, "Supplier", supp_v, [s[1] for s in supps] + ["— None —"])

        def submit():
            n, p_s, c_s, s_s, r_s = name_v.get().strip(), price_v.get().strip(), cost_v.get().strip(), stock_v.get().strip(), reorder_v.get().strip()
            if not all([n, p_s, s_s]):
                messagebox.showwarning("Warning", "Name, Price and Stock are required.", parent=win)
                return
            try:
                price = float(p_s); cost = float(c_s) if c_s else 0
                stock = int(s_s); reorder = int(r_s) if r_s else 5
                cat_id = cat_map.get(cat_v.get())
                supp_id = supp_map.get(supp_v.get())
                pid = generate_product_id(n)
                sku = generate_sku(n, cat_id)
                cursor.execute("""INSERT INTO product (product_id, product_name, sku, price, cost_price, stock, reorder_level, category_id, supplier_id)
                                  VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                               (pid, n, sku, price, cost, stock, reorder, cat_id, supp_id))
                connect.commit()
                messagebox.showinfo("Added", f"Product added!\nID: {pid}\nSKU: {sku}", parent=win)
                win.destroy(); self._load()
            except ValueError:
                messagebox.showerror("Error", "Invalid number format.", parent=win)
            except mysql.connector.Error as e:
                messagebox.showerror("Error", str(e), parent=win)
        win.set_action("Add Product", submit)

    def _update(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Select a product first.")
            return
        row = self.tree.item(sel[0])["values"]
        pid = row[0]
        win = FormWindow(self, f"Update: {pid}")
        parent = win.scroll_frame  # ✅ SINGLE PARENT SOURCE
        tk.Label(parent, text="✓ FORM ACTIVE", bg="yellow", fg="black", font=("Helvetica", 9, "bold")).pack(pady=5)
        
        price_v = tk.StringVar(value=str(row[3]))
        stock_v = tk.StringVar(value=str(row[4]))
        reorder_v = tk.StringVar(value=str(row[5]))
        form_entry(parent, "Price (₹)", price_v)
        form_entry(parent, "Stock", stock_v)
        form_entry(parent, "Reorder Level", reorder_v)

        def submit():
            try:
                cursor.execute("UPDATE product SET price=%s, stock=%s, reorder_level=%s WHERE product_id=%s",
                               (float(price_v.get()), int(stock_v.get()), int(reorder_v.get()), pid))
                connect.commit()
                messagebox.showinfo("Updated", "Product updated!", parent=win)
                win.destroy(); self._load()
            except ValueError:
                messagebox.showerror("Error", "Invalid numbers.", parent=win)
            except mysql.connector.Error as e:
                messagebox.showerror("Error", str(e), parent=win)
        win.set_action("Update", submit)

    def _delete(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Select a product first.")
            return
        pid = self.tree.item(sel[0])["values"][0]
        if not messagebox.askyesno("Confirm", f"Delete product {pid}?"):
            return
        try:
            cursor.execute("""SELECT order_id FROM orders WHERE product_id=%s
                              AND order_status NOT IN ('cancelled','delivered')""", (pid,))
            if cursor.fetchall():
                messagebox.showerror("Error", "Product has active orders.")
                return
            cursor.execute("UPDATE product SET is_deleted=1 WHERE product_id=%s", (pid,))
            connect.commit()
            messagebox.showinfo("Deleted", "Product deleted.")
            self._load()
        except mysql.connector.Error as e:
            messagebox.showerror("Error", str(e))

    def _search(self):
        win = FormWindow(self, "Search Products")
        parent = win.scroll_frame  # ✅ SINGLE PARENT SOURCE
        tk.Label(parent, text="✓ FORM ACTIVE", bg="yellow", fg="black", font=("Helvetica", 9, "bold")).pack(pady=5)
        
        name_v = tk.StringVar()
        form_entry(parent, "Product Name", name_v)
        def submit():
            win.destroy(); self._load(name_v.get().strip())
        win.set_action("Search", submit)

    def _show_low(self):
        self._load(low_only=True)


#!  CATEGORIES PAGE

class CategoriesPage(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg=T()["bg"], padx=28, pady=20)
        self.pack(fill="both", expand=True)
        self._build()

    def _build(self):
        page_header(self, "Categories", "Organise products into categories")
        bf = tk.Frame(self, bg=T()["bg"])
        bf.pack(fill="x", pady=(0, 10))
        action_btn(bf, "＋ Add", self._add).pack(side="left", padx=(0,6))
        action_btn(bf, "🗑 Delete", self._delete, T()["danger"]).pack(side="left", padx=(0,6))
        action_btn(bf, "⟳ Refresh", self._load, T()["success"]).pack(side="right")
        self.tree = styled_table(self, ["ID","Category Name","Description","Products"])
        self._load()

    def _load(self):
        for r in self.tree.get_children():
            self.tree.delete(r)
        try:
            cursor.execute("""
                SELECT c.category_id, c.category_name, c.description,
                       COUNT(p.product_id) AS cnt
                FROM categories c
                LEFT JOIN product p ON c.category_id=p.category_id AND p.is_deleted=0
                GROUP BY c.category_id, c.category_name, c.description
                ORDER BY c.category_name
            """)
            for r in cursor.fetchall():
                self.tree.insert("", "end", values=r)
        except mysql.connector.Error as e:
            messagebox.showerror("Error", str(e))

    def _add(self):
        win = FormWindow(self, "Add Category")
        parent = win.scroll_frame  # ✅ SINGLE PARENT SOURCE
        tk.Label(parent, text="✓ FORM ACTIVE", bg="yellow", fg="black", font=("Helvetica", 9, "bold")).pack(pady=5)
        
        name_v = tk.StringVar(); desc_v = tk.StringVar()
        form_entry(parent, "Category Name", name_v)
        form_entry(parent, "Description (optional)", desc_v)
        def submit():
            n = name_v.get().strip()
            if not n:
                messagebox.showwarning("Warning", "Name required.", parent=win)
                return
            try:
                cursor.execute("INSERT INTO categories (category_name, description) VALUES (%s,%s)",
                               (n, desc_v.get().strip() or None))
                connect.commit()
                messagebox.showinfo("Added", f"Category '{n}' created.", parent=win)
                win.destroy(); self._load()
            except mysql.connector.IntegrityError:
                messagebox.showerror("Error", "Category name already exists.", parent=win)
            except mysql.connector.Error as e:
                messagebox.showerror("Error", str(e), parent=win)
        win.set_action("Add Category", submit)

    def _delete(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Select a category first.")
            return
        row = self.tree.item(sel[0])["values"]
        cid, name, _, count = row
        if count > 0:
            messagebox.showerror("Error", f"Cannot delete: {count} product(s) use this category.")
            return
        if not messagebox.askyesno("Confirm", f"Delete category '{name}'?"):
            return
        try:
            cursor.execute("DELETE FROM categories WHERE category_id=%s", (cid,))
            connect.commit()
            messagebox.showinfo("Deleted", "Category deleted.")
            self._load()
        except mysql.connector.Error as e:
            messagebox.showerror("Error", str(e))


#!  SUPPLIERS PAGE

class SuppliersPage(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg=T()["bg"], padx=28, pady=20)
        self.pack(fill="both", expand=True)
        self._build()

    def _build(self):
        page_header(self, "Suppliers", "Manage your product suppliers")
        bf = tk.Frame(self, bg=T()["bg"])
        bf.pack(fill="x", pady=(0, 10))
        action_btn(bf, "＋ Add Supplier", self._add).pack(side="left", padx=(0,6))
        action_btn(bf, "✎ Update", self._update, "#2E5F9E").pack(side="left", padx=(0,6))
        action_btn(bf, "🗑 Delete", self._delete, T()["danger"]).pack(side="left", padx=(0,6))
        action_btn(bf, "⟳ Refresh", self._load, T()["success"]).pack(side="right")
        self.tree = styled_table(self, ["ID","Company","Contact","Phone","Email","Products"])
        self._load()

    def _load(self):
        for r in self.tree.get_children():
            self.tree.delete(r)
        try:
            cursor.execute("""
                SELECT s.supplier_id, s.supplier_name, s.contact_name, s.phone, s.email,
                       COUNT(p.product_id) AS cnt
                FROM suppliers s
                LEFT JOIN product p ON s.supplier_id=p.supplier_id AND p.is_deleted=0
                WHERE s.is_deleted=0
                GROUP BY s.supplier_id, s.supplier_name, s.contact_name, s.phone, s.email
                ORDER BY s.supplier_name
            """)
            for r in cursor.fetchall():
                self.tree.insert("", "end", values=r)
        except mysql.connector.Error as e:
            messagebox.showerror("Error", str(e))

    def _add(self):
        win = FormWindow(self, "Add Supplier")
        parent = win.scroll_frame  # ✅ SINGLE PARENT SOURCE
        tk.Label(parent, text="✓ FORM ACTIVE", bg="yellow", fg="black", font=("Helvetica", 9, "bold")).pack(pady=5)
        
        name_v = tk.StringVar(); contact_v = tk.StringVar()
        phone_v = tk.StringVar(); email_v = tk.StringVar(); addr_v = tk.StringVar()
        form_entry(parent, "Company Name *", name_v)
        form_entry(parent, "Contact Person", contact_v)
        form_entry(parent, "Phone", phone_v)
        form_entry(parent, "Email", email_v)
        form_entry(parent, "Address", addr_v)
        def submit():
            n = name_v.get().strip()
            if not n:
                messagebox.showwarning("Warning", "Company name required.", parent=win)
                return
            try:
                cursor.execute("""INSERT INTO suppliers (supplier_name, contact_name, phone, email, address)
                                  VALUES (%s,%s,%s,%s,%s)""",
                               (n, contact_v.get() or None, phone_v.get() or None,
                                email_v.get() or None, addr_v.get() or None))
                connect.commit()
                messagebox.showinfo("Added", f"Supplier '{n}' added.", parent=win)
                win.destroy(); self._load()
            except mysql.connector.Error as e:
                messagebox.showerror("Error", str(e), parent=win)
        win.set_action("Add Supplier", submit)

    def _update(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Select a supplier first.")
            return
        row = self.tree.item(sel[0])["values"]
        sid = row[0]
        cursor.execute("SELECT supplier_name, contact_name, phone, email, address FROM suppliers WHERE supplier_id=%s", (sid,))
        s = cursor.fetchone()
        win = FormWindow(self, f"Update Supplier: {sid}")
        parent = win.scroll_frame  # ✅ SINGLE PARENT SOURCE
        tk.Label(parent, text="✓ FORM ACTIVE", bg="yellow", fg="black", font=("Helvetica", 9, "bold")).pack(pady=5)
        
        name_v = tk.StringVar(value=s[0]); contact_v = tk.StringVar(value=s[1] or "")
        phone_v = tk.StringVar(value=s[2] or ""); email_v = tk.StringVar(value=s[3] or "")
        addr_v = tk.StringVar(value=s[4] or "")
        form_entry(parent, "Company Name", name_v)
        form_entry(parent, "Contact Person", contact_v)
        form_entry(parent, "Phone", phone_v)
        form_entry(parent, "Email", email_v)
        form_entry(parent, "Address", addr_v)
        def submit():
            try:
                cursor.execute("""UPDATE suppliers SET supplier_name=%s, contact_name=%s,
                                  phone=%s, email=%s, address=%s WHERE supplier_id=%s""",
                               (name_v.get(), contact_v.get() or None, phone_v.get() or None,
                                email_v.get() or None, addr_v.get() or None, sid))
                connect.commit()
                messagebox.showinfo("Updated", "Supplier updated!", parent=win)
                win.destroy(); self._load()
            except mysql.connector.Error as e:
                messagebox.showerror("Error", str(e), parent=win)
        win.set_action("Update Supplier", submit)

    def _delete(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Select a supplier first.")
            return
        row = self.tree.item(sel[0])["values"]
        sid, name, _, _, _, count = row
        if count > 0:
            messagebox.showerror("Error", f"Cannot delete: {count} product(s) linked to this supplier.")
            return
        if not messagebox.askyesno("Confirm", f"Delete supplier '{name}'?"):
            return
        try:
            cursor.execute("UPDATE suppliers SET is_deleted=1 WHERE supplier_id=%s", (sid,))
            connect.commit()
            messagebox.showinfo("Deleted", "Supplier deleted.")
            self._load()
        except mysql.connector.Error as e:
            messagebox.showerror("Error", str(e))


#!  USERS PAGE

class UsersPage(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg=T()["bg"], padx=28, pady=20)
        self.pack(fill="both", expand=True)
        self._build()

    def _build(self):
        page_header(self, "Users", "Manage system users")
        bf = tk.Frame(self, bg=T()["bg"])
        bf.pack(fill="x", pady=(0,10))
        action_btn(bf, "＋ Add User", self._add).pack(side="left", padx=(0,6))
        action_btn(bf, "✉ Update Email", self._update_email, "#2E5F9E").pack(side="left", padx=(0,6))
        action_btn(bf, "🗑 Delete", self._delete, T()["danger"]).pack(side="left", padx=(0,6))
        action_btn(bf, "⟳ Refresh", self._load, T()["success"]).pack(side="right")
        self.tree = styled_table(self, ["User ID","Name","Email","Role"])
        self._load()

    def _load(self):
        for r in self.tree.get_children():
            self.tree.delete(r)
        try:
            cursor.execute("SELECT user_id, name, email, role FROM users WHERE is_deleted=0")
            for r in cursor.fetchall():
                self.tree.insert("", "end", values=r)
        except mysql.connector.Error as e:
            messagebox.showerror("Error", str(e))

    def _add(self):
        win = FormWindow(self, "Add User")
        parent = win.scroll_frame  # ✅ SINGLE PARENT SOURCE
        tk.Label(parent, text="✓ FORM ACTIVE", bg="yellow", fg="black", font=("Helvetica", 9, "bold")).pack(pady=5)
        
        name_v = tk.StringVar(); email_v = tk.StringVar()
        pass_v = tk.StringVar(); role_v = tk.StringVar(value="user")
        form_entry(parent, "Name", name_v)
        form_entry(parent, "Email", email_v)
        form_entry(parent, "Password", pass_v, show="●")
        form_dropdown(parent, "Role", role_v, ["user","admin"])
        def submit():
            n, e, p, r = name_v.get().strip(), email_v.get().strip(), pass_v.get(), role_v.get()
            if not all([n, e, p, r]):
                messagebox.showwarning("Warning", "All fields required.", parent=win); return
            if not is_valid_email(e):
                messagebox.showwarning("Warning", "Invalid email.", parent=win); return
            try:
                uid = generate_user_id(n)
                hashed = bcrypt.hashpw(p.encode(), bcrypt.gensalt())
                cursor.execute("INSERT INTO users (user_id, name, email, password, role) VALUES (%s,%s,%s,%s,%s)",
                               (uid, n, e, hashed, r))
                connect.commit()
                messagebox.showinfo("Success", f"User added! ID: {uid}", parent=win)
                win.destroy(); self._load()
            except mysql.connector.IntegrityError:
                messagebox.showerror("Error", "Email already exists.", parent=win)
            except mysql.connector.Error as e2:
                messagebox.showerror("Error", str(e2), parent=win)
        win.set_action("Add User", submit)

    def _update_email(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Select a user first."); return
        uid = self.tree.item(sel[0])["values"][0]
        win = FormWindow(self, f"Update Email: {uid}")
        parent = win.scroll_frame  # ✅ SINGLE PARENT SOURCE
        tk.Label(parent, text="✓ FORM ACTIVE", bg="yellow", fg="black", font=("Helvetica", 9, "bold")).pack(pady=5)
        
        email_v = tk.StringVar()
        form_entry(parent, "New Email", email_v)
        def submit():
            e = email_v.get().strip()
            if not is_valid_email(e):
                messagebox.showwarning("Warning", "Invalid email.", parent=win); return
            try:
                cursor.execute("UPDATE users SET email=%s WHERE user_id=%s", (e, uid))
                connect.commit()
                messagebox.showinfo("Updated", "Email updated!", parent=win)
                win.destroy(); self._load()
            except mysql.connector.Error as e2:
                messagebox.showerror("Error", str(e2), parent=win)
        win.set_action("Update Email", submit)

    def _delete(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Select a user first."); return
        uid = self.tree.item(sel[0])["values"][0]
        if not messagebox.askyesno("Confirm", f"Delete user {uid}?"): return
        try:
            cursor.execute("""SELECT order_id FROM orders WHERE user_id=%s
                              AND order_status NOT IN ('cancelled','delivered')""", (uid,))
            if cursor.fetchall():
                messagebox.showerror("Error", "User has active orders."); return
            cursor.execute("UPDATE users SET is_deleted=1 WHERE user_id=%s", (uid,))
            connect.commit()
            messagebox.showinfo("Deleted", "User deleted.")
            self._load()
        except mysql.connector.Error as e:
            messagebox.showerror("Error", str(e))


#!  ORDERS PAGE (Admin)

class OrdersPage(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg=T()["bg"], padx=28, pady=20)
        self.pack(fill="both", expand=True)
        self._build()

    def _build(self):
        page_header(self, "Orders", "View and manage all orders")
        bf = tk.Frame(self, bg=T()["bg"])
        bf.pack(fill="x", pady=(0,10))
        action_btn(bf, "✎ Change Status", self._change_status, "#2E5F9E").pack(side="left", padx=(0,6))
        action_btn(bf, "⟳ Refresh", self._load, T()["success"]).pack(side="right")
        self.tree = styled_table(self, ["Order ID","User","Product","Qty","Status","Date"])
        self._load()

    def _load(self):
        for r in self.tree.get_children():
            self.tree.delete(r)
        try:
            cursor.execute("""SELECT o.order_id, o.user_id, p.product_name, o.quantity, o.order_status,
                                     DATE(o.created_at)
                              FROM orders o JOIN product p ON o.product_id=p.product_id
                              ORDER BY o.order_id DESC""")
            for r in cursor.fetchall():
                self.tree.insert("", "end", values=r)
        except mysql.connector.Error as e:
            messagebox.showerror("Error", str(e))

    def _change_status(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Select an order first."); return
        oid = self.tree.item(sel[0])["values"][0]
        win = FormWindow(self, f"Change Status: #{oid}")
        parent = win.scroll_frame  # ✅ SINGLE PARENT SOURCE
        tk.Label(parent, text="✓ FORM ACTIVE", bg="yellow", fg="black", font=("Helvetica", 9, "bold")).pack(pady=5)
        
        status_v = tk.StringVar(value="shipped")
        form_dropdown(parent, "New Status", status_v, ["placed","shipped","delivered","cancelled"])
        def submit():
            try:
                cursor.execute("UPDATE orders SET order_status=%s WHERE order_id=%s", (status_v.get(), oid))
                connect.commit()
                messagebox.showinfo("Updated", "Order status updated!", parent=win)
                win.destroy(); self._load()
            except mysql.connector.Error as e:
                messagebox.showerror("Error", str(e), parent=win)
        win.set_action("Update Status", submit)


#!  MY ORDERS PAGE (User)

class MyOrdersPage(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg=T()["bg"], padx=28, pady=20)
        self.pack(fill="both", expand=True)
        self._build()

    def _build(self):
        page_header(self, "My Orders", "Browse products and manage your orders")
        tk.Label(self, text="Available Products", font=("Georgia", 13, "bold"),
                 bg=T()["bg"], fg=T()["fg"]).pack(anchor="w", pady=(0,4))
        self.prod_tree = styled_table(self, ["Product ID","Name","SKU","Price","Stock"], height=4)
        self._load_products()

        tk.Label(self, text="My Orders", font=("Georgia", 13, "bold"),
                 bg=T()["bg"], fg=T()["fg"]).pack(anchor="w", pady=(10, 4))
        bf = tk.Frame(self, bg=T()["bg"])
        bf.pack(fill="x", pady=(0,6))
        action_btn(bf, "＋ Place Order", self._place_order).pack(side="left", padx=(0,6))
        action_btn(bf, "💳 Make Payment", self._make_payment, "#2E5F9E").pack(side="left", padx=(0,6))
        action_btn(bf, "✕ Cancel Order", self._cancel_order, T()["danger"]).pack(side="left", padx=(0,6))
        action_btn(bf, "⟳ Refresh", self._load_data, T()["success"]).pack(side="right")
        self.tree = styled_table(self, ["Order ID","Product","Qty","Status"], height=6)
        self._load_data()

    def _load_products(self):
        for r in self.prod_tree.get_children():
            self.prod_tree.delete(r)
        try:
            cursor.execute("""SELECT product_id, product_name, sku, price, stock
                              FROM product WHERE stock>0 AND is_deleted=0 ORDER BY product_name""")
            for r in cursor.fetchall():
                self.prod_tree.insert("", "end", values=r)
        except mysql.connector.Error as e:
            messagebox.showerror("Error", str(e))

    def _load_data(self):
        for r in self.tree.get_children():
            self.tree.delete(r)
        try:
            cursor.execute("""SELECT o.order_id, p.product_name, o.quantity, o.order_status
                              FROM orders o JOIN product p ON o.product_id=p.product_id
                              WHERE o.user_id=%s ORDER BY o.order_id DESC""", (current_user_id,))
            for r in cursor.fetchall():
                self.tree.insert("", "end", values=r)
        except mysql.connector.Error as e:
            messagebox.showerror("Error", str(e))

    def _place_order(self):
        sel = self.prod_tree.selection()
        default_pid = self.prod_tree.item(sel[0])["values"][0] if sel else ""
        win = FormWindow(self, "Place New Order")
        parent = win.scroll_frame  # ✅ SINGLE PARENT SOURCE
        tk.Label(parent, text="✓ FORM ACTIVE", bg="yellow", fg="black", font=("Helvetica", 9, "bold")).pack(pady=5)
        
        pid_v = tk.StringVar(value=str(default_pid)); qty_v = tk.StringVar()
        form_entry(parent, "Product ID", pid_v)
        form_entry(parent, "Quantity", qty_v)
        def submit():
            pid, qty_s = pid_v.get().strip(), qty_v.get().strip()
            if not pid or not qty_s:
                messagebox.showwarning("Warning", "All fields required.", parent=win); return
            try:
                qty = int(qty_s)
                if qty <= 0:
                    messagebox.showwarning("Warning", "Qty must be > 0.", parent=win); return
                cursor.execute("SELECT stock, price FROM product WHERE product_id=%s AND is_deleted=0", (pid,))
                r = cursor.fetchone()
                if not r:
                    messagebox.showerror("Error", "Product not found.", parent=win); return
                stock, price = r
                if stock < qty:
                    messagebox.showerror("Error", f"Only {stock} in stock.", parent=win); return
                cursor.execute("INSERT INTO orders (user_id, product_id, quantity) VALUES (%s,%s,%s)",
                               (current_user_id, pid, qty))
                cursor.execute("UPDATE product SET stock=stock-%s WHERE product_id=%s", (qty, pid))
                connect.commit()
                oid = cursor.lastrowid
                messagebox.showinfo("Placed", f"Order placed! ID: {oid}\nTotal: ₹{qty * float(price):.2f}", parent=win)
                win.destroy(); self._load_data(); self._load_products()
            except ValueError:
                messagebox.showerror("Error", "Invalid quantity.", parent=win)
            except mysql.connector.Error as e2:
                connect.rollback(); messagebox.showerror("Error", str(e2), parent=win)
        win.set_action("Place Order", submit)

    def _make_payment(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Select an order first."); return
        row = self.tree.item(sel[0])["values"]
        oid, pid_name, qty, status = row[0], row[1], row[2], row[3]
        if status != "placed":
            messagebox.showerror("Error", "Only 'placed' orders can be paid."); return
        cursor.execute("SELECT payment_id, amount, payment_status FROM payment WHERE order_id=%s", (oid,))
        existing = cursor.fetchone()
        if existing and existing[2] == "completed":
            messagebox.showinfo("Info", "Already fully paid."); return
        cursor.execute("""SELECT p.price FROM orders o JOIN product p ON o.product_id=p.product_id
                          WHERE o.order_id=%s""", (oid,))
        price_r = cursor.fetchone()
        if not price_r:
            messagebox.showerror("Error", "Product not found."); return
        total = qty * float(price_r[0])
        already_paid = float(existing[1]) if existing else 0
        remaining = total - already_paid
        win = FormWindow(self, f"Pay — Order #{oid}")
        parent = win.scroll_frame  # ✅ SINGLE PARENT SOURCE
        tk.Label(parent, text="✓ FORM ACTIVE", bg="yellow", fg="black", font=("Helvetica", 9, "bold")).pack(pady=5)
        
        tk.Label(parent, text=f"Total: ₹{total:.2f}", font=("Georgia", 13, "bold"),
                 bg=T()["card_bg"], fg=T()["accent"]).pack(anchor="w", pady=(8,2))
        if already_paid > 0:
            tk.Label(parent, text=f"Paid: ₹{already_paid:.2f}  |  Remaining: ₹{remaining:.2f}",
                     font=("Helvetica", 10), bg=T()["card_bg"], fg=T()["warning"]).pack(anchor="w")
        amount_v = tk.StringVar()
        form_entry(parent, "Amount (₹)", amount_v)
        def submit():
            try:
                amount = float(amount_v.get())
                if amount <= 0:
                    messagebox.showwarning("Warning", "Amount must be > 0.", parent=win); return
                if amount > remaining:
                    messagebox.showwarning("Warning", f"Max: ₹{remaining:.2f}", parent=win); return
                new_total = already_paid + amount
                pay_status = "completed" if new_total >= total else "pending"
                if existing:
                    cursor.execute("UPDATE payment SET amount=%s, payment_status=%s WHERE order_id=%s",
                                   (new_total, pay_status, oid))
                else:
                    cursor.execute("INSERT INTO payment (order_id, amount, payment_status) VALUES (%s,%s,%s)",
                                   (oid, amount, pay_status))
                if pay_status == "completed":
                    cursor.execute("UPDATE orders SET order_status='shipped' WHERE order_id=%s", (oid,))
                connect.commit()
                msg = "Payment complete! Order shipped." if pay_status=="completed" else f"Partial saved. ₹{remaining-amount:.2f} still due."
                messagebox.showinfo("Payment", msg, parent=win)
                win.destroy(); self._load_data(); self._load_products()
            except ValueError:
                messagebox.showerror("Error", "Invalid amount.", parent=win)
            except mysql.connector.Error as e:
                connect.rollback(); messagebox.showerror("Error", str(e), parent=win)
        win.set_action("Pay Now", submit)

    def _cancel_order(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Select an order first."); return
        row = self.tree.item(sel[0])["values"]
        oid, status = row[0], row[3]
        if status != "placed":
            messagebox.showerror("Error", "Only 'placed' orders can be cancelled."); return
        if not messagebox.askyesno("Confirm", f"Cancel order #{oid}?"): return
        try:
            cursor.execute("SELECT product_id, quantity FROM orders WHERE order_id=%s", (oid,))
            r = cursor.fetchone()
            cursor.execute("UPDATE product SET stock=stock+%s WHERE product_id=%s", (r[1], r[0]))
            cursor.execute("UPDATE orders SET order_status='cancelled' WHERE order_id=%s", (oid,))
            cursor.execute("SELECT payment_status FROM payment WHERE order_id=%s", (oid,))
            pay = cursor.fetchone()
            if pay and pay[0] == "completed":
                cursor.execute("UPDATE payment SET payment_status='refunded' WHERE order_id=%s", (oid,))
            elif pay and pay[0] == "pending":
                cursor.execute("UPDATE payment SET payment_status='refunded' WHERE order_id=%s", (oid,))
            connect.commit()
            if pay and pay[0] == "completed":
                messagebox.showinfo("Cancelled", f"Order #{oid} cancelled.\nYour full payment has been refunded.")
            elif pay and pay[0] == "pending":
                messagebox.showinfo("Cancelled", f"Order #{oid} cancelled.\nYour partial payment has been refunded.")
            else:
                messagebox.showinfo("Cancelled", f"Order #{oid} cancelled.")
            self._load_data(); self._load_products()
        except mysql.connector.Error as e:
            connect.rollback(); messagebox.showerror("Error", str(e))


#!  PAYMENTS PAGE (Admin)

class PaymentsPage(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg=T()["bg"], padx=28, pady=20)
        self.pack(fill="both", expand=True)
        page_header(self, "Payments", "All payment records")
        action_btn(self, "⟳ Refresh", self._load, T()["success"]).pack(anchor="e", pady=(0,10))
        self.tree = styled_table(self, ["Pay ID","Order ID","Amount","Status","Date"])
        self._load()

    def _load(self):
        for r in self.tree.get_children():
            self.tree.delete(r)
        try:
            cursor.execute("SELECT payment_id, order_id, amount, payment_status, DATE(paid_at) FROM payment ORDER BY payment_id DESC")
            for r in cursor.fetchall():
                self.tree.insert("", "end", values=r)
        except mysql.connector.Error as e:
            messagebox.showerror("Error", str(e))


#!  MY PAYMENTS PAGE (User)

class MyPaymentsPage(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg=T()["bg"], padx=28, pady=20)
        self.pack(fill="both", expand=True)
        page_header(self, "My Payments", "Your payment history")
        action_btn(self, "⟳ Refresh", self._load, T()["success"]).pack(anchor="e", pady=(0,10))
        self.tree = styled_table(self, ["Pay ID","Order ID","Amount","Status","Date"])
        self._load()

    def _load(self):
        for r in self.tree.get_children():
            self.tree.delete(r)
        try:
            cursor.execute("""SELECT p.payment_id, p.order_id, p.amount, p.payment_status, DATE(p.paid_at)
                              FROM payment p JOIN orders o ON p.order_id=o.order_id
                              WHERE o.user_id=%s ORDER BY p.payment_id DESC""", (current_user_id,))
            for r in cursor.fetchall():
                self.tree.insert("", "end", values=r)
        except mysql.connector.Error as e:
            messagebox.showerror("Error", str(e))


#!  REVENUE PAGE (Admin)

class RevenuePage(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg=T()["bg"], padx=28, pady=20)
        self.pack(fill="both", expand=True)
        self._build()

    def _build(self):
        page_header(self, "Revenue", "Financial overview")
        try:
            cursor.execute("SELECT COALESCE(SUM(amount),0) FROM payment WHERE payment_status='completed'"); total = cursor.fetchone()[0]
            cursor.execute("SELECT COALESCE(SUM(amount),0) FROM payment WHERE payment_status='pending'"); pending = cursor.fetchone()[0]
            cursor.execute("SELECT COALESCE(SUM(amount),0) FROM payment WHERE payment_status='refunded'"); refunded = cursor.fetchone()[0]
        except:
            total = pending = refunded = 0

        cards = tk.Frame(self, bg=T()["bg"])
        cards.pack(fill="x", pady=(0,20))
        cards.columnconfigure((0,1,2), weight=1)
        stat_card(cards, "Total Revenue (₹)", f"₹{total:.2f}", "#10B981", 0)
        stat_card(cards, "Pending (₹)", f"₹{pending:.2f}", T()["warning"], 1)
        stat_card(cards, "Refunded (₹)", f"₹{refunded:.2f}", T()["danger"], 2)

        tk.Label(self, text="All Payments", font=("Georgia", 14, "bold"),
                 bg=T()["bg"], fg=T()["fg"]).pack(anchor="w", pady=(0,8))
        tree = styled_table(self, ["Pay ID","Order ID","Amount","Status","Date"])
        try:
            cursor.execute("SELECT payment_id, order_id, amount, payment_status, DATE(paid_at) FROM payment ORDER BY payment_id DESC")
            for r in cursor.fetchall():
                tree.insert("", "end", values=r)
        except mysql.connector.Error as e:
            messagebox.showerror("Error", str(e))


#!  REPORTS PAGE (Admin)

class ReportsPage(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg=T()["bg"], padx=28, pady=20)
        self.pack(fill="both", expand=True)
        self._build()

    def _build(self):
        page_header(self, "Reports", "Sales, inventory and profit analytics")

        tabs = ttk.Notebook(self)
        tabs.pack(fill="both", expand=True, pady=(4, 0))

        # Tab 1: Sales by product
        t1 = tk.Frame(tabs, bg=T()["bg"])
        tabs.add(t1, text="  Sales by Product  ")
        action_btn(t1, "⟳ Load", lambda: self._load_product_sales(tree1), T()["success"]).pack(anchor="e", pady=6, padx=4)
        tree1 = styled_table(t1, ["Product ID","Product Name","Qty Sold","Revenue (₹)"])
        self._load_product_sales(tree1)

        # Tab 2: Sales by category
        t2 = tk.Frame(tabs, bg=T()["bg"])
        tabs.add(t2, text="  Sales by Category  ")
        action_btn(t2, "⟳ Load", lambda: self._load_cat_sales(tree2), T()["success"]).pack(anchor="e", pady=6, padx=4)
        tree2 = styled_table(t2, ["Category","Products","Qty Sold","Revenue (₹)"])
        self._load_cat_sales(tree2)

        # Tab 3: Profit
        t3 = tk.Frame(tabs, bg=T()["bg"])
        tabs.add(t3, text="  Profit Report  ")
        action_btn(t3, "⟳ Load", lambda: self._load_profit(tree3), T()["success"]).pack(anchor="e", pady=6, padx=4)
        tree3 = styled_table(t3, ["Product ID","Name","Price","Cost","Margin","Sold","Total Profit"])
        self._load_profit(tree3)

        # Tab 4: Low stock
        t4 = tk.Frame(tabs, bg=T()["bg"])
        tabs.add(t4, text="  ⚠ Low Stock  ")
        action_btn(t4, "⟳ Load", lambda: self._load_low_stock(tree4), T()["success"]).pack(anchor="e", pady=6, padx=4)
        tree4 = styled_table(t4, ["Product ID","Name","SKU","Stock","Reorder","Supplier","Phone"])
        self._load_low_stock(tree4)

    def _load_product_sales(self, tree):
        for r in tree.get_children(): tree.delete(r)
        try:
            cursor.execute("""
                SELECT p.product_id, p.product_name,
                       COALESCE(SUM(o.quantity),0) AS sold,
                       COALESCE(SUM(o.quantity * p.price),0) AS revenue
                FROM product p
                LEFT JOIN orders o ON p.product_id=o.product_id
                    AND o.order_status NOT IN ('cancelled','refunded')
                WHERE p.is_deleted=0
                GROUP BY p.product_id, p.product_name
                ORDER BY revenue DESC
            """)
            for r in cursor.fetchall():
                tree.insert("", "end", values=(r[0], r[1], r[2], f"₹{r[3]:.2f}"))
        except mysql.connector.Error as e:
            messagebox.showerror("Error", str(e))

    def _load_cat_sales(self, tree):
        for r in tree.get_children(): tree.delete(r)
        try:
            cursor.execute("""
                SELECT c.category_name, COUNT(DISTINCT p.product_id),
                       COALESCE(SUM(o.quantity),0),
                       COALESCE(SUM(o.quantity * p.price),0)
                FROM categories c
                LEFT JOIN product p ON c.category_id=p.category_id AND p.is_deleted=0
                LEFT JOIN orders o ON p.product_id=o.product_id
                    AND o.order_status NOT IN ('cancelled','refunded')
                GROUP BY c.category_id, c.category_name
                ORDER BY 4 DESC
            """)
            for r in cursor.fetchall():
                tree.insert("", "end", values=(r[0], r[1], r[2], f"₹{r[3]:.2f}"))
        except mysql.connector.Error as e:
            messagebox.showerror("Error", str(e))

    def _load_profit(self, tree):
        for r in tree.get_children(): tree.delete(r)
        try:
            cursor.execute("""
                SELECT p.product_id, p.product_name, p.price, p.cost_price,
                       (p.price - p.cost_price),
                       COALESCE(SUM(o.quantity),0),
                       COALESCE(SUM(o.quantity * (p.price - p.cost_price)),0)
                FROM product p
                LEFT JOIN orders o ON p.product_id=o.product_id
                    AND o.order_status NOT IN ('cancelled','refunded')
                WHERE p.is_deleted=0
                GROUP BY p.product_id, p.product_name, p.price, p.cost_price
                ORDER BY 7 DESC
            """)
            for r in cursor.fetchall():
                tree.insert("", "end", values=(r[0], r[1], f"₹{r[2]:.2f}", f"₹{r[3]:.2f}",
                                               f"₹{r[4]:.2f}", r[5], f"₹{r[6]:.2f}"))
        except mysql.connector.Error as e:
            messagebox.showerror("Error", str(e))

    def _load_low_stock(self, tree):
        for r in tree.get_children(): tree.delete(r)
        try:
            cursor.execute("""
                SELECT p.product_id, p.product_name, p.sku, p.stock, p.reorder_level,
                       s.supplier_name, s.phone
                FROM product p
                LEFT JOIN suppliers s ON p.supplier_id=s.supplier_id
                WHERE p.stock <= p.reorder_level AND p.is_deleted=0
                ORDER BY p.stock ASC
            """)
            for r in cursor.fetchall():
                tag = "out" if r[3] == 0 else "low"
                item = tree.insert("", "end", values=(r[0], r[1], r[2] or "", r[3], r[4], r[5] or "N/A", r[6] or "N/A"), tags=(tag,))
            tree.tag_configure("out", foreground=T()["out_stock"])
            tree.tag_configure("low", foreground=T()["low_stock"])
        except mysql.connector.Error as e:
            messagebox.showerror("Error", str(e))


#!  FORM WINDOW POPUP

class FormWindow(tk.Toplevel):
    def __init__(self, master, title):
        super().__init__(master)
        self.title(title)
        self.configure(bg=T()["card_bg"])
        self.resizable(False, False)
        self.geometry("400x600")
        self.grab_set()
        
        # Header
        tk.Label(self, text=title, font=("Georgia", 15, "bold"),
                 bg=T()["card_bg"], fg=T()["fg"]).pack(anchor="w", padx=24, pady=(18,4))
        tk.Frame(self, bg=T()["accent"], height=2).pack(fill="x", padx=24, pady=(0,10))
        
        # Canvas container frame
        canvas_frame = tk.Frame(self, bg=T()["card_bg"])
        canvas_frame.pack(fill="both", expand=True, padx=24, pady=(0,14))
        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)
        
        # Scrollable canvas
        canvas = tk.Canvas(canvas_frame, bg=T()["card_bg"], highlightthickness=0, width=352)
        scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        
        self.scroll_frame = tk.Frame(canvas, bg=T()["card_bg"])
        
        self.scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw", width=352)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Mousewheel support
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        try:
            canvas.bind("<MouseWheel>", _on_mousewheel)
            self.scroll_frame.bind("<MouseWheel>", _on_mousewheel)
        except tk.TclError:
            pass
        
        # Linux scrollwheel support
        canvas.bind("<Button-4>", lambda e: canvas.yview_scroll(-5, "units"))
        canvas.bind("<Button-5>", lambda e: canvas.yview_scroll(5, "units"))

    def set_action(self, label, command):
        btn_frame = tk.Frame(self.scroll_frame, bg=T()["card_bg"])
        btn_frame.pack(pady=10, fill="x")

        tk.Button(btn_frame, text="Cancel", font=("Helvetica", 10),
                  bg=T()["entry_bg"], fg=T()["fg_sub"], relief="flat",
                  bd=0, padx=12, pady=8, cursor="hand2",
                  command=self.destroy).pack(side="left", padx=5)
        tk.Button(btn_frame, text=label, font=("Helvetica", 10, "bold"),
                  bg=T()["accent"], fg="#FFFFFF", relief="flat",
                  bd=0, padx=12, pady=8, cursor="hand2", width=16,
                  activebackground=T()["accent_hover"], command=command).pack(side="right", padx=5)


#!  RUN

if __name__ == "__main__":
    app = InvenTrackApp()
    app.mainloop()
    try:
        connect.close()
    except:
        pass