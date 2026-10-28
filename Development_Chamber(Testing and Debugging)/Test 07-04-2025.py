import tkinter as tk
import threading

def display_floating_text(content, color="white", size=20, position="top-left"):
    def run():
        root = tk.Tk()
        root.overrideredirect(True)
        root.wm_attributes("-topmost", True)
        root.wm_attributes("-transparentcolor", "black")
        root.configure(bg="black")

        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()

        # Create label
        label = tk.Label(root, text=content, font=("Consolas", size), fg=color, bg="black")
        label.pack()

        # Determine position
        x_offset, y_offset = 20, 20
        if position == "top-left":
            x, y = x_offset, y_offset
        elif position == "top-right":
            x, y = screen_width - label.winfo_reqwidth() - x_offset, y_offset
        elif position == "bottom-left":
            x, y = x_offset, screen_height - label.winfo_reqheight() - y_offset
        elif position == "bottom-right":
            x, y = screen_width - label.winfo_reqwidth() - x_offset, screen_height - label.winfo_reqheight() - y_offset
        else:
            x, y = x_offset, y_offset  # Default to top-left if invalid

        root.geometry(f"+{x}+{y}")

        root.mainloop()

    # Use a separate thread to avoid blocking main program
    threading.Thread(target=run, daemon=True).start()

display_floating_text("Jarvis is Online", color="lime", size=22, position="top-left")

# Show CPU warning at top-right (no auto-close)
display_floating_text("CPU usage high!", color="red", size=18, position="top-right")