# gui.py - Fixed Modern Version
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
import threading
import time
from PIL import Image, ImageTk

from config import (
    TRANSLATIONS, current_language, app_settings, last_fetched_data,
    active_timer_id, active_fetch_id, watchdog_timer_id,
    load_settings, save_settings, resource_path
)
from network_utils import process_all_data, update_ip_check_hosts
from dns_manager import check_dns_status, set_dns, unset_dns, unset_dns_synchronously
from ui_helpers import start_countdown, manage_subscription_link, retranslate_results_data
import config

class ModernVexoChecker:
    def __init__(self):
        self.is_dns_connected = False
        self.is_operation_in_progress = False
        self.window = None
        self.labels = {}
        self.cards = {}
        self.dns_toggle_button = None
        self.fetch_button = None
        self.context_menu = None
        self.window_width = 500
        self.window_height = 600
        
    def get_theme_colors(self):
        """Get colors based on current theme"""
        current_theme = self.window.style.theme_use()
        
        if current_theme in ['darkly', 'superhero', 'cyborg', 'vapor', 'solar']:
            # Dark theme colors
            return {
                'bg': '#1a1d23',
                'card_bg': '#2b3035',
                'text_primary': '#ffffff',
                'text_secondary': '#8B949E',
                'accent': '#00D9FF',
                'success': '#00D084',
                'warning': '#FFA500',
                'danger': '#FF6B6B',
                'border': '#3d4148'
            }
        else:
            # Light theme colors
            return {
                'bg': '#f8f9fa',
                'card_bg': '#ffffff',
                'text_primary': '#212529',
                'text_secondary': '#6c757d',
                'accent': '#0d6efd',
                'success': '#198754',
                'warning': '#fd7e14',
                'danger': '#dc3545',
                'border': '#dee2e6'
            }
    
    def create_logo_image(self, image_path, size=(48, 48)):
        """Create properly sized logo WITHOUT deformation"""
        try:
            img = Image.open(image_path).convert("RGBA")
            
            # Calculate aspect ratio
            original_width, original_height = img.size
            target_width, target_height = size
            
            # Calculate scaling to fit within target size while maintaining aspect ratio
            width_ratio = target_width / original_width
            height_ratio = target_height / original_height
            scale_ratio = min(width_ratio, height_ratio)
            
            new_width = int(original_width * scale_ratio)
            new_height = int(original_height * scale_ratio)
            
            # Resize with high quality
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            return ImageTk.PhotoImage(img)
        except Exception as e:
            print(f"Error loading logo: {e}")
            return None
        
    def create_window(self):
        """Create modern styled window with FIXED size"""
        load_settings()
        
        # Use dark theme by default
        initial_theme = app_settings.get("theme", "darkly")
        
        self.window = ttk.Window(themename=initial_theme)
        self.window.title("")
        
        # Set FIXED window size
        self.window.geometry(f"{self.window_width}x{self.window_height}")
        self.window.resizable(False, False)
        
        # Set window icon
        try:
            icon_path = resource_path("logo.ico")
            self.window.iconbitmap(icon_path)
        except:
            pass
        
        # Apply custom styling
        self.setup_modern_styles()
        self.create_modern_ui()
        self.setup_event_handlers()
        
        return self.window
    
    def setup_modern_styles(self):
        """Setup modern, beautiful styles with theme-aware colors"""
        style = ttk.Style()
        colors = self.get_theme_colors()
        
        # Modern fonts
        style.configure(".", font=("Segoe UI", 10))
        style.configure("Title.TLabel", font=("Segoe UI", 22, "bold"))
        style.configure("Subtitle.TLabel", font=("Segoe UI", 10))
        style.configure("Header.TLabel", font=("Segoe UI", 9, "bold"))
        style.configure("Value.TLabel", font=("Segoe UI", 11, "bold"))
        style.configure("Status.TLabel", font=("Segoe UI", 9))
        
        # Modern buttons
        style.configure("Modern.TButton", 
                       font=("Segoe UI", 10, "bold"),
                       borderwidth=0,
                       focuscolor='none')
        
        # Card frames
        style.configure("Card.TFrame", relief="flat", borderwidth=1)
        style.configure("Header.TFrame", relief="flat")
    
    def create_modern_ui(self):
        """Create modern UI layout"""
        colors = self.get_theme_colors()
        
        # Main container
        main_container = ttk.Frame(self.window, padding=0)
        main_container.pack(fill="both", expand=True)
        
        # Header
        self.create_modern_header(main_container)
        
        # Content area
        content_frame = ttk.Frame(main_container, padding=(25, 15, 25, 25))
        content_frame.pack(fill="both", expand=True)
        
        # Stats cards
        self.create_stats_cards(content_frame)
        
        # Action buttons
        self.create_action_buttons(content_frame)
        
        # Status footer
        self.create_status_footer(content_frame)
    
    def create_modern_header(self, parent):
        """Create modern header"""
        colors = self.get_theme_colors()
        
        header_frame = ttk.Frame(parent, style="Header.TFrame", padding=(25, 15, 25, 10))
        header_frame.pack(fill="x")
        
        # Left side - Logo and title
        left_frame = ttk.Frame(header_frame)
        left_frame.pack(side="left", fill="x", expand=True)
        
        logo_container = ttk.Frame(left_frame)
        logo_container.pack(side="left")
        
        # Logo with proper sizing
        self.logo_label = ttk.Label(logo_container)
        self.logo_label.pack(side="left", padx=(0, 12))
        
        try:
            logo_path = resource_path("logo.png")
            photo = self.create_logo_image(logo_path, (42, 42))
            if photo:
                self.logo_label.config(image=photo)
                self.logo_label.image = photo
        except Exception as e:
            print(f"Logo error: {e}")
        
        # Title
        title_frame = ttk.Frame(left_frame)
        title_frame.pack(side="left")
        
        self.title_label = ttk.Label(title_frame, 
                               text="Vexo", 
                               style="Title.TLabel",
                               foreground=colors['accent'])
        self.title_label.pack(anchor="w")
        
        self.subtitle_label = ttk.Label(title_frame,
                                  text="DNS Subscription Manager",
                                  style="Subtitle.TLabel",
                                  foreground=colors['text_secondary'])
        self.subtitle_label.pack(anchor="w")
        
        # Right side - Controls
        controls_frame = ttk.Frame(header_frame)
        controls_frame.pack(side="right")
        
        # Add subscription button
        add_btn = ttk.Button(controls_frame,
                            text="➕",
                            width=3,
                            bootstyle="info-outline",
                            cursor="hand2")
        add_btn.pack(side="right", padx=5)
        add_btn.config(command=lambda: manage_subscription_link(self.window, config.current_language))
        
        # Theme toggle
        self.theme_var = tk.BooleanVar()
        theme_toggle = ttk.Checkbutton(controls_frame,
                                      text="🌙",
                                      bootstyle="info-round-toggle",
                                      variable=self.theme_var,
                                      command=self.toggle_theme)
        theme_toggle.pack(side="right", padx=5)
        
        if app_settings.get("theme", "darkly") == "darkly":
            self.theme_var.set(True)
        
        # Language selector
        self.lang_var = tk.StringVar()
        lang_options = {"🇬🇧 EN": "en", "🇮🇷 FA": "fa", "🇷🇺 RU": "ru", "🇨🇳 ZH": "zh"}
        
        lang_combo = ttk.Combobox(controls_frame,
                                 textvariable=self.lang_var,
                                 values=list(lang_options.keys()),
                                 state="readonly",
                                 width=8,
                                 font=("Segoe UI", 9))
        lang_combo.pack(side="right", padx=5)
        
        for name, code in lang_options.items():
            if code == config.current_language:
                self.lang_var.set(name)
        
        def on_language_change(event):
            selected = self.lang_var.get()
            new_lang_code = lang_options[selected]
            
            # مرحله ۱: هم متغیر موقت و هم دیکشنری اصلی را آپدیت کن
            config.current_language = new_lang_code
            config.app_settings['language'] = new_lang_code # <--- این خط کلیدی است
            
            # مرحله ۲: حالا تنظیمات را ذخیره کن
            save_settings()
            self.update_ui_text()
        
        lang_combo.bind("<<ComboboxSelected>>", on_language_change)
        self.lang_options = lang_options
        
        # Separator
        separator = ttk.Separator(parent, orient="horizontal")
        separator.pack(fill="x", pady=(0, 0))
    
    def create_stats_cards(self, parent):
        """Create stats display"""
        colors = self.get_theme_colors()
        
        cards_container = ttk.Frame(parent)
        cards_container.pack(fill="x", pady=(0, 15))
        
        # Main info card
        main_card = ttk.Frame(cards_container, style="Card.TFrame", padding=18)
        main_card.pack(fill="x", pady=(0, 10))
        
        info_items = [
            ("username", "👤 Username", colors['text_secondary']),
            ("status", "📊 Status", colors['text_secondary']),
            ("time", "⏱️ Time Left", colors['text_secondary']),
            ("volume", "💾 Volume Left", colors['text_secondary']),
            ("ip", "🌐 IP Address", colors['text_secondary'])
        ]
        
        for idx, (key, label_text, color) in enumerate(info_items):
            item_frame = ttk.Frame(main_card)
            item_frame.grid(row=idx, column=0, columnspan=3, sticky="ew", pady=6)
            main_card.grid_rowconfigure(idx, weight=1)
            
            header_label = ttk.Label(item_frame,
                                    text=label_text,
                                    style="Header.TLabel",
                                    foreground=color)
            header_label.pack(side="left")
            
            value_label = ttk.Label(item_frame,
                                   text="...",
                                   style="Value.TLabel",
                                   foreground=colors['accent'])
            value_label.pack(side="right")
            
            self.labels[f"{key}_header"] = header_label
            self.labels[key] = value_label
        
        main_card.grid_columnconfigure(0, weight=1)
    
    def create_action_buttons(self, parent):
        """Create action buttons"""
        buttons_frame = ttk.Frame(parent)
        buttons_frame.pack(fill="x", pady=(0, 15))
        
        # Fetch button
        self.fetch_button = ttk.Button(buttons_frame,
                                      text="🔄 Check Subscription",
                                      bootstyle="success",
                                      style="Modern.TButton")
        self.fetch_button.pack(fill="x", ipady=10)
        
        # DNS toggle button
        self.dns_toggle_button = ttk.Button(buttons_frame,
                                           text="🛡️ Connect DNS",
                                           bootstyle="info-outline",
                                           style="Modern.TButton")
        self.dns_toggle_button.pack(fill="x", pady=(8, 0), ipady=10)
    
    def create_status_footer(self, parent):
        """Create status footer"""
        colors = self.get_theme_colors()
        
        footer_frame = ttk.Frame(parent, padding=(0, 8, 0, 0))
        footer_frame.pack(fill="x", side="top", pady=(15, 0))
        
        self.labels['status_bar'] = ttk.Label(footer_frame,
                                             text="",
                                             style="Status.TLabel",
                                             foreground=colors['text_secondary'],
                                             anchor="center")
        self.labels['status_bar'].pack(fill="x", pady=4)
        
        self.labels['timer_label'] = ttk.Label(footer_frame,
                                              text="",
                                              font=("Segoe UI", 11, "bold"),
                                              foreground=colors['danger'],
                                              anchor="center")
    
    def toggle_theme(self):
        """Toggle theme and MAINTAIN window size"""
        # Save current geometry
        current_geometry = self.window.geometry()
        
        if self.theme_var.get():
            self.window.style.theme_use('darkly')
            app_settings["theme"] = "darkly"
        else:
            self.window.style.theme_use('flatly')
            app_settings["theme"] = "flatly"
        
        save_settings()
        
        # Restore window size after theme change
        self.window.geometry(current_geometry)
        
        # Update colors for all elements
        self.update_theme_colors()
    
    def update_theme_colors(self):
        """Update all colors when theme changes"""
        colors = self.get_theme_colors()
        
        # Update title colors
        self.title_label.config(foreground=colors['accent'])
        self.subtitle_label.config(foreground=colors['text_secondary'])
        
        # Update header labels
        for key in ['username', 'status', 'time', 'volume', 'ip']:
            if f"{key}_header" in self.labels:
                self.labels[f"{key}_header"].config(foreground=colors['text_secondary'])
            if key in self.labels:
                # Re-apply proper color based on current data
                if key == 'status' and config.last_fetched_data:
                    status_key = config.last_fetched_data.get('status_key')
                    if status_key == 'table_status_active':
                        self.labels[key].config(foreground=colors['success'])
                    elif status_key == 'table_status_expired':
                        self.labels[key].config(foreground=colors['danger'])
                    elif status_key in ['sub_status_disabled', 'limited']:
                        self.labels[key].config(foreground=colors['warning'])
                else:
                    self.labels[key].config(foreground=colors['accent'])
        
        # Update status bar
        self.labels['status_bar'].config(foreground=colors['text_secondary'])
        self.labels['timer_label'].config(foreground=colors['danger'])
    
    def setup_event_handlers(self):
        """Setup event handlers"""
        self.fetch_button.config(command=self.on_fetch_click)
        self.dns_toggle_button.config(command=self.on_dns_toggle_click)
        self.window.protocol("WM_DELETE_WINDOW", self.on_window_close)
    
    def update_ui_text(self):
        """Update UI text"""
        lang_code = config.current_language
        colors = self.get_theme_colors()
        
        self.window.title(TRANSLATIONS[lang_code]["window_title"])
        self.fetch_button.config(text=f"🔄 {TRANSLATIONS[lang_code]['fetch_button']}")
        
        labels_map = {
            "username": "👤 " + TRANSLATIONS[lang_code]["username_header"],
            "status": "📊 " + TRANSLATIONS[lang_code]["status_header"],
            "time": "⏱️ " + TRANSLATIONS[lang_code]["time_header"],
            "volume": "💾 " + TRANSLATIONS[lang_code]["volume_header"],
            "ip": "🌐 " + TRANSLATIONS[lang_code]["ip_header"]
        }
        
        for key, text in labels_map.items():
            if f"{key}_header" in self.labels:
                self.labels[f"{key}_header"].config(text=text)
        
        if config.last_fetched_data:
            retranslate_results_data(self.labels, config.last_fetched_data, lang_code, colors)

        if config.active_timer_id:
            wait_message = TRANSLATIONS[lang_code]["ip_wait_notice"]
            self.labels['status_bar'].config(text=wait_message)
        
        self.update_dns_button_status_ui_only(self.is_dns_connected, lang_code)
    
    def update_dns_button_status_ui_only(self, status, lang_code):
        """Update DNS button"""
        if not self.dns_toggle_button.winfo_exists():
            return
        
        if status:
            text = f"✅ {TRANSLATIONS[lang_code].get('disconnect_dns_button', 'Disconnect DNS')}"
            style = "success"
        else:
            text = f"🛡️ {TRANSLATIONS[lang_code]['connect_dns_button']}"
            style = "info-outline"
        
        self.dns_toggle_button.config(text=text, bootstyle=style)
        
        if not (config.last_fetched_data and config.last_fetched_data.get('dou_ip1')):
            self.dns_toggle_button.config(state="disabled")
        else:
            self.dns_toggle_button.config(state="normal")
    
    def update_dns_button_status(self):
        """Monitor DNS status"""
        if self.is_operation_in_progress:
            self.window.after(1000, self.update_dns_button_status)
            return
        
        def background_check():
            target_dns = config.last_fetched_data.get('dou_ip1') if config.last_fetched_data else None
            status = check_dns_status(target_dns)
            self.window.after(0, update_ui_on_main_thread, status)
        
        def update_ui_on_main_thread(status):
            self.is_dns_connected = status
            self.update_dns_button_status_ui_only(status, config.current_language)
            self.window.after(3000, self.update_dns_button_status)
        
        threading.Thread(target=background_check, daemon=True).start()
    
    def on_dns_toggle_click(self):
        """Toggle DNS"""
        if self.is_dns_connected:
            self.on_dns_unset_click()
        else:
            self.on_dns_connect_click()
    
    def on_dns_connect_click(self):
        """
        Refreshes subscription data first, then connects DNS if the subscription is active.
        """
        if not self.is_dns_connected:
            threading.Thread(target=update_ip_check_hosts, daemon=True).start()        
        if self.is_operation_in_progress:
            return

        lang_code = config.current_language
        self.dns_toggle_button.config(
            state="disabled",
            text=f"⏳ {TRANSLATIONS[lang_code]['checking_status_before_dns']}" # نیاز به کلید ترجمه جدید
        )
        self.is_operation_in_progress = True

        # Define the function that will run ONLY if the data fetch is successful
        def _proceed_with_dns_connection():
            status = config.last_fetched_data.get('status_key')
            
            # Check if subscription is active
            if status == 'table_status_active':
                # Original DNS connection logic starts here
                dns_ip1 = config.last_fetched_data.get('dou_ip1')
                dns_ip2 = config.last_fetched_data.get('dou_ip2')
                
                def background_task():
                    return set_dns(dns_ip1, dns_ip2)

                def handle_result(result):
                    if result["success"]:
                        messagebox.showinfo(
                            TRANSLATIONS[lang_code]["dns_set_success_title"],
                            TRANSLATIONS[lang_code]["dns_set_success_message"].format(dns_ip=result["dns_ip"])
                        )
                        self.is_dns_connected = True
                    else:
                        messagebox.showerror(
                            TRANSLATIONS[lang_code]["error_title"],
                            TRANSLATIONS[lang_code].get(result["error_key"])
                        )
                        self.is_dns_connected = False
                    
                    self.is_operation_in_progress = False
                    self.update_dns_button_status_ui_only(self.is_dns_connected, lang_code)

                threading.Thread(
                    target=lambda: self.window.after(0, handle_result, background_task()),
                    daemon=True
                ).start()
            else:
                # If subscription is not active, show a warning
                messagebox.showwarning(
                    TRANSLATIONS[lang_code]["warning_title"],
                    TRANSLATIONS[lang_code]["dns_connect_denied_status"]
                )
                self.is_operation_in_progress = False
                self.update_dns_button_status_ui_only(self.is_dns_connected, lang_code)

        # Start the process by fetching the latest data
        self._execute_fetch(on_success_callback=_proceed_with_dns_connection)
    
    def on_dns_unset_click(self):
        """Disconnect DNS"""
        if self.is_operation_in_progress:
            return
        
        self.is_operation_in_progress = True
        lang_code = config.current_language
        
        self.dns_toggle_button.config(
            state="disabled",
            text=f"⏳ {TRANSLATIONS[lang_code]['unset_dns_button_loading']}"
        )
        
        def background_task():
            return unset_dns()
        
        def handle_result(result):
            if result["success"]:
                messagebox.showinfo(
                    TRANSLATIONS[lang_code]["dns_unset_success_title"],
                    TRANSLATIONS[lang_code]["dns_unset_success_message"]
                )
                self.is_dns_connected = False
                text = f"🛡️ {TRANSLATIONS[lang_code]['connect_dns_button']}"
                style = "info-outline"
            else:
                messagebox.showerror(
                    TRANSLATIONS[lang_code]["error_title"],
                    TRANSLATIONS[lang_code].get(result["error_key"])
                )
                self.is_dns_connected = True
                text = f"✅ {TRANSLATIONS[lang_code].get('disconnect_dns_button', 'Disconnect DNS')}"
                style = "success"
            
            self.dns_toggle_button.config(text=text, bootstyle=style, state="normal")
            self.is_operation_in_progress = False
        
        threading.Thread(
            target=lambda: self.window.after(0, handle_result, background_task()),
            daemon=True
        ).start()
    
    def on_fetch_click(self):
        """Fetch data"""
        self._execute_fetch()

    def _execute_fetch(self, on_success_callback=None):
        """
        Core logic to fetch subscription data.
        Optionally executes a callback function upon successful data retrieval.
        """
        if not self.is_dns_connected:
            threading.Thread(target=update_ip_check_hosts, daemon=True).start()        
        url = app_settings.get("last_used_url", "").strip()
        if not url:
            messagebox.showwarning(
                TRANSLATIONS[config.current_language]["warning_title"],
                TRANSLATIONS[config.current_language]["warning_add_link_first"]
            )
            manage_subscription_link(self.window, config.current_language)
            return

        colors = self.get_theme_colors()

        self.fetch_button.config(
            state="disabled",
            text=f"⏳ {TRANSLATIONS[config.current_language]['fetch_button_loading']}"
        )
        self.labels['status_bar'].config(
            text=TRANSLATIONS[config.current_language]["connecting_status"],
            foreground=colors['warning']
        )

        for key in ['username', 'status', 'time', 'volume', 'ip']:
            self.labels[key].config(text="...")

        fetch_id = time.time()
        config.active_fetch_id = fetch_id

        def background_task():
            result = process_all_data(url, config.current_language)
            # Pass the callback to the UI update function
            self.window.after(0, self.update_ui, result, config.current_language, fetch_id, on_success_callback)

        config.watchdog_timer_id = self.window.after(20000, lambda: self.on_fetch_timeout(fetch_id))

        thread = threading.Thread(target=background_task)
        thread.daemon = True
        thread.start()
    
    def on_fetch_timeout(self, fetch_id):
        """Handle timeout"""
        if fetch_id == config.active_fetch_id:
            config.active_fetch_id = None
            self.fetch_button.config(
                state="normal",
                text=f"🔄 {TRANSLATIONS[config.current_language]['fetch_button']}"
            )
            self.labels['status_bar'].config(text="")
            messagebox.showerror(
                TRANSLATIONS[config.current_language]["error_title"],
                TRANSLATIONS[config.current_language]["error_timeout"]
            )
    
    def update_ui(self, result, lang_code, fetch_id, on_success_callback=None):
        """Update UI with data"""
        if fetch_id != config.active_fetch_id:
            return
        
        if config.watchdog_timer_id:
            self.window.after_cancel(config.watchdog_timer_id)
            config.watchdog_timer_id = None
        
        config.active_fetch_id = None
        colors = self.get_theme_colors()
        
        try:
            if not result["success"]:
                self.labels['timer_label'].pack_forget()
                messagebox.showerror(TRANSLATIONS[lang_code]["error_title"], result["error"])
                config.last_fetched_data = None
            else:
                config.last_fetched_data = result["sub_data"]
                data = result["sub_data"]
                
                # Status with proper colors
                status_map = {
                    'table_status_active': (TRANSLATIONS[lang_code]["status_active"], colors['success']),
                    'sub_status_disabled': (TRANSLATIONS[lang_code]["status_disabled"], colors['warning']),
                    'limited': (TRANSLATIONS[lang_code]["status_limited"], colors['warning']),
                    'table_status_expired': (TRANSLATIONS[lang_code]["status_expired"], colors['danger'])
                }
                
                status_key = data.get('status_key')
                status_text, status_color = status_map.get(status_key, (status_key, colors['text_secondary']))
                
                # Time
                if data.get('is_unlimited_time'):
                    remaining_time = TRANSLATIONS[lang_code]["unlimited"]
                else:
                    days = data.get('remaining_days', 0)
                    hours = data.get('remaining_hours', 0)
                    remaining_time = TRANSLATIONS[lang_code]["time_format"].format(days=days, hours=hours)
                
                # Volume
                if data.get('is_unlimited_volume'):
                    remaining_volume = TRANSLATIONS[lang_code]["unlimited"]
                else:
                    allowed_gb = data.get('allowed_volume_gb') or 0
                    used_gb = data.get('used_volume_gb', 0)
                    remaining_gb = max(0, allowed_gb - used_gb)
                    remaining_volume = f"{remaining_gb:.2f} GB"
                
                # Update labels
                self.labels['username'].config(text=data.get('username', "..."), foreground=colors['accent'])
                self.labels['status'].config(text=status_text, foreground=status_color)
                self.labels['time'].config(text=remaining_time, foreground=colors['accent'])
                self.labels['volume'].config(text=remaining_volume, foreground=colors['accent'])
                self.labels['ip'].config(text=data.get('last_ip') or "N/A", foreground=colors['accent'])
                
                # IP status
                ip_status = result.get("ip_status")
                if ip_status:
                    if ip_status.get("key") == "ip_changed_from_to":
                        wait_message = TRANSLATIONS[lang_code]["ip_wait_notice"]
                        self.labels['status_bar'].config(text=wait_message, foreground=colors['warning'])
                        
                        if config.active_timer_id:
                            self.window.after_cancel(config.active_timer_id)
                        
                        start_countdown(60, self.labels['timer_label'], 
                                      self.labels['status_bar'], self.window)
                    else:
                        if not config.active_timer_id:
                            self.labels['timer_label'].pack_forget()
                        
                        message = TRANSLATIONS[lang_code][ip_status["key"]].format(
                            **ip_status.get("params", {})
                        )
                        style_key = ip_status.get("style", "success")
                        color = colors.get(style_key, colors['success'])
                        self.labels['status_bar'].config(text=message, foreground=color)
                else:
                    self.labels['timer_label'].pack_forget()
                    self.labels['status_bar'].config(
                        text=TRANSLATIONS[lang_code]["success_status"],
                        foreground=colors['success']
                    )
                
                app_settings["last_fetched_data"] = config.last_fetched_data
                save_settings()
                if on_success_callback:
                    on_success_callback()                
        
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"--- CRASH ---\n{error_details}")
            messagebox.showerror("Error", f"An error occurred:\n\n{error_details}")
        finally:
            self.fetch_button.config(
                state="normal",
                text=f"🔄 {TRANSLATIONS[lang_code]['fetch_button']}"
            )
    
    def on_window_close(self):
        """Handle close"""
        lang_code = config.current_language
        title = TRANSLATIONS[lang_code]["exit_confirm_title"]
        
        if self.is_dns_connected:
            message = TRANSLATIONS[lang_code]["exit_confirm_dns_set"]
            if messagebox.askyesno(title, message):
                unset_dns_synchronously()
                self.window.destroy()
        else:
            message = TRANSLATIONS[lang_code]["exit_confirm_no_dns"]
            if messagebox.askyesno(title, message):
                self.window.destroy()
    
    def run(self):
        """Run application"""
        import sys
        
        self.update_ui_text()
        
        if "--set-dns" in sys.argv:
            self.on_dns_connect_click()
        elif "--unset-dns" in sys.argv:
            self.on_dns_unset_click()
        
        self.update_dns_button_status()
        self.window.mainloop()