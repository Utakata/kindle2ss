import platform
import subprocess
import time
import sys

class WindowDetector:
    def __init__(self):
        self.os_type = platform.system()

    def get_active_window_title(self):
        """Returns the title of the currently active window."""
        try:
            if self.os_type == "Windows":
                return self._get_active_window_title_windows()
            elif self.os_type == "Linux":
                return self._get_active_window_title_linux()
            elif self.os_type == "Darwin":
                return self._get_active_window_title_macos()
            else:
                return None
        except Exception as e:
            print(f"Error getting active window title: {e}")
            return None

    def _get_active_window_title_windows(self):
        try:
            import ctypes
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
            buff = ctypes.create_unicode_buffer(length + 1)
            ctypes.windll.user32.GetWindowTextW(hwnd, buff, length + 1)
            return buff.value
        except ImportError:
            return None

    def _get_active_window_title_linux(self):
        # Use xprop to get the active window ID and then its title
        try:
            root = subprocess.check_output(['xprop', '-root', '_NET_ACTIVE_WINDOW']).decode('utf-8')
            # Output format: _NET_ACTIVE_WINDOW(WINDOW): window id # 0x...
            try:
                window_id = root.split()[-1]
                if window_id == "0x0":
                    return None
            except IndexError:
                return None

            window_props = subprocess.check_output(['xprop', '-id', window_id, 'WM_NAME']).decode('utf-8')
            # Output format: WM_NAME(STRING) = "Title"
            # or WM_NAME(UTF8_STRING) = "Title"
            if '"' in window_props:
                return window_props.split('"', 1)[1].rsplit('"', 1)[0]
            return None
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None

    def _get_active_window_title_macos(self):
        # macOS implementation (requires applescript or similar)
        # For now, return None or implement a basicosascript call if needed.
        # Simple implementation using AppleScript via osascript
        try:
            script = 'tell application "System Events" to get name of first application process whose frontmost is true'
            result = subprocess.check_output(['osascript', '-e', script]).decode('utf-8').strip()
            return result
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None

if __name__ == "__main__":
    detector = WindowDetector()
    print(f"Current OS: {detector.os_type}")
    print(f"Active Window: {detector.get_active_window_title()}")
