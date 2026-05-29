import cv2
import mediapipe as mp
import numpy as np
import time
import winsound

def play_rep_audio(count):
    path = f'audio/{count}.wav'
    try:
        winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
    except Exception as e:
        pass

def play_wrong_audio():
    path = 'audio/wrong.wav'
    try:
        winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
    except Exception as e:
        pass

mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

# Independent counters and states
counter_l, counter_r = 0, 0
stage_l, stage_r = "down", "down"
min_time = 0.5
last_time_l, last_time_r = 0, 0
partial_l, partial_r = False, False

cap = cv2.VideoCapture(0)

# wrist curl requires tracking wrist flexion, using elbow, wrist, and hand joint
def calculate_angle(a, b, c):
    a, b, c = np.array(a), np.array(b), np.array(c)
    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
    angle = np.abs(radians*180.0/np.pi)
    return 360 - angle if angle > 180.0 else angle

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

            l_el = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x, landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
            l_wr = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x, landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y]
            l_index = [landmarks[mp_pose.PoseLandmark.LEFT_INDEX.value].x, landmarks[mp_pose.PoseLandmark.LEFT_INDEX.value].y]

            r_el = [landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].y]
            r_wr = [landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].y]
            r_index = [landmarks[mp_pose.PoseLandmark.RIGHT_INDEX.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_INDEX.value].y]

            # The angle between elbow -> wrist -> index finger maps wrist flexion
            angle_l = calculate_angle(l_el, l_wr, l_index)
            angle_r = calculate_angle(r_el, r_wr, r_index)

            cur_time = time.time()

            # WRIST CURL LOGIC LEFT
            # When forearm is flat, hand extended neutral = ~160-180
            # curled = < 130
            if angle_l > 160:
                if stage_l == "partial" and partial_l:
                    play_wrong_audio()
                stage_l = "down" # Hand extended / flat
                partial_l = False
            elif angle_l < 130:
                if stage_l in ["down", "partial"] and cur_time - last_time_l > min_time:
                    stage_l = "up" # Hand curled up towards forearm
                    counter_l += 1
                    play_rep_audio(counter_l)
                    last_time_l = cur_time
                partial_l = False
            elif 130 <= angle_l <= 150 and stage_l == "down":
                stage_l = "partial" # Started curling but hasn't closed angle
                partial_l = True

            # WRIST RIGHT
            if angle_r > 160:
                if stage_r == "partial" and partial_r:
                    play_wrong_audio()
                stage_r = "down"
                partial_r = False
            elif angle_r < 130:
                if stage_r in ["down", "partial"] and cur_time - last_time_r > min_time:
                    stage_r = "up"
                    counter_r += 1
                    play_rep_audio(counter_r)
                    last_time_r = cur_time
                partial_r = False
            elif 130 <= angle_r <= 150 and stage_r == "down":
                stage_r = "partial"
                partial_r = True

            # Draw counters
            cv2.putText(image, 'L FOREARM', (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(image, str(counter_l), (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)
            if stage_l == "partial": cv2.putText(image, '!', (70, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)

            cv2.putText(image, 'R FOREARM', (450, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(image, str(counter_r), (450, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)
            if stage_r == "partial": cv2.putText(image, '!', (500, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)

        except:
            pass

        mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
        cv2.imshow('SMART FOREARM WRIST CURL TRACKER', image)

        if cv2.waitKey(10) & 0xFF == ord('q'): break

cap.release()
cv2.destroyAllWindows()