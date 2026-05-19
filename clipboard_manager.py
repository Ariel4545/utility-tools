import os
import sys
import json
import tkinter
from tkinter import messagebox
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from ttkbootstrap.widgets.scrolled import ScrolledFrame

class ClipboardManager(tb.Window):
    CONFIG_FILE = 'clipboard_settings.json'
    HISTORY_FILE = 'clipboard_history.json'

    def __init__(self):
        super().__init__(themename="darkly")

        self.last_clipboard_text = ""
        self.history = []

        # Configuration variables
        self.max_history = tkinter.IntVar(value=50)
        self.current_theme = tkinter.StringVar(value="darkly")
        self.search_query = tkinter.StringVar()

        self.load_settings()
        self.load_history()

        self.style.theme_use(self.current_theme.get())

        self.title("Clipboard History (v0.07)")
        self.geometry("380x500")
        self.resizable(False, False)

        self.create_widgets()
        self.after(500, self.poll_clipboard)

    def create_widgets(self):
        # Search Bar
        search_frame = tb.Frame(self, padding=10)
        search_frame.pack(fill='x')

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

        # Clear All Button
        action_frame = tb.Frame(self, padding=(10, 0))
        action_frame.pack(fill='x')

        tb.Button(
            action_frame, 
            text="Clear All History", 
            command=self.clear_all_history, 
            bootstyle="danger-outline-sm"
        ).pack(side='right')

        # List Area
        self.list_container = ScrolledFrame(self, bootstyle="light")
        self.list_container.pack(expand=True, fill='both', padx=10, pady=10)

        self.rebuild_history_list()

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

    def copy_item_to_clipboard(self, text):
        self.last_clipboard_text = text
        self.clipboard_clear()
        self.clipboard_append(text)
        self.update()

        if text in self.history:
            self.history.remove(text)
        self.history.insert(0, text)
        self.save_history()
        self.rebuild_history_list(self.search_query.get())

    def rebuild_history_list(self, filter_query=""):
        for widget in self.list_container.winfo_children():
            widget.destroy()

        filter_query = filter_query.lower()
        items_displayed = 0

        for i, text in enumerate(self.history):
            if filter_query and filter_query not in text.lower():
                continue

            card = tb.Frame(self.list_container, bootstyle=SECONDARY, padding=8)
            card.pack(fill='x', pady=4, padx=5)

            header = tb.Frame(card)
            header.pack(fill='x')

            char_count = len(text)
            tb.Label(header, text=f"📋 {char_count} chars", font=('Helvetica', 8), bootstyle="muted").pack(side='left')

            actions = tb.Frame(header)
            actions.pack(side='right')

            btn_copy = tb.Button(
                actions, 
                text="Copy", 
                command=lambda t=text: self.copy_item_to_clipboard(t),
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

            preview_text = text.replace('\n', ' ')
            if len(preview_text) > 85:
                preview_text = preview_text[:82] + "..."

            lbl_preview = tb.Label(
                card, 
                text=preview_text, 
                font=('Helvetica', 9), 
                justify=LEFT, 
                wraplength=330,
                bootstyle=LIGHT
            )
            lbl_preview.pack(fill='x', pady=(5, 0), anchor='w')

            items_displayed += 1
            if items_displayed >= self.max_history.get():
                break

        if items_displayed == 0:
            tb.Label(
                self.list_container, 
                text="No clipboard items matches.", 
                font=('Helvetica', 10), 
                bootstyle="muted"
            ).pack(pady=20)

    def filter_history(self, *args):
        self.rebuild_history_list(self.search_query.get())

    def poll_clipboard(self):
        try:
            current_text = self.clipboard_get()
        except tkinter.TclError:
            current_text = None

        if current_text and current_text != self.last_clipboard_text:
            self.last_clipboard_text = current_text
            
            if current_text in self.history:
                self.history.remove(current_text)
            self.history.insert(0, current_text)

            max_limit = self.max_history.get()
            if len(self.history) > max_limit:
                self.history = self.history[:max_limit]

            self.save_history()
            self.rebuild_history_list(self.search_query.get())

        self.after(500, self.poll_clipboard)

    def load_settings(self):
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    if 'max_history' in data: self.max_history.set(data['max_history'])
                    if 'theme' in data: self.current_theme.set(data['theme'])
            except Exception as e:
                pass

    def save_settings(self):
        try:
            data = {
                'max_history': self.max_history.get(),
                'theme': self.current_theme.get()
            }
            with open(self.CONFIG_FILE, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            pass

    def load_history(self):
        if os.path.exists(self.HISTORY_FILE):
            try:
                with open(self.HISTORY_FILE, 'r') as f:
                    self.history = json.load(f)
            except Exception as e:
                self.history = []

    def save_history(self):
        try:
            with open(self.HISTORY_FILE, 'w') as f:
                json.dump(self.history, f)
        except Exception as e:
            pass

if __name__ == '__main__':
    app = ClipboardManager()
    app.mainloop()
