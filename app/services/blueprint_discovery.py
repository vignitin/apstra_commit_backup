"""
Blueprint discovery service for automatically discovering and managing Apstra blueprints.
"""
import logging
import requests
import urllib3
from datetime import datetime

# Suppress insecure request warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

def discover_blueprints(server, token):
    """
    Discover all available blueprints from the Apstra API.
    
    Args:
        server (str): Apstra server address
        token (str): API authentication token
        
    Returns:
        list: List of blueprint configurations or empty list if failed
    """
    url = f"https://{server}/api/blueprints"
    headers = {"AuthToken": token}
    
    try:
        response = requests.get(
            url,
            headers=headers,
            verify=False
        )
        
        if 200 <= response.status_code < 300:
            data = response.json()
            blueprints = []
            
            if "items" in data:
                logger.info(f"Discovered {len(data['items'])} blueprints")
                
                for blueprint in data["items"]:
                    blueprint_id = blueprint.get("id")
                    blueprint_name = blueprint.get("label", blueprint_id)
                    
                    if blueprint_id:
                        blueprint_config = {
                            "id": blueprint_id,
                            "name": blueprint_name,
                            "endpoint": f"/api/blueprints/{blueprint_id}/revisions"
                        }
                        blueprints.append(blueprint_config)
                        logger.debug(f"Added blueprint: {blueprint_name} ({blueprint_id})")
                
                return blueprints
            else:
                logger.warning("No 'items' found in blueprints API response")
                return []
        
        logger.error(f"Failed to discover blueprints. Status code: {response.status_code}")
        if response.status_code == 404:
            logger.error("Blueprints API endpoint not found. Check Apstra version compatibility.")
        return []
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error connecting to Apstra server for blueprint discovery: {str(e)}")
        return []

def update_blueprints_in_config(config, discovered_blueprints):
    """
    Update the configuration with discovered blueprints.
    
    Args:
        config (dict): Current configuration dictionary
        discovered_blueprints (list): List of discovered blueprint configurations
        
    Returns:
        dict: Updated configuration dictionary
    """
    if not discovered_blueprints:
        logger.warning("No blueprints discovered, keeping existing configuration")
        return config
    
    # Create a copy of the config to avoid modifying the original
    updated_config = config.copy()
    
    # Ensure api section exists
    if "api" not in updated_config:
        updated_config["api"] = {}
    
    # Get current blueprints for comparison
    current_blueprints = updated_config["api"].get("blueprints", [])
    current_blueprint_ids = {bp.get("id") for bp in current_blueprints}
    discovered_blueprint_ids = {bp.get("id") for bp in discovered_blueprints}
    
    # Log changes
    new_blueprints = discovered_blueprint_ids - current_blueprint_ids
    removed_blueprints = current_blueprint_ids - discovered_blueprint_ids
    
    if new_blueprints:
        logger.info(f"New blueprints discovered: {', '.join(new_blueprints)}")
    if removed_blueprints:
        logger.info(f"Blueprints no longer available: {', '.join(removed_blueprints)}")
    
    # Update the blueprints list
    updated_config["api"]["blueprints"] = discovered_blueprints
    
    # Add discovery timestamp
    updated_config["api"]["last_blueprint_discovery"] = datetime.now().isoformat()
    
    logger.info(f"Configuration updated with {len(discovered_blueprints)} blueprints")
    return updated_config

def should_refresh_blueprints(config, refresh_interval_seconds=300):
    """
    Check if blueprint discovery should be refreshed based on the last discovery time.
    
    Args:
        config (dict): Current configuration dictionary
        refresh_interval_seconds (int): Seconds between blueprint discovery refreshes
        
    Returns:
        bool: True if blueprints should be refreshed
    """
    api_config = config.get("api", {})
    last_discovery = api_config.get("last_blueprint_discovery")
    
    if not last_discovery:
        logger.info("No previous blueprint discovery found, refresh needed")
        return True
    
    try:
        last_discovery_time = datetime.fromisoformat(last_discovery)
        current_time = datetime.now()
        time_diff = current_time - last_discovery_time
        
        seconds_since_discovery = time_diff.total_seconds()
        
        if seconds_since_discovery >= refresh_interval_seconds:
            logger.info(f"Blueprint discovery is {seconds_since_discovery:.0f} seconds old, refresh needed")
            return True
        else:
            logger.debug(f"Blueprint discovery is {seconds_since_discovery:.0f} seconds old, no refresh needed")
            return False
            
    except ValueError as e:
        logger.error(f"Error parsing last discovery time: {e}")
        return True

def refresh_blueprints_if_needed(config, server, token, refresh_interval_seconds=300):
    """
    Refresh blueprints if the configured interval has passed.
    
    Args:
        config (dict): Current configuration dictionary
        server (str): Apstra server address
        token (str): API authentication token
        refresh_interval_seconds (int): Seconds between blueprint discovery refreshes
        
    Returns:
        dict: Updated configuration dictionary (may be unchanged)
    """
    if not should_refresh_blueprints(config, refresh_interval_seconds):
        return config
    
    logger.info("Refreshing blueprint discovery...")
    discovered_blueprints = discover_blueprints(server, token)
    
    if discovered_blueprints:
        return update_blueprints_in_config(config, discovered_blueprints)
    else:
        logger.warning("Blueprint discovery failed, keeping existing configuration")
        return config