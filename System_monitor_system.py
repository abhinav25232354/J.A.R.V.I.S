import psutil
import time
import tkinter as tk
import threading

def silent_notification(title, message):
    def show_notification():
        root = tk.Tk()
        root.overrideredirect(True)  # Remove window decorations
        root.attributes("-topmost", True)
        root.configure(bg='black')
        root.attributes('-alpha', 0.30)  # Transparency

        screen_width = root.winfo_screenwidth()
        x = screen_width - 300  # Notification width offset
        y = 50  # Distance from top
        root.geometry(f"280x80+{x}+{y}")  # Size and position

        title_label = tk.Label(root, text=title, font=('Segoe UI', 10, 'bold'), fg='cyan', bg='black')
        msg_label = tk.Label(root, text=message, font=('Segoe UI', 9), fg='white', bg='black', wraplength=260)

        title_label.pack(pady=(10, 0))
        msg_label.pack(pady=(5, 10))

        # Auto-close after 5 seconds
        root.after(5000, root.destroy)
        root.mainloop()

    # Run in background to avoid blocking
    threading.Thread(target=show_notification).start()


from Speech_Drive.Short_speech import *

def speak(audio):
    asyncio.run(speech(audio))
    playsound("output.mp3")

def get_cpu_usage():
    return psutil.cpu_percent(interval=1)

def get_ram_usage():
    return psutil.virtual_memory().percent

def get_disk_usage():
    return psutil.disk_usage('/').percent

def monitor_system():
    while True:
        cpu = get_cpu_usage()
        ram = get_ram_usage()
        disk = get_disk_usage()

        if cpu > 90:
            print(f"[ALERT] CPU Usage is high: {cpu}%")
            silent_notification(f"[ALERT] CPU Usage is high: {cpu}%", "you should consider a checkup sir - from jarvis")
        if ram > 90:
            print(f"[WARNING] RAM Usage is above normal: {ram}%")
            silent_notification(f"[WARNING] RAM Usage is above normal: {ram}%", "you should consider a checkup sir - from jarvis")

        if disk > 90:
            print(f"[CRITICAL] Disk Usage is above safe limit: {disk}%")
            silent_notification(f"[CRITICAL] Disk Usage is above safe limit: {disk}%", "you should consider a checkup sir - from jarvis")

        time.sleep(2)  # Delay between checks (adjust as needed)

if __name__ == "__main__":
    print("🔍 System Monitor Started... Press Ctrl+C to stop.")
    try:
        monitor_system()
    except KeyboardInterrupt:
        print("\n🛑 Monitoring stopped by user.")