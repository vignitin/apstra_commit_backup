"""
State management for the API polling and backup service.
"""
import os
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def load_state(state_file_path):
    """
    Load the state from a JSON file.
    
    Args:
        state_file_path (str): Path to the state file
    
    Returns:
        dict: Loaded state or empty dict if file doesn't exist
    """
    try:
        # Create directory if it doesn't exist
        state_dir = os.path.dirname(state_file_path)
        if state_dir:
            os.makedirs(state_dir, exist_ok=True)
        
        # Check if file exists
        if os.path.exists(state_file_path):
            with open(state_file_path, 'r') as file:
                state = json.load(file)
                logger.debug(f"State loaded from {state_file_path}")
                return state
        else:
            logger.info(f"State file {state_file_path} does not exist, creating new state")
            return {"last_revision_id": None, "last_poll_time": None}
    except Exception as e:
        logger.error(f"Error loading state: {str(e)}")
        return {"last_revision_id": None, "last_poll_time": None}

def save_state(state_file_path, state):
    """
    Save the state to a JSON file.
    
    Args:
        state_file_path (str): Path to the state file
        state (dict): State to save
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create directory if it doesn't exist
        state_dir = os.path.dirname(state_file_path)
        if state_dir:
            os.makedirs(state_dir, exist_ok=True)
        
        with open(state_file_path, 'w') as file:
            json.dump(state, file, indent=2)
            logger.debug(f"State saved to {state_file_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving state: {str(e)}")
        return False

def update_state(state_file_path, revision_id, poll_time):
    """
    Update the state with new revision ID and poll time.
    
    Args:
        state_file_path (str): Path to the state file
        revision_id (str): Latest revision ID
        poll_time (str): Current poll time
    
    Returns:
        dict: Updated state
    """
    # Load current state
    state = load_state(state_file_path)
    
    # Update state
    state["last_revision_id"] = revision_id
    state["last_poll_time"] = poll_time
    
    # Save updated state
    save_state(state_file_path, state)
    
    return state
