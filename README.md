# Calculated Turn Off 🌙

**Calculated Turn Off** is a modern, cross-platform power management utility designed to give you full control over when your computer shuts down, sleeps, or restarts. 

Whether you're waiting for a download to finish, automating a nightly shutdown, or just want to save energy when you're away, this tool provides a sleek and reliable solution.

## Key Features 🚀

-   **Multiple Triggers**:
    -   ⏳ **Countdown**: Set a timer in minutes.
    -   🕒 **Target Time**: Schedule an action for a specific time of day (24h format).
    -   🖱️ **Inactivity**: Trigger actions after a period of mouse/keyboard idle time.
    -   ⚡ **Instant**: Execute power actions immediately.
-   **Actions**: Support for **Shut Down**, **Restart**, and **Sleep**.
-   **Cross-Platform**: Works seamlessly on **Windows**, **macOS**, and **Linux**.
-   **Modern UI**: Beautiful dark mode and customizable themes powered by `ttkbootstrap`.
-   **System Tray**: Minimizes to the system tray to run quietly in the background.
-   **Notifications**: Sends a native desktop warning 60 seconds before execution.
-   **Auto-Start**: Optional "Run on Startup" feature to keep your settings active across reboots.
-   **Persistence**: Automatically saves your preferences and themes.

## Getting Started 🛠️

### Prerequisites

You'll need **Python 3.7+** installed.

### Installation

1. Clone the repository or download the source.
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### How to Run

Run the main script:
```bash
python auto_turnoff.py
```

## How to Use 📖

1.  **Settings Tab**:
    -   Select your **Trigger Type**.
    -   Select the **Action** you want to perform.
    -   Configure the time or inactivity threshold.
    -   Choose a **Theme** that fits your style.
    -   Toggle **Run on Startup** if desired.
2.  **Main Tab**:
    -   Click **Start Timer** to begin.
    -   Monitor the progress bar and time remaining.
    -   Click **Stop Timer** at any time to cancel.

## License 📄

This project is licensed under the **MIT License**.

## Important Notes ⚠️

-   **Save your work!** Native notifications will warn you 60 seconds before an action, but the execution is final once the timer hits zero.
-   **Linux Users**: Ensure `xprintidle` is installed for the best inactivity detection experience.

Enjoy your automated power management! 💤
