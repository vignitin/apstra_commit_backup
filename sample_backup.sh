#!/bin/bash
# Sample backup script

# Set the backup directory
BACKUP_DIR="/tmp/apstra_backups"
mkdir -p "$BACKUP_DIR"

# Generate a timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Create a backup file
BACKUP_FILE="$BACKUP_DIR/apstra_backup_$TIMESTAMP.tar.gz"

# Create a sample backup (in a real script, this would be your actual backup command)
echo "Creating backup file..."
echo "This is a sample backup file" > "$BACKUP_DIR/sample_data.txt"
tar -czf "$BACKUP_FILE" -C "$BACKUP_DIR" sample_data.txt

# Output the backup file location for the script to parse
echo "BACKUP_FILE: $BACKUP_FILE"

# Return success
exit 0
