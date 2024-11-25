# visualization.py
import tkinter as tk
from tkinter import ttk
import queue

class Visualizer:
    def __init__(self, update_queue: queue.Queue, command_queue: queue.Queue):
        self.update_queue = update_queue
        self.command_queue = command_queue
        self.punch_count = 0
        self.previous_max_speed = 0.0
        self.previous_max_force = 0.0
        self.historical_max_speed = 0.0
        self.historical_max_force = 0.0

        # Initialize Tkinter UI
        self.root = tk.Tk()
        self.root.title("Smart Boxing Glove Trainer")
        self.root.geometry("800x600")  # 调整窗口大小
        self.root.configure(bg="#34495e")

        self._create_widgets()

        # Start the periodic GUI update
        self.root.after(100, self.process_queue)

    def _create_widgets(self):
        """Creates and places all UI widgets."""
        # Title
        title_label = tk.Label(
            self.root,
            text="Smart Boxing Glove Trainer",
            font=("Helvetica", 22, "bold"),
            bg="#34495e",
            fg="#ecf0f1"
        )
        title_label.pack(pady=20)

        # Top Frame for Punch Count and Reset Button
        top_frame = tk.Frame(self.root, bg="#34495e")
        top_frame.pack(pady=10, padx=20, fill="x")

        # Punch Count Section
        punch_count_frame = tk.Frame(
            top_frame,
            bg="#1abc9c",
            highlightbackground="#16a085",
            highlightthickness=2
        )
        punch_count_frame.pack(side="left", padx=10, fill="both", expand=True)

        punch_count_label = tk.Label(
            punch_count_frame,
            text="Punch Count",
            font=("Helvetica", 18, "bold"),
            bg="#1abc9c",
            fg="white"
        )
        punch_count_label.pack(pady=5)

        self.punch_count_var = tk.StringVar(value="0")
        punch_count_display = tk.Label(
            punch_count_frame,
            textvariable=self.punch_count_var,
            font=("Helvetica", 24, "bold"),
            bg="#1abc9c",
            fg="white"
        )
        punch_count_display.pack(pady=10)

        # Reset Button
        reset_button = tk.Button(
            top_frame,
            text="Reset",
            font=("Helvetica", 14, "bold"),
            bg="#e74c3c",
            fg="white",
            command=self.reset
        )
        reset_button.pack(side="right", padx=10)

        # Middle Frame for Current and Previous Speed and Force
        middle_frame = tk.Frame(self.root, bg="#34495e")
        middle_frame.pack(pady=10, padx=20, fill="x")

        # Current Max Speed
        current_speed_frame = tk.Frame(middle_frame, bg="#2c3e50", highlightbackground="#16a085", highlightthickness=2)
        current_speed_frame.pack(side="left", padx=10, fill="both", expand=True)

        current_speed_label = tk.Label(
            current_speed_frame,
            text="Current Max Speed (m/s)",
            font=("Helvetica", 16, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        current_speed_label.pack(pady=10)

        self.current_speed_var = tk.StringVar(value="0.00")
        current_speed_display = tk.Label(
            current_speed_frame,
            textvariable=self.current_speed_var,
            font=("Helvetica", 20, "bold"),
            bg="#2c3e50",
            fg="#1abc9c"
        )
        current_speed_display.pack(pady=10)

        # Current Max Force
        current_force_frame = tk.Frame(middle_frame, bg="#2c3e50", highlightbackground="#16a085", highlightthickness=2)
        current_force_frame.pack(side="left", padx=10, fill="both", expand=True)

        current_force_label = tk.Label(
            current_force_frame,
            text="Current Max Force (N)",
            font=("Helvetica", 16, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        current_force_label.pack(pady=10)

        self.current_force_var = tk.StringVar(value="0.00")
        current_force_display = tk.Label(
            current_force_frame,
            textvariable=self.current_force_var,
            font=("Helvetica", 20, "bold"),
            bg="#2c3e50",
            fg="#1abc9c"
        )
        current_force_display.pack(pady=10)

        # Previous Punch Max Speed and Force
        previous_frame = tk.Frame(middle_frame, bg="#34495e")
        previous_frame.pack(pady=10, padx=20, fill="x")

        # Previous Max Speed
        previous_speed_frame = tk.Frame(previous_frame, bg="#2c3e50", highlightbackground="#16a085", highlightthickness=2)
        previous_speed_frame.pack(side="left", padx=10, fill="both", expand=True)

        previous_speed_label = tk.Label(
            previous_speed_frame,
            text="Previous Punch Max Speed (m/s)",
            font=("Helvetica", 16, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        previous_speed_label.pack(pady=10)

        self.previous_speed_var = tk.StringVar(value="0.00")
        previous_speed_display = tk.Label(
            previous_speed_frame,
            textvariable=self.previous_speed_var,
            font=("Helvetica", 20, "bold"),
            bg="#2c3e50",
            fg="#1abc9c"
        )
        previous_speed_display.pack(pady=10)

        # Previous Max Force
        previous_force_frame = tk.Frame(previous_frame, bg="#2c3e50", highlightbackground="#16a085", highlightthickness=2)
        previous_force_frame.pack(side="left", padx=10, fill="both", expand=True)

        previous_force_label = tk.Label(
            previous_force_frame,
            text="Previous Punch Max Force (N)",
            font=("Helvetica", 16, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        previous_force_label.pack(pady=10)

        self.previous_force_var = tk.StringVar(value="0.00")
        previous_force_display = tk.Label(
            previous_force_frame,
            textvariable=self.previous_force_var,
            font=("Helvetica", 20, "bold"),
            bg="#2c3e50",
            fg="#1abc9c"
        )
        previous_force_display.pack(pady=10)

        # Historical Max Speed and Force
        history_frame = tk.Frame(self.root, bg="#34495e")
        history_frame.pack(pady=10, padx=20, fill="both", expand=True)

        # Historical Max Speed
        history_speed_frame = tk.Frame(history_frame, bg="#2c3e50", highlightbackground="#16a085", highlightthickness=2)
        history_speed_frame.pack(side="left", padx=10, fill="both", expand=True)

        history_speed_label = tk.Label(
            history_speed_frame,
            text="Historical Max Speed (m/s)",
            font=("Helvetica", 16, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        history_speed_label.pack(pady=10)

        self.historical_speed_var = tk.StringVar(value="0.00")
        historical_speed_display = tk.Label(
            history_speed_frame,
            textvariable=self.historical_speed_var,
            font=("Helvetica", 20, "bold"),
            bg="#2c3e50",
            fg="#1abc9c"
        )
        historical_speed_display.pack(pady=10)

        # Historical Max Force
        history_force_frame = tk.Frame(history_frame, bg="#2c3e50", highlightbackground="#16a085", highlightthickness=2)
        history_force_frame.pack(side="left", padx=10, fill="both", expand=True)

        history_force_label = tk.Label(
            history_force_frame,
            text="Historical Max Force (N)",
            font=("Helvetica", 16, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        history_force_label.pack(pady=10)

        self.historical_force_var = tk.StringVar(value="0.00")
        historical_force_display = tk.Label(
            history_force_frame,
            textvariable=self.historical_force_var,
            font=("Helvetica", 20, "bold"),
            bg="#2c3e50",
            fg="#1abc9c"
        )
        historical_force_display.pack(pady=10)

        # Footer
        footer_label = tk.Label(
            self.root,
            text="Designed for Performance Tracking",
            font=("Helvetica", 12),
            bg="#34495e",
            fg="gray"
        )
        footer_label.pack(pady=10)

    def process_queue(self):
        """Processes incoming data from the queue and updates the UI."""
        try:
            while True:
                update_type, value = self.update_queue.get_nowait()
                if update_type == 'count':
                    self.update_punch_count(value)
                elif update_type == 'previous_max_speed':
                    self.update_previous_max_speed(value)
                elif update_type == 'previous_max_force':
                    self.update_previous_max_force(value)
                elif update_type == 'historical_max_speed':
                    self.update_historical_max_speed(value)
                elif update_type == 'historical_max_force':
                    self.update_historical_max_force(value)
                elif update_type == 'reset':
                    self.reset_ui()
        except queue.Empty:
            pass
        finally:
            # Schedule the next queue check
            self.root.after(100, self.process_queue)

    def update_punch_count(self, count: int):
        """Updates the punch count display."""
        self.punch_count = count
        self.punch_count_var.set(str(self.punch_count))

    def update_previous_max_speed(self, speed: float):
        """Updates the previous punch max speed display."""
        self.previous_max_speed = speed
        self.previous_speed_var.set(f"{self.previous_max_speed:.2f}")

    def update_previous_max_force(self, force: float):
        """Updates the previous punch max force display."""
        self.previous_max_force = force
        self.previous_force_var.set(f"{self.previous_max_force:.2f}")

    def update_historical_max_speed(self, speed: float):
        """Updates the historical max speed display."""
        self.historical_max_speed = speed
        self.historical_speed_var.set(f"{self.historical_max_speed:.2f}")

    def update_historical_max_force(self, force: float):
        """Updates the historical max force display."""
        self.historical_max_force = force
        self.historical_force_var.set(f"{self.historical_max_force:.2f}")

    def reset(self):
        """Handles the Reset button click."""
        # Send reset command to DataProcessor
        self.command_queue.put(('reset', None))

    def reset_ui(self):
        """Resets the UI elements."""
        self.punch_count = 0
        self.previous_max_speed = 0.0
        self.previous_max_force = 0.0
        self.historical_max_speed = 0.0
        self.historical_max_force = 0.0

        self.punch_count_var.set("0")
        self.previous_speed_var.set("0.00")
        self.previous_force_var.set("0.00")
        self.historical_speed_var.set("0.00")
        self.historical_force_var.set("0.00")

    def start(self):
        """Starts the Tkinter main loop."""
        self.root.mainloop()
