# config_manager.py
"""
Configuration management for DialLoop Pro
"""

import configparser
import os
from datetime import datetime

class ConfigManager:
    def __init__(self, config_file='settings.ini'):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        
        # Create default config if doesn't exist
        if not os.path.exists(config_file):
            self.create_default_config()
    
    def create_default_config(self):
        """Create default configuration"""
        self.config['Configuration'] = {
            'DialerTitle': '',
            'SpreadsheetTitle': '',
            'HangupX': '0',
            'HangupY': '0',
            'DialX': '0',
            'DialY': '0',
            'WaitTime': '35000',
            'DialPrefix': '1'
        }
        
        self.config['Goals'] = {
            'DailyGoal': '300',
            'WeeklyGoal': '1500',
            'BestHourlyRate': '0'
        }
        
        self.config['Info'] = {
            'Version': '4.4',
            'Created': datetime.now().strftime('%Y-%m-%d'),
            'Platform': 'macOS'
        }
        
        self.save_config()
    
    def load_config(self):
        """Load configuration from file"""
        self.config.read(self.config_file)
        
        config_dict = {}
        
        # Configuration section
        if 'Configuration' in self.config:
            config_dict.update({
                'dialer_title': self.config['Configuration'].get('DialerTitle', ''),
                'spreadsheet_title': self.config['Configuration'].get('SpreadsheetTitle', ''),
                'hangup_x': self.config['Configuration'].getint('HangupX', 0),
                'hangup_y': self.config['Configuration'].getint('HangupY', 0),
                'dial_x': self.config['Configuration'].getint('DialX', 0),
                'dial_y': self.config['Configuration'].getint('DialY', 0),
                'wait_time': self.config['Configuration'].getint('WaitTime', 35000),
                'dial_prefix': self.config['Configuration'].get('DialPrefix', '1')
            })
        
        # Goals section
        if 'Goals' in self.config:
            config_dict.update({
                'daily_goal': self.config['Goals'].getint('DailyGoal', 300),
                'weekly_goal': self.config['Goals'].getint('WeeklyGoal', 1500),
                'best_hourly_rate': self.config['Goals'].getfloat('BestHourlyRate', 0.0)
            })
        
        return config_dict
    
    def save_setting(self, key, value, section='Configuration'):
        """Save a single setting"""
        if section not in self.config:
            self.config[section] = {}
        
        if isinstance(value, bool):
            value = '1' if value else '0'
        else:
            value = str(value)
        
        self.config[section][key] = value
        self.save_config()
    
    def save_config(self):
        """Save configuration to file"""
        with open(self.config_file, 'w') as f:
            self.config.write(f)
    
    def update_config(self, config_dict):
        """Update multiple configuration values"""
        for section, settings in config_dict.items():
            if section not in self.config:
                self.config[section] = {}
            
            for key, value in settings.items():
                self.config[section][key] = str(value)
        
        self.save_config()