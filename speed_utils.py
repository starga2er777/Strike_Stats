# speed_utils.py
import numpy as np

G_TO_MS2 = 9.80665
MOTION_THRESHOLD = 3.0
CLEANSE_THRESHOLD = 0.05
MOTION_STATE_REMAIN = 5

class SpeedUtils:
    def __init__(self):
        self.rest_counter = MOTION_STATE_REMAIN

    def cleanse_accel(self, ax: float, ay: float, az: float) -> tuple:
        """
        Removes small accelerations below the cleanse threshold.
        """
        ax = ax if abs(ax) >= CLEANSE_THRESHOLD else 0.0
        ay = ay if abs(ay) >= CLEANSE_THRESHOLD else 0.0
        az = az if abs(az) >= CLEANSE_THRESHOLD else 0.0
        return ax, ay, az

    def detect_motion(self, accel: tuple, delta_time: float, current_state: str) -> str:
        """
        Detects whether the current state is 'Motion' or 'Static' based on acceleration.
        """
        magnitude = np.linalg.norm(accel)
        jerk = magnitude * G_TO_MS2 * delta_time

        if current_state == 'Motion':
            if jerk <= MOTION_THRESHOLD:
                self.rest_counter -= 1
                if self.rest_counter <= 0:
                    self.rest_counter = MOTION_STATE_REMAIN
                    return 'Static'
                return 'Motion'
            else:
                self.rest_counter = MOTION_STATE_REMAIN
                return 'Motion'
        else:  # Static state
            if jerk > MOTION_THRESHOLD:
                self.rest_counter = MOTION_STATE_REMAIN
                return 'Motion'
            return 'Static'

    def update_speed(self, accel: tuple, delta_time: float) -> np.ndarray:
        """
        Updates the velocity vector based on acceleration and elapsed time.
        """
        delta_v = np.array([
            accel[0] * G_TO_MS2 * delta_time,
            accel[1] * G_TO_MS2 * delta_time,
            accel[2] * G_TO_MS2 * delta_time
        ])
        return delta_v
