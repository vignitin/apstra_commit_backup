# Apstra API Polling and Backup Tool

A robust utility that monitors commits across multiple blueprints and triggers backups when changes are detected, with secure transfer to remote storage.

## Features

- **Automatic Blueprint Discovery**: Automatically discovers and tracks all blueprints in your Apstra system
- **Immediate Detection**: Blueprint discovery runs on every startup for immediate detection of changes
- **Fast Refresh Cycles**: Blueprint discovery runs every 5 minutes by default (configurable down to seconds)
- **Multi-Blueprint Support**: Monitor multiple Apstra blueprints simultaneously
- **Dynamic Configuration**: Configuration file is automatically updated with discovered blueprints
- **Periodic Polling**: Configurable polling intervals for each blueprint
- **Change Detection**: Identifies new revisions based on revision IDs
- **Automated Backups**: Triggers backup script when changes are detected
- **Remote Transfer**: Securely transfers backup files to remote storage
- **Flexible Authentication**: Supports password and SSH key authentication
- **Comprehensive Logging**: Detailed logs for monitoring and troubleshooting
- **State Management**: Persistent tracking of blueprint states across restarts

## Installation

### Prerequisites

- Python 3.8 or higher
- pip3 package manager
- Access to an Apstra server
- Remote storage server (for backup transfers)

### Basic Installation and Useage

**Video Guide**

