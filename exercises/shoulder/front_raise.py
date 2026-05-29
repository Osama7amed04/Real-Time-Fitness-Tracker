import cv2
import mediapipe as mp
import numpy as np
import time
import winsound
import os

def play_rep_audio(count):
    path = f"audio/{count}.wav"
    abs_path = os.path.abspath(path)
    if os.path.exists(abs_path):
        try:
            winsound.PlaySound(abs_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
        except Exception:
            pass

def play_wrong_audio():
    path = "audio/wrong.wav"
    abs_path = os.path.abspath(path)
    if os.path.exists(abs_path):
        try:
            winsound.PlaySound(abs_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
        except Exception:
            pass

def calculate_angle(a, b, c):
    a, b, c = np.array(a), np.array(b), np.array(c)
    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
    angle = np.abs(radians*180.0/np.pi)
    return 360 - angle if angle > 180.0 else angle

def calculate_slope_angle(p1, p2):
    dy = p2[1] - p1[1]
    dx = p2[0] - p1[0]
    return np.abs(np.arctan2(dy, dx) * 180.0 / np.pi)

mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose
cap = cv2.VideoCapture(0)

state = {"counter_l": 0, "counter_r": 0, "stage_l": "down", "stage_r": "down", "error_msg": "", "error_time": 0, "last_time_l": 0, "last_time_r": 0}
min_time = 0.5
ANGLE_UP = 80
ANGLE_DOWN = 30

with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break

        frame = cv2.resize(frame, (640, 480))
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False
        results = pose.process(image)
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        try:
            landmarks = results.pose_landmarks.landmark

            l_hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x, landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
            l_sh = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x, landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
            l_el = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x, landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
            l_wr = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x, landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y]
            
            r_hip = [landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].y]
            r_sh = [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y]
            r_el = [landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].y]
            r_wr = [landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].y]

            torso_angle_l = calculate_slope_angle(l_sh, l_hip)
            torso_angle_r = calculate_slope_angle(r_sh, r_hip)
            angle_l = calculate_angle(l_hip, l_sh, l_el)
            angle_r = calculate_angle(r_hip, r_sh, r_el)

            cur_time = time.time()
            is_valid_l, is_valid_r = True, True
            
            if torso_angle_l < 60:
                is_valid_l = False
                state["error_msg"] = "STAND STRAIGHT L!"
                state["error_time"] = cur_time
            if torso_angle_r < 60:
                is_valid_r = False
                state["error_msg"] = "STAND STRAIGHT R!"
                state["error_time"] = cur_time

            # LEFT ARM LOGIC
            if is_valid_l:
                if angle_l < ANGLE_DOWN:
                    if state["stage_l"] == "going_up":
                        state["error_msg"] = "HALF REP L! GO HIGHER!"
                        state["error_time"] = time.time()
                        play_wrong_audio()
                    elif state["stage_l"] == "going_down":
                        if cur_time - state["last_time_l"] > min_time:
                            state["counter_l"] += 1
                            play_rep_audio(state["counter_l"])
                            state["last_time_l"] = cur_time
                    state["stage_l"] = "down"

                elif angle_l > ANGLE_UP:
                    if state["stage_l"] == "going_down":
                        state["error_msg"] = "FAILED L! LOWER ARM FULLY!"
                        state["error_time"] = time.time()
                        play_wrong_audio()
                    state["stage_l"] = "up"

                elif ANGLE_DOWN <= angle_l <= ANGLE_UP:
                    if state["stage_l"] == "down":
                        state["stage_l"] = "going_up"
                    elif state["stage_l"] == "up":
                        state["stage_l"] = "going_down"
            else:
                if state["stage_l"] in ["going_up", "going_down"]: 
                    play_wrong_audio()

            # RIGHT ARM LOGIC
            if is_valid_r:
                if angle_r < ANGLE_DOWN:
                    if state["stage_r"] == "going_up":
                        state["error_msg"] = "HALF REP R! GO HIGHER!"
                        state["error_time"] = time.time()
                        play_wrong_audio()
                    elif state["stage_r"] == "going_down":
                        if cur_time - state["last_time_r"] > min_time:
                            state["counter_r"] += 1
                            play_rep_audio(state["counter_r"])
                            state["last_time_r"] = cur_time
                    state["stage_r"] = "down"

                elif angle_r > ANGLE_UP:
                    if state["stage_r"] == "going_down":
                        state["error_msg"] = "FAILED R! LOWER ARM FULLY!"
                        state["error_time"] = time.time()
                        play_wrong_audio()
                    state["stage_r"] = "up"

                elif ANGLE_DOWN <= angle_r <= ANGLE_UP:
                    if state["stage_r"] == "down":
                        state["stage_r"] = "going_up"
                    elif state["stage_r"] == "up":
                        state["stage_r"] = "going_down"
            else:
                if state["stage_r"] in ["going_up", "going_down"]: 
                    play_wrong_audio()

            cv2.putText(image, "FRONT RAISE", (150, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            cv2.putText(image, "LEFT", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            cv2.putText(image, str(state["counter_l"]), (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)
            cv2.putText(image, "RIGHT", (450, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            cv2.putText(image, str(state["counter_r"]), (450, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)

            if time.time() - state["error_time"] < 2.0:
                cv2.putText(image, state["error_msg"], (100, 400), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)

        except Exception as e:
            pass

        mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
        cv2.imshow("FRONT RAISE TRACKER", image)

        if cv2.waitKey(10) & 0xFF == ord('q'): 
            break

cap.release()
cv2.destroyAllWindows()
