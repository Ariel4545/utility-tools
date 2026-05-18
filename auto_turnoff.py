import os
import tkinter
from tkinter import messagebox
import time
import datetime
import sys
import threading
import json
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import logging
import subprocess

# Setup logging
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

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

class App(tb.Window):
    CONFIG_FILE = 'settings.json'

    def __init__(self):
        super().__init__(themename="darkly")

        self.running = False
        self.timer_id = None
        self.inhibit_proc = None # For Linux/macOS sleep inhibition

        # Configuration Variables
        self.triggers = ('countdown', 'instant', 'timedate', 'inactivity')
        self.current_trigger = tkinter.StringVar(value=self.triggers[0])
        
        self.exe_methods = ('shut down', 'restart', 'sleep')
        self.function_type = tkinter.StringVar(value=self.exe_methods[0])
        
        self.countdown_minutes = tkinter.IntVar(value=10)
        self.inactivity_minutes = tkinter.IntVar(value=30)
        self.target_time_str = tkinter.StringVar(value='00:00')
        self.autostart_enabled = tkinter.BooleanVar(value=False)
        self.current_theme = tkinter.StringVar(value="darkly")

        # Internal state
        self.remaining_seconds = 0
        self.total_seconds = 0

        self.load_preferences()
        
        # Apply theme from preferences
        self.style.theme_use(self.current_theme.get())

        # UI Setup
        self.title('Calculated Turn Off')
        self.geometry('450x450')
        self.resizable(False, False)

        self.create_widgets()
        
        if HAS_TRAY:
            self.protocol('WM_DELETE_WINDOW', self.hide_window)
            self.setup_tray()
        else:
            self.protocol('WM_DELETE_WINDOW', self.quit_app)

    def create_widgets(self):
        # Tabs
        self.notebook = tb.Notebook(self, bootstyle=PRIMARY)
        self.notebook.pack(expand=True, fill='both', padx=15, pady=15)

        self.main_tab = tb.Frame(self.notebook)
        self.settings_tab = tb.Frame(self.notebook)

        self.notebook.add(self.main_tab, text='Main')
        self.notebook.add(self.settings_tab, text='Settings')

        # --- Main Tab ---
        self.status_label = tb.Label(self.main_tab, text='Ready to start', font=('Helvetica', 16, 'bold'), bootstyle=INFO)
        self.status_label.pack(pady=(30, 10))

        self.time_display = tb.Label(self.main_tab, text='--:--', font=('Helvetica', 36, 'bold'))
        self.time_display.pack(pady=10)

        self.progress_bar = tb.Progressbar(self.main_tab, orient='horizontal', mode='determinate', bootstyle=SUCCESS, length=300)
        self.progress_bar.pack(pady=30, padx=30, fill='x')

        self.onoff_button = tb.Button(self.main_tab, text='Start Timer', command=self.onoff, bootstyle=SUCCESS, width=20)
        self.onoff_button.pack(pady=20)

        # --- Settings Tab ---
        settings_container = tb.Frame(self.settings_tab)
        settings_container.pack(fill='both', expand=True, padx=20, pady=10)

        # Trigger Selection
        tb.Label(settings_container, text='Trigger Type:').grid(row=0, column=0, sticky='w', pady=10)
        trigger_combo = tb.Combobox(settings_container, values=self.triggers, textvariable=self.current_trigger, state='readonly', bootstyle=PRIMARY)
        trigger_combo.grid(row=0, column=1, sticky='ew', padx=(10, 0), pady=10)

        # Method Selection
        tb.Label(settings_container, text='Action:').grid(row=1, column=0, sticky='w', pady=10)
        method_frame = tb.Frame(settings_container)
        method_frame.grid(row=1, column=1, sticky='w', padx=(10, 0))
        tb.Radiobutton(method_frame, text='Shut Down', value='shut down', variable=self.function_type, bootstyle="danger-toolbutton").pack(side='left', padx=2)
        tb.Radiobutton(method_frame, text='Restart', value='restart', variable=self.function_type, bootstyle="warning-toolbutton").pack(side='left', padx=2)
        tb.Radiobutton(method_frame, text='Sleep', value='sleep', variable=self.function_type, bootstyle="info-toolbutton").pack(side='left', padx=2)

        # Countdown Input
        tb.Label(settings_container, text='Countdown (min):').grid(row=2, column=0, sticky='w', pady=10)
        tb.Entry(settings_container, textvariable=self.countdown_minutes, bootstyle=PRIMARY).grid(row=2, column=1, sticky='ew', padx=(10, 0), pady=10)

        # Inactivity Input
        tb.Label(settings_container, text='Inactivity (min):').grid(row=3, column=0, sticky='w', pady=10)
        tb.Entry(settings_container, textvariable=self.inactivity_minutes, bootstyle=PRIMARY).grid(row=3, column=1, sticky='ew', padx=(10, 0), pady=10)

        # Time Input
        tb.Label(settings_container, text='Target Time (24h):').grid(row=4, column=0, sticky='w', pady=10)
        tb.Entry(settings_container, textvariable=self.target_time_str, bootstyle=PRIMARY).grid(row=4, column=1, sticky='ew', padx=(10, 0), pady=10)

        # Theme Selection
        tb.Label(settings_container, text='Theme:').grid(row=5, column=0, sticky='w', pady=10)
        theme_combo = tb.Combobox(settings_container, values=self.style.theme_names(), textvariable=self.current_theme, state='readonly', bootstyle=SECONDARY)
        theme_combo.grid(row=5, column=1, sticky='ew', padx=(10, 0), pady=10)
        theme_combo.bind('<<ComboboxSelected>>', self.change_theme)

        # Footer Actions
        footer_frame = tb.Frame(settings_container)
        footer_frame.grid(row=6, column=0, columnspan=2, pady=20)
        
        tb.Checkbutton(footer_frame, text='Run on Startup', variable=self.autostart_enabled, command=self.toggle_autostart, bootstyle="round-toggle").pack(side='left', padx=10)

    def change_theme(self, event=None):
        theme = self.current_theme.get()
        self.style.theme_use(theme)

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
        dc.rectangle((16, 16, 48, 48), fill='#dc3545') # Using a nice Bootstrap red
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
                    if 'inactivity' in data: self.inactivity_minutes.set(data['inactivity'])
                    if 'target_time' in data: self.target_time_str.set(data['target_time'])
                    if 'theme' in data: self.current_theme.set(data['theme'])
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
                'inactivity': self.inactivity_minutes.get(),
                'target_time': self.target_time_str.get(),
                'theme': self.current_theme.get(),
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
        logging.info(f"Activating {action}")
        
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
                try:
                    import ctypes
                    # SetSuspendState(bHibernate, bForce, bWakeupEventsDisabled)
                    # Use 0 for bHibernate to ensure SLEEP not HIBERNATE
                    ctypes.windll.powrprof.SetSuspendState(0, 1, 0)
                except:
                    os.system('rundll32.exe powrprof.dll,SetSuspendState 0,1,0')
            elif platform == 'darwin':
                os.system('osascript -e \'tell app "System Events" to sleep\'')
            else:
                os.system('systemctl suspend')

    def inhibit_sleep(self):
        """Prevents the system from sleeping while a timer is active."""
        platform = sys.platform
        try:
            if platform == 'win32':
                import ctypes
                # ES_CONTINUOUS (0x80000000) | ES_SYSTEM_REQUIRED (0x00000001) | ES_AWAYMODE_REQUIRED (0x00000040)
                ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000001 | 0x00000040)
                logging.info("Windows sleep inhibition enabled")
            elif platform == 'darwin':
                # caffeinate -i (prevent idle sleep)
                self.inhibit_proc = subprocess.Popen(['caffeinate', '-i'])
                logging.info("macOS sleep inhibition enabled")
            elif platform.startswith('linux'):
                # Try systemd-inhibit
                try:
                    self.inhibit_proc = subprocess.Popen([
                        'systemd-inhibit', 
                        '--what=idle:sleep', 
                        '--who=Calculated Turn Off', 
                        '--why=Timer is active', 
                        'sleep', 'infinity'
                    ])
                    logging.info("Linux (systemd) sleep inhibition enabled")
                except FileNotFoundError:
                    logging.warning("systemd-inhibit not found, sleep inhibition might not work")
        except Exception as e:
            logging.error(f"Failed to inhibit sleep: {e}")

    def release_sleep(self):
        """Allows the system to sleep normally again."""
        platform = sys.platform
        try:
            if platform == 'win32':
                import ctypes
                # ES_CONTINUOUS (0x80000000) - resets to default
                ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)
                logging.info("Windows sleep inhibition released")
            elif self.inhibit_proc:
                self.inhibit_proc.terminate()
                self.inhibit_proc = None
                logging.info(f"{platform} sleep inhibition released")
        except Exception as e:
            logging.error(f"Failed to release sleep inhibition: {e}")

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

    def get_idle_duration(self):
        import subprocess
        platform = sys.platform
        if platform == 'win32':
            import ctypes
            class LASTINPUTINFO(ctypes.Structure):
                _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]
            lii = LASTINPUTINFO()
            lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
            if ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii)):
                millis = ctypes.windll.kernel32.GetTickCount() - lii.dwTime
                return millis / 1000.0
        elif platform == 'darwin':
            try:
                cmd = "ioreg -c IOHIDSystem | grep -i idle | tail -n1 | awk '{print $NF}'"
                output = subprocess.check_output(cmd, shell=True).decode().strip()
                return int(output) / 1_000_000_000.0
            except:
                pass
        elif platform.startswith('linux'):
            # 1. Try xprintidle
            try:
                return int(subprocess.check_output(['xprintidle']).decode().strip()) / 1000.0
            except:
                pass
            
            # 2. Try GNOME D-Bus fallback
            try:
                # Query GNOME Mutter for idle time
                cmd = [
                    'gdbus', 'call', '--session', 
                    '--dest', 'org.gnome.Mutter.IdleMonitor', 
                    '--object-path', '/org/gnome/Mutter/IdleMonitor/Core', 
                    '--method', 'org.gnome.Mutter.IdleMonitor.GetIdletime'
                ]
                output = subprocess.check_output(cmd).decode()
                # Output looks like: (uint64 12345,)
                return int(output.split()[1].strip(',)')) / 1000.0
            except:
                pass
            
            # 3. Try KDE D-Bus fallback (optional, but good to have)
            try:
                cmd = ['qdbus', 'org.kde.screensaver', '/ScreenSaver', 'GetSessionIdleTime']
                return int(subprocess.check_output(cmd).decode().strip())
            except:
                pass

        return 0

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

        elif trigger == 'inactivity':
            idle_sec = self.get_idle_duration()
            target_sec = self.inactivity_minutes.get() * 60
            
            self.remaining_seconds = max(0, int(target_sec - idle_sec))
            
            mins, secs = divmod(self.remaining_seconds, 60)
            self.time_display.config(text=f'Idle: {int(idle_sec)}s\nRemaining: {mins:02}:{secs:02}', font=('Helvetica', 14))
            
            self.progress_bar.config(maximum=target_sec, value=idle_sec)
            
            if self.remaining_seconds == 60:
                if not hasattr(self, '_notified_inactivity') or not self._notified_inactivity:
                    self.send_notification(self.function_type.get())
                    self._notified_inactivity = True
            elif self.remaining_seconds > 60:
                self._notified_inactivity = False

            if idle_sec >= target_sec:
                self.activate()
            else:
                self.timer_id = self.after(1000, self.update_timer)

        elif trigger == 'timedate':
            now = datetime.datetime.now()
            current_time = now.strftime('%H:%M')
            target = self.target_time_str.get()
            
            self.time_display.config(text=f'Now: {current_time}\nTarget: {target}', font=('Helvetica', 14))
            self.progress_bar.stop()
            
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
            self.status_label.config(text=f'Counting down to {self.function_type.get()}...', bootstyle=WARNING)

        elif trigger == 'inactivity':
            try:
                mins = self.inactivity_minutes.get()
                if mins <= 0: raise ValueError
            except:
                messagebox.showerror('Error', 'Invalid inactivity minutes.')
                return
            self.status_label.config(text=f'Waiting for inactivity...', bootstyle=INFO)
            self._notified_inactivity = False

        elif trigger == 'timedate':
            target = self.target_time_str.get()
            try:
                time.strptime(target, '%H:%M')
            except ValueError:
                messagebox.showerror('Error', 'Invalid time format. Use HH:MM (24h).')
                return
            
            self.status_label.config(text=f'Waiting for {target}...', bootstyle=INFO)
            self.progress_bar.config(maximum=100, value=0)

        self.inhibit_sleep()
        self.running = True
        self.onoff_button.config(text='Stop Timer', bootstyle=DANGER)
        self.notebook.select(self.main_tab)
        logging.info(f"Timer started (trigger={trigger}, action={self.function_type.get()})")
        self.update_timer()

    def stop_timer(self):
        self.running = False
        if self.timer_id:
            self.after_cancel(self.timer_id)
            self.timer_id = None
        
        self.onoff_button.config(text='Start Timer', bootstyle=SUCCESS)
        self.status_label.config(text='Ready to start', bootstyle=INFO)
        self.time_display.config(text='--:--', font=('Helvetica', 36, 'bold'))
        self.progress_bar['value'] = 0
        self.release_sleep()
        logging.info("Timer stopped manually")

    def onoff(self):
        if self.running:
            self.stop_timer()
        else:
            self.start_timer()

if __name__ == '__main__':
    app = App()
    app.mainloop()
