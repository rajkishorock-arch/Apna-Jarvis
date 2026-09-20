import os
import sys
import subprocess
import psutil
import pyautogui
import webbrowser
import time

# Add root folder to sys.path to allow absolute imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class SystemAutomation:
    def __init__(self):
        # Dictionary of common application names mapped to their launch commands or URLs
        self.app_mapping = {
            "chrome": "start chrome",
            "browser": "start chrome",
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "vscode": "code",
            "code": "code",
            "explorer": "explorer.exe",
            "taskmanager": "taskmgr.exe"
        }

    def open_app(self, app_name):
        """Launches an application or website based on string name."""
        app_name = app_name.lower().strip()
        
        if "youtube" in app_name:
            return self.open_url("https://www.youtube.com")
        if "google" in app_name:
            return self.open_url("https://www.google.com")
            
        # Check mapping first
        if app_name in self.app_mapping:
            cmd = self.app_mapping[app_name]
            try:
                subprocess.Popen(cmd, shell=True)
                print(f"[Automation] Opened {app_name}")
                return True
            except Exception as e:
                print(f"[Automation Error] Failed to open {app_name}: {e}")
                return False
        
        # Fallback to direct raw command
        try:
            subprocess.Popen(app_name, shell=True)
            print(f"[Automation] Attempted to open raw command: {app_name}")
            return True
        except Exception as e:
            print(f"[Automation Error] Failed to run {app_name}: {e}")
            return False

    def launch_app(self, app_name):
        """Alias for open_app."""
        return self.open_app(app_name)

    def close_app(self, process_name):
        """Terminates processes by matching their names."""
        process_name = process_name.lower().strip()
        closed_any = False
        
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                pname = proc.info['name'].lower()
                if process_name in pname or (process_name == "chrome" and "chrome" in pname) or (process_name == "code" and "code" in pname):
                    proc.terminate()
                    print(f"[Automation] Closed process {proc.info['name']} (PID: {proc.info['pid']})")
                    closed_any = True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
                
        return closed_any

    def open_url(self, url):
        """Opens a web page in the default web browser."""
        if not url.startswith("http"):
            url = "https://" + url
        try:
            webbrowser.open(url)
            print(f"[Automation] Opened URL: {url}")
            return True
        except Exception as e:
            print(f"[Automation Error] Failed to open URL {url}: {e}")
            return False

    def open_website(self, url):
        """Alias for open_url."""
        return self.open_url(url)

    def search_web(self, query):
        """Performs a Google search in the default web browser."""
        url = f"https://www.google.com/search?q={query}"
        return self.open_url(url)

    def take_screenshot(self, name_prefix="screenshot"):
        """Takes a screenshot and saves it to Pictures directory."""
        sc_dir = os.path.join(os.path.expanduser("~"), "Pictures", "Jarvis")
        os.makedirs(sc_dir, exist_ok=True)
        
        filename = f"{name_prefix}_{int(time.time())}.png"
        filepath = os.path.join(sc_dir, filename)
        
        try:
            screenshot = pyautogui.screenshot()
            screenshot.save(filepath)
            print(f"[Automation] Screenshot saved to: {filepath}")
            return filepath
        except Exception as e:
            print(f"[Automation Error] Failed to capture screenshot: {e}")
            return None

    def control_volume(self, action):
        """Controls system audio volume."""
        try:
            action = action.lower()
            if "up" in action or "increase" in action:
                pyautogui.press("volumeup", presses=5)
            elif "down" in action or "decrease" in action:
                pyautogui.press("volumedown", presses=5)
            elif "mute" in action:
                pyautogui.press("volumemute")
            return True
        except Exception as e:
            print(f"[Automation Error] Volume control failed: {e}")
            return False

    def get_system_stats(self):
        """Returns CPU, RAM, and Battery percentages."""
        cpu = psutil.cpu_percent(interval=0.1)
        ram = psutil.virtual_memory().percent
        battery = psutil.sensors_battery()
        
        battery_percent = battery.percent if battery else None
        is_plugged = battery.power_plugged if battery else None
        
        return {
            "cpu_percent": cpu,
            "ram_percent": ram,
            "battery_percent": battery_percent,
            "battery_plugged": is_plugged
        }

    def shutdown(self):
        print("[Automation] SHUTDOWN TRIGGERED!")
        subprocess.Popen("shutdown /s /t 10", shell=True)

    def abort_shutdown(self):
        print("[Automation] Aborting shutdown.")
        subprocess.Popen("shutdown /a", shell=True)

if __name__ == "__main__":
    auto = SystemAutomation()
    print("Testing launch_app & open_website:")
    auto.open_website("https://www.youtube.com")
