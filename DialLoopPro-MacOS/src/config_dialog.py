# config_dialog.py
"""
Configuration dialog for DialLoop Pro macOS
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QLineEdit, QPushButton, QGroupBox, QFormLayout,
                            QMessageBox, QSpinBox, QComboBox)
from PyQt5.QtCore import Qt
import pyautogui
import time

class ConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("DialLoop Pro Configuration")
        self.setFixedSize(500, 600)
        
        self.setup_ui()
        self.load_current_config()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Window titles
        window_group = QGroupBox("Window Titles")
        window_layout = QFormLayout()
        
        self.dialer_edit = QLineEdit()
        self.dialer_pick_btn = QPushButton("Pick")
        self.dialer_pick_btn.clicked.connect(self.pick_dialer_window)
        self.dialer_test_btn = QPushButton("Test")
        self.dialer_test_btn.clicked.connect(self.test_dialer_window)
        
        dialer_layout = QHBoxLayout()
        dialer_layout.addWidget(self.dialer_edit)
        dialer_layout.addWidget(self.dialer_pick_btn)
        dialer_layout.addWidget(self.dialer_test_btn)
        
        window_layout.addRow("Dialer App:", dialer_layout)
        
        self.spreadsheet_edit = QLineEdit()
        self.spreadsheet_pick_btn = QPushButton("Pick")
        self.spreadsheet_pick_btn.clicked.connect(self.pick_spreadsheet_window)
        self.spreadsheet_test_btn = QPushButton("Test")
        self.spreadsheet_test_btn.clicked.connect(self.test_spreadsheet_window)
        
        spreadsheet_layout = QHBoxLayout()
        spreadsheet_layout.addWidget(self.spreadsheet_edit)
        spreadsheet_layout.addWidget(self.spreadsheet_pick_btn)
        spreadsheet_layout.addWidget(self.spreadsheet_test_btn)
        
        window_layout.addRow("Spreadsheet:", spreadsheet_layout)
        window_group.setLayout(window_layout)
        layout.addWidget(window_group)
        
        # Coordinates
        coord_group = QGroupBox("Mouse Coordinates")
        coord_layout = QFormLayout()
        
        # Hangup coordinates
        self.hangup_x_edit = QSpinBox()
        self.hangup_x_edit.setRange(0, 5000)
        self.hangup_y_edit = QSpinBox()
        self.hangup_y_edit.setRange(0, 5000)
        self.hangup_pick_btn = QPushButton("Pick")
        self.hangup_pick_btn.clicked.connect(self.pick_hangup_coord)
        self.hangup_test_btn = QPushButton("Test")
        self.hangup_test_btn.clicked.connect(self.test_hangup_coord)
        
        hangup_layout = QHBoxLayout()
        hangup_layout.addWidget(QLabel("X:"))
        hangup_layout.addWidget(self.hangup_x_edit)
        hangup_layout.addWidget(QLabel("Y:"))
        hangup_layout.addWidget(self.hangup_y_edit)
        hangup_layout.addWidget(self.hangup_pick_btn)
        hangup_layout.addWidget(self.hangup_test_btn)
        
        coord_layout.addRow("Hangup:", hangup_layout)
        
        # Dial coordinates
        self.dial_x_edit = QSpinBox()
        self.dial_x_edit.setRange(0, 5000)
        self.dial_y_edit = QSpinBox()
        self.dial_y_edit.setRange(0, 5000)
        self.dial_pick_btn = QPushButton("Pick")
        self.dial_pick_btn.clicked.connect(self.pick_dial_coord)
        self.dial_test_btn = QPushButton("Test")
        self.dial_test_btn.clicked.connect(self.test_dial_coord)
        
        dial_layout = QHBoxLayout()
        dial_layout.addWidget(QLabel("X:"))
        dial_layout.addWidget(self.dial_x_edit)
        dial_layout.addWidget(QLabel("Y:"))
        dial_layout.addWidget(self.dial_y_edit)
        dial_layout.addWidget(self.dial_pick_btn)
        dial_layout.addWidget(self.dial_test_btn)
        
        coord_layout.addRow("Dial:", dial_layout)
        coord_group.setLayout(coord_layout)
        layout.addWidget(coord_group)
        
        # Timing settings
        timing_group = QGroupBox("Timing Settings")
        timing_layout = QFormLayout()
        
        self.wait_time_edit = QSpinBox()
        self.wait_time_edit.setRange(10, 120)
        self.wait_time_edit.setSuffix(" seconds")
        timing_layout.addRow("Wait Time:", self.wait_time_edit)
        
        self.prefix_edit = QLineEdit()
        self.prefix_edit.setMaxLength(10)
        timing_layout.addRow("Dial Prefix:", self.prefix_edit)
        
        timing_group.setLayout(timing_layout)
        layout.addWidget(timing_group)
        
        # Goals
        goals_group = QGroupBox("Goals")
        goals_layout = QFormLayout()
        
        self.daily_goal_edit = QSpinBox()
        self.daily_goal_edit.setRange(1, 1000)
        self.daily_goal_edit.setValue(300)
        goals_layout.addRow("Daily Goal:", self.daily_goal_edit)
        
        self.weekly_goal_edit = QSpinBox()
        self.weekly_goal_edit.setRange(1, 5000)
        self.weekly_goal_edit.setValue(1500)
        goals_layout.addRow("Weekly Goal:", self.weekly_goal_edit)
        
        goals_group.setLayout(goals_layout)
        layout.addWidget(goals_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.save_btn = QPushButton("💾 Save")
        self.save_btn.clicked.connect(self.save_config)
        self.cancel_btn = QPushButton("❌ Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def load_current_config(self):
        """Load current configuration"""
        config = self.parent.config_manager.load_config()
        
        self.dialer_edit.setText(config.get('dialer_title', ''))
        self.spreadsheet_edit.setText(config.get('spreadsheet_title', ''))
        self.hangup_x_edit.setValue(config.get('hangup_x', 0))
        self.hangup_y_edit.setValue(config.get('hangup_y', 0))
        self.dial_x_edit.setValue(config.get('dial_x', 0))
        self.dial_y_edit.setValue(config.get('dial_y', 0))
        self.wait_time_edit.setValue(config.get('wait_time', 35000) // 1000)
        self.prefix_edit.setText(config.get('dial_prefix', '1'))
        self.daily_goal_edit.setValue(config.get('daily_goal', 300))
        self.weekly_goal_edit.setValue(config.get('weekly_goal', 1500))
    
    def pick_dialer_window(self):
        """Pick dialer window"""
        QMessageBox.information(self, "Pick Window", 
                              "1. Make sure your dialer app is visible\n"
                              "2. Click OK\n"
                              "3. Click on the dialer window within 5 seconds")
        
        self.showMinimized()
        time.sleep(1)
        
        # We'll use AppleScript to get frontmost window after click
        script = '''
        tell application "System Events"
            set frontApp to name of first application process whose frontmost is true
            return frontApp
        end tell
        '''
        
        import subprocess
        result = subprocess.check_output(['osascript', '-e', script])
        app_name = result.decode().strip()
        
        self.showNormal()
        self.activateWindow()
        
        if app_name:
            self.dialer_edit.setText(app_name)
            QMessageBox.information(self, "Window Selected", 
                                  f"Dialer app set to: {app_name}")
    
    def pick_spreadsheet_window(self):
        """Pick spreadsheet window"""
        # Similar implementation to pick_dialer_window
        pass
    
    def pick_hangup_coord(self):
        """Pick hangup coordinates"""
        QMessageBox.information(self, "Pick Coordinates",
                              "Move your mouse to the HANGUP button\n"
                              "Press OK, then click when ready")
        
        self.showMinimized()
        time.sleep(1)
        
        # Wait for click
        import subprocess
        script = '''
        tell application "System Events"
            repeat until (click it = true)
                delay 0.1
            end repeat
            set mousePos to mouse position
            return mousePos
        end tell
        '''
        
        # For now, use pyautogui
        input("Move mouse to hangup button and press Enter...")
        x, y = pyautogui.position()
        
        self.showNormal()
        self.activateWindow()
        
        self.hangup_x_edit.setValue(x)
        self.hangup_y_edit.setValue(y)
        
        QMessageBox.information(self, "Coordinates Set",
                              f"Hangup coordinates: X={x}, Y={y}")
    
    def pick_dial_coord(self):
        """Pick dial coordinates"""
        # Similar to pick_hangup_coord
        pass
    
    def test_dialer_window(self):
        """Test dialer window activation"""
        dialer_title = self.dialer_edit.text()
        if not dialer_title:
            QMessageBox.warning(self, "Error", "Dialer title is empty!")
            return
        
        success = self.parent.automation.activate_window(dialer_title)
        if success:
            QMessageBox.information(self, "Success", 
                                  f"Activated: {dialer_title}")
        else:
            QMessageBox.warning(self, "Failed", 
                              f"Could not activate: {dialer_title}")
    
    def test_spreadsheet_window(self):
        """Test spreadsheet window"""
        # Similar to test_dialer_window
        pass
    
    def test_hangup_coord(self):
        """Test hangup coordinates"""
        x = self.hangup_x_edit.value()
        y = self.hangup_y_edit.value()
        
        pyautogui.moveTo(x, y, duration=0.5)
        
        QMessageBox.information(self, "Test Complete",
                              f"Mouse moved to: X={x}, Y={y}\n"
                              "Is it on the hangup button?")
    
    def test_dial_coord(self):
        """Test dial coordinates"""
        # Similar to test_hangup_coord
        pass
    
    def save_config(self):
        """Save configuration"""
        # Validate
        if not self.dialer_edit.text():
            QMessageBox.warning(self, "Error", "Dialer title is required!")
            return
        
        if not self.spreadsheet_edit.text():
            QMessageBox.warning(self, "Error", "Spreadsheet title is required!")
            return
        
        if self.hangup_x_edit.value() == 0 or self.hangup_y_edit.value() == 0:
            QMessageBox.warning(self, "Error", "Hangup coordinates are required!")
            return
        
        if self.dial_x_edit.value() == 0 or self.dial_y_edit.value() == 0:
            QMessageBox.warning(self, "Error", "Dial coordinates are required!")
            return
        
        # Save to parent's config manager
        config_dict = {
            'Configuration': {
                'DialerTitle': self.dialer_edit.text(),
                'SpreadsheetTitle': self.spreadsheet_edit.text(),
                'HangupX': str(self.hangup_x_edit.value()),
                'HangupY': str(self.hangup_y_edit.value()),
                'DialX': str(self.dial_x_edit.value()),
                'DialY': str(self.dial_y_edit.value()),
                'WaitTime': str(self.wait_time_edit.value() * 1000),
                'DialPrefix': self.prefix_edit.text()
            },
            'Goals': {
                'DailyGoal': str(self.daily_goal_edit.value()),
                'WeeklyGoal': str(self.weekly_goal_edit.value())
            }
        }
        
        self.parent.config_manager.update_config(config_dict)
        QMessageBox.information(self, "Success", "Configuration saved!")
        self.accept()