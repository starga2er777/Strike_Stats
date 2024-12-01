import tkinter as tk
from tkinter import ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import queue

class Visualizer:
    def __init__(self, update_queue: queue.Queue, command_queue: queue.Queue):
        self.update_queue = update_queue
        self.command_queue = command_queue

        # Initialize data variables
        self.punch_count = 0
        self.previous_max_speed = 0.0
        self.previous_max_force = 0.0
        self.historical_max_speed = 0.0
        self.historical_max_force = 0.0
        self.speed_history = []
        self.force_history = []

        # Initialize main window
        self.root = tk.Tk()
        self.root.title("Smart Boxing Gloves Visualization")
        self.root.configure(bg='#2E3440')  # Dark background for modern look

        # Create the frames
        self.create_frames()

        # Create UI elements
        self.create_ui_elements()

        # Start periodic update
        self.root.after(100, self.update_ui)

    def create_frames(self):
        # Create a grid layout for better balance
        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=2)
        self.root.rowconfigure(2, weight=3)

        # Top frame for punch count and reset button
        self.frame_top = tk.Frame(self.root, bg='#2E3440')
        self.frame_top.grid(row=0, column=0, columnspan=2, sticky='nsew', padx=20, pady=10)

        # Middle frame for stats
        self.frame_middle = tk.Frame(self.root, bg='#2E3440')
        self.frame_middle.grid(row=1, column=0, columnspan=2, sticky='nsew', padx=20, pady=10)

        # Bottom left frame for speed graph
        self.frame_bottom_left = tk.Frame(self.root, bg='#2E3440')
        self.frame_bottom_left.grid(row=2, column=0, sticky='nsew', padx=20, pady=10)

        # Bottom right frame for force graph
        self.frame_bottom_right = tk.Frame(self.root, bg='#2E3440')
        self.frame_bottom_right.grid(row=2, column=1, sticky='nsew', padx=20, pady=10)

    def create_ui_elements(self):
        # Define colors
        bg_color = '#2E3440'      # Dark background
        primary_color = '#88C0D0'  # Soft blue for accents
        accent_color = '#81A1C1'   # Slightly darker blue
        text_color = '#ECEFF4'     # Light text for contrast

        # Fonts
        title_font = ("Segoe UI", 24, "bold")
        label_font = ("Segoe UI", 16)
        button_font = ("Segoe UI", 10)  # Smaller font size for the button

        # First frame (Top): Punch Count and Reset Button
        # Create a sub-frame to better align elements
        self.top_left_frame = tk.Frame(self.frame_top, bg=bg_color)
        self.top_left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.top_right_frame = tk.Frame(self.frame_top, bg=bg_color)
        self.top_right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Punch Count Label
        self.punch_count_label = tk.Label(
            self.top_left_frame, text="Punch Count: 0", font=title_font,
            bg=bg_color, fg=primary_color)
        self.punch_count_label.pack(anchor='w')

        # Progress bar (punch meter)
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Custom.Horizontal.TProgressbar", troughcolor=bg_color,
                        background=primary_color, thickness=20, bordercolor=bg_color)
        self.punch_meter = ttk.Progressbar(
            self.top_left_frame, orient='horizontal', length=200, mode='determinate',
            style="Custom.Horizontal.TProgressbar")
        self.punch_meter.pack(anchor='w', pady=10)
        self.punch_meter['maximum'] = 100

        # Reset button
        self.reset_button = tk.Button(
            self.top_right_frame, text="Reset", command=self.reset_data,
            bg=bg_color, fg=primary_color, font=button_font, activebackground=bg_color,
            activeforeground=accent_color, relief='flat', borderwidth=0)
        self.reset_button.pack(anchor='e', padx=10, pady=10)

        # Second frame (Middle): Latest and Max Stats
        # Use a grid layout for better balance
        self.frame_middle.columnconfigure(0, weight=1, uniform='middle')
        self.frame_middle.columnconfigure(1, weight=1, uniform='middle')

        # Latest Stats
        self.latest_stats_frame = tk.Frame(self.frame_middle, bg=bg_color)
        self.latest_stats_frame.grid(row=0, column=0, sticky='nsew', padx=10)

        self.latest_label = tk.Label(
            self.latest_stats_frame, text="Latest Stats", font=label_font,
            bg=bg_color, fg=accent_color)
        self.latest_label.pack(anchor='w')

        self.latest_speed_label = tk.Label(
            self.latest_stats_frame, text="Speed: 0.0 m/s", font=label_font,
            bg=bg_color, fg=text_color)
        self.latest_speed_label.pack(anchor='w', pady=5)

        self.latest_force_label = tk.Label(
            self.latest_stats_frame, text="Force: 0.0 N", font=label_font,
            bg=bg_color, fg=text_color)
        self.latest_force_label.pack(anchor='w', pady=5)

        # Max Stats
        self.max_stats_frame = tk.Frame(self.frame_middle, bg=bg_color)
        self.max_stats_frame.grid(row=0, column=1, sticky='nsew', padx=10)

        self.max_label = tk.Label(
            self.max_stats_frame, text="Maximum Stats", font=label_font,
            bg=bg_color, fg=accent_color)
        self.max_label.pack(anchor='w')

        self.max_speed_label = tk.Label(
            self.max_stats_frame, text="Speed: 0.0 m/s", font=label_font,
            bg=bg_color, fg=text_color)
        self.max_speed_label.pack(anchor='w', pady=5)

        self.max_force_label = tk.Label(
            self.max_stats_frame, text="Force: 0.0 N", font=label_font,
            bg=bg_color, fg=text_color)
        self.max_force_label.pack(anchor='w', pady=5)

        # Third frame (Bottom Left): Line graph of speed
        self.figure_speed = Figure(figsize=(5, 4), dpi=100, facecolor=bg_color)
        self.ax_speed = self.figure_speed.add_subplot(111)
        self.ax_speed.set_title("Speed per Punch", color=text_color, fontsize=14)
        self.ax_speed.set_xlabel("Punch Number", color=text_color)
        self.ax_speed.set_ylabel("Speed (m/s)", color=text_color)
        self.ax_speed.tick_params(axis='x', colors=text_color)
        self.ax_speed.tick_params(axis='y', colors=text_color)
        self.ax_speed.set_facecolor(bg_color)
        self.figure_speed.subplots_adjust(left=0.15, right=0.95, top=0.9, bottom=0.15)

        self.canvas_speed = FigureCanvasTkAgg(self.figure_speed, master=self.frame_bottom_left)
        self.canvas_speed.draw()
        self.canvas_speed.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Fourth frame (Bottom Right): Bar graph of force
        self.figure_force = Figure(figsize=(5, 4), dpi=100, facecolor=bg_color)
        self.ax_force = self.figure_force.add_subplot(111)
        self.ax_force.set_title("Force per Punch", color=text_color, fontsize=14)
        self.ax_force.set_xlabel("Punch Number", color=text_color)
        self.ax_force.set_ylabel("Force (N)", color=text_color)
        self.ax_force.tick_params(axis='x', colors=text_color)
        self.ax_force.tick_params(axis='y', colors=text_color)
        self.ax_force.set_facecolor(bg_color)
        self.figure_force.subplots_adjust(left=0.15, right=0.95, top=0.9, bottom=0.15)

        self.canvas_force = FigureCanvasTkAgg(self.figure_force, master=self.frame_bottom_right)
        self.canvas_force.draw()
        self.canvas_force.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Store colors for later use
        self.intensity_colors = {
            'low': '#A3BE8C',    # Soft green
            'medium': '#EBCB8B', # Soft yellow
            'high': '#BF616A'    # Soft red
        }
        self.primary_color = primary_color
        self.text_color = text_color
        self.bg_color = bg_color

    def reset_data(self):
        # Send reset command to the command_queue
        self.command_queue.put(('reset', None))

    def handle_reset(self):
        # Reset data variables
        self.punch_count = 0
        self.previous_max_speed = 0.0
        self.previous_max_force = 0.0
        self.historical_max_speed = 0.0
        self.historical_max_force = 0.0
        self.speed_history.clear()
        self.force_history.clear()

        # Reset UI elements
        self.punch_count_label.config(text="Punch Count: 0")
        self.latest_speed_label.config(text="Speed: 0.0 m/s")
        self.latest_force_label.config(text="Force: 0.0 N")
        self.max_speed_label.config(text="Speed: 0.0 m/s")
        self.max_force_label.config(text="Force: 0.0 N")
        self.punch_meter['value'] = 0

        self.update_speed_graph()
        self.update_force_graph()

    def update_ui(self):
        try:
            while True:
                data = self.update_queue.get_nowait()
                key, value = data

                if key == 'reset':
                    self.handle_reset()
                elif key == 'previous_max_speed':
                    self.previous_max_speed = value
                    self.latest_speed_label.config(
                        text=f"Speed: {self.previous_max_speed:.2f} m/s")
                    self.speed_history.append(self.previous_max_speed)
                    self.update_speed_graph()
                elif key == 'previous_max_force':
                    self.previous_max_force = value
                    self.latest_force_label.config(
                        text=f"Force: {self.previous_max_force:.2f} N")
                    self.force_history.append(self.previous_max_force)
                    self.update_force_graph()
                elif key == 'historical_max_speed':
                    self.historical_max_speed = value
                    self.max_speed_label.config(
                        text=f"Speed: {self.historical_max_speed:.2f} m/s")
                elif key == 'historical_max_force':
                    self.historical_max_force = value
                    self.max_force_label.config(
                        text=f"Force: {self.historical_max_force:.2f} N")
                elif key == 'count':
                    self.punch_count = value
                    self.punch_count_label.config(text=f"Punch Count: {self.punch_count}")
                    # Update the punch meter
                    self.punch_meter['value'] = min(self.punch_count, 100)  # Example scaling
        except queue.Empty:
            pass
        except Exception as e:
            print(f"Error in UI update: {e}")

        # Schedule the next update
        self.root.after(100, self.update_ui)

    def update_speed_graph(self):
        self.ax_speed.clear()
        self.ax_speed.plot(
            self.speed_history, color=self.primary_color, linewidth=2, marker='o', linestyle='-')
        self.ax_speed.set_title("Speed per Punch", color=self.text_color, fontsize=14)
        self.ax_speed.set_xlabel("Punch Number", color=self.text_color)
        self.ax_speed.set_ylabel("Speed (m/s)", color=self.text_color)
        self.ax_speed.tick_params(axis='x', colors=self.text_color)
        self.ax_speed.tick_params(axis='y', colors=self.text_color)
        self.ax_speed.set_facecolor(self.bg_color)
        self.figure_speed.set_facecolor(self.bg_color)
        self.canvas_speed.draw()

    def update_force_graph(self):
        self.ax_force.clear()
        x = list(range(len(self.force_history)))
        y = self.force_history
        colors = [self.get_force_color(force) for force in y]
        self.ax_force.bar(x, y, color=colors)
        self.ax_force.set_title("Force per Punch", color=self.text_color, fontsize=14)
        self.ax_force.set_xlabel("Punch Number", color=self.text_color)
        self.ax_force.set_ylabel("Force (N)", color=self.text_color)
        self.ax_force.tick_params(axis='x', colors=self.text_color)
        self.ax_force.tick_params(axis='y', colors=self.text_color)
        self.ax_force.set_facecolor(self.bg_color)
        self.figure_force.set_facecolor(self.bg_color)
        self.canvas_force.draw()

    def get_force_color(self, force):
        # Determine color based on force intensity
        if force < 50:
            return self.intensity_colors['low']    # Low intensity
        elif force < 100:
            return self.intensity_colors['medium']  # Medium intensity
        else:
            return self.intensity_colors['high']   # High intensity

    def start(self):
        self.root.mainloop()