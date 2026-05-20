# Ariel's Utility Tools Suite 🛠️

A modern, high-aesthetics suite of lightweight, cross-platform desktop utility tools designed to make your daily computer interactions seamless and powerful. Built with Python and beautiful `ttkbootstrap` themes.

---

## 1. Calculated Turn Off 🌙

A robust power-management utility that puts you in full control of when your computer shuts down, restarts, or sleeps.

### Key Features 🚀
*   **Multiple Triggers**:
    *   ⏳ **Countdown**: Run an action after a specified number of minutes.
    *   🕒 **Target Time**: Schedule an action for a specific time of day (24h format).
    *   🖱️ **Inactivity Trigger**: Detects keyboard/mouse idle time to automatically trigger power actions.
    *   ⚡ **Instant**: Execute power actions immediately.
*   **Safety Warning**: Native desktop notifications warn you 60 seconds before executing any scheduled power action.
*   **Persistent Preferences**: Automatically remembers your settings and trigger preferences across launches.

### How to Run
```bash
python auto_turnoff.py
```

---

## 2. Sleek Clipboard History & Manager 📋

A premium, vertical clipboard manager that tracks your copy history, allows lightning-fast search filtering, and automates copying and pasting.

### Key Features ✨
*   **Clipboard Polling**: Safe, background polling that tracks copied text, updates the list instantly, and deduplicates items.
*   **Search Filter**: Dynamically query history in real time with immediate search filtering.
*   **Auto-Paste Automation**: Double-clicking an item (or selecting it) automatically copies it, hides the window, and injects a native system paste shortcut (`Ctrl+V` / `Cmd+V`) back into your active window.
*   **Local Socket IPC**: Runs on local port `50099`. When you run the script a second time, it triggers the background instance to show the popup at your mouse cursor, avoiding duplicate tray icons and offering instant response.
*   **Persistent Storage**: Saves your clipboard history (`clipboard_history.json`) and settings (`clipboard_settings.json`) across reboots.

### How to Run
```bash
python clipboard_manager.py
```

---

## ⚙️ How to Setup a System-Wide Global Hotkey

To make the Clipboard Manager feel like a native OS feature, you can bind it to a keyboard shortcut (like `Ctrl+Alt+V` or `Super+Shift+V`). 

Because of our **Zero-Dependency IPC Socket system**, running the command when the app is already in the tray will instantly slide open the history panel at your mouse cursor!

### 🐧 Linux (GNOME / KDE)
1.  Open **Settings** -> **Keyboard** -> **Keyboard Shortcuts** (or Custom Shortcuts).
2.  Click **Add Custom Shortcut** (or the `+` button).
3.  Fill in the details:
    *   **Name**: `Clipboard Manager`
    *   **Command**: `python3 /absolute/path/to/clipboard_manager.py`
4.  Click **Set Shortcut** and press your desired keys (e.g., `Super` + `Shift` + `V` or `Ctrl` + `Alt` + `V`).
5.  Click **Add**. Done!
> [NOTE]
> On Linux, automatic paste simulation requires `xdotool` to be installed on X11 environments. Install it via: `sudo apt-get install xdotool`.

### 🪟 Windows
1.  Right-click on your desktop, select **New** -> **Shortcut**.
2.  Set the location to: `pythonw.exe "C:\path\to\clipboard_manager.py"` (using `pythonw` hides the command prompt window!).
3.  Click **Next**, name the shortcut `Clipboard History`, and click **Finish**.
4.  Right-click the newly created shortcut -> **Properties**.
5.  Click on the **Shortcut key** field and press your desired hotkey (e.g., `Ctrl` + `Alt` + `V`).
6.  Click **Apply** and **OK**.

### 🍏 macOS
1.  Open **Automator** and select **Quick Action**.
2.  Set "Workflow receives" to **no input** in **any application**.
3.  Search for **Run Shell Script** in the left panel and drag it in.
4.  Change the script content to: `/usr/bin/python3 /absolute/path/to/clipboard_manager.py`.
5.  Save the Quick Action as `Show Clipboard History`.
6.  Open **System Settings** -> **Keyboard** -> **Keyboard Shortcuts** -> **Services**.
7.  Find `Show Clipboard History` under "General" and double-click it to bind your hotkey (e.g., `Cmd` + `Option` + `V`).

---

## 🛠️ Getting Started

### Prerequisites
*   **Python 3.7+**
*   **Linux Users**: For inactivity detection in the turn-off tool and auto-paste, ensure `xprintidle` and `xdotool` are installed.

### Installation
1. Clone the repository.
2. Install the required python packages:
   ```bash
   pip install -r requirements.txt
   ```

Enjoy a faster, automated, and more beautiful desktop experience! 🚀
