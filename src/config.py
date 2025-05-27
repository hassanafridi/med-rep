import json
import os
import logging

class Config:
    """Configuration manager for the application"""
    def __init__(self, config_path=None):
        """Initialize configuration"""
        if config_path is None:
            # Default to data directory
            self.config_path = os.path.join('data', 'config.json')
        else:
            self.config_path = config_path
        
        # Default configuration
        self.default_config = {
            'db_path': os.path.join('data', 'medtran.db'),
            'backup_path': os.path.join('data', 'backups'),
            'currency_format': 'Rs.  (PKR)',
            'log_level': 'INFO',
            'window_width': 1000,
            'window_height': 700
        }
        
        # Current configuration (start with defaults)
        self.config = self.default_config.copy()
        
        # Load configuration from file
        self.load()
    
    def load(self):
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    loaded_config = json.load(f)
                    
                    # Update config with loaded values
                    self.config.update(loaded_config)
                    
                logging.info(f"Configuration loaded from {self.config_path}")
            else:
                logging.info("Configuration file not found, using defaults")
                
                # Ensure directory exists
                os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
                
                # Save default configuration
                self.save()
        except Exception as e:
            logging.error(f"Failed to load configuration: {str(e)}")
    
    def save(self):
        """Save configuration to file"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
                
            logging.info(f"Configuration saved to {self.config_path}")
        except Exception as e:
            logging.error(f"Failed to save configuration: {str(e)}")
    
    def get(self, key, default=None):
        """Get a configuration value"""
        return self.config.get(key, default)
    
    def set(self, key, value):
        """Set a configuration value"""
        self.config[key] = value
        self.save()
    
    def reset(self):
        """Reset configuration to defaults"""
        self.config = self.default_config.copy()
        self.save()