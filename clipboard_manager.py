import os
import sys
import time
import datetime
import json
import socket
import threading
import subprocess
import tkinter
from tkinter import messagebox
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from ttkbootstrap.widgets.scrolled import ScrolledFrame
import logging

# Setup logging
logging.basicConfig(
    filename='clipboard.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Port for local IPC hotkey messaging and single-instance check
IPC_PORT = 50099

try:
    import pystray
    from PIL import Image, ImageDraw
    HAS_TRAY = True
except ImportError:
    HAS_TRAY = False

try:
    from plyer import notification
    HAS_PLYER = True
except ImportError:
    HAS_PLYER = False

class ClipboardManager(tb.Window):
    CONFIG_FILE = 'clipboard_settings.json'
    HISTORY_FILE = 'clipboard_history.json'

    def __init__(self, start_popup=False):
        super().__init__(themename="darkly")

        self.last_clipboard_text = ""
        self.history = []
        self.polling_active = True
        self.ipc_server_socket = None

        # Configuration variables
        self.max_history = tkinter.IntVar(value=50)
        self.auto_paste = tkinter.BooleanVar(value=True)
        self.autostart_enabled = tkinter.BooleanVar(value=False)
        self.current_theme = tkinter.StringVar(value="darkly")
        self.search_query = tkinter.StringVar()

        self.load_settings()
        self.load_history()

        # Apply correct theme
        self.style.theme_use(self.current_theme.get())

        # Setup GUI structure
        self.title("Clipboard History")
        self.geometry("380x550")
        self.resizable(False, False)

        # Track window visibility state
        self.is_visible = True

        self.create_widgets()
        
        # Start clipboard polling safely
        self.after(500, self.poll_clipboard)

        # Startup Window state
        if start_popup:
            self.position_at_mouse()
            self.show_window()
        else:
            if HAS_TRAY and self.autostart_enabled.get():
                # Started via boot, hide directly to system tray
                self.after(10, self.hide_window)
            else:
                self.show_window()

        # Handle window closing protocol
        if HAS_TRAY:
            self.protocol('WM_DELETE_WINDOW', self.hide_window)
            self.setup_tray()
        else:
            self.protocol('WM_DELETE_WINDOW', self.quit_app)

    def create_widgets(self):
        # Notebook for Tabs
        self.notebook = tb.Notebook(self, bootstyle=PRIMARY)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=10)

        self.main_tab = tb.Frame(self.notebook)
        self.settings_tab = tb.Frame(self.notebook)

        self.notebook.add(self.main_tab, text='History')
        self.notebook.add(self.settings_tab, text='Settings')

        # --- MAIN TAB ---
        # Search Frame
        search_frame = tb.Frame(self.main_tab)
        search_frame.pack(fill='x', padx=10, pady=(10, 5))

        self.search_entry = tb.Entry(
            search_frame, 
            textvariable=self.search_query, 
            bootstyle=PRIMARY
        )
        self.search_entry.pack(side='left', expand=True, fill='x')
        self.search_query.trace_add("write", self.filter_history)

        tb.Button(
            search_frame, 
            text="✕", 
            command=self.clear_search, 
            bootstyle=SECONDARY, 
            width=3
        ).pack(side='left', padx=(5, 0))

        # Action bar
        action_frame = tb.Frame(self.main_tab)
        action_frame.pack(fill='x', padx=10, pady=5)

        tb.Checkbutton(
            action_frame, 
            text="Auto-Paste on Click", 
            variable=self.auto_paste, 
            command=self.save_settings,
            bootstyle="round-toggle"
        ).pack(side='left', pady=5)

        tb.Button(
            action_frame, 
            text="Clear All", 
            command=self.clear_all_history, 
            bootstyle="danger-outline-sm"
        ).pack(side='right', pady=5)

        # Scrolled Frame for List
        self.list_container = ScrolledFrame(self.main_tab, bootstyle="light")
        self.list_container.pack(expand=True, fill='both', padx=10, pady=(5, 10))

        # Initialize history list UI
        self.rebuild_history_list()

        # --- SETTINGS TAB ---
        settings_container = tb.Frame(self.settings_tab)
        settings_container.pack(fill='both', expand=True, padx=15, pady=15)

        # Theme Selection
        tb.Label(settings_container, text='Theme:').grid(row=0, column=0, sticky='w', pady=10)
        theme_combo = tb.Combobox(
            settings_container, 
            values=self.style.theme_names(), 
            textvariable=self.current_theme, 
            state='readonly', 
            bootstyle=SECONDARY
        )
        theme_combo.grid(row=0, column=1, sticky='ew', padx=(15, 0), pady=10)
        theme_combo.bind('<<ComboboxSelected>>', self.change_theme)

        # Max History Limit
        tb.Label(settings_container, text='Max History Limit:').grid(row=1, column=0, sticky='w', pady=10)
        max_entry = tb.Entry(settings_container, textvariable=self.max_history, bootstyle=PRIMARY)
        max_entry.grid(row=1, column=1, sticky='ew', padx=(15, 0), pady=10)
        max_entry.bind('<FocusOut>', lambda e: self.save_settings())

        # Run on Startup Toggle
        tb.Label(settings_container, text='Run on Startup:').grid(row=2, column=0, sticky='w', pady=10)
        startup_chk = tb.Checkbutton(
            settings_container, 
            text="", 
            variable=self.autostart_enabled, 
            command=self.toggle_autostart, 
            bootstyle="round-toggle"
        )
        startup_chk.grid(row=2, column=1, sticky='w', padx=(15, 0), pady=10)

        # Informational Panel
        info_frame = tb.Labelframe(settings_container, text="Keyboard Shortcut Guide", padding=10)
        info_frame.grid(row=3, column=0, columnspan=2, sticky='nsew', pady=(20, 10))

        guide_text = (
            "Bind a custom system hotkey (e.g., Ctrl+Alt+V) to run:\n\n"
            "  python3 clipboard_manager.py\n\n"
            "This communicates with the running instance to pop up "
            "the history list instantly at your cursor location!"
        )
        tb.Label(info_frame, text=guide_text, justify=LEFT, font=('Helvetica', 9)).pack()

    def change_theme(self, event=None):
        self.style.theme_use(self.current_theme.get())
        self.save_settings()

    def clear_search(self):
        self.search_query.set("")
        self.rebuild_history_list()

    def clear_all_history(self):
        if messagebox.askyesno("Confirm", "Are you sure you want to clear your clipboard history?"):
            self.history = []
            self.save_history()
            self.rebuild_history_list()

    def delete_history_item(self, idx):
        if 0 <= idx < len(self.history):
            del self.history[idx]
            self.save_history()
            self.rebuild_history_list(self.search_query.get())

    def copy_item_to_clipboard(self, text, auto_paste_trigger=False):
        # Update last copied tracking to avoid infinite loop addition
        self.last_clipboard_text = text
        self.clipboard_clear()
        self.clipboard_append(text)
        self.update() # Flush clipboard contents to system
        
        logging.info("Item copied to clipboard manually")

        # Move item to top of history
        if text in self.history:
            self.history.remove(text)
        self.history.insert(0, text)
        self.save_history()

        if auto_paste_trigger and self.auto_paste.get():
            self.hide_window()
            # Asynchronous delay to let the window lose focus before pasting
            self.after(150, self.simulate_paste)
        else:
            self.rebuild_history_list(self.search_query.get())

    def simulate_paste(self):
        platform = sys.platform
        logging.info(f"Attempting auto-paste on platform: {platform}")
        try:
            if platform == 'win32':
                import ctypes
                # Simulate Ctrl+V keyboard inputs
                ctypes.windll.user32.keybd_event(0x11, 0, 0, 0)      # Ctrl Down
                ctypes.windll.user32.keybd_event(0x56, 0, 0, 0)      # V Down
                ctypes.windll.user32.keybd_event(0x56, 0, 0x0002, 0) # V Up
                ctypes.windll.user32.keybd_event(0x11, 0, 0x0002, 0) # Ctrl Up
            elif platform == 'darwin':
                # AppleScript simulating Command+V
                subprocess.run([
                    "osascript", 
                    "-e", 
                    'tell application "System Events" to keystroke "v" using command down'
                ])
            else:  # Linux
                # Check for xdotool
                try:
                    subprocess.run(["xdotool", "key", "ctrl+v"], check=True)
                except (subprocess.CalledProcessError, FileNotFoundError):
                    logging.warning("xdotool not found or failed, standard copy complete. Auto-paste requires 'xdotool' on Linux X11.")
        except Exception as e:
            logging.error(f"Error simulating keypress paste: {e}")

    def on_card_hover(self, frame, is_hovered):
        # Subtle hover styling for item cards
        if is_hovered:
            frame.configure(bootstyle=DARK)
        else:
            frame.configure(bootstyle=SECONDARY)

    def rebuild_history_list(self, filter_query=""):
        # Clear existing cards in list
        for widget in self.list_container.winfo_children():
            widget.destroy()

        filter_query = filter_query.lower()
        items_displayed = 0

        for i, text in enumerate(self.history):
            if filter_query and filter_query not in text.lower():
                continue

            # Card structure
            card = tb.Frame(self.list_container, bootstyle=SECONDARY, padding=8)
            card.pack(fill='x', pady=4, padx=5)

            # Keep bindings safe
            card.bind("<Enter>", lambda e, c=card: self.on_card_hover(c, True))
            card.bind("<Leave>", lambda e, c=card: self.on_card_hover(c, False))

            # Header Frame
            header = tb.Frame(card)
            header.pack(fill='x')

            # Truncated display and text stats
            char_count = len(text)
            char_label = tb.Label(header, text=f"📋 {char_count} chars", font=('Helvetica', 8), bootstyle="muted")
            char_label.pack(side='left')

            # Actions Frame
            actions = tb.Frame(header)
            actions.pack(side='right')

            # Use direct text buttons to prevent custom asset missing warnings
            btn_copy = tb.Button(
                actions, 
                text="Copy", 
                command=lambda t=text: self.copy_item_to_clipboard(t, auto_paste_trigger=True),
                bootstyle="success-sm"
            )
            btn_copy.pack(side='left', padx=2)

            btn_del = tb.Button(
                actions, 
                text="✕", 
                command=lambda idx=i: self.delete_history_item(idx),
                bootstyle="danger-sm"
            )
            btn_del.pack(side='left', padx=2)

            # Preview content
            preview_text = text.replace('\n', ' ')
            if len(preview_text) > 85:
                preview_text = preview_text[:82] + "..."

            # Main preview label
            lbl_preview = tb.Label(
                card, 
                text=preview_text, 
                font=('Helvetica', 9), 
                justify=LEFT, 
                wraplength=330,
                bootstyle=LIGHT
            )
            lbl_preview.pack(fill='x', pady=(5, 0), anchor='w')

            # Make clicking anywhere on the card select/copy it
            lbl_preview.bind("<Button-1>", lambda e, t=text: self.copy_item_to_clipboard(t, auto_paste_trigger=True))
            card.bind("<Button-1>", lambda e, t=text: self.copy_item_to_clipboard(t, auto_paste_trigger=True))

            items_displayed += 1
            if items_displayed >= self.max_history.get():
                break

        if items_displayed == 0:
            lbl_empty = tb.Label(
                self.list_container, 
                text="No clipboard items matches.", 
                font=('Helvetica', 10), 
                bootstyle="muted"
            )
            lbl_empty.pack(pady=20)

    def filter_history(self, *args):
        self.rebuild_history_list(self.search_query.get())

    def poll_clipboard(self):
        if not self.polling_active:
            return

        try:
            current_text = self.clipboard_get()
        except tkinter.TclError:
            current_text = None

        if current_text and current_text != self.last_clipboard_text:
            self.last_clipboard_text = current_text
            
            # Clean duplicate item if already present, and push to front
            if current_text in self.history:
                self.history.remove(current_text)
            self.history.insert(0, current_text)

            # Maintain max limit
            max_limit = self.max_history.get()
            if len(self.history) > max_limit:
                self.history = self.history[:max_limit]

            self.save_history()
            self.rebuild_history_list(self.search_query.get())
            logging.info("New clipboard item added from polling")

        self.after(500, self.poll_clipboard)

    def position_at_mouse(self):
        # Center or display popup at the mouse pointer location safely
        try:
            pointer_x, pointer_y = self.winfo_pointerxy()
            screen_w = self.winfo_screenwidth()
            screen_h = self.winfo_screenheight()

            # Window dimensions
            w, h = 380, 550

            # Keep window bounds fully on the screen
            x = max(10, min(pointer_x - 100, screen_w - w - 10))
            y = max(10, min(pointer_y - 20, screen_h - h - 40))

            self.geometry(f"{w}x{h}+{x}+{y}")
        except Exception as e:
            # Fallback to center
            self.geometry("380x550")
            logging.error(f"Error positioning window at mouse coordinates: {e}")

    def hide_window(self):
        self.withdraw()
        self.is_visible = False

    def show_window(self, icon=None, item=None):
        self.deiconify()
        self.lift()
        self.focus_force()
        self.is_visible = True
        self.search_entry.focus()

    def create_tray_image(self):
        # Dynamic creation of a beautiful blue tray icon
        image = Image.new('RGB', (64, 64), color='white')
        dc = ImageDraw.Draw(image)
        # Blue gradient base representing standard clipboard color
        dc.rectangle((16, 16, 48, 48), fill='#0275d8') 
        # Clipboard shape lines
        dc.rectangle((24, 12, 40, 20), fill='#f0ad4e')
        return image

    def setup_tray(self):
        menu = pystray.Menu(
            pystray.MenuItem('Show History', self.show_window, default=True),
            pystray.MenuItem('Quit', self.quit_app)
        )
        self.icon = pystray.Icon("clipboard_manager", self.create_tray_image(), "Clipboard History", menu)
        threading.Thread(target=self.icon.run, daemon=True).start()

    def load_settings(self):
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    if 'max_history' in data: self.max_history.set(data['max_history'])
                    if 'auto_paste' in data: self.auto_paste.set(data['auto_paste'])
                    if 'theme' in data: self.current_theme.set(data['theme'])
                    if 'autostart' in data:
                        self.autostart_enabled.set(data['autostart'])
            except Exception as e:
                print("Failed to load settings:", e)

    def save_settings(self):
        try:
            data = {
                'max_history': self.max_history.get(),
                'auto_paste': self.auto_paste.get(),
                'theme': self.current_theme.get(),
                'autostart': self.autostart_enabled.get()
            }
            with open(self.CONFIG_FILE, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            print("Failed to save settings:", e)

    def load_history(self):
        if os.path.exists(self.HISTORY_FILE):
            try:
                with open(self.HISTORY_FILE, 'r') as f:
                    self.history = json.load(f)
            except Exception as e:
                logging.error(f"Failed to load history list: {e}")
                self.history = []

    def save_history(self):
        try:
            with open(self.HISTORY_FILE, 'w') as f:
                json.dump(self.history, f)
        except Exception as e:
            logging.error(f"Failed to save history list: {e}")

    def toggle_autostart(self):
        self.save_settings()
        enable = self.autostart_enabled.get()
        platform = sys.platform
        script_path = os.path.abspath(sys.argv[0])
        
        try:
            if platform == 'win32':
                startup_dir = os.path.join(os.getenv('APPDATA', ''), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
                if not startup_dir: return
                bat_path = os.path.join(startup_dir, 'clipboard_manager.bat')
                if enable:
                    with open(bat_path, 'w') as f:
                        f.write(f'@echo off\npythonw "{script_path}"')
                else:
                    if os.path.exists(bat_path): os.remove(bat_path)
            elif platform == 'darwin':
                plist_dir = os.path.expanduser('~/Library/LaunchAgents')
                os.makedirs(plist_dir, exist_ok=True)
                plist_path = os.path.join(plist_dir, 'com.user.clipboardmanager.plist')
                if enable:
                    plist_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.clipboardmanager</string>
    <key>ProgramArguments</key>
    <array>
        <string>python3</string>
        <string>{script_path}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>'''
                    with open(plist_path, 'w') as f:
                        f.write(plist_content)
                else:
                    if os.path.exists(plist_path): os.remove(plist_path)
            else: # Linux
                autostart_dir = os.path.expanduser('~/.config/autostart')
                os.makedirs(autostart_dir, exist_ok=True)
                desktop_path = os.path.join(autostart_dir, 'clipboard_manager.desktop')
                if enable:
                    desktop_content = f'''[Desktop Entry]
Type=Application
Name=Clipboard Manager
Exec=python3 "{script_path}"
Terminal=false
'''
                    with open(desktop_path, 'w') as f:
                        f.write(desktop_content)
                else:
                    if os.path.exists(desktop_path): os.remove(desktop_path)
        except Exception as e:
            print("Failed to toggle autostart:", e)

    def quit_app(self, icon=None, item=None):
        self.polling_active = False
        self.save_settings()
        self.save_history()
        
        # Shut down IPC socket server if running
        if self.ipc_server_socket:
            try:
                self.ipc_server_socket.close()
            except:
                pass

        if HAS_TRAY and hasattr(self, 'icon'):
            self.icon.stop()
            
        self.after(0, self.destroy)

def ipc_listener_thread(app, server_socket):
    while app.polling_active:
        try:
            conn, addr = server_socket.accept()
            data = conn.recv(1024).decode('utf-8')
            if data:
                logging.info(f"IPC command received: {data}")
                if data == "show":
                    app.after(0, lambda: app.position_at_mouse())
                    app.after(0, lambda: app.show_window())
                elif data.startswith("popup:"):
                    try:
                        coords = data.split(":")[1].split(",")
                        x, y = int(coords[0]), int(coords[1])
                        # Directly position at hotkey trigger pointer
                        app.after(0, lambda: app.geometry(f"+{x}+{y}"))
                        app.after(0, lambda: app.position_at_mouse())
                        app.after(0, lambda: app.show_window())
                    except Exception as e:
                        logging.error(f"Failed parsing coordinate popup message: {e}")
                        app.after(0, lambda: app.position_at_mouse())
                        app.after(0, lambda: app.show_window())
            conn.close()
        except socket.error:
            break

def check_single_instance_and_ipc(app_class):
    # Attempt to grab mouse pointer coordinates using brief Tkinter root
    try:
        temp = tkinter.Tk()
        temp.withdraw()
        mouse_x, mouse_y = temp.winfo_pointerxy()
        temp.destroy()
    except:
        mouse_x, mouse_y = 0, 0

    try:
        # Connect to existing server socket
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(1.0)
        client.connect(('127.0.0.1', IPC_PORT))
        # Send current mouse coordinates to display popup near cursor
        client.sendall(f"popup:{mouse_x},{mouse_y}".encode('utf-8'))
        client.close()
        logging.info("Secondary instance notified primary instance. Exiting.")
        sys.exit(0)
    except socket.error:
        # Binding is free; start server socket listener
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind(('127.0.0.1', IPC_PORT))
            server_socket.listen(5)
            
            # Start master GUI application
            app = app_class(start_popup=True)
            app.ipc_server_socket = server_socket
            
            # Daemon thread to handle IPC show signals
            threading.Thread(
                target=ipc_listener_thread, 
                args=(app, server_socket), 
                daemon=True
            ).start()
            
            app.mainloop()
        except Exception as e:
            logging.critical(f"Server socket start failed: {e}")
            sys.exit(1)

if __name__ == '__main__':
    check_single_instance_and_ipc(ClipboardManager)
