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

A premium, vertical clipboard manager that tracks your copy history, allows lightning-fast search filtering, and preserves copied snippets.

### Key Features ✨
*   **Clipboard Polling**: Safe, background polling that tracks copied text, updates the list instantly, and deduplicates items.
*   **Search Filter**: Dynamically query history in real time with immediate search filtering.
*   **Interactive Cards**: Clean, modern cards that show item lengths and feature quick actions:
    *   **Copy**: Instantly copy an item back to your clipboard.
    *   **Delete (✕)**: Remove specific items from your history list.
*   **Persistent Storage**: Saves your clipboard history (`clipboard_history.json`) and settings (`clipboard_settings.json`) across reboots.

### How to Run
```bash
python clipboard_manager.py
```

---

## 🛠️ Getting Started

### Prerequisites
*   **Python 3.7+**
*   **Linux Users**: For inactivity detection in the turn-off tool, ensure `xprintidle` is installed:
    ```bash
    sudo apt-get install xprintidle
    ```

### Installation
1. Clone the repository.
2. Install the required python packages:
   ```bash
   pip install -r requirements.txt
   ```

Enjoy a faster, automated, and more beautiful desktop experience! 🚀
