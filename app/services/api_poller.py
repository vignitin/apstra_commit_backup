"""
API polling service for monitoring changes in Apstra revisions.
"""
import time
import logging
import requests
import json
import urllib3
from datetime import datetime

# Suppress insecure request warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

def authenticate(server, username, password):
    """
    Authenticate to the Apstra API and get token.
    
    Args:
        server (str): Apstra server address
        username (str): Apstra username
        password (str): Apstra password
        
    Returns:
        str: Authentication token or None if failed
    """
    url = f"https://{server}/api/aaa/login"
    headers = {"Content-Type": "application/json"}
    body = {"username": username, "password": password}
    
    try:
        response = requests.post(
            url,
            json=body,
            headers=headers,
            verify=False
        )
        
        if 200 <= response.status_code < 300:
            data = response.json()
            if "token" in data:
                logger.info("Successfully authenticated to Apstra API")
                return data["token"]
        
        logger.error(f"Authentication failed. Status code: {response.status_code}")
        return None
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error connecting to Apstra server: {str(e)}")
        return None

def get_revisions(server, token, endpoint):
    """
    Get all revisions from the specified endpoint.
    
    Args:
        server (str): Apstra server address
        token (str): API token
        endpoint (str): API endpoint
        
    Returns:
        list: List of revisions or empty list if failed
    """
    # Ensure endpoint starts with /
    if not endpoint.startswith("/"):
        endpoint = f"/{endpoint}"
    
    url = f"https://{server}{endpoint}"
    headers = {"AuthToken": token}
    
    try:
        response = requests.get(
            url,
            headers=headers,
            verify=False
        )
        
        if 200 <= response.status_code < 300:
            data = response.json()
            if "items" in data:
                logger.debug(f"Retrieved {len(data['items'])} revisions")
                return data["items"]
            else:
                logger.warning("No 'items' found in API response")
                return []
        
        logger.error(f"Failed to get revisions. Status code: {response.status_code}")
        return []
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error connecting to Apstra server: {str(e)}")
        return []

def get_latest_revision(revisions):
    """
    Get the latest revision from the list of revisions.
    
    Args:
        revisions (list): List of revision dictionaries
        
    Returns:
        dict: Latest revision or None if list is empty
    """
    if not revisions:
        return None
    
    # Sort revisions by revision_id as integers (assuming they're numeric)
    sorted_revisions = sorted(
        revisions, 
        key=lambda x: int(x.get("revision_id", "0")), 
        reverse=True
    )
    
    # Return the revision with the highest revision_id
    return sorted_revisions[0]

def check_for_new_revision(server, token, endpoint, last_revision_id):
    """
    Check if there's a new revision.
    
    Args:
        server (str): Apstra server address
        token (str): API token
        endpoint (str): API endpoint
        last_revision_id (str): Last seen revision ID
        
    Returns:
        tuple: (has_new_revision, latest_revision)
    """
    revisions = get_revisions(server, token, endpoint)
    
    if not revisions:
        logger.warning("No revisions retrieved, cannot check for changes")
        return False, None
    
    latest_revision = get_latest_revision(revisions)
    
    if not latest_revision:
        logger.warning("Failed to determine latest revision")
        return False, None
    
    latest_id = latest_revision.get("revision_id")
    
    # If we don't have a previous revision ID or the new one is greater
    if last_revision_id is None:
        logger.info(f"First run, latest revision is {latest_id}")
        return True, latest_revision
    
    if int(latest_id) > int(last_revision_id):
        logger.info(f"New revision detected: {latest_id} (previous: {last_revision_id})")
        return True, latest_revision
    
    logger.debug(f"No new revision (latest: {latest_id}, previous: {last_revision_id})")
    return False, latest_revision

def poll_api(config, state):
    """
    Poll the API and check for changes.
    
    Args:
        config (dict): Configuration dictionary
        state (dict): Current state
        
    Returns:
        tuple: (changes_detected, new_state, token)
    """
    api_config = config.get("api", {})
    server = api_config.get("server")
    endpoint = api_config.get("endpoint")
    username = api_config.get("username")
    password = api_config.get("password")
    
    if not all([server, endpoint, username, password]):
        logger.error("Missing required API configuration")
        return False, state, None
    
    # Authenticate
    token = authenticate(server, username, password)
    if not token:
        logger.error("Failed to authenticate to API")
        return False, state, None
    
    # Get the last revision ID from state
    last_revision_id = state.get("last_revision_id")
    
    # Check for new revision
    has_new_revision, latest_revision = check_for_new_revision(
        server, token, endpoint, last_revision_id
    )
    
    # If we have a latest revision, update the state
    if latest_revision:
        current_time = datetime.now().isoformat()
        new_state = {
            "last_revision_id": latest_revision.get("revision_id"),
            "last_poll_time": current_time
        }
    else:
        new_state = state
    
    return has_new_revision, new_state, token
