# config.py
import json
import os
import sys

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

# Load translations from external JSON files
TRANSLATIONS = {}
for lang in ["en", "fa", "ru", "zh"]:
    try:
        filepath = resource_path(f"{lang}.json")
        with open(filepath, "r", encoding='utf-8') as f:
            TRANSLATIONS[lang] = json.load(f)
    except Exception as e:
        print(f"FATAL ERROR: Could not load language file {lang}.json. Error: {e}")

# Global settings
current_language = "en"
APP_DATA_PATH = os.path.join(os.getenv('APPDATA'), 'VexoChecker')
SETTINGS_FILE = os.path.join(APP_DATA_PATH, 'settings.json')
app_settings = {"language": "en", "last_used_url": "", "last_known_ip": ""}
last_fetched_data = None
active_timer_id = None
active_fetch_id = None
watchdog_timer_id = None

# config.py

def load_settings():
    """Load settings from file"""
    global current_language, app_settings, last_fetched_data
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r", encoding='utf-8') as f:
            try:
                # اطلاعات را از فایل JSON می‌خوانیم
                settings_from_file = json.load(f)

                # مهم: به جای جایگزینی، دیکشنری اصلی را آپدیت می‌کنیم
                if isinstance(settings_from_file, dict):
                    app_settings.update(settings_from_file)

                # حالا مقادیر را از دیکشنری به‌روز شده می‌خوانیم
                lang = app_settings.get("language", "fa")
                if lang in TRANSLATIONS:
                    current_language = lang
                
                # همچنین داده‌های fetch شده را نیز از همان دیکشنری اصلی می‌خوانیم
                last_fetched_data = app_settings.get("last_fetched_data", None)

            except json.JSONDecodeError:
                # اگر فایل خراب بود، از تنظیمات پیش‌فرض استفاده می‌شود
                pass
                
def save_settings():
    """Save settings to file"""
    global app_settings
    os.makedirs(APP_DATA_PATH, exist_ok=True)
    with open(SETTINGS_FILE, "w", encoding='utf-8') as f:
        json.dump(app_settings, f, indent=2)
