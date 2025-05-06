"""
Tests for configuration management.
"""
import os
import sys
import unittest
from pathlib import Path
import tempfile
import yaml

# Add the app directory to the path
app_dir = Path(__file__).resolve().parent.parent
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

from app.utils.config import load_config, get_environment_variables, merge_config_with_env

class TestConfig(unittest.TestCase):
    """Test cases for configuration functions."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary config file
        self.config_file = tempfile.NamedTemporaryFile(delete=False, suffix='.yaml')
        self.config_data = {
            "api": {
                "server": "test.server.com",
                "endpoint": "/api/test",
                "polling_interval_seconds": 60
            },
            "transfer": {
                "method": "scp",
                "host": "remote.test.com",
                "port": 2222
            }
        }
        with open(self.config_file.name, 'w') as f:
            yaml.dump(self.config_data, f)
    
    def tearDown(self):
        """Clean up after tests."""
        os.unlink(self.config_file.name)
    
    def test_load_config(self):
        """Test loading configuration from file."""
        config = load_config(self.config_file.name)
        self.assertEqual(config["api"]["server"], "test.server.com")
        self.assertEqual(config["api"]["polling_interval_seconds"], 60)
    
    def test_merge_config_with_env(self):
        """Test merging configuration with environment variables."""
        # Set up test environment variables
        env_vars = {
            "APSTRA_USERNAME": "test_user",
            "APSTRA_PASSWORD": "test_pass",
            "REMOTE_USERNAME": "remote_user",
            "REMOTE_PASSWORD": "remote_pass"
        }
        
        # Merge config with env vars
        merged_config = merge_config_with_env(self.config_data, env_vars)
        
        # Check that the API credentials were added
        self.assertEqual(merged_config["api"]["username"], "test_user")
        self.assertEqual(merged_config["api"]["password"], "test_pass")
        
        # Check that the transfer credentials were added
        self.assertEqual(merged_config["transfer"]["username"], "remote_user")
        self.assertEqual(merged_config["transfer"]["password"], "remote_pass")

if __name__ == "__main__":
    unittest.main()
