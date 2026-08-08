import os
import sys
import time
import cv2
from dotenv import load_dotenv

# Load environment configuration
load_dotenv()

RTSP_URL = os.getenv("RTSP_URL")
RTSP_SUB_URL = os.getenv("RTSP_SUB_URL")

def capture_snapshot(url=RTSP_URL, output_path="snapshots/snapshot.jpg"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    print(f"Connecting to RTSP stream: {url}")
    
    cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if not cap.isOpened():
        print("❌ Error: Unable to open RTSP stream.")
        return False

    ret, frame = cap.read()
    if ret:
        height, width, channels = frame.shape
        print(f"✅ Success! Captured frame ({width}x{height}, {channels} channels)")
        cv2.imwrite(output_path, frame)
        print(f"📷 Snapshot saved to: {output_path}")
        cap.release()
        return True
    else:
        print("❌ Error: Connected to stream but failed to read frame.")
        cap.release()
        return False

def live_stream(url=RTSP_URL):
    print(f"Starting low-latency live stream from: {url}")
    print("Press 'q' in the video window to quit.")
    
    cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if not cap.isOpened():
        print("❌ Error: Unable to open RTSP stream.")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            print("⚠️ Stream disconnected or frame drop.")
            break

        cv2.imshow("Camera Stream - Eagle Cement", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "snapshot"
    
    if mode == "stream":
        live_stream()
    else:
        capture_snapshot()
