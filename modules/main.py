# main.py
import sys
import ctypes
from tkinter import messagebox

from dns_manager import is_admin, get_main_executable_path
from gui import ModernVexoChecker  # تغییر: gui_modern به gui

def main():
    """Main entry point"""
    if not is_admin():
        try:
            executable_path = get_main_executable_path()
            ret_code = ctypes.windll.shell32.ShellExecuteW(
                None, "runas", executable_path, None, None, 1
            )
            if ret_code <= 32:
                pass
        except Exception as e:
            messagebox.showerror("Startup Error", f"Failed to elevate privileges: {e}")
        finally:
            sys.exit()
    
    app = ModernVexoChecker()
    app.create_window()
    app.run()

if __name__ == "__main__":
    main()