[![Video Title](https://img.youtube.com/vi/nbq1oGrmVS0/maxresdefault.jpg)](https://youtu.be/nbq1oGrmVS0)

**Commmands**

1. Clone the repository:
   ```bash
   git clone https://github.com/iamjarvs/apstra_commit_backup.git
   cd apstra_commit_backup
   ```

2. Install the requirements:
   ```bash
   pip install -r requirements.txt
   ```

3. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

4. Update the `.env` file with your credentials:
   ```
   # Apstra API credentials
   APSTRA_USERNAME=admin
   APSTRA_PASSWORD=your_password

   # Remote server credentials
   REMOTE_USERNAME=backup_user
   REMOTE_PASSWORD=your_remote_password
   # Or use SSH key authentication
   # SSH_KEY_PATH=/path/to/private_key
   ```

5. Update the configuration in `app/config/config.yaml`
   ```bash
   cp app/config/example.config.yaml app/config/config.yaml
   vi app/config/config.yaml
   ```
   
   **Note**: The blueprint list in the configuration file will be automatically discovered and updated by the application. You only need to configure the server address and other settings.

6. Run script
   ```bash
   python3 app/main.py
   ```
   
   **Note**: The service no longer requires sudo privileges. It runs with regular user permissions and should be configured to run as a service with appropriate permissions for accessing the aos_backup script. 



## Configuration

Configuration is handled through a combination of the `config.yaml` file and environment variables.

# Environment Variable Management

Two methods are supported for providing environment variables:

1. **System environment variables**
2. **`.env` file** in the project root directory

#### Required Environment Variables

- `APSTRA_USERNAME`: Username for Apstra API authentication
- `APSTRA_PASSWORD`: Password for Apstra API authentication

## Using a .env File

Create a file named `.env` in the project root directory with the following format:

```
# Apstra API credentials
APSTRA_USERNAME=admin
APSTRA_PASSWORD=your_password

# Remote server credentials
REMOTE_USERNAME=backup_user
REMOTE_PASSWORD=your_remote_password
# Alternatively, use SSH key authentication
SSH_KEY_PATH=/path/to/private_key
SSH_KEY_PASSPHRASE=your_key_passphrase
```

The application will automatically load this file if it exists.

## Required Environment Variables

The following environment variables are required:

- `APSTRA_USERNAME`: Username for Apstra API authentication
- `APSTRA_PASSWORD`: Password for Apstra API authentication

## Optional Environment Variables

These environment variables are optional:

- `REMOTE_USERNAME`: Username for remote server
- `REMOTE_PASSWORD`: Password for remote server (for password authentication)
- `SSH_KEY_PATH`: Path to SSH key file (for key-based authentication)
- `SSH_KEY_PASSPHRASE`: Passphrase for SSH key if it's protected

## Command Line Options

The application supports the following command line options:

```
--config PATH                    Path to custom config file (default: app/config/config.yaml)
--env-file PATH                  Path to .env file (default: .env in project root)
--blueprint-refresh-seconds SECONDS  Seconds between blueprint discovery refreshes (default: 300)
--force-blueprint-discovery       Force blueprint discovery on startup regardless of last discovery time (deprecated - discovery now always runs on startup)
```

Examples:
```bash
# Run with default settings
python3 app/main.py

# Run with custom config and environment files
python3 app/main.py --config custom-config.yaml --env-file /path/to/.env

# Set blueprint refresh interval to 60 seconds  
python3 app/main.py --blueprint-refresh-seconds 60

# Set blueprint refresh interval to 10 minutes (600 seconds)
python3 app/main.py --blueprint-refresh-seconds 600

# Combine options with custom config
python3 app/main.py --blueprint-refresh-seconds 120 --config custom-config.yaml
```

## Configuration File

The configuration file (`app/config/config.yaml`) contains settings for:

### Automatic Blueprint Discovery

**Important**: The blueprint list in the configuration file is now automatically managed by the application. You no longer need to manually add or remove blueprints from the configuration.

```yaml
# API Configuration
api:
  server: "10.28.143.3"
  polling_interval_seconds: 30
  
  # Blueprints configuration - This section is automatically populated
  # by the blueprint discovery service
  blueprints:
    # This section will be automatically updated by blueprint discovery
    # Example entries (automatically generated):
    # - id: "494c107b-3620-4be1-9ffc-1ffc8611482b"
    #   name: "DataCenter-1"
    #   endpoint: "/api/blueprints/494c107b-3620-4be1-9ffc-1ffc8611482b/revisions"
    #
    # - id: "5a7e309c-4521-4af2-8971-12b96c5adef8"
    #   name: "DataCenter-2"
    #   endpoint: "/api/blueprints/5a7e309c-4521-4af2-8971-12b96c5adef8/revisions"
  
  # Timestamp of last blueprint discovery (automatically managed)
  # last_blueprint_discovery: "2025-01-01T00:00:00.000000"

backup:
  script_path: "/usr/sbin/aos_backup"
  parameters: []
  
transfer:
  method: "scp"
  host: "backup.example.com"
  port: 22
  remote_directory: "/backups/apstra/"
```

### Blueprint Configuration Details

The application automatically discovers blueprints from your Apstra system and populates the configuration. Each discovered blueprint will have:

- `id`: The UUID of the blueprint (automatically discovered)
- `name`: The friendly name of the blueprint (automatically discovered from Apstra)
- `endpoint`: The API endpoint to poll for this blueprint (automatically generated)

### Blueprint Discovery Process

1. **On Startup**: The application **always** automatically discovers all blueprints from your Apstra system on every startup
2. **Periodic Refresh**: Blueprint discovery runs every 5 minutes (300 seconds) by default (configurable with `--blueprint-refresh-seconds`)
3. **Configuration Update**: The `config.yaml` file is automatically updated with discovered blueprints
4. **Backup Safety**: A single backup of the configuration file is maintained (config.yaml.backup) - only updated when content changes
5. **Logging**: All blueprint discovery activities are logged for visibility

## Usage

### Running the Application

#### Basic Usage

```bash
# Run with automatic blueprint discovery (always runs on startup)
python3 app/main.py
```

#### Advanced Usage Examples

```bash
# Set faster blueprint refresh interval (every 60 seconds)
python3 app/main.py --blueprint-refresh-seconds 60

# Set custom blueprint refresh interval (every 10 minutes)
python3 app/main.py --blueprint-refresh-seconds 600

# Use custom configuration and environment files
python3 app/main.py --config /path/to/custom-config.yaml --env-file /path/to/.env

# Combine multiple options
python3 app/main.py --blueprint-refresh-seconds 120 --config custom-config.yaml
```


## How It Works

### Blueprint Discovery Process

1. **Authentication**: The application authenticates with the Apstra server using the provided credentials
2. **Blueprint Discovery**: The application calls the Apstra API to discover all available blueprints
3. **Configuration Update**: The discovered blueprints are automatically added to the configuration file
4. **Backup Creation**: A single backup of the configuration file is maintained (config.yaml.backup) - only updated when content actually changes

### Polling Process

1. **Startup Discovery**: The application **always** discovers blueprints on startup to ensure immediate detection of changes
2. **Periodic Discovery**: The application periodically re-discovers blueprints (every 5 minutes by default, configurable)
3. **Blueprint Monitoring**: For each discovered blueprint:
   - The API endpoint is polled for revision information
   - The latest revision is compared with the last known revision
   - If a new revision is detected, the backup process is triggered

### Backup Process

1. When changes are detected in a blueprint, the backup script
2. The backup script creates a snapshot of the AOS server
3. The path to the backup file is extracted from the script output
4. The backup file is transferred to the remote server

### File Transfer

Backup files are transferred to the remote server with filenames that include:
- The blueprint name that triggered the backup (or ID if no name is provided)
- A timestamp
- The file extension

Example: `DataCenter-1-20250508_101530-aos.data.tar.gz`

### State Management

The application maintains state about each blueprint in a JSON file:

```json
{
  "last_poll_time": "2025-05-08T10:15:30.123456",
  "last_updated": "2025-05-08T10:15:30.123456",
  "blueprints": {
    "494c107b-3620-4be1-9ffc-1ffc8611482b": {
      "last_revision_id": "123",
      "last_poll_time": "2025-05-08T10:15:30.123456",
      "blueprint_id": "494c107b-3620-4be1-9ffc-1ffc8611482b",
      "blueprint_name": "DataCenter-1"
    },
    "5a7e309c-4521-4af2-8971-12b96c5adef8": {
      "last_revision_id": "456",
      "last_poll_time": "2025-05-08T10:15:25.123456",
      "blueprint_id": "5a7e309c-4521-4af2-8971-12b96c5adef8", 
      "blueprint_name": "DataCenter-2"
    }
  }
}
```

## Advanced Configuration

### Full Configuration Reference

```yaml
# API Configuration
api:
  # Apstra server address (without http/https)
  server: "10.28.143.3"
  # Polling interval in seconds
  polling_interval_seconds: 30
  # Custom headers (optional)
  headers:
    Content-Type: "application/json"
    Accept: "application/json"
  # API request timeout in seconds (optional)
  timeout: 10
  # Whether to verify SSL certificates (optional)
  verify_ssl: false
  
  # Multiple blueprints configuration
  blueprints:
    - id: "494c107b-3620-4be1-9ffc-1ffc8611482b"
      name: "DataCenter-1"
      endpoint: "/api/blueprints/494c107b-3620-4be1-9ffc-1ffc8611482b/revisions"
    
    - id: "5a7e309c-4521-4af2-8971-12b96c5adef8"
      name: "DataCenter-2"
      endpoint: "/api/blueprints/5a7e309c-4521-4af2-8971-12b96c5adef8/revisions"

# Backup Configuration
backup:
  # Path to the backup script
  script_path: "/usr/sbin/aos_backup"
  # Additional parameters to pass to the script (optional)
  parameters: ["--full", "--compress"]
  # Timeout for backup script execution in seconds (optional)
  timeout: 600
  # Working directory for the backup script (optional)
  working_dir: "/path/to/working/dir"
  # Environment variables to pass to the backup script (optional)
  env:
    BACKUP_LEVEL: "full"
    COMPRESSION: "gzip"

# Remote Transfer Configuration
transfer:
  # Transfer method: scp, sftp, or ftp
  method: "scp"
  # Remote server hostname or IP
  host: "backup.example.com"
  # Remote server port (default: 22 for scp/sftp, 21 for ftp)
  port: 22
  # Directory on the remote server where backups will be stored
  remote_directory: "/backups/apstra/"
  # Number of retry attempts for failed transfers (optional)
  retry_attempts: 3
  # Delay between retry attempts in seconds (optional)
  retry_delay: 5
  # Additional SCP options (optional, only for SCP method)
  scp_options: ["-C", "-o", "ConnectTimeout=10"]
  # Whether to create remote directory if it doesn't exist (optional)
  create_remote_dir: true
  # Timeout for transfer operations in seconds (optional)
  timeout: 300
  # Whether to keep the local backup file after transfer (optional)
  keep_local: true

# State Management
state:
  # Path to the state file (stores the last seen revision ID)
  file_path: "data/backup_state.json"
  # Backup state file after each update (optional)
  backup_state: true
  # Maximum number of state backups to keep (optional)
  max_backups: 5

# Logging
logging:
  # Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL
  level: "INFO"
  # Log file path
  file: "logs/backup_service.log"
  # Maximum log file size in bytes before rotation (optional)
  max_size: 10485760  # 10 MB
  # Number of backup logs to keep (optional)
  backup_count: 5
  # Log format (optional)
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  # Whether to log to console as well (optional)
  console: true
  # Console log level (optional, can be different from file log level)
  console_level: "INFO"
```

### Transfer Method Examples

#### SCP Transfer (with password)

```yaml
transfer:
  method: "scp"
  host: "backup.example.com"
  port: 22
```

**Required Environment Variables:**
```
REMOTE_USERNAME=backup_user
REMOTE_PASSWORD=your_remote_password
```

#### SCP Transfer (with SSH key)

```yaml
transfer:
  method: "scp"
  host: "backup.example.com"
  port: 22
```

**Required Environment Variables:**
```
REMOTE_USERNAME=backup_user
SSH_KEY_PATH=/home/user/.ssh/id_rsa
# Optional passphrase if key is protected
SSH_KEY_PASSPHRASE=your_key_passphrase
```

## Backup Script

The backup script is called when changes are detected. The application passes the blueprint ID as a parameter to the script, which should:

1. Perform the backup operation for the specified blueprint
2. Output the path to the backup file with a format that can be parsed by the application
3. Return exit code 0 on success

Sample output format:
```
New AOS snapshot: snapshot-20250508-101530
```

## Logging

Logs are written to both stdout and a log file specified in the configuration.

Default log location: `logs/backup_service.log`

Log example:
```
2025-05-08 10:15:30,123 - app.main - INFO - Starting API polling and backup service
2025-05-08 10:15:31,456 - app.services.api_poller - INFO - Successfully authenticated to Apstra API
2025-05-08 10:15:32,789 - app.services.api_poller - INFO - Polling blueprint: DataCenter-1 (494c107b-3620-4be1-9ffc-1ffc8611482b)
2025-05-08 10:15:33,012 - app.services.api_poller - INFO - New revision detected: 124 (previous: 123)
2025-05-08 10:15:33,345 - app.main - INFO - Changes detected in blueprint: DataCenter-1 (494c107b-3620-4be1-9ffc-1ffc8611482b)
```

## Debug Mode

To enable more detailed logging, set the logging level to DEBUG in the configuration:

```yaml
logging:
  level: "DEBUG"
```

## Blueprint Discovery Troubleshooting

### Common Issues

1. **No Blueprints Discovered**
   - Check that your Apstra credentials are correct
   - Verify network connectivity to the Apstra server
   - Ensure the Apstra API is accessible at `/api/blueprints`

2. **Configuration File Not Updated**
   - Check file permissions on the configuration file
   - Verify that the configuration directory is writable
   - Review logs for any error messages during configuration updates

3. **Blueprint Discovery Always Runs on Startup**
   - Blueprint discovery now automatically runs on every startup
   - No need to use `--force-blueprint-discovery` flag (deprecated but still supported)
   - Deleted blueprints are detected immediately when the application is restarted

4. **Check Configuration Backups**
   - A single configuration backup is maintained in the same directory as the config file
   - Backup file is named `config.yaml.backup` (no timestamp - single file maintained)

### Logs Related to Blueprint Discovery

Look for these log messages to understand blueprint discovery status:

```
INFO - Performing blueprint discovery on startup
INFO - Starting blueprint discovery...
INFO - Discovered 3 blueprints
INFO - New blueprints to add to config: blueprint-id-1, blueprint-id-2
INFO - Blueprints to remove from config: deleted-blueprint-id
INFO - Configuration file updated with 3 blueprints
INFO - Blueprint discovery completed. Found 3 blueprints
```

### Immediate Detection of Changes

The application now provides immediate detection of blueprint changes:

- **Deleted Blueprints**: When you delete a blueprint from Apstra and restart the application, it will immediately detect the deletion and update the configuration
- **New Blueprints**: New blueprints are detected on startup and during the 5-minute refresh cycles
- **No Manual Intervention**: No need to manually update configuration files or use special flags

Example workflow for blueprint deletion:
1. Delete a blueprint in Apstra
2. Restart the application: `python3 app/main.py`
3. Application detects the deletion immediately
4. Configuration file is automatically updated
5. Application stops monitoring the deleted blueprint

## Running as a Service

### Permissions and Setup

The application no longer requires sudo privileges. Instead, it should be run as a service with appropriate permissions:

#### Run as a dedicated service user

1. Create a service user:
   ```bash
   sudo useradd -r -s /bin/false apstra-backup
   ```

2. Install Python packages for the service user:
   ```bash
   # Switch to service user and install packages
   sudo -u apstra-backup pip3 install --user -r requirements.txt
   ```
   
   **Note**: The service user must have access to all required Python packages. You can alternatively install packages system-wide with `sudo pip3 install -r requirements.txt`.

3. Grant the service user permission to execute the backup script:
   ```bash
   # Add to sudoers file for specific command only
   sudo visudo
   # Add this line:
   apstra-backup ALL=(ALL) NOPASSWD: /usr/sbin/aos_backup
   ```

4. Set proper ownership for the application directory:
   ```bash
   sudo chown -R apstra-backup:apstra-backup /path/to/apstra_commit_backup
   ```

5. Create a systemd service file `/etc/systemd/system/apstra-backup.service`:
   ```ini
   [Unit]
   Description=Apstra Blueprint Backup Service
   After=network.target

   [Service]
   Type=simple
   User=apstra-backup
   Group=apstra-backup
   WorkingDirectory=/path/to/apstra_commit_backup
   ExecStart=/usr/bin/python3 /path/to/apstra_commit_backup/app/main.py
   Restart=always
   RestartSec=10
   EnvironmentFile=/path/to/apstra_commit_backup/.env

   [Install]
   WantedBy=multi-user.target
   ```

6. Enable and start the service:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable apstra-backup.service
   sudo systemctl start apstra-backup.service
   ```

### Service Management

Check service status:
```bash
sudo systemctl status apstra-backup.service
```

View service logs:
```bash
sudo journalctl -u apstra-backup.service -f
```

Stop the service:
```bash
sudo systemctl stop apstra-backup.service
```

### Security Considerations

- The application no longer runs with full sudo privileges
- Only the specific backup script execution requires elevated permissions
- Service user has minimal system access
- Environment variables are loaded from a secure .env file
- Configuration backups are maintained with proper file permissions

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
