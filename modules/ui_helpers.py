# ui_helpers.py
import tkinter as tk
import ttkbootstrap as ttk
from config import TRANSLATIONS, app_settings, save_settings

def start_countdown(counter, timer_label, status_bar_label, window):
    """تابع شمارش معکوس که همیشه از زبان فعلی برنامه استفاده می‌کند."""
    import config
    
    timer_label.pack(side="bottom", fill="x", pady=(2, 0))

    def update_timer(count):
        if count >= 0:
            # تغییر کلیدی: زبان فعال در هر تکرار حلقه خوانده می‌شود
            lang_code = config.current_language
            
            # تنظیم جهت لیبل بر اساس زبان فعال
            if lang_code == 'fa':
                timer_label.config(anchor='e')
            else:
                timer_label.config(anchor='w')

            # ترجمه متن تایمر با زبان صحیح
            timer_message = TRANSLATIONS[lang_code]["timer_text"].format(seconds=count)
            
            if lang_code == 'fa':
                timer_message = '\u202B' + timer_message + '\u202C'

            timer_label.config(text=timer_message)
            config.active_timer_id = window.after(1000, update_timer, count - 1)
        else:
            timer_label.pack_forget()
            status_bar_label.config(text="")
            config.active_timer_id = None
            
    update_timer(counter)

# ui_helpers.py

# ui_helpers.py

def manage_subscription_link(parent_window, lang_code):
    """Opens a Toplevel window to add or edit the subscription link."""
    
    dialog = ttk.Toplevel(parent_window)
    dialog.title(TRANSLATIONS[lang_code]["add_link_title"])
    dialog.transient(parent_window)
    dialog.grab_set()
    dialog.resizable(False, False)

    dialog_frame = ttk.Frame(dialog, padding=20)
    dialog_frame.pack(fill="both", expand=True)

    ttk.Label(dialog_frame, text=TRANSLATIONS[lang_code]["add_link_label"]).pack(pady=(0, 5))
    link_entry = ttk.Entry(dialog_frame, width=50)
    link_entry.pack(pady=5)
    link_entry.insert(0, app_settings.get("last_used_url", ""))

    # --- START: NEW LANGUAGE-INDEPENDENT SHORTCUT HANDLER ---
    
    # This dictionary will hold the state of the Control key
    control_key_state = {'pressed': False}

    def on_key_press(event):
        # When Control_L or Control_R is pressed, set the flag
        if event.keysym in ('Control_L', 'Control_R'):
            control_key_state['pressed'] = True
        # If the flag is already true, check for other keys
        elif control_key_state['pressed'] and event.widget == link_entry:
            # Map of physical keycodes to virtual events
            keymap = {
                65: '<<SelectAll>>',  # Physical key 'A'
                67: '<<Copy>>',       # Physical key 'C'
                86: '<<Paste>>',      # Physical key 'V'
                88: '<<Cut>>'         # Physical key 'X'
            }
            virtual_event = keymap.get(event.keycode)
            if virtual_event:
                # If a mapped key is found, generate the event and stop propagation
                link_entry.event_generate(virtual_event)
                return 'break'

    def on_key_release(event):
        # When Control_L or Control_R is released, reset the flag
        if event.keysym in ('Control_L', 'Control_R'):
            control_key_state['pressed'] = False

    # Bind the handlers to the entire dialog window to reliably capture key events
    dialog.bind('<KeyPress>', on_key_press)
    dialog.bind('<KeyRelease>', on_key_release)
    
    # --- END: NEW HANDLER ---

    # Context menu for right-click (remains the same)
    context_menu = tk.Menu(dialog, tearoff=0)
    context_menu.add_command(
        label=TRANSLATIONS[lang_code]["right_click_copy"],
        command=lambda: link_entry.event_generate('<<Copy>>')
    )
    context_menu.add_command(
        label=TRANSLATIONS[lang_code]["right_click_paste"],
        command=lambda: link_entry.event_generate('<<Paste>>')
    )
    context_menu.add_command(
        label=TRANSLATIONS[lang_code]["right_click_cut"],
        command=lambda: link_entry.event_generate('<<Cut>>')
    )
    context_menu.add_separator()
    context_menu.add_command(
        label=TRANSLATIONS[lang_code]["right_click_select_all"],
        command=lambda: link_entry.event_generate('<<SelectAll>>')
    )

    def show_context_menu(event):
        context_menu.post(event.x_root, event.y_root)

    link_entry.bind("<Button-3>", show_context_menu)
    
    def on_ok():
        app_settings["last_used_url"] = link_entry.get().strip()
        save_settings() 
        dialog.destroy()

    ok_button = ttk.Button(dialog_frame, text=TRANSLATIONS[lang_code]["ok_button"], command=on_ok, bootstyle="success")
    ok_button.pack(pady=(10, 0), fill='x', ipady=4)
    
    link_entry.focus_set()

    dialog.update_idletasks()
    x = parent_window.winfo_x() + (parent_window.winfo_width() // 2) - (dialog.winfo_width() // 2)
    y = parent_window.winfo_y() + (parent_window.winfo_height() // 2) - (dialog.winfo_height() // 2)
    dialog.geometry(f"+{x}+{y}")
    
    dialog.wait_window()

def retranslate_results_data(labels, last_fetched_data, lang_code, colors):
    """Only re-translates the data in the results frame without touching the status bar."""
    if not last_fetched_data:
        return

    data = last_fetched_data
    # ترجمه متن وضعیت
    status_translations = {
        'table_status_active': TRANSLATIONS[lang_code]["status_active"],
        'sub_status_disabled': TRANSLATIONS[lang_code]["status_disabled"],
        'limited': TRANSLATIONS[lang_code]["status_limited"],
        'table_status_expired': TRANSLATIONS[lang_code]["status_expired"]
    }
    status_key = data.get('status_key')
    status_text = status_translations.get(status_key, status_key)

    # تعیین رنگ وضعیت بر اساس کلید وضعیت و رنگ‌های تم
    status_color_map = {
        'table_status_active': colors.get('success'),
        'table_status_expired': colors.get('danger'),
        'sub_status_disabled': colors.get('warning'),
        'limited': colors.get('warning')
    }
    status_color = status_color_map.get(status_key, colors.get('text_secondary'))

    # محاسبه زمان باقی‌مانده
    if data.get('is_unlimited_time'):
        remaining_time = TRANSLATIONS[lang_code]["unlimited"]
    else:
        days, hours = data.get('remaining_days', 0), data.get('remaining_hours', 0)
        remaining_time = TRANSLATIONS[lang_code]["time_format"].format(days=days, hours=hours)

    # محاسبه حجم باقی‌مانده
    if data.get('is_unlimited_volume'):
        remaining_volume_text = TRANSLATIONS[lang_code]["unlimited"]
    else:
        allowed_gb = data.get('allowed_volume_gb') or 0
        used_gb = data.get('used_volume_gb', 0)
        remaining_gb = max(0, allowed_gb - used_gb)
        remaining_volume_text = f"{remaining_gb:.2f} GB"

    # تنظیم متن و رنگ تمام لیبل‌ها به صورت هماهنگ
    labels['username'].config(text=data.get('username', "..."), foreground=colors.get('accent'))
    labels['status'].config(text=status_text, foreground=status_color)
    labels['time'].config(text=remaining_time, foreground=colors.get('accent'))
    labels['volume'].config(text=remaining_volume_text, foreground=colors.get('accent'))
    labels['ip'].config(text=data.get('last_ip') or "N/A", foreground=colors.get('accent'))