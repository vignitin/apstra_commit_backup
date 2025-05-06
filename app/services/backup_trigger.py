"""
Functions for triggering the backup script.
"""
import os
import subprocess
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def run_backup_script(script_path, parameters=None):
    """
    Execute the backup bash script.
    
    Args:
        script_path (str): Path to the backup script
        parameters (list): Additional parameters to pass to the script
        
    Returns:
        tuple: (success, output, error)
    """
    if not os.path.exists(script_path):
        logger.error(f"Backup script not found at {script_path}")
        return False, "", f"Script not found: {script_path}"
    
    # Prepare command
    command = [script_path]
    if parameters:
        command.extend(parameters)
    
    logger.info(f"Executing backup script: {' '.join(command)}")
    
    try:
        # Execute the script
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for the process to complete
        stdout, stderr = process.communicate(timeout=600)  # 10 minute timeout
        
        # Check return code
        if process.returncode == 0:
            logger.info("Backup script executed successfully")
            return True, stdout, stderr
        else:
            logger.error(f"Backup script failed with return code {process.returncode}")
            return False, stdout, stderr
        
    except subprocess.TimeoutExpired:
        logger.error("Backup script timed out")
        return False, "", "Backup script timed out"
    except Exception as e:
        logger.error(f"Error executing backup script: {str(e)}")
        return False, "", str(e)

def get_latest_backup_file(backup_output):
    """
    Extract the path to the latest backup file from the script output.
    
    Args:
        backup_output (str): Output from the backup script
        
    Returns:
        str: Path to the backup file or None
    """
    # This function assumes the backup script outputs the path to the
    # backup file somewhere in its stdout, possibly in a specific format.
    # You'll need to adapt this to match how your script reports the backup file.
    
    # Example: Look for a line starting with "BACKUP_FILE:"
    for line in backup_output.splitlines():
        if line.startswith("BACKUP_FILE:"):
            file_path = line.split(":", 1)[1].strip()
            if os.path.exists(file_path):
                logger.info(f"Found backup file: {file_path}")
                return file_path
    
    # Fallback: Look for any path-like string that exists as a file
    import re
    path_pattern = r'/[/\w\.-]+'
    for match in re.finditer(path_pattern, backup_output):
        potential_path = match.group(0)
        if os.path.isfile(potential_path):
            logger.info(f"Found potential backup file: {potential_path}")
            return potential_path
    
    logger.warning("Could not determine backup file path from script output")
    return None
