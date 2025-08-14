"""Video stream processor for licence plate recognition.

This script connects to an RTSP camera, periodically saves frames, sends them
to an external LPR service for recognition, and posts any detected plate to
the Instagate backend at `/lpr-event`.  The recognition logic is kept in
`lpr_recognizer.py` to separate I/O from the core algorithm.
"""

import os
import time
import cv2
import requests

from lpr_recognizer import recognize_plate

# === CONFIGURATION ===
# Replace with your camera's RTSP stream URI; use 0 for a local webcam.
RTSP_URL = os.environ.get("LPR_RTSP_URL", "0")
# API key for OpenALPR (or similar service); set as env var for security.
API_KEY = os.environ.get("OPENALPR_API_KEY", "")
# Directory to store captured frames
SAVE_FOLDER = os.environ.get("LPR_SAVE_FOLDER", "captured_frames")
# Process every Nth frame to reduce API usage
FRAME_SKIP = int(os.environ.get("LPR_FRAME_SKIP", "30"))

# Ensure the save folder exists
os.makedirs(SAVE_FOLDER, exist_ok=True)


def main() -> None:
    """Connect to the camera and process frames indefinitely."""
    cap = cv2.VideoCapture(RTSP_URL)
    if not cap.isOpened():
        print(f"Failed to connect to camera at {RTSP_URL}.")
        return

    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to read frame.")
            break

        if frame_count % FRAME_SKIP == 0:
            timestamp = int(time.time())
            image_path = os.path.join(SAVE_FOLDER, f"frame_{timestamp}.jpg")
            cv2.imwrite(image_path, frame)

            # Recognize plate using external API
            plate, conf = recognize_plate(image_path, API_KEY)
            if plate:
                print(f"[✓] Plate: {plate} | Confidence: {conf:.1f}%")
                # send detected plate to backend
                try:
                    resp = requests.post(
                        "http://127.0.0.1:5000/lpr-event",
                        json={"plate": plate, "confidence": conf, "timestamp": timestamp},
                        timeout=3,
                    )
                    if resp.status_code != 200:
                        print(f"Backend responded with status {resp.status_code}: {resp.text}")
                except requests.RequestException as exc:
                    print(f"Error posting to backend: {exc}")
            else:
                print("[x] No plate detected.")

        frame_count += 1
        cv2.imshow("LPR Camera", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
