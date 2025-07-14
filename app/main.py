#!/usr/bin/env python3
"""
Main entry point for the API polling and backup service.
"""
import os
import sys
import time
import logging
import signal
import argparse
from pathlib import Path
from utils.config import load_config
from utils.env_loader import load_environment_variables, apply_env_to_config
from utils.state import load_state, save_state, update_state
from services.api_poller import poll_api
from services.backup_trigger import run_backup_script, get_latest_backup_file
from services.transfer import transfer_file


# Add the app directory to the path
app_dir = Path(__file__).resolve().parent
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

# Import utility functions
from utils.config import load_config, update_config_with_blueprints
from utils.env_loader import load_environment_variables, apply_env_to_config
from utils.state import load_state, save_state, update_state
from services.api_poller import poll_api, authenticate
from services.backup_trigger import run_backup_script, get_latest_backup_file
from services.transfer import transfer_file
from services.blueprint_discovery import discover_blueprints, should_refresh_blueprints

# Global variables for signal handling
running = True

def setup_logging(config):
    """
    Set up logging configuration.
    
    Args:
        config (dict): Configuration dictionary
    """
    log_config = config.get("logging", {})
    log_level = getattr(logging, log_config.get("level", "INFO"))
    log_file = log_config.get("file", "logs/backup_service.log")
    
    # Create logs directory if it doesn't exist
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file) if log_file else logging.NullHandler()
        ]
    )

def handle_signal(signum, frame):
    """Signal handler for graceful shutdown."""
    global running
    logging.info(f"Received signal {signum}, shutting down...")
    running = False

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='API Polling and Backup Service')
    parser.add_argument(
        '--config', 
        default='app/config/config.yaml',
        help='Path to configuration file'
    )
    parser.add_argument(
        '--env-file',
        help='Path to .env file (defaults to .env in the project root)'
    )
    parser.add_argument(
        '--blueprint-refresh-seconds',
        type=int,
        default=300,
        help='Seconds between blueprint discovery refreshes (default: 300 seconds / 5 minutes)'
    )
    parser.add_argument(
        '--force-blueprint-discovery',
        action='store_true',
        help='Force blueprint discovery on startup regardless of last discovery time'
    )
    return parser.parse_args()

def refresh_blueprint_discovery(config, config_path, refresh_interval_seconds=300):
    """
    Refresh blueprint discovery if needed and update the configuration file.
    
    Args:
        config (dict): Configuration dictionary
        config_path (str): Path to the configuration file
        refresh_interval_seconds (int): Seconds between blueprint discovery refreshes
        
    Returns:
        dict: Updated configuration dictionary (may be unchanged)
    """
    logger = logging.getLogger(__name__)
    
    # Check if refresh is needed
    if not should_refresh_blueprints(config, refresh_interval_seconds):
        return config
    
    logger.info("Starting blueprint discovery...")
    
    # Get API credentials
    api_config = config.get("api", {})
    server = api_config.get("server")
    username = api_config.get("username")
    password = api_config.get("password")
    
    if not all([server, username, password]):
        logger.error("Missing required API configuration for blueprint discovery")
        return config
    
    # Authenticate to API
    token = authenticate(server, username, password)
    if not token:
        logger.error("Failed to authenticate for blueprint discovery")
        return config
    
    # Discover blueprints
    discovered_blueprints = discover_blueprints(server, token)
    
    logger.info(f"Blueprint discovery returned: {type(discovered_blueprints)} with {len(discovered_blueprints) if discovered_blueprints else 0} items")
    
    if discovered_blueprints:
        # Update configuration file
        success = update_config_with_blueprints(config_path, discovered_blueprints)
        
        if success:
            # Reload config to get updated blueprints
            updated_config = load_config(config_path)
            # Preserve API credentials from the original config
            updated_config["api"]["username"] = config["api"]["username"]
            updated_config["api"]["password"] = config["api"]["password"]
            # Preserve transfer credentials from the original config
            if "transfer" in config:
                updated_config["transfer"] = config["transfer"]
            logger.info(f"Blueprint discovery completed. Found {len(discovered_blueprints)} blueprints")
            return updated_config
        else:
            logger.error("Failed to update configuration file with discovered blueprints")
            return config
    else:
        logger.warning("No blueprints discovered")
        return config

