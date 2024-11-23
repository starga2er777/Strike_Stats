# visualization.py
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import queue
from typing import Any


class Visualizer:
    def __init__(self, update_queue: queue.Queue, command_queue: queue.Queue):
        self.update_queue = update_queue
        self.command_queue = command_queue
        self.punch_count = 0
        self.punch_forces = []
        self.punch_speeds = []
        self.max_data_points = 100  # Maximum number of historical records to display

        # Historical records
        self.history_max_speeds = []
        self.history_max_forces = []

        # Initialize Tkinter UI
        self.root = tk.Tk()
        self.root.title("Smart Boxing Glove Trainer")
        self.root.geometry("1200x800")  # Adjusted window size to accommodate new elements
        self.root.configure(bg="#34495e")

        self._create_widgets()
        self._init_plots()

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
        punch_meter_frame = tk.Frame(
            top_frame,
            bg="#1abc9c",
            highlightbackground="#16a085",
            highlightthickness=2
        )
        punch_meter_frame.pack(side="left", padx=10, fill="both", expand=True)

        punch_meter_label = tk.Label(
            punch_meter_frame,
            text="Punch Count",
            font=("Helvetica", 18, "bold"),
            bg="#1abc9c",
            fg="white"
        )
        punch_meter_label.pack(pady=5)

        self.punch_meter_canvas = tk.Canvas(
            punch_meter_frame,
            width=200,
            height=200,
            bg="white",
            highlightthickness=0
        )
        self.punch_meter_canvas.pack(pady=10)
        self.draw_circular_meter(self.punch_meter_canvas, self.punch_count)

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

        # Middle Frame for Current Speed and Force
        middle_frame = tk.Frame(self.root, bg="#34495e")
        middle_frame.pack(pady=10, padx=20, fill="x")

        # Current Max Speed
        speed_frame = tk.Frame(middle_frame, bg="#2c3e50", highlightbackground="#16a085", highlightthickness=2)
        speed_frame.pack(side="left", padx=10, fill="both", expand=True)

        speed_label = tk.Label(
            speed_frame,
            text="Current Max Speed (m/s)",
            font=("Helvetica", 16, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        speed_label.pack(pady=10)

        self.current_speed_var = tk.StringVar(value="0.00")
        current_speed_display = tk.Label(
            speed_frame,
            textvariable=self.current_speed_var,
            font=("Helvetica", 20, "bold"),
            bg="#2c3e50",
            fg="#1abc9c"
        )
        current_speed_display.pack(pady=10)

        # Current Max Force
        force_frame = tk.Frame(middle_frame, bg="#2c3e50", highlightbackground="#16a085", highlightthickness=2)
        force_frame.pack(side="left", padx=10, fill="both", expand=True)

        force_label = tk.Label(
            force_frame,
            text="Current Max Force (N)",
            font=("Helvetica", 16, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        force_label.pack(pady=10)

        self.current_force_var = tk.StringVar(value="0.00")
        current_force_display = tk.Label(
            force_frame,
            textvariable=self.current_force_var,
            font=("Helvetica", 20, "bold"),
            bg="#2c3e50",
            fg="#1abc9c"
        )
        current_force_display.pack(pady=10)

        # Historical Max Speed and Force
        history_frame = tk.Frame(self.root, bg="#34495e")
        history_frame.pack(pady=10, padx=20, fill="both", expand=True)

        # Historical Max Speed
        history_speed_frame = tk.Frame(history_frame, bg="#2c3e50", highlightbackground="#16a085", highlightthickness=2)
        history_speed_frame.pack(side="left", padx=10, fill="both", expand=True)

        history_speed_label = tk.Label(
            history_speed_frame,
            text="Historical Max Speeds (m/s)",
            font=("Helvetica", 16, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        history_speed_label.pack(pady=10)

        self.history_speed_listbox = tk.Listbox(
            history_speed_frame,
            font=("Helvetica", 14),
            bg="#ecf0f1",
            fg="#2c3e50"
        )
        self.history_speed_listbox.pack(pady=10, padx=10, fill="both", expand=True)

        # Historical Max Force
        history_force_frame = tk.Frame(history_frame, bg="#2c3e50", highlightbackground="#16a085", highlightthickness=2)
        history_force_frame.pack(side="left", padx=10, fill="both", expand=True)

        history_force_label = tk.Label(
            history_force_frame,
            text="Historical Max Forces (N)",
            font=("Helvetica", 16, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        history_force_label.pack(pady=10)

        self.history_force_listbox = tk.Listbox(
            history_force_frame,
            font=("Helvetica", 14),
            bg="#ecf0f1",
            fg="#2c3e50"
        )
        self.history_force_listbox.pack(pady=10, padx=10, fill="both", expand=True)

        # Visualization Frame
        visualization_frame = tk.Frame(self.root, bg="#2c3e50")
        visualization_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.fig, (self.force_ax, self.speed_ax) = plt.subplots(2, 1, figsize=(6, 8))
        self.fig.tight_layout(pad=3.0)

        self.canvas = FigureCanvasTkAgg(self.fig, visualization_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        # Footer
        footer_label = tk.Label(
            self.root,
            text="Designed for Performance Tracking",
            font=("Helvetica", 12),
            bg="#34495e",
            fg="gray"
        )
        footer_label.pack(pady=10)

    def _init_plots(self):
        """Initializes the force and speed plots."""
        # Configure Punch Force Plot
        self.force_ax.set_title("Punch Force", fontsize=14, color="white")
        self.force_ax.set_facecolor("#2c3e50")
        self.force_ax.set_ylim(0, 10)
        self.force_ax.set_ylabel("Force (N)", color="white")
        self.force_ax.set_xlabel("Punch Count", color="white")
        self.force_ax.tick_params(axis='x', colors='white')
        self.force_ax.tick_params(axis='y', colors='white')

        # Configure Punch Speed Plot
        self.speed_ax.set_title("Punch Speed", fontsize=14, color="white")
        self.speed_ax.set_facecolor("#34495e")
        self.speed_ax.set_ylim(0, 25)
        self.speed_ax.set_ylabel("Speed (m/s)", color="white")
        self.speed_ax.set_xlabel("Punch Count", color="white")
        self.speed_ax.tick_params(axis='x', colors='white')
        self.speed_ax.tick_params(axis='y', colors='white')

    def process_queue(self):
        """Processes incoming data from the queue and updates the UI."""
        try:
            while True:
                update_type, value = self.update_queue.get_nowait()
                if update_type == 'count':
                    self.update_punch_count(value)
                elif update_type == 'force':
                    self.update_current_force(value)
                elif update_type == 'speed':
                    self.update_current_speed(value)
                elif update_type == 'history_max_speed':
                    self.update_history_max_speed(value)
                elif update_type == 'history_max_force':
                    self.update_history_max_force(value)
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
        self.draw_circular_meter(self.punch_meter_canvas, self.punch_count)

    def update_current_speed(self, speed: float):
        """Updates the current max speed display."""
        self.current_speed_var.set(f"{speed:.2f}")

    def update_current_force(self, force: float):
        """Updates the current max force display."""
        self.current_force_var.set(f"{force:.2f}")

    def update_history_max_speed(self, speed: float):
        """Updates the historical max speed list."""
        self.history_max_speeds.append(speed)
        self.history_speed_listbox.insert(tk.END, f"{speed:.2f} m/s")
        # Optionally, limit the number of historical records displayed
        if len(self.history_max_speeds) > self.max_data_points:
            self.history_max_speeds.pop(0)
            self.history_speed_listbox.delete(0)

    def update_history_max_force(self, force: float):
        """Updates the historical max force list."""
        self.history_max_forces.append(force)
        self.history_force_listbox.insert(tk.END, f"{force:.2f} N")
        # Optionally, limit the number of historical records displayed
        if len(self.history_max_forces) > self.max_data_points:
            self.history_max_forces.pop(0)
            self.history_force_listbox.delete(0)

    def draw_circular_meter(self, canvas: tk.Canvas, value: int):
        """Draws a circular meter representing the punch count."""
        canvas.delete("all")  # Clear previous drawings
        angle = (value % 100) * 3.6  # Full circle is 360 degrees
        color = "green" if value < 30 else "orange" if value < 70 else "red"
        canvas.create_arc(20, 20, 180, 180, start=90, extent=-angle, fill=color, outline="")
        canvas.create_text(
            100,
            100,
            text=f"{value}\nPunches",
            font=("Helvetica", 16, "bold"),
            fill="black"
        )

    def update_punch_force(self, force: float):
        """Updates the punch force bar chart."""
        self.punch_forces.append(force)
        if len(self.punch_forces) > self.max_data_points:
            self.punch_forces.pop(0)

        self.force_ax.clear()
        colors = [
            "#5cb85c" if f < 3 else "#f0ad4e" if f < 7 else "#d9534f"
            for f in self.punch_forces
        ]
        self.force_ax.bar(
            range(1, len(self.punch_forces) + 1),
            self.punch_forces,
            color=colors,
            label="Force (N)"
        )
        self._reconfigure_force_plot()

        self.canvas.draw()

    def _reconfigure_force_plot(self):
        """Reconfigures the force plot after updating."""
        self.force_ax.set_title("Punch Force", fontsize=14, color="white")
        self.force_ax.set_facecolor("#2c3e50")
        self.force_ax.set_ylim(0, max(10, max(self.punch_forces, default=10) + 1))
        self.force_ax.set_ylabel("Force (N)", color="white")
        self.force_ax.set_xlabel("Punch Count", color="white")
        self.force_ax.tick_params(axis='x', colors='white')
        self.force_ax.tick_params(axis='y', colors='white')

        if self.punch_forces:
            self.force_ax.legend()

    def update_punch_speed(self, speed: float):
        """Updates the punch speed line chart."""
        self.punch_speeds.append(speed)
        if len(self.punch_speeds) > self.max_data_points:
            self.punch_speeds.pop(0)

        self.speed_ax.clear()
        x = list(range(1, len(self.punch_speeds) + 1))
        self.speed_ax.plot(
            x,
            self.punch_speeds,
            label="Speed (m/s)",
            color="#1abc9c",
            linewidth=2,
            marker="o",
            markerfacecolor="white"
        )
        self.speed_ax.fill_between(
            x,
            self.punch_speeds,
            color="#16a085",
            alpha=0.5
        )
        self._reconfigure_speed_plot()

        self.canvas.draw()

    def _reconfigure_speed_plot(self):
        """Reconfigures the speed plot after updating."""
        self.speed_ax.set_title("Punch Speed", fontsize=14, color="white")
        self.speed_ax.set_facecolor("#34495e")
        self.speed_ax.set_ylim(0, max(25, max(self.punch_speeds, default=25) + 1))
        self.speed_ax.set_ylabel("Speed (m/s)", color="white")
        self.speed_ax.set_xlabel("Punch Count", color="white")
        self.speed_ax.tick_params(axis='x', colors='white')
        self.speed_ax.tick_params(axis='y', colors='white')

        if self.punch_speeds:
            self.speed_ax.legend()

    def update_history_max_speed(self, speed: float):
        """Updates the historical max speed list."""
        self.history_max_speeds.append(speed)
        self.history_speed_listbox.insert(tk.END, f"{speed:.2f} m/s")
        # Optionally, limit the number of historical records displayed
        if len(self.history_max_speeds) > self.max_data_points:
            self.history_max_speeds.pop(0)
            self.history_speed_listbox.delete(0)

    def update_history_max_force(self, force: float):
        """Updates the historical max force list."""
        self.history_max_forces.append(force)
        self.history_force_listbox.insert(tk.END, f"{force:.2f} N")
        # Optionally, limit the number of historical records displayed
        if len(self.history_max_forces) > self.max_data_points:
            self.history_max_forces.pop(0)
            self.history_force_listbox.delete(0)

    def reset(self):
        """Handles the Reset button click."""
        # Send reset command to DataProcessor
        self.command_queue.put(('reset', None))
        # The UI will be reset upon receiving the 'reset' message from DataProcessor

    def reset_ui(self):
        """Resets the UI elements."""
        self.punch_count = 0
        self.history_max_speeds.clear()
        self.history_max_forces.clear()
        self.history_speed_listbox.delete(0, tk.END)
        self.history_force_listbox.delete(0, tk.END)
        self.draw_circular_meter(self.punch_meter_canvas, self.punch_count)
        self.current_speed_var.set("0.00")
        self.current_force_var.set("0.00")

        # Clear and reset force plot
        self.force_ax.clear()
        self._reconfigure_force_plot()

        # Clear and reset speed plot
        self.speed_ax.clear()
        self._reconfigure_speed_plot()

        self.canvas.draw()

    def start(self):
        """Starts the Tkinter main loop."""
        self.root.mainloop()
