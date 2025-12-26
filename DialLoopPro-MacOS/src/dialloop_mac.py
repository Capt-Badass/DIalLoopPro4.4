#!/usr/bin/env python3
# dialloop_mac.py
"""
DialLoop Pro v4.4 - macOS Edition
Complete calling automation system for macOS
"""

import sys
import os
import time
import json
import threading
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QPushButton, QProgressBar,
                            QSystemTrayIcon, QMenu, QAction, QMessageBox,
                            QGroupBox, QGridLayout)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QIcon, QFont, QColor, QPalette
import pyautogui
import pynput
from pynput import keyboard
import applescript
import Quartz
from AppKit import NSWorkspace
import configparser
import signal

# Local imports
from mac_automation import MacAutomation
from config_manager import ConfigManager
from stats_manager import StatsManager

class DialLoopMac(QMainWindow):
    """Main application window - macOS edition"""
    
    # Signals for thread-safe GUI updates
    update_status = pyqtSignal(str)
    update_stats = pyqtSignal(dict)
    update_progress = pyqtSignal(int, int)  # daily, weekly
    
    def __init__(self):
        super().__init__()
        self.running = False
        self.on_call = False
        self.dialing_active = False
        self.force_break = False
        self.first_run = False
        
        # Window visibility
        self.indicator_visible = True
        self.quick_access_visible = False
        
        # Statistics
        self.total_calls = 0
        self.session_calls = 0
        self.session_display_calls = 0
        self.weekly_calls = 0
        self.connected_calls = 0
        self.total_talk_time = 0
        
        # Goals
        self.daily_goal = 300
        self.weekly_goal = 1500
        self.best_hourly_rate = 0
        
        # Hourly tracking
        self.current_hour_start = 0
        self.current_hour_calls = 0
        self.current_hour_rate = 0
        
        # Timing
        self.call_start_time = 0
        self.session_start_time = 0
        self.first_start_time = 0
        self.session_active = False
        
        # Configuration
        self.config_manager = ConfigManager()
        self.stats_manager = StatsManager()
        self.automation = MacAutomation()
        
        # Threading
        self.dial_thread = None
        self.hotkey_listener = None
        
        # Setup
        self.load_configuration()
        self.setup_gui()
        self.setup_hotkeys()
        self.setup_tray()
        self.check_first_run()
        
        # Connect signals
        self.update_status.connect(self.update_status_text)
        self.update_stats.connect(self.update_stats_display)
        self.update_progress.connect(self.update_progress_bars)
        
        # Start update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(1000)  # Update every second
        
    def load_configuration(self):
        """Load configuration from INI files"""
        config = self.config_manager.load_config()
        
        # Basic configuration
        self.dialer_window_title = config.get('dialer_title', '')
        self.spreadsheet_window_title = config.get('spreadsheet_title', '')
        self.hangup_x = config.get('hangup_x', 0)
        self.hangup_y = config.get('hangup_y', 0)
        self.dial_x = config.get('dial_x', 0)
        self.dial_y = config.get('dial_y', 0)
        self.wait_time = config.get('wait_time', 35000)
        self.dial_prefix = config.get('dial_prefix', '1')
        
        # Goals
        self.daily_goal = config.get('daily_goal', 300)
        self.weekly_goal = config.get('weekly_goal', 1500)
        self.best_hourly_rate = config.get('best_hourly_rate', 0)
        
        # Statistics
        stats = self.stats_manager.load_stats()
        self.total_calls = stats.get('total_calls', 0)
        self.weekly_calls = stats.get('weekly_calls', 0)
        self.session_calls = stats.get('session_calls', 0)
        self.session_display_calls = self.session_calls
        
        # Check for first run
        if not all([self.dialer_window_title, self.spreadsheet_window_title, 
                    self.hangup_x, self.dial_x]):
            self.first_run = True
    
    def setup_gui(self):
        """Setup the macOS-native GUI"""
        self.setWindowTitle("DialLoop Pro v4.4 - macOS")
        self.setGeometry(100, 100, 920, 390)
        
        # macOS-style styling
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f7;
            }
            QLabel {
                color: #1d1d1f;
            }
            QPushButton {
                background-color: #007aff;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #0056cc;
            }
            QPushButton:pressed {
                background-color: #004499;
            }
            QPushButton#stop {
                background-color: #ff3b30;
            }
            QPushButton#stop:hover {
                background-color: #d70015;
            }
            QProgressBar {
                border: 1px solid #c7c7cc;
                border-radius: 4px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #34c759;
                border-radius: 4px;
            }
        """)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Header
        header = QLabel("📞 DialLoop Pro v4.4 - macOS Edition")
        header.setFont(QFont("SF Pro Display", 16, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        # Status area
        self.status_label = QLabel("READY")
        self.status_label.setFont(QFont("SF Pro Display", 36, QFont.Bold))
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #007aff;")
        layout.addWidget(self.status_label)
        
        # Stats area
        stats_layout = QHBoxLayout()
        
        # Left panel - Call stats
        call_group = QGroupBox("Call Statistics")
        call_layout = QVBoxLayout()
        
        self.connected_label = QLabel("Connected: 0")
        self.connected_label.setFont(QFont("SF Pro Display", 24))
        call_layout.addWidget(self.connected_label)
        
        self.talk_time_label = QLabel("Talk Time: 0s")
        call_layout.addWidget(self.talk_time_label)
        
        self.session_time_label = QLabel("Session: 0m 0s")
        call_layout.addWidget(self.session_time_label)
        
        call_group.setLayout(call_layout)
        stats_layout.addWidget(call_group)
        
        # Right panel - Progress
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout()
        
        # Daily progress
        self.daily_label = QLabel(f"Today: 0/{self.daily_goal}")
        progress_layout.addWidget(self.daily_label)
        
        self.daily_progress = QProgressBar()
        self.daily_progress.setMaximum(100)
        progress_layout.addWidget(self.daily_progress)
        
        # Weekly progress
        self.weekly_label = QLabel(f"Week: 0/{self.weekly_goal}")
        progress_layout.addWidget(self.weekly_label)
        
        self.weekly_progress = QProgressBar()
        self.weekly_progress.setMaximum(100)
        progress_layout.addWidget(self.weekly_progress)
        
        # Rate display
        self.rate_label = QLabel("Rate: 0/hr | Best: 0/hr")
        progress_layout.addWidget(self.rate_label)
        
        progress_group.setLayout(progress_layout)
        stats_layout.addWidget(progress_group)
        
        layout.addLayout(stats_layout)
        
        # Control buttons
        button_layout = QGridLayout()
        
        buttons = [
            ("▶ Start Dialing", self.start_dialing, 0, 0),
            ("⏹ Stop", self.stop_dialing, 0, 1),
            ("📞 Hangup & Next", self.hangup_next, 1, 0),
            ("🎤 On/Off Call", self.toggle_call, 1, 1),
            ("⚙ Configure", self.open_config, 2, 0),
            ("👁 Hide Window", self.hide_window, 2, 1),
            ("📊 Statistics", self.show_stats, 3, 0),
            ("🎯 Goals", self.update_goals, 3, 1),
        ]
        
        for text, slot, row, col in buttons:
            btn = QPushButton(text)
            if text == "⏹ Stop":
                btn.setObjectName("stop")
            btn.clicked.connect(slot)
            button_layout.addWidget(btn, row, col)
        
        layout.addLayout(button_layout)
        
        # Footer
        footer = QLabel("Press ⌘+Q to quit | Green dot in menu bar indicates active")
        footer.setStyleSheet("color: #8e8e93; font-size: 11px;")
        footer.setAlignment(Qt.AlignCenter)
        layout.addWidget(footer)
    
    def setup_hotkeys(self):
        """Setup global hotkeys for macOS"""
        try:
            # Use pynput for global hotkeys
            self.hotkey_listener = keyboard.GlobalHotKeys({
                '<cmd>+<alt>+c': self.start_dialing,
                '<cmd>+<alt>+s': self.stop_dialing,
                '<cmd>+<alt>+h': self.hangup_next,
                '<cmd>+<alt>+l': self.toggle_call,
                '<cmd>+<alt>+o': self.open_config,
                '<cmd>+<alt>+i': self.show_stats,
                '<cmd>+<alt>+q': self.show_window,
                '<cmd>+<alt>+a': self.hide_window,
            })
            self.hotkey_listener.start()
        except Exception as e:
            print(f"Hotkey setup failed: {e}")
            QMessageBox.warning(self, "Hotkey Warning", 
                              "Some hotkeys may not work. Please grant accessibility permissions in System Preferences > Security & Privacy > Privacy > Accessibility.")
    
    def setup_tray(self):
        """Setup system tray icon for macOS"""
        self.tray_icon = QSystemTrayIcon(self)
        
        # Create tray menu
        tray_menu = QMenu()
        
        show_action = QAction("Show", self)
        show_action.triggered.connect(self.show_window)
        tray_menu.addAction(show_action)
        
        hide_action = QAction("Hide", self)
        hide_action.triggered.connect(self.hide_window)
        tray_menu.addAction(hide_action)
        
        tray_menu.addSeparator()
        
        start_action = QAction("Start Dialing", self)
        start_action.triggered.connect(self.start_dialing)
        tray_menu.addAction(start_action)
        
        stop_action = QAction("Stop Dialing", self)
        stop_action.triggered.connect(self.stop_dialing)
        tray_menu.addAction(stop_action)
        
        tray_menu.addSeparator()
        
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.quit_app)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.setIcon(QIcon.fromTheme("phone"))
        self.tray_icon.show()
        
        # Tray icon click
        self.tray_icon.activated.connect(self.tray_icon_clicked)
    
    def tray_icon_clicked(self, reason):
        """Handle tray icon clicks"""
        if reason == QSystemTrayIcon.Trigger:  # Single click
            if self.isVisible():
                self.hide_window()
            else:
                self.show_window()
    
    def check_first_run(self):
        """Check if this is first run and show setup"""
        if self.first_run:
            self.show_setup_wizard()
    
    def show_setup_wizard(self):
        """Show first-time setup wizard"""
        msg = QMessageBox(self)
        msg.setWindowTitle("DialLoop Pro - First Time Setup")
        msg.setText("""
        <h2>Welcome to DialLoop Pro for macOS! 🎉</h2>
        
        <p>This appears to be your first time running DialLoop Pro.</p>
        
        <p><b>Required Setup:</b></p>
        <ol>
        <li>Open your dialer app (like Zoiper, Bria, etc.)</li>
        <li>Open your spreadsheet (Google Sheets, Numbers, Excel)</li>
        <li>Click "Configure" button to set up window titles and coordinates</li>
        </ol>
        
        <p><b>Hotkeys:</b></p>
        <ul>
        <li>⌘+Alt+C = Start dialing</li>
        <li>⌘+Alt+S = Stop dialing</li>
        <li>⌘+Alt+H = Hangup & next</li>
        <li>⌘+Alt+L = On/Off call (with auto-dial!)</li>
        <li>⌘+Alt+O = Configuration</li>
        <li>⌘+Alt+Q = Show window</li>
        <li>⌘+Alt+A = Hide window</li>
        </ul>
        
        <p>You'll need to grant Accessibility permissions for automation to work.</p>
        """)
        
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
        
        # Open config after welcome
        self.open_config()
    
    def start_dialing(self):
        """Start automated dialing"""
        if self.running:
            return
        
        # Check configuration
        if not all([self.dialer_window_title, self.spreadsheet_window_title,
                   self.hangup_x, self.dial_x]):
            QMessageBox.warning(self, "Configuration Required",
                              "Please configure DialLoop first!")
            self.open_config()
            return
        
        self.running = True
        self.force_break = False
        self.dialing_active = False
        
        if self.first_start_time == 0:
            self.first_start_time = int(time.time() * 1000)
            self.session_active = True
            self.current_hour_start = int(time.time() * 1000)
            self.current_hour_calls = 0
        
        self.session_start_time = int(time.time() * 1000)
        
        # Show window if hidden
        if not self.isVisible():
            self.show()
        
        self.update_status.emit("DIALING NEXT...")
        
        # Start dialing in separate thread
        self.dial_thread = threading.Thread(target=self.dial_loop, daemon=True)
        self.dial_thread.start()
    
    def dial_loop(self):
        """Main dialing automation loop"""
        while self.running:
            # Count the call
            self.total_calls += 1
            self.weekly_calls += 1
            self.session_calls += 1
            self.session_display_calls = self.session_calls
            self.current_hour_calls += 1
            
            # Save stats
            self.save_daily_count()
            self.stats_manager.save_stats({
                'total_calls': self.total_calls,
                'weekly_calls': self.weekly_calls,
            })
            
            # Update GUI via signal
            self.update_stats.emit({
                'connected': self.connected_calls,
                'session_calls': self.session_calls,
                'weekly_calls': self.weekly_calls,
                'total_calls': self.total_calls,
            })
            
            # Check if stopped
            if not self.running:
                break
            
            # Activate dialer
            self.automation.activate_window(self.dialer_window_title)
            time.sleep(0.5)
            
            # Check if on call
            if self.on_call:
                self.update_status.emit("ON CALL - WAITING...")
                
                # Update call timer while on call
                while self.on_call and self.running:
                    call_duration = int(time.time() * 1000) - self.call_start_time
                    seconds = call_duration // 1000
                    self.update_status.emit(f"CALL {seconds:02d}s")
                    time.sleep(1)
                
                if not self.running:
                    break
            
            # Dialing sequence
            self.update_status.emit("COPYING NEXT NUMBER...")
            
            # Activate spreadsheet and copy
            success = self.automation.copy_next_number(
                self.spreadsheet_window_title
            )
            
            if not success or not self.running:
                break
            
            # Activate dialer and paste
            self.update_status.emit("DIALING...")
            success = self.automation.paste_and_dial(
                self.dialer_window_title,
                self.dial_x, self.dial_y,
                self.dial_prefix
            )
            
            if not success or not self.running:
                break
            
            # Move to hangup position
            pyautogui.moveTo(self.hangup_x, self.hangup_y, duration=0.2)
            
            self.dialing_active = True
            self.update_status.emit("WAITING FOR CALL...")
            
            # Wait for call
            start_wait = int(time.time() * 1000)
            while (self.running and 
                   (int(time.time() * 1000) - start_wait < self.wait_time)):
                
                if self.force_break:
                    self.force_break = False
                    self.dialing_active = False
                    break
                
                if self.on_call:
                    self.dialing_active = False
                    break
                
                # Update countdown
                elapsed = int(time.time() * 1000) - start_wait
                remaining = max(0, self.wait_time - elapsed)
                seconds = remaining // 1000
                self.update_status.emit(f"WAIT {seconds:02d}s")
                time.sleep(0.1)
            
            self.dialing_active = False
            
            if not self.running:
                break
            
            # If timer completed, click hangup
            if not self.on_call:
                pyautogui.click(self.hangup_x, self.hangup_y)
                time.sleep(1.5)
            
            self.update_status.emit("DIALING NEXT...")
    
    def stop_dialing(self):
        """Stop automated dialing"""
        if self.running:
            if self.on_call:
                QMessageBox.warning(self, "Cannot Stop",
                                  "You are currently on a call! End the call first.")
                return
            
            self.running = False
            self.force_break = False
            self.dialing_active = False
            
            self.update_status.emit("DIALING PAUSED")
            self.save_session_stats()
    
    def hangup_next(self):
        """Hangup and dial next number"""
        if self.on_call:
            QMessageBox.warning(self, "Cannot Hangup",
                              "You are currently on a call! End the call first.")
            return
        
        # Click hangup
        pyautogui.click(self.hangup_x, self.hangup_y)
        time.sleep(0.3)
        
        self.update_status.emit("HANGUP + NEXT...")
        
        # If not running, do manual dial
        if not self.running:
            success = self.manual_dial_next()
            if success:
                self.update_status.emit("MANUAL DIAL COMPLETE")
        else:
            self.force_break = True
            self.dialing_active = False
            self.update_status.emit("DIALING NEXT...")
    
    def manual_dial_next(self):
        """Manual dialing sequence"""
        self.update_status.emit("MANUAL DIALING...")
        
        # Copy next number from spreadsheet
        success = self.automation.copy_next_number(self.spreadsheet_window_title)
        if not success:
            QMessageBox.warning(self, "Error", "Spreadsheet not found!")
            return False
        
        # Paste and dial
        success = self.automation.paste_and_dial(
            self.dialer_window_title,
            self.dial_x, self.dial_y,
            self.dial_prefix
        )
        
        if success:
            # Update counts
            self.total_calls += 1
            self.weekly_calls += 1
            self.session_calls += 1
            self.session_display_calls = self.session_calls
            self.current_hour_calls += 1
            
            self.save_daily_count()
            self.stats_manager.save_stats({
                'total_calls': self.total_calls,
                'weekly_calls': self.weekly_calls,
            })
            
            self.update_status.emit("MANUAL CALL DIALED")
            return True
        
        return False
    
    def toggle_call(self):
        """Toggle on/off call with auto-hangup and auto-dial"""
        if self.on_call:
            # End call - first hangup
            pyautogui.click(self.hangup_x, self.hangup_y)
            time.sleep(0.5)
            
            self.on_call = False
            call_duration = int(time.time() * 1000) - self.call_start_time
            self.total_talk_time += call_duration
            
            # Update connected calls
            self.connected_calls += 1
            
            self.update_status.emit("CALL ENDED + HANGUP")
            
            # Auto-dial next if not running
            if not self.running:
                time.sleep(0.5)
                success = self.manual_dial_next()
        else:
            # Start call
            self.on_call = True
            self.connected_calls += 1
            self.call_start_time = int(time.time() * 1000)
            
            self.update_status.emit("LIVE CALL")
            
            # Show notification
            self.tray_icon.showMessage("Live Call!", "Client answered!", 
                                      QSystemTrayIcon.Information, 2000)
        
        # Update stats
        self.update_stats.emit({
            'connected': self.connected_calls,
            'on_call': self.on_call,
        })
    
    def save_daily_count(self):
        """Save daily call count with auto-reset at midnight"""
        self.stats_manager.save_daily_count(self.session_calls)
    
    def save_session_stats(self):
        """Save session statistics"""
        if self.session_active:
            total_session_ms = int(time.time() * 1000) - self.first_start_time
            self.stats_manager.save_session_stats(
                self.total_calls,
                total_session_ms,
                self.current_hour_rate,
                self.best_hourly_rate
            )
    
    def update_display(self):
        """Update all display elements"""
        # Calculate hourly rate
        if self.session_active:
            total_time_ms = int(time.time() * 1000) - self.first_start_time
            if total_time_ms > 0:
                self.current_hour_rate = round(
                    (self.session_calls * 3600000) / total_time_ms, 1
                )
                
                if (self.current_hour_rate > self.best_hourly_rate and 
                    self.session_calls >= 10):
                    self.best_hourly_rate = self.current_hour_rate
                    self.config_manager.save_setting(
                        'best_hourly_rate', self.best_hourly_rate
                    )
        
        # Calculate progress
        daily_progress = 0
        if self.daily_goal > 0:
            daily_progress = min(100, round(
                (self.session_display_calls / self.daily_goal) * 100
            ))
        
        weekly_progress = 0
        if self.weekly_goal > 0:
            weekly_progress = min(100, round(
                (self.weekly_calls / self.weekly_goal) * 100
            ))
        
        # Update progress bars via signal
        self.update_progress.emit(daily_progress, weekly_progress)
        
        # Update labels
        talk_time_seconds = self.total_talk_time // 1000
        talk_time_str = self.format_time(talk_time_seconds)
        
        stats_dict = {
            'connected': self.connected_calls,
            'talk_time': talk_time_str,
            'session_calls': self.session_display_calls,
            'weekly_calls': self.weekly_calls,
            'daily_goal': self.daily_goal,
            'weekly_goal': self.weekly_goal,
            'current_rate': self.current_hour_rate,
            'best_rate': self.best_hourly_rate,
        }
        
        self.update_stats.emit(stats_dict)
    
    def update_status_text(self, text):
        """Update status label (thread-safe)"""
        self.status_label.setText(text)
        
        # Color coding
        if "WAIT" in text:
            if "05" in text or "04" in text or "03" in text or "02" in text or "01" in text or "00" in text:
                self.status_label.setStyleSheet("color: #ff3b30;")  # Red
            elif "10" in text or "09" in text or "08" in text or "07" in text or "06" in text:
                self.status_label.setStyleSheet("color: #ff9500;")  # Orange
            else:
                self.status_label.setStyleSheet("color: #34c759;")  # Green
        elif "CALL" in text:
            self.status_label.setStyleSheet("color: #5856d6;")  # Purple
        elif "LIVE" in text:
            self.status_label.setStyleSheet("color: #ff2d55;")  # Pink
        else:
            self.status_label.setStyleSheet("color: #007aff;")  # Blue
    
    def update_stats_display(self, stats):
        """Update statistics display (thread-safe)"""
        self.connected_label.setText(f"Connected: {stats.get('connected', 0)}")
        
        if 'talk_time' in stats:
            self.talk_time_label.setText(f"Talk Time: {stats['talk_time']}")
        
        if 'session_calls' in stats:
            self.daily_label.setText(
                f"Today: {stats['session_calls']}/{self.daily_goal}"
            )
        
        if 'weekly_calls' in stats:
            self.weekly_label.setText(
                f"Week: {stats['weekly_calls']}/{self.weekly_goal}"
            )
        
        if 'current_rate' in stats and 'best_rate' in stats:
            self.rate_label.setText(
                f"Rate: {stats['current_rate']}/hr | Best: {stats['best_rate']}/hr"
            )
    
    def update_progress_bars(self, daily_progress, weekly_progress):
        """Update progress bars (thread-safe)"""
        self.daily_progress.setValue(daily_progress)
        self.weekly_progress.setValue(weekly_progress)
    
    def format_time(self, seconds):
        """Format time in human-readable format"""
        if seconds > 3600:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m"
        elif seconds > 60:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes}m {secs}s"
        else:
            return f"{seconds}s"
    
    def open_config(self):
        """Open configuration dialog"""
        from config_dialog import ConfigDialog
        dialog = ConfigDialog(self)
        if dialog.exec_():
            # Reload configuration
            self.load_configuration()
            self.update_status.emit("CONFIG UPDATED")
    
    def show_stats(self):
        """Show statistics dialog"""
        from stats_dialog import StatsDialog
        dialog = StatsDialog(self)
        dialog.exec_()
    
    def update_goals(self):
        """Update daily/weekly goals"""
        # Implementation for goals dialog
        pass
    
    def show_window(self):
        """Show main window"""
        self.show()
        self.activateWindow()
        self.raise_()
    
    def hide_window(self):
        """Hide main window"""
        self.hide()
    
    def quit_app(self):
        """Quit application"""
        self.stop_dialing()
        self.save_session_stats()
        QApplication.quit()
    
    def closeEvent(self, event):
        """Handle window close event"""
        event.ignore()
        self.hide_window()
        self.tray_icon.showMessage("DialLoop Pro", 
                                  "App is still running in background", 
                                  QSystemTrayIcon.Information, 2000)

def main():
    # Handle Ctrl+C gracefully
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    app = QApplication(sys.argv)
    app.setApplicationName("DialLoop Pro")
    app.setApplicationDisplayName("DialLoop Pro v4.4")
    
    # Set application icon (you'll need to add an icon file)
    # app.setWindowIcon(QIcon("dialloop.icns"))
    
    window = DialLoopMac()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()