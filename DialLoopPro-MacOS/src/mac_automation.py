# mac_automation.py
"""
macOS-specific automation functions
"""

import subprocess
import time
import pyautogui
import applescript
import Quartz
from AppKit import NSWorkspace, NSApplicationActivateIgnoringOtherApps

class MacAutomation:
    """Handle macOS-specific automation tasks"""
    
    def activate_window(self, window_title):
        """Activate a window by title on macOS"""
        try:
            # Try AppleScript first (most reliable)
            script = f'''
            tell application "System Events"
                set frontmost of process "{window_title}" to true
            end tell
            '''
            subprocess.run(['osascript', '-e', script], check=False)
            
            # Alternative: Use NSWorkspace
            ws = NSWorkspace.sharedWorkspace()
            apps = ws.runningApplications()
            for app in apps:
                if window_title.lower() in app.localizedName().lower():
                    app.activateWithOptions_(NSApplicationActivateIgnoringOtherApps)
                    break
            
            time.sleep(0.5)
            return True
        except Exception as e:
            print(f"Window activation failed: {e}")
            return False
    
    def copy_next_number(self, spreadsheet_title):
        """Activate spreadsheet and copy next number"""
        try:
            # Activate spreadsheet
            if not self.activate_window(spreadsheet_title):
                return False
            
            time.sleep(0.3)
            
            # Press down arrow
            pyautogui.press('down')
            time.sleep(0.3)
            
            # Copy (Cmd+C on macOS)
            pyautogui.hotkey('command', 'c')
            time.sleep(0.5)
            
            return True
        except Exception as e:
            print(f"Copy failed: {e}")
            return False
    
    def paste_and_dial(self, dialer_title, x, y, prefix):
        """Paste number into dialer and dial"""
        try:
            # Activate dialer
            if not self.activate_window(dialer_title):
                return False
            
            time.sleep(0.5)
            
            # Click dial field
            pyautogui.moveTo(x, y, duration=0.2)
            pyautogui.click()
            time.sleep(0.2)
            
            # Type prefix if any
            if prefix:
                pyautogui.write(prefix)
                time.sleep(0.1)
            
            # Paste (Cmd+V on macOS)
            pyautogui.hotkey('command', 'v')
            time.sleep(0.3)
            
            # Press enter
            pyautogui.press('enter')
            time.sleep(0.5)
            
            return True
        except Exception as e:
            print(f"Dial failed: {e}")
            return False
    
    def get_mouse_position(self):
        """Get current mouse position"""
        return pyautogui.position()
    
    def get_window_info(self, window_title):
        """Get window position and size"""
        script = f'''
        tell application "System Events"
            tell process "{window_title}"
                set windowPos to position of window 1
                set windowSize to size of window 1
                return windowPos & windowSize
            end tell
        end tell
        '''
        
        try:
            result = subprocess.check_output(['osascript', '-e', script])
            coords = result.decode().strip().split(', ')
            return {
                'x': int(coords[0]),
                'y': int(coords[1]),
                'width': int(coords[2]),
                'height': int(coords[3])
            }
        except:
            return None
    
    def is_window_focused(self, window_title):
        """Check if a window is focused"""
        script = '''
        tell application "System Events"
            set frontApp to name of first application process whose frontmost is true
            return frontApp
        end tell
        '''
        
        try:
            result = subprocess.check_output(['osascript', '-e', script])
            front_app = result.decode().strip()
            return window_title.lower() in front_app.lower()
        except:
            return False