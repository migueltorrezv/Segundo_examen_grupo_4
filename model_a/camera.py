# camera.py
import cv2
import subprocess
import os

def capture():
    subprocess.run(
        ['rpicam-still', '-o', '/tmp/frame.jpg', '--nopreview', '-t', '1'],
        capture_output=True
    )
    if not os.path.exists('/tmp/frame.jpg'):
        return None
    return cv2.imread('/tmp/frame.jpg')
