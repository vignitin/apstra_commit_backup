"""
Configuration management for the API polling and backup service.
"""
import os
import yaml
import logging
from from dotenv import load_dotenv import load_dotenv

logger = logging.getLogger(__name__)

def load_config(config_path):
    """
    Load the configuration from a YAML file.
    
    Args:
        config_path (str): Path to the YAML config file
    
    Returns:
        dict: Loaded configuration
    """
    try:
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
            logger.info(f"Configuration loaded from {config_path}")
            return config
    except Exception as e:
        logger.error(f"Error loading configuration: {str(e)}")
        # Return minimal default config
        return {
            "api": {"polling_interval_seconds": 30},
            "state": {"file_path": "data/backup_state.json"}
        }

def get_environment_variables():
    """
    Get authentication environment variables.
    
    Returns:
        dict: Dictionary with environment variables
    """
    env_vars = {
        "APSTRA_USERNAME": os.getenv("APSTRA_USERNAME"),
        "APSTRA_PASSWORD": os.getenv("APSTRA_PASSWORD"),
        "REMOTE_USERNAME": os.getenv("REMOTE_USERNAME"),
        "REMOTE_PASSWORD": os.getenv("REMOTE_PASSWORD"),
        "SSH_KEY_PATH": os.getenv("SSH_KEY_PATH")
    }
    

    # env_vars = {
    #     "APSTRA_USERNAME": os.environ.get("APSTRA_USERNAME"),
    #     "APSTRA_PASSWORD": os.environ.get("APSTRA_PASSWORD"),
    #     "REMOTE_USERNAME": os.environ.get("REMOTE_USERNAME"),
    #     "REMOTE_PASSWORD": os.environ.get("REMOTE_PASSWORD"),
    #     "SSH_KEY_PATH": os.environ.get("SSH_KEY_PATH")
    # }
    
    # Check if essential variables are missing
    missing_vars = []
    if not env_vars["APSTRA_USERNAME"]:
        missing_vars.append("APSTRA_USERNAME")
    if not env_vars["APSTRA_PASSWORD"]:
        missing_vars.append("APSTRA_PASSWORD")
    
    if missing_vars:
        env_help_message = """
Missing essential environment variables: {missing_vars_list}

How to set environment variables:

In Linux/macOS terminal:
  export APSTRA_USERNAME=your_username
  export APSTRA_PASSWORD=your_password

In Windows Command Prompt:
  set APSTRA_USERNAME=your_username
  set APSTRA_PASSWORD=your_password

In Windows PowerShell:
  $env:APSTRA_USERNAME="your_username"
  $env:APSTRA_PASSWORD="your_password"

Or create a .env file in the project root with:
  APSTRA_USERNAME=your_username
  APSTRA_PASSWORD=your_password
  
To make env vars persistent, add them to your shell profile (~/.bashrc, ~/.bash_profile, etc.)
        """.format(missing_vars_list=", ".join(missing_vars))
        
        logger.warning(env_help_message)
    
    return env_vars

def merge_config_with_env(config, env_vars):
    """
    Merge configuration with environment variables.
    
    Args:
        config (dict): Configuration dictionary
        env_vars (dict): Environment variables dictionary
    
    Returns:
        dict: Merged configuration
    """
    # Create a new config to avoid modifying the original
    merged_config = config.copy()
    
    # Check if required API credentials are missing
    if not env_vars.get("APSTRA_USERNAME") or not env_vars.get("APSTRA_PASSWORD"):
        logger.error("""
API authentication credentials are missing! Please set environment variables or use a .env file.

Required environment variables for API authentication:
  APSTRA_USERNAME - Your Apstra username
  APSTRA_PASSWORD - Your Apstra password

To set environment variables:
  Linux/macOS: export APSTRA_USERNAME=your_username
  Windows CMD: set APSTRA_USERNAME=your_username
  Windows PS: $env:APSTRA_USERNAME="your_username"
  
Or create a .env file in the project root.
        """)
    
    # Add transfer authentication if available
    if "transfer" in merged_config:
        transfer_config = merged_config["transfer"]
        
        if env_vars.get("REMOTE_USERNAME"):
            transfer_config["username"] = env_vars["REMOTE_USERNAME"]
        
        if env_vars.get("REMOTE_PASSWORD"):
            transfer_config["password"] = env_vars["REMOTE_PASSWORD"]
        
        if env_vars.get("SSH_KEY_PATH"):
            transfer_config["ssh_key_path"] = env_vars["SSH_KEY_PATH"]
        
        # Check if remote auth is missing
        if transfer_config.get("method") in ["scp", "sftp", "ftp"] and not (
            transfer_config.get("username") or 
            (transfer_config.get("ssh_key_path") and transfer_config.get("method") != "ftp")
        ):
            logger.warning("""
Remote transfer credentials are missing! Please set environment variables or update config.

Required environment variables for remote transfers:
  REMOTE_USERNAME - Username for remote server
  REMOTE_PASSWORD - Password for remote server (if not using SSH key)
  SSH_KEY_PATH - Path to SSH key file (alternative to password for SCP/SFTP)

To set environment variables:
  Linux/macOS: export REMOTE_USERNAME=your_username
  Windows CMD: set REMOTE_USERNAME=your_username
  Windows PS: $env:REMOTE_USERNAME="your_username"
  
Or create a .env file in the project root.
            """)
    
    # Add API authentication
    if "api" in merged_config:
        merged_config["api"]["username"] = env_vars.get("APSTRA_USERNAME")
        merged_config["api"]["password"] = env_vars.get("APSTRA_PASSWORD")
    
    return merged_config
