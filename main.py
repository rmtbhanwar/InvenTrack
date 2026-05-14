import sys
sys.dont_write_bytecode = True
import os

def check_env():
    """Make sure .env file exists before launching."""
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.exists(env_path):
        print("=" * 52)
        print("  ⚠  No .env file found.")
        print("  Run setup first:  python setup.py")
        print("=" * 52)
        sys.exit(1)

def check_packages():
    """Make sure required packages are installed."""
    required = {
        "mysql.connector": "mysql-connector-python",
        "dotenv":          "python-dotenv",
        "bcrypt":          "bcrypt",
    }
    missing = []
    for import_name, pip_name in required.items():
        try:
            __import__(import_name)
        except ImportError:
            missing.append(pip_name)

    if missing:
        print("=" * 52)
        print("  ⚠  Missing packages:", ", ".join(missing))
        print("  Run setup first:  python setup.py")
        print("=" * 52)
        sys.exit(1)

if __name__ == "__main__":
    check_env()
    check_packages()

    from InvenTrackUI import InvenTrackApp, connect

    app = InvenTrackApp()
    app.mainloop()

    try:
        connect.close()
    except:
        pass