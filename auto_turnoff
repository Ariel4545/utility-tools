import os
import tkinter
from tkinter import ttk, messagebox
import time
import datetime
import win32api

class App(tkinter.Tk):
    def __init__(self):
        super().__init__()

        self.running = False
        self.timer_id = None

        # Configuration Variables
        self.triggers = ('countdown', 'instant', 'timedate')
        self.current_trigger = tkinter.StringVar(value=self.triggers[0])
        
        self.exe_methods = ('shut down', 'restart')
        self.function_type = tkinter.StringVar(value=self.exe_methods[0])
        
        self.countdown_minutes = tkinter.IntVar(value=10)
        self.target_time_str = tkinter.StringVar(value='00:00')

        # Internal state
        self.remaining_seconds = 0
        self.total_seconds = 0

        # UI Setup
        self.title('Calculated Turn Off')
        self.geometry('400x350')
        self.resizable(False, False)

        self.create_widgets()

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

        # Countdown Input
        ttk.Label(self.settings_tab, text='Countdown (min):').grid(row=2, column=0, sticky='w', padx=10, pady=10)
        ttk.Entry(self.settings_tab, textvariable=self.countdown_minutes).grid(row=2, column=1, sticky='ew', padx=10, pady=10)

        # Time Input
        ttk.Label(self.settings_tab, text='Target Time (HH:MM):').grid(row=3, column=0, sticky='w', padx=10, pady=10)
        ttk.Entry(self.settings_tab, textvariable=self.target_time_str).grid(row=3, column=1, sticky='ew', padx=10, pady=10)

        # Note
        ttk.Label(self.settings_tab, text='* Ensure time format is 24h', font=('Arial', 8, 'italic')).grid(row=4, column=0, columnspan=2, pady=5)

    def activate(self):
        action = self.function_type.get()
        # Reset UI
        self.stop_timer()
        self.status_label.config(text=f'Executing {action}...')
        
        # Execute
        if action == 'shut down':
            # Windows shutdown command
            os.system('shutdown -s -t 0')
        elif action == 'restart':
            try:
                # Try win32api first (Windows specific)
                # InitiateSystemShutdown(machineName, message, timeout, forceAppsClosed, rebootAfterShutdown)
                win32api.InitiateSystemShutdown(None, "Restarting...", 0, 1, 1)
            except:
                # Fallback
                os.system('shutdown -r -t 0')

    def update_timer(self):
        if not self.running:
            return

        trigger = self.current_trigger.get()

        if trigger == 'countdown':
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
            current_time = datetime.datetime.now().strftime('%H:%M')
            target = self.target_time_str.get()
            
            self.time_display.config(text=f'Now: {current_time}\nTarget: {target}')
            self.progress_bar.stop() # Indeterminate or just static
            
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
