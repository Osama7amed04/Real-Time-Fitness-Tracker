import cv2
import mediapipe as mp
import numpy as np
import time
import os
import winsound

def play_rep_audio(count):
    path = f'audio/{count}.wav'
    print(f"Playing audio for count: {count}")
    try:
        winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
    except Exception as e:
        print(f"Audio error for {count}: {e}")

def play_wrong_audio():
    path = 'audio/wrong.wav'
    print("Playing wrong rep audio")
    try:
        winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
    except Exception as e:
        print(f"Audio error for wrong: {e}")

# Initialize MediaPipe Pose
mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

# Repetition counter variables
counter = 0
stage = None

# Time buffer to avoid double-counting
last_rep_time = 0
min_time_between_reps = 0.5  # seconds

# Video capture
cap = cv2.VideoCapture(0)

# Output video writer
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter('triceps_session.mp4', fourcc, 20.0, (640, 480))

# Calculate angle between three points
def calculate_angle(a, b, c):
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)
    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
    angle = np.abs(radians*180.0/np.pi)
    if angle > 180.0:
        angle = 360 - angle
    return angle

# Pose detection
with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.resize(frame, (640, 480))

        # Convert to RGB
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False
        results = pose.process(image)
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        try:
            landmarks = results.pose_landmarks.landmark

            # Triceps extension (e.g. overhead or pushdown)
            # Both rely on elbow joint opening

            # Left arm
            l_shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,
                          landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
            l_elbow = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x,
                       landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
            l_wrist = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x,
                       landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y]

            # Right arm
            r_shoulder = [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x,
                          landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y]
            r_elbow = [landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].x,
                       landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].y]
            r_wrist = [landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].x,
                       landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].y]

            # Use arm closer to camera
            l_elbow_z = landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].z
            r_elbow_z = landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].z
            use_left = l_elbow_z < r_elbow_z

            if use_left:
                angle = calculate_angle(l_shoulder, l_elbow, l_wrist)
                arm_side = "Left"
            else:
                angle = calculate_angle(r_shoulder, r_elbow, r_wrist)
                arm_side = "Right"

            # Display angles and arm used
            cv2.putText(image, f'Elbow: {int(angle)}', (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            cv2.putText(image, f'Using: {arm_side} Arm', (20, 70),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

            # Triceps extension logic
            # Start position / curled = elbow angle < 90
            # End position / extended = elbow angle > 160
            current_time = time.time()
            if angle < 90:
                stage = "down" # elbows bent
            elif angle > 150 and stage == "down":
                if current_time - last_rep_time > min_time_between_reps:
                    stage = "up" # elbows extended
                    counter += 1
                    play_rep_audio(counter)
                    last_rep_time = current_time

            # Rep counter text
            cv2.putText(image, "REPS", (20, 400),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            cv2.putText(image, str(counter), (120, 410),
                        cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 3)

        except:
            pass

        # Render skeleton
        mp_drawing.draw_landmarks(
            image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
            mp_drawing.DrawingSpec(color=(245, 117, 66), thickness=2, circle_radius=2),
            mp_drawing.DrawingSpec(color=(245, 66, 230), thickness=2, circle_radius=2)
        )

        # Show frame
        out.write(image)
        cv2.imshow('TRICEPS TRACKER', image)

        # Exit on 'q'
        if cv2.waitKey(10) & 0xFF == ord('q'):
            break

cap.release()
out.release()
cv2.destroyAllWindows()