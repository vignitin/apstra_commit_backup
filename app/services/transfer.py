"""
File transfer service for copying backups to remote storage.
"""
import os
import subprocess
import logging
import ftplib
from pathlib import Path
import paramiko
from paramiko import SSHClient
from scp import SCPClient

logger = logging.getLogger(__name__)

def transfer_file(config, full_path):
    """
    Transfer a file to the remote server using the configured method.
    
    Args:
        config (dict): Transfer configuration
        local_file_path (str): Path to the local file
        
    Returns:
        bool: True if successful, False otherwise
    """
    local_file_path=os.path.basename(full_path)

    
    transfer_config = config.get("transfer", {})
    # method = transfer_config.get("method", "scp").lower()
    method="scp"
    
    if method == "scp":
        return transfer_scp(transfer_config, local_file_path, full_path)
    elif method == "sftp":
        return transfer_sftp(transfer_config, local_file_path)
    elif method == "ftp":
        return transfer_ftp(transfer_config, local_file_path)
    else:
        logger.error(f"Unsupported transfer method: {method}")
        return False


logger = logging.getLogger(__name__)

def transfer_scp(config, local_file_path, full_path):
    """
    Transfer a file using SCP via Paramiko.
    
    Args:
        config (dict): SCP configuration
        local_file_path (str): Path to the local file
        full_path (str): Full path information
        
    Returns:
        bool: True if successful, False otherwise
    """
    host = config.get("host")
    port = config.get("port", 22)
    username = config.get("username")
    password = config.get("password")
    ssh_key_path = config.get("ssh_key_path")
    
    if not all([host, username]):
        logger.error("Missing required SCP configuration")
        return False
    
    # Get filename from path
    filename = os.path.basename(full_path)
    full_aos_path = f"/var/lib/aos/snapshot/{local_file_path}/aos.data.tar.gz"
    remote_filename = f"{filename}-aos.data.tar.gz"
    
    print("filename: " + local_file_path)
    print("path: " + full_aos_path)
    
    try:
        # Create SSH client
        ssh = SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Connect with appropriate authentication
        connect_kwargs = {
            "hostname": host,
            "port": port,
            "username": username,
        }
        
        if ssh_key_path:
            connect_kwargs["key_filename"] = ssh_key_path
            logger.info(f"Using SSH key authentication with key: {ssh_key_path}")
        elif password:
            connect_kwargs["password"] = password
            logger.info("Using password authentication")
        else:
            logger.warning("No authentication method provided, using default keys")
        
        # Connect to the remote server
        ssh.connect(**connect_kwargs)
        
        # Create SCP client
        scp = SCPClient(ssh.get_transport())
        
        # If we need to run with sudo privileges for reading the local file
        # we need to use a temporary file approach or modify permissions
        # This solution assumes the running user has access to the file
        logger.info(f"Transferring file via SCP: {full_aos_path} -> {host}:~/{remote_filename}")
        
        # Transfer the file
        scp.put(full_aos_path, f"~/{remote_filename}")
        
        # Close connections
        scp.close()
        ssh.close()
        
        logger.info("SCP transfer completed successfully")
        return True
        
    except paramiko.AuthenticationException as e:
        logger.error(f"Authentication failed: {str(e)}")
        return False
    except paramiko.SSHException as e:
        logger.error(f"SSH error: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error during SCP transfer: {str(e)}")
        return False

def transfer_sftp(config, local_file_path):
    """
    Transfer a file using SFTP.
    
    Args:
        config (dict): SFTP configuration
        local_file_path (str): Path to the local file
        
    Returns:
        bool: True if successful, False otherwise
    """
    logger.info("SFTP transfer requested - importing paramiko")
    try:
        import paramiko
    except ImportError:
        logger.error("Paramiko library not found. Install with 'pip install paramiko'")
        return False
    
    host = config.get("host")
    port = config.get("port", 22)
    username = config.get("username")
    password = config.get("password")
    ssh_key_path = config.get("ssh_key_path")
    remote_dir = config.get("remote_directory", "~/")
    
    if not all([host, username]) or (not password and not ssh_key_path):
        logger.error("Missing required SFTP configuration")
        return False
    
    # Get filename from path
    filename = os.path.basename(local_file_path)
    
    # Create SSH client
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        # Connect to the remote server
        if ssh_key_path:
            key = paramiko.RSAKey.from_private_key_file(ssh_key_path)
            client.connect(host, port=port, username=username, pkey=key)
        else:
            client.connect(host, port=port, username=username, password=password)
        
        # Open SFTP session
        sftp = client.open_sftp()
        
        # Ensure remote directory exists
        try:
            sftp.chdir(remote_dir)
        except IOError:
            logger.warning(f"Remote directory {remote_dir} doesn't exist, attempting to create")
            sftp.mkdir(remote_dir)
            sftp.chdir(remote_dir)
        
        # Upload the file
        remote_path = f"{remote_dir}/{filename}"
        logger.info(f"Transferring file via SFTP: {local_file_path} -> {host}:{remote_path}")
        sftp.put(local_file_path, filename)
        
        # Close connections
        sftp.close()
        client.close()
        
        logger.info("SFTP transfer completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error during SFTP transfer: {str(e)}")
        if 'client' in locals() and client:
            client.close()
        return False

def transfer_ftp(config, local_file_path):
    """
    Transfer a file using FTP.
    
    Args:
        config (dict): FTP configuration
        local_file_path (str): Path to the local file
        
    Returns:
        bool: True if successful, False otherwise
    """
    host = config.get("host")
    port = config.get("port", 21)
    username = config.get("username")
    password = config.get("password")
    remote_dir = config.get("remote_directory", ".")
    
    if not all([host, username, password]):
        logger.error("Missing required FTP configuration")
        return False
    
    # Get filename from path
    filename = os.path.basename(local_file_path)
    
    try:
        # Connect to FTP server
        ftp = ftplib.FTP()
        ftp.connect(host, port)
        ftp.login(username, password)
        
        # Try to change to the remote directory
        try:
            ftp.cwd(remote_dir)
        except ftplib.error_perm:
            # Create directory if it doesn't exist
            logger.warning(f"Remote directory {remote_dir} doesn't exist, attempting to create")
            # Split the path and create directories recursively
            dirs = remote_dir.split('/')
            for d in dirs:
                if d:  # Skip empty parts (leading/trailing /)
                    try:
                        ftp.cwd(d)
                    except ftplib.error_perm:
                        ftp.mkd(d)
                        ftp.cwd(d)
        
        # Upload the file
        logger.info(f"Transferring file via FTP: {local_file_path} -> {host}:{remote_dir}/{filename}")
        with open(local_file_path, 'rb') as file:
            ftp.storbinary(f'STOR {filename}', file)
        
        # Close connection
        ftp.quit()
        
        logger.info("FTP transfer completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error during FTP transfer: {str(e)}")
        return False
