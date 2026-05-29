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

state = {"counter": 0, "stage": "start", "error_msg": "", "error_time": 0}
min_time_between_reps = 0.5
last_rep_time = 0
START_ANGLE = 160
TARGET_ANGLE = 90

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
            l_knee = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x, landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y]
            l_ankle = [landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].x, landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].y]
            l_foot = [landmarks[mp_pose.PoseLandmark.LEFT_FOOT_INDEX.value].x, landmarks[mp_pose.PoseLandmark.LEFT_FOOT_INDEX.value].y]
            
            r_hip = [landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].y]
            r_knee = [landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].y]
            r_ankle = [landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value].y]
            r_foot = [landmarks[mp_pose.PoseLandmark.RIGHT_FOOT_INDEX.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_FOOT_INDEX.value].y]

            use_left = landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].visibility > landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].visibility

            hip = l_hip if use_left else r_hip
            knee = l_knee if use_left else r_knee
            ankle = l_ankle if use_left else r_ankle
            foot = l_foot if use_left else r_foot

            knee_angle = calculate_angle(hip, knee, ankle)
            ankle_angle = calculate_angle(knee, ankle, foot)

            cur_time = time.time()
            
            if knee_angle > START_ANGLE:
                if state["stage"] == "going_target":
                    state["error_msg"] = "HALF CURL! PULL HIGHER!"
                    state["error_time"] = time.time()
                    play_wrong_audio()
                elif state["stage"] == "going_start":
                    if time.time() - last_rep_time > min_time_between_reps:
                        state["counter"] += 1
                        play_rep_audio(state["counter"])
                        last_rep_time = time.time()
                state["stage"] = "start"

            elif knee_angle < TARGET_ANGLE:
                if state["stage"] == "going_start":
                    state["error_msg"] = "FAILED REP! EXTEND LEG FULLY!"
                    state["error_time"] = time.time()
                    play_wrong_audio()
                state["stage"] = "target"

            elif TARGET_ANGLE <= knee_angle <= START_ANGLE:
                if state["stage"] == "start":
                    state["stage"] = "going_target"
                elif state["stage"] == "target":
                    state["stage"] = "going_start"

            cv2.putText(image, "BACK CURL", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 200, 0), 2)
            cv2.putText(image, "REPS: " + str(state["counter"]), (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 2)
            
            if time.time() - state["error_time"] < 2.0:
                cv2.putText(image, state["error_msg"], (20, 120), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)

        except Exception as e:
            pass

        mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
        cv2.imshow("BACK CURL TRACKER", image)

        if cv2.waitKey(10) & 0xFF == ord('q'): 
            break

cap.release()
cv2.destroyAllWindows()
