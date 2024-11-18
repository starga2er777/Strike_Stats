import numpy as np
MOTION_THRESHOLD = 3
CLEANSE_THRESHOLD = 0.05
G_TO_MS2 = 9.80665
MOTION_STATE_REMAIN = 5
rest_counter = MOTION_STATE_REMAIN

def cleanse_accel(ax, ay, az):
    if abs(ax) < CLEANSE_THRESHOLD:
        ax = 0
    if abs(ay) < CLEANSE_THRESHOLD:
        ay = 0
    if abs(ay) < CLEANSE_THRESHOLD:
        az = 0
    return ax, ay, az
    

def detect_motion(accel : tuple, delta_time, current_state):
    global rest_counter
    magnitude = np.linalg.norm(accel)
    jerk = magnitude * G_TO_MS2 * delta_time
    if current_state == 'Motion' and jerk <= MOTION_THRESHOLD:
        if rest_counter > 0:
            rest_counter = rest_counter - 1
            return 'Motion'
    elif current_state == 'Static' and jerk > MOTION_THRESHOLD:
        rest_counter = MOTION_STATE_REMAIN
        return 'Motion'
    elif current_state == 'Motion' and jerk > MOTION_THRESHOLD:
        if rest_counter > (MOTION_STATE_REMAIN // 2):
            rest_counter = rest_counter - 1
            return 'Motion'
    else:
        return 'Static'
        
def update_spd(accel : tuple, delta_time):
    delta_vx = accel[0] * G_TO_MS2 * delta_time
    delta_vy = accel[1] * G_TO_MS2 * delta_time
    delta_vz = accel[2] * G_TO_MS2 * delta_time
    return np.array([delta_vx, delta_vy, delta_vz])