def process_blueprint_changes(config, blueprint_id, blueprint_name):
    """
    Process changes for a specific blueprint.
    
    Args:
        config (dict): Configuration dictionary
        blueprint_id (str): ID of the blueprint with changes
        blueprint_name (str): Name of the blueprint with changes
        
    Returns:
        bool: True if backup and transfer succeeded, False otherwise
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Processing changes for blueprint: {blueprint_name} ({blueprint_id})")
    
    # Run backup script
    backup_script = config.get("backup", {}).get("script_path") or "/usr/sbin/aos_backup"
    
    # Add blueprint ID as a parameter if not already in the parameters list
    backup_params = config.get("backup", {}).get("parameters", []).copy()
    if "--blueprint" not in " ".join(backup_params):
        backup_params.extend(["--blueprint", blueprint_id])
    
    success, output, error = run_backup_script(backup_script, backup_params)
    
    if success:
        # Get the backup file path from the output
        backup_file = get_latest_backup_file(output)
        if backup_file:
            # Transfer the backup file
            logger.info(f"Transferring backup file for {blueprint_name}: {backup_file}")
            transfer_success = transfer_file(config, backup_file, blueprint_id, blueprint_name)
            
            if transfer_success:
                logger.info(f"Backup process for {blueprint_name} completed successfully")
                return True
            else:
                logger.error(f"Failed to transfer backup file for {blueprint_name}")
                return False
        else:
            logger.error(f"Could not determine backup file path for {blueprint_name}")
            return False
    else:
        logger.error(f"Backup script failed for {blueprint_name}: {error}")
        return False

def process_full_system_backup(config, changed_blueprints):
    """
    Process a full system backup when any blueprints have changes.
    
    Args:
        config (dict): Configuration dictionary
        changed_blueprints (list): List of tuples (blueprint_id, blueprint_name) that had changes
        
    Returns:
        bool: True if backup and transfer succeeded, False otherwise
    """
    logger = logging.getLogger(__name__)
    logger.info("Starting full system backup")
    
    # Run backup script without blueprint parameter for full system backup
    backup_script = config.get("backup", {}).get("script_path") or "/usr/sbin/aos_backup"
    backup_params = config.get("backup", {}).get("parameters", []).copy()
    
    # Make sure we don't include any blueprint-specific parameters for full backup
    backup_params = [param for param in backup_params if param != "--blueprint"]
    
    success, output, error = run_backup_script(backup_script, backup_params)
    
    if success:
        # Get the backup file path from the output
        backup_file = get_latest_backup_file(output)
        if backup_file:
            # Create a descriptive name for the transfer that includes changed blueprint count
            blueprint_summary = f"{len(changed_blueprints)}_blueprints_changed"
            
            # Transfer the backup file with descriptive naming
            logger.info(f"Transferring full system backup file: {backup_file}")
            transfer_success = transfer_file(config, backup_file, "full_system", blueprint_summary)
            
            if transfer_success:
                logger.info("Full system backup process completed successfully")
                return True
            else:
                logger.error("Failed to transfer full system backup file")
                return False
        else:
            logger.error("Could not determine backup file path for full system backup")
            return False
    else:
        logger.error(f"Full system backup script failed: {error}")
        return False

def main():
    """Main function to run the service."""
    # Parse command line arguments
    args = parse_arguments()
    
    # Load configuration
    config = load_config(args.config)
    
    # Set up logging
    setup_logging(config)
    logger = logging.getLogger(__name__)
    
    # Get environment variables
    env_vars, env_success = load_environment_variables(args.env_file)
    
    if not env_success:
        logger.error("Missing required environment variables. Service cannot start.")
        logger.error("Please set APSTRA_USERNAME and APSTRA_PASSWORD environment variables or in .env file.")
        sys.exit(1)
    
    # Apply environment variables to config
    config = apply_env_to_config(config, env_vars)
    
    # Verify transfer configuration
    transfer_config = config.get("transfer", {})
    if "username" not in transfer_config:
        logger.warning("Remote username not found in configuration")
        logger.warning("Make sure REMOTE_USERNAME is set in environment or .env file")

    
    # Load initial state
    state_file = config.get("state", {}).get("file_path", "data/backup_state.json")
    state = load_state(state_file)
    
    # Initialize blueprints state if not present
    if "blueprints" not in state:
        state["blueprints"] = {}
    
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    
    logger.info("Starting API polling and backup service")
    
    # Always force blueprint discovery on startup
    logger.info("Performing blueprint discovery on startup")
    # Temporarily set last discovery to None to force refresh
    api_config = config.get("api", {})
    api_config["last_blueprint_discovery"] = None
    config["api"] = api_config
    
    # Perform initial blueprint discovery
    config = refresh_blueprint_discovery(config, args.config, args.blueprint_refresh_seconds)
    
    # For compatibility with older code - handle single blueprint configuration
    api_config = config.get("api", {})
    if "endpoint" in api_config and "blueprints" not in api_config:
        logger.info("Converting single blueprint configuration to multi-blueprint format")
        api_config["blueprints"] = [{
            "id": "default",
            "name": "Default Blueprint",
            "endpoint": api_config["endpoint"]
        }]
        config["api"] = api_config
    
    # Main polling loop
    global running
    while running:
        try:
            # Refresh blueprint discovery if needed
            config = refresh_blueprint_discovery(config, args.config, args.blueprint_refresh_seconds)
            
            # Poll the API and check for changes across all blueprints
            changes_by_blueprint, new_state, token = poll_api(config, state)
            
            if not changes_by_blueprint:
                logger.warning("Failed to poll API or no blueprints configured")
                time.sleep(5)
                continue
            
            # Check if any blueprints have changes
            changed_blueprints = []
            any_changes = False
            
            for blueprint_id, has_changes in changes_by_blueprint.items():
                if has_changes:
                    # Get blueprint details from new state
                    blueprint_state = new_state["blueprints"].get(blueprint_id, {})
                    blueprint_name = blueprint_state.get("blueprint_name", blueprint_id)
                    
                    logger.info(f"Changes detected in blueprint: {blueprint_name} ({blueprint_id})")
                    changed_blueprints.append((blueprint_id, blueprint_name))
                    any_changes = True
            
            # If any changes detected, take a single full system backup
            if any_changes:
                logger.info(f"Changes detected in {len(changed_blueprints)} blueprint(s). Taking full system backup.")
                
                # List the changed blueprints for logging
                for blueprint_id, blueprint_name in changed_blueprints:
                    logger.info(f"  - {blueprint_name} ({blueprint_id})")
                
                # Take full system backup
                success = process_full_system_backup(config, changed_blueprints)
                
                if success:
                    # Update state for all blueprints that had changes
                    for blueprint_id, _ in changed_blueprints:
                        state["blueprints"][blueprint_id] = new_state["blueprints"][blueprint_id]
                    save_state(state_file, state)
                    logger.info("Full system backup completed successfully")
                else:
                    logger.error("Full system backup failed")
            elif new_state != state:
                # If no backups were needed but state changed, update it
                state = new_state
                save_state(state_file, state)

            
            # Wait for the next polling interval
            polling_interval = config.get("api", {}).get("polling_interval_seconds", 30)
            logger.debug(f"Waiting {polling_interval} seconds before next poll")
            
            # Break the sleep into smaller chunks to respond to signals quickly
            for _ in range(polling_interval):
                if not running:
                    break
                time.sleep(1)
                
        except Exception as e:
            logger.error(f"Error in main loop: {str(e)}")
            # Wait before retrying
            time.sleep(5)
    
    logger.info("Service shutting down gracefully")

if __name__ == "__main__":
    main()