import os
import tkinter
from tkinter import ttk, messagebox
import time
import datetime
import sys
import threading
import json

try:
    import win32api
    HAS_WIN32API = True
except ImportError:
    HAS_WIN32API = False

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

class App(tkinter.Tk):
    CONFIG_FILE = 'settings.json'

    def __init__(self):
        super().__init__()

        self.running = False
        self.timer_id = None

        # Configuration Variables
        self.triggers = ('countdown', 'instant', 'timedate')
        self.current_trigger = tkinter.StringVar(value=self.triggers[0])
        
        self.exe_methods = ('shut down', 'restart', 'sleep')
        self.function_type = tkinter.StringVar(value=self.exe_methods[0])
        
        self.countdown_minutes = tkinter.IntVar(value=10)
        self.target_time_str = tkinter.StringVar(value='00:00')
        self.autostart_enabled = tkinter.BooleanVar(value=False)

        # Internal state
        self.remaining_seconds = 0
        self.total_seconds = 0

        self.load_preferences()

        # UI Setup
        self.title('Calculated Turn Off')
        self.geometry('400x350')
        self.resizable(False, False)

        self.create_widgets()
        
        if HAS_TRAY:
            self.protocol('WM_DELETE_WINDOW', self.hide_window)
            self.setup_tray()
        else:
            self.protocol('WM_DELETE_WINDOW', self.quit_app)

    def create_widgets(self):
        # Tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=10)

        self.main_tab = ttk.Frame(self.notebook)
        self.settings_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.main_tab, text='Main')
        self.notebook.add(self.settings_tab, text='Settings')

        # --- Main Tab ---
        self.status_label = tkinter.Label(self.main_tab, text='Ready to start', font=('Arial', 14))
        self.status_label.pack(pady=20)

        self.time_display = tkinter.Label(self.main_tab, text='--:--', font=('Arial', 24, 'bold'))
        self.time_display.pack(pady=10)

        self.progress_bar = ttk.Progressbar(self.main_tab, orient='horizontal', mode='determinate')
        self.progress_bar.pack(pady=20, padx=20, fill='x')

        self.onoff_button = tkinter.Button(self.main_tab, text='Start', command=self.onoff, bg='#dddddd', font=('Arial', 10))
        self.onoff_button.pack(pady=10, ipadx=20)

        # --- Settings Tab ---
        # Grid layout for settings
        self.settings_tab.columnconfigure(1, weight=1)

        # Trigger Selection
        ttk.Label(self.settings_tab, text='Trigger Type:').grid(row=0, column=0, sticky='w', padx=10, pady=10)
        trigger_combo = ttk.Combobox(self.settings_tab, values=self.triggers, textvariable=self.current_trigger, state='readonly')
        trigger_combo.grid(row=0, column=1, sticky='ew', padx=10, pady=10)

        # Method Selection
        ttk.Label(self.settings_tab, text='Action:').grid(row=1, column=0, sticky='w', padx=10, pady=10)
        method_frame = ttk.Frame(self.settings_tab)
        method_frame.grid(row=1, column=1, sticky='w', padx=10)
        ttk.Radiobutton(method_frame, text='Shut Down', value='shut down', variable=self.function_type).pack(side='left', padx=5)
        ttk.Radiobutton(method_frame, text='Restart', value='restart', variable=self.function_type).pack(side='left', padx=5)
        ttk.Radiobutton(method_frame, text='Sleep', value='sleep', variable=self.function_type).pack(side='left', padx=5)

        # Countdown Input
        ttk.Label(self.settings_tab, text='Countdown (min):').grid(row=2, column=0, sticky='w', padx=10, pady=10)
        ttk.Entry(self.settings_tab, textvariable=self.countdown_minutes).grid(row=2, column=1, sticky='ew', padx=10, pady=10)

        # Time Input
        ttk.Label(self.settings_tab, text='Target Time (HH:MM):').grid(row=3, column=0, sticky='w', padx=10, pady=10)
        ttk.Entry(self.settings_tab, textvariable=self.target_time_str).grid(row=3, column=1, sticky='ew', padx=10, pady=10)

        # Note
        ttk.Label(self.settings_tab, text='* Ensure time format is 24h', font=('Arial', 8, 'italic')).grid(row=4, column=0, columnspan=2, pady=5)
        
        # Autostart Checkbox
        ttk.Checkbutton(self.settings_tab, text='Run on Startup', variable=self.autostart_enabled, command=self.toggle_autostart).grid(row=5, column=0, columnspan=2, pady=10)

    def toggle_autostart(self):
        enable = self.autostart_enabled.get()
        platform = sys.platform
        script_path = os.path.abspath(sys.argv[0])
        
        try:
            if platform == 'win32':
                startup_dir = os.path.join(os.getenv('APPDATA', ''), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
                if not startup_dir: return
                bat_path = os.path.join(startup_dir, 'auto_turnoff.bat')
                if enable:
                    with open(bat_path, 'w') as f:
                        f.write(f'@echo off\npythonw "{script_path}"')
                else:
                    if os.path.exists(bat_path): os.remove(bat_path)
            elif platform == 'darwin':
                plist_dir = os.path.expanduser('~/Library/LaunchAgents')
                os.makedirs(plist_dir, exist_ok=True)
                plist_path = os.path.join(plist_dir, 'com.user.autoturnoff.plist')
                if enable:
                    plist_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.autoturnoff</string>
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
                desktop_path = os.path.join(autostart_dir, 'auto_turnoff.desktop')
                if enable:
                    desktop_content = f'''[Desktop Entry]
Type=Application
Name=Auto Turnoff
Exec=python3 "{script_path}"
Terminal=false
'''
                    with open(desktop_path, 'w') as f:
                        f.write(desktop_content)
                else:
                    if os.path.exists(desktop_path): os.remove(desktop_path)
        except Exception as e:
            print("Failed to toggle autostart:", e)

    def create_tray_image(self):
        # Generate a simple red square icon for the tray
        image = Image.new('RGB', (64, 64), color='white')
        dc = ImageDraw.Draw(image)
        dc.rectangle((16, 16, 48, 48), fill='red')
        return image

    def setup_tray(self):
        menu = pystray.Menu(
            pystray.MenuItem('Show', self.show_window, default=True),
            pystray.MenuItem('Quit', self.quit_app)
        )
        self.icon = pystray.Icon("auto_turnoff", self.create_tray_image(), "Auto Turnoff", menu)
        threading.Thread(target=self.icon.run, daemon=True).start()

    def hide_window(self):
        self.withdraw()

    def show_window(self, icon, item):
        self.after(0, self.deiconify)

    def load_preferences(self):
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    if 'trigger' in data: self.current_trigger.set(data['trigger'])
                    if 'action' in data: self.function_type.set(data['action'])
                    if 'countdown' in data: self.countdown_minutes.set(data['countdown'])
                    if 'target_time' in data: self.target_time_str.set(data['target_time'])
                    if 'autostart' in data:
                        self.autostart_enabled.set(data['autostart'])
                        self.toggle_autostart()
            except Exception as e:
                print("Could not load preferences:", e)

    def save_preferences(self):
        try:
            data = {
                'trigger': self.current_trigger.get(),
                'action': self.function_type.get(),
                'countdown': self.countdown_minutes.get(),
                'target_time': self.target_time_str.get(),
                'autostart': self.autostart_enabled.get()
            }
            with open(self.CONFIG_FILE, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            print("Could not save preferences:", e)

    def quit_app(self, icon=None, item=None):
        self.save_preferences()
        if HAS_TRAY and hasattr(self, 'icon'):
            self.icon.stop()
        self.after(0, self.destroy)

    def activate(self):
        action = self.function_type.get()
        # Reset UI
        self.stop_timer()
        self.status_label.config(text=f'Executing {action}...')
        
        # Execute
        platform = sys.platform
        
        if action == 'shut down':
            if platform == 'win32':
                os.system('shutdown -s -t 0')
            elif platform == 'darwin':
                os.system('osascript -e \'tell app "System Events" to shut down\'')
            else:
                os.system('systemctl poweroff')
        elif action == 'restart':
            if platform == 'win32':
                try:
                    if HAS_WIN32API:
                        win32api.InitiateSystemShutdown(None, "Restarting...", 0, 1, 1)
                    else:
                        os.system('shutdown -r -t 0')
                except:
                    os.system('shutdown -r -t 0')
            elif platform == 'darwin':
                os.system('osascript -e \'tell app "System Events" to restart\'')
            else:
                os.system('systemctl reboot')
        elif action == 'sleep':
            if platform == 'win32':
                os.system('rundll32.exe powrprof.dll,SetSuspendState 0,1,0')
            elif platform == 'darwin':
                os.system('osascript -e \'tell app "System Events" to sleep\'')
            else:
                os.system('systemctl suspend')

    def send_notification(self, action):
        if HAS_PLYER:
            try:
                notification.notify(
                    title="Auto Turnoff Warning",
                    message=f"Your PC will {action} in 60 seconds!",
                    app_name="Auto Turnoff",
                    timeout=10
                )
            except Exception as e:
                print("Notification failed:", e)

    def update_timer(self):
        if not self.running:
            return

        trigger = self.current_trigger.get()

        if trigger == 'countdown':
            if self.remaining_seconds == 60:
                self.send_notification(self.function_type.get())
                
            if self.remaining_seconds > 0:
                self.remaining_seconds -= 1
                # Update UI
                mins, secs = divmod(self.remaining_seconds, 60)
                self.time_display.config(text=f'{mins:02}:{secs:02}')
                self.progress_bar['value'] = self.total_seconds - self.remaining_seconds
                
                # Schedule next check
                self.timer_id = self.after(1000, self.update_timer)
            else:
                self.activate()

        elif trigger == 'timedate':
            now = datetime.datetime.now()
            current_time = now.strftime('%H:%M')
            target = self.target_time_str.get()
            
            self.time_display.config(text=f'Now: {current_time}\nTarget: {target}')
            self.progress_bar.stop() # Indeterminate or just static
            
            # Notification check
            try:
                target_dt = datetime.datetime.strptime(target, '%H:%M')
                target_dt = target_dt.replace(year=now.year, month=now.month, day=now.day)
                if target_dt <= now:
                    target_dt += datetime.timedelta(days=1)
                
                diff = (target_dt - now).total_seconds()
                if 59 < diff <= 60:
                    self.send_notification(self.function_type.get())
            except ValueError:
                pass
            
            if current_time == target:
                self.activate()
            else:
                # Check every second
                self.timer_id = self.after(1000, self.update_timer)

    def start_timer(self):
        trigger = self.current_trigger.get()

        if trigger == 'instant':
            if messagebox.askyesno('Confirm', f'Are you sure you want to {self.function_type.get()} immediately?'):
                self.activate()
            return

        if trigger == 'countdown':
            try:
                mins = self.countdown_minutes.get()
                self.total_seconds = mins * 60
                self.remaining_seconds = self.total_seconds
                if self.total_seconds <= 0:
                    raise ValueError
            except:
                messagebox.showerror('Error', 'Invalid countdown minutes.')
                return
            
            self.progress_bar.config(maximum=self.total_seconds, value=0)
            self.status_label.config(text=f'Counting down to {self.function_type.get()}...')

        elif trigger == 'timedate':
            target = self.target_time_str.get()
            # Simple validation
            try:
                time.strptime(target, '%H:%M')
            except ValueError:
                messagebox.showerror('Error', 'Invalid time format. Use HH:MM (24h).')
                return
            
            self.status_label.config(text=f'Waiting for {target} to {self.function_type.get()}...')
            self.progress_bar.config(maximum=100, value=0) # Just reset

        self.running = True
        self.onoff_button.config(text='Stop', bg='#ffcccc')
        self.notebook.select(self.main_tab) # Switch to main tab
        self.update_timer()

    def stop_timer(self):
        self.running = False
        if self.timer_id:
            self.after_cancel(self.timer_id)
            self.timer_id = None
        
        self.onoff_button.config(text='Start', bg='#dddddd')
        self.status_label.config(text='Stopped')
        self.time_display.config(text='--:--')
        self.progress_bar['value'] = 0

    def onoff(self):
        if self.running:
            self.stop_timer()
        else:
            self.start_timer()

if __name__ == '__main__':
    app = App()
    app.mainloop()
