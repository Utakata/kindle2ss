import time
import os
import shutil
from PIL import Image, ImageChops
import mss
import platform
from threading import Thread, Event
import numpy as np

# Handle headless environment for pyautogui
try:
    import pyautogui
    if platform.system() == "Linux" and os.environ.get("DISPLAY") is None:
        raise ImportError("Headless environment detected")

    try:
        pyautogui.FAILSAFE = True
    except AttributeError:
        pass
except (ImportError, KeyError):
    # Mock pyautogui
    class MockPyAutoGUI:
        FAILSAFE = False
        def press(self, key):
            pass # Mock

    pyautogui = MockPyAutoGUI()

class CaptureEngine:
    def __init__(self, save_dir="output", interval=1.0, turn_key='left'):
        self.save_dir = save_dir
        self.interval = interval
        self.turn_key = turn_key
        self.running = False
        self.paused = False
        self.stop_event = Event()
        self.capture_region = None # (left, top, width, height)
        self.header_height = 0
        self.footer_height = 0
        self.duplicate_threshold = 3
        self.consecutive_duplicates = 0
        self.last_image = None
        self.page_count = 0

        self.sct = None

    def _init_mss(self):
        if self.sct is None:
            try:
                self.sct = mss.mss()
            except Exception:
                 # Mock for headless tests
                 class MockMSS:
                     def grab(self, region):
                         # Return a dummy object with size and bgra
                         class DummyShot:
                             size = (region['width'], region['height'])
                             bgra = b'\x00' * (region['width'] * region['height'] * 4)
                         return DummyShot()
                 self.sct = MockMSS()

    def set_region(self, x, y, w, h):
        self.capture_region = {"top": int(y), "left": int(x), "width": int(w), "height": int(h)}

    def set_crop_margins(self, top_px, bottom_px):
        self.header_height = int(top_px)
        self.footer_height = int(bottom_px)

    def _ensure_dir(self):
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)

    def _get_screenshot(self):
        self._init_mss()
        if not self.capture_region:
            raise ValueError("Capture region not set")

        # Capture
        sct_img = self.sct.grab(self.capture_region)
        img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
        return img

    def _is_duplicate(self, img1, img2):
        if img1 is None or img2 is None:
            return False

        # Crop header/footer for comparison
        w, h = img1.size
        # Valid crop?
        if self.header_height + self.footer_height < h:
            box = (0, self.header_height, w, h - self.footer_height)
            c1 = img1.crop(box)
            c2 = img2.crop(box)
        else:
            c1 = img1
            c2 = img2

        # Fast difference check
        diff = ImageChops.difference(c1, c2)
        if diff.getbbox():
            return False # Differences found
        return True # Identical

    def start_capture(self, callback_status=None):
        self._ensure_dir()
        self.running = True
        self.stop_event.clear()
        self.page_count = 0
        self.consecutive_duplicates = 0
        self.last_image = None

        thread = Thread(target=self._capture_loop, args=(callback_status,))
        thread.daemon = True
        thread.start()

    def stop_capture(self):
        self.running = False
        self.stop_event.set()

    def _capture_loop(self, callback_status):
        while self.running and not self.stop_event.is_set():
            if self.paused:
                time.sleep(0.5)
                continue

            try:
                # 1. Capture
                current_img = self._get_screenshot()

                # 2. Check Duplicate
                if self._is_duplicate(self.last_image, current_img):
                    self.consecutive_duplicates += 1
                    if callback_status:
                        callback_status("duplicate", self.consecutive_duplicates)
                else:
                    self.consecutive_duplicates = 0
                    self.page_count += 1

                    # Save
                    filename = f"page_{self.page_count:04d}.png"
                    filepath = os.path.join(self.save_dir, filename)
                    current_img.save(filepath)
                    self.last_image = current_img

                    if callback_status:
                        callback_status("saved", filepath)

                    # 3. Turn Page
                    self._press_key()

                # Check stop condition
                if self.consecutive_duplicates >= self.duplicate_threshold:
                    if callback_status:
                        callback_status("finished", "Duplicate threshold reached")
                    self.stop_capture()
                    break

                # Wait
                time.sleep(self.interval)

            except Exception as e:
                if callback_status:
                    callback_status("error", str(e))
                self.stop_capture()
                break

    def _press_key(self):
        try:
            pyautogui.press(self.turn_key)
        except Exception as e:
            print(f"Key press failed: {e}")

if __name__ == "__main__":
    # Test stub
    engine = CaptureEngine(save_dir="test_output")
    engine.set_region(0, 0, 100, 100)
    print("Engine initialized")
