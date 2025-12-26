# stats_manager.py
"""
Statistics management for DialLoop Pro
"""

import configparser
import os
from datetime import datetime, timedelta

class StatsManager:
    def __init__(self, stats_file='stats.ini'):
        self.stats_file = stats_file
        self.stats = configparser.ConfigParser()
        
        # Create default stats if doesn't exist
        if not os.path.exists(stats_file):
            self.create_default_stats()
        else:
            self.stats.read(stats_file)
            
        # Ensure daily section exists
        self.initialize_daily_stats()
    
    def create_default_stats(self):
        """Create default statistics file"""
        today = datetime.now().strftime('%Y%m%d')
        
        self.stats['Lifetime'] = {
            'TotalCalls': '0',
            'LastSession': 'Never'
        }
        
        self.stats['Weekly'] = {
            'TotalCalls': '0',
            'LastResetDate': '0'
        }
        
        self.stats['Daily'] = {
            'LastResetDate': today,
            'Calls': '0'
        }
        
        self.stats['Session'] = {
            'AccumulatedTime': '0',
            'ConnectedCalls': '0'
        }
        
        self.save_stats_file()
    
    def initialize_daily_stats(self):
        """Initialize daily statistics with auto-reset"""
        today = datetime.now().strftime('%Y%m%d')
        
        if 'Daily' not in self.stats:
            self.stats['Daily'] = {}
        
        last_reset = self.stats['Daily'].get('LastResetDate', '0')
        
        # Reset if it's a new day
        if last_reset != today:
            self.stats['Daily']['LastResetDate'] = today
            self.stats['Daily']['Calls'] = '0'
            self.save_stats_file()
    
    def load_stats(self):
        """Load all statistics"""
        stats_dict = {}
        
        if 'Lifetime' in self.stats:
            stats_dict['total_calls'] = self.stats['Lifetime'].getint('TotalCalls', 0)
        
        if 'Weekly' in self.stats:
            stats_dict['weekly_calls'] = self.stats['Weekly'].getint('TotalCalls', 0)
        
        if 'Daily' in self.stats:
            stats_dict['session_calls'] = self.stats['Daily'].getint('Calls', 0)
        
        if 'Session' in self.stats:
            stats_dict['accumulated_time'] = self.stats['Session'].getint('AccumulatedTime', 0)
            stats_dict['connected_calls'] = self.stats['Session'].getint('ConnectedCalls', 0)
        
        return stats_dict
    
    def save_stats(self, stats_dict):
        """Save statistics"""
        if 'total_calls' in stats_dict:
            self.stats['Lifetime']['TotalCalls'] = str(stats_dict['total_calls'])
            self.stats['Lifetime']['LastSession'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if 'weekly_calls' in stats_dict:
            self.stats['Weekly']['TotalCalls'] = str(stats_dict['weekly_calls'])
            
            # Check for weekly reset (Monday)
            self.check_weekly_reset()
        
        if 'connected_calls' in stats_dict:
            self.stats['Session']['ConnectedCalls'] = str(stats_dict['connected_calls'])
        
        self.save_stats_file()
    
    def save_daily_count(self, count):
        """Save daily call count"""
        self.stats['Daily']['Calls'] = str(count)
        self.save_stats_file()
    
    def save_session_stats(self, total_calls, session_time_ms, current_rate, best_rate):
        """Save session statistics"""
        self.stats['Lifetime']['TotalCalls'] = str(total_calls)
        self.stats['Lifetime']['LastSession'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.stats['Session']['AccumulatedTime'] = str(session_time_ms)
        self.save_stats_file()
    
    def check_weekly_reset(self):
        """Check and reset weekly stats on Monday"""
        today = datetime.now()
        
        # Monday is weekday 0 in Python
        if today.weekday() == 0:  # Monday
            last_reset = self.stats['Weekly'].get('LastResetDate', '0')
            today_str = today.strftime('%Y%m%d')
            
            if last_reset != today_str:
                self.stats['Weekly']['LastResetDate'] = today_str
                self.stats['Weekly']['TotalCalls'] = '0'
    
    def save_stats_file(self):
        """Save statistics to file"""
        with open(self.stats_file, 'w') as f:
            self.stats.write(f)