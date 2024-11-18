import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import queue

class Visualizer:
    def __init__(self, update_queue):
        self.update_queue = update_queue

        self.punch_count = 0
        self.punch_forces = []
        self.punch_speeds = []
        self.max_data_points = 10

        # Initialize Tkinter UI
        self.root = tk.Tk()
        self.root.title("Smart Boxing Glove Trainer")

        # Configure layout
        self.root.geometry("900x750")
        self.root.configure(bg="#34495e")

        # Title
        title_label = tk.Label(
            self.root,
            text="Smart Boxing Glove Trainer",
            font=("Helvetica", 22, "bold"),
            bg="#34495e",
            fg="#ecf0f1"
        )
        title_label.pack(pady=20)

        # Punch Count Section
        punch_meter_frame = tk.Frame(
            self.root,
            bg="#1abc9c",
            highlightbackground="#16a085",
            highlightthickness=2
        )
        punch_meter_frame.pack(pady=10, padx=20, fill="both")

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

        # Visualization Frame
        visualization_frame = tk.Frame(self.root, bg="#2c3e50")
        visualization_frame.pack(fill="both", expand=True, padx=10, pady=10)

        fig, (self.force_ax, self.speed_ax) = plt.subplots(2, 1, figsize=(6, 8))
        fig.tight_layout(pad=3.0)

        self.canvas = FigureCanvasTkAgg(fig, visualization_frame)
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

        # Initialize plots
        self.init_plots()

        # Start the periodic GUI update
        self.root.after(100, self.process_queue)

    def init_plots(self):
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
        self.speed_ax.set_xlabel("Time", color="white")
        self.speed_ax.tick_params(axis='x', colors='white')
        self.speed_ax.tick_params(axis='y', colors='white')

    def process_queue(self):
        try:
            while True:
                update_type, value = self.update_queue.get_nowait()
                if update_type == 'count':
                    self.update_punch_count(value)
                elif update_type == 'force':
                    self.update_punch_force(value)
                elif update_type == 'speed':
                    self.update_punch_speed(value)
        except queue.Empty:
            pass
        finally:
            # Schedule the next queue check
            self.root.after(100, self.process_queue)

    def update_punch_count(self, count):
        self.punch_count = count
        self.punch_meter_canvas.delete("all")
        self.draw_circular_meter(self.punch_meter_canvas, self.punch_count)

    def draw_circular_meter(self, canvas, value):
        canvas.delete("all")  # Clear previous drawings
        angle = (value % 100) * 3.6
        color = "green" if value < 30 else "orange" if value < 70 else "red"
        canvas.create_arc(20, 20, 180, 180, start=90, extent=-angle, fill=color, outline="")
        canvas.create_text(
            100,
            100,
            text=f"{value}\nPunches",
            font=("Helvetica", 16, "bold"),
            fill="black"
        )

    def update_punch_force(self, force):
        self.punch_forces.append(force)
        if len(self.punch_forces) > self.max_data_points:
            self.punch_forces.pop(0)

        self.force_ax.clear()
        colors = [
            "#5cb85c" if f < 3 else "#f0ad4e" if f < 7 else "#d9534f"
            for f in self.punch_forces
        ]
        bars = self.force_ax.bar(
            range(len(self.punch_forces)),
            self.punch_forces,
            color=colors,
            label="Force (N)"
        )
        self.force_ax.set_title("Punch Force", fontsize=14, color="white")
        self.force_ax.set_facecolor("#2c3e50")
        self.force_ax.set_ylim(0, 10)
        self.force_ax.set_ylabel("Force (N)", color="white")
        self.force_ax.set_xlabel("Punch Count", color="white")
        self.force_ax.tick_params(axis='x', colors='white')
        self.force_ax.tick_params(axis='y', colors='white')

        # Add legend only if there are bars
        if bars:
            self.force_ax.legend()

        self.canvas.draw()

    def update_punch_speed(self, speed):
        self.punch_speeds.append(speed)
        if len(self.punch_speeds) > self.max_data_points:
            self.punch_speeds.pop(0)

        self.speed_ax.clear()
        x = range(len(self.punch_speeds))
        speed_plot, = self.speed_ax.plot(
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
        self.speed_ax.set_title("Punch Speed", fontsize=14, color="white")
        self.speed_ax.set_facecolor("#34495e")
        self.speed_ax.set_ylim(0, 25)
        self.speed_ax.set_ylabel("Speed (m/s)", color="white")
        self.speed_ax.set_xlabel("Time", color="white")

        # Add legend only if the plot has a label
        if speed_plot.get_label():
            self.speed_ax.legend()

        self.canvas.draw()

    def start(self):
        self.root.mainloop()
