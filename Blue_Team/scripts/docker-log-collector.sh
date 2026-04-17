#!/bin/bash
#
# Docker Log Collector using Docker CLI
# Sends Juice Shop logs to Wazuh via syslog
#

WAZUH_HOST="${1:-127.0.0.1}"
WAZUH_PORT="${2:-514}"
CONTAINER_NAME="${3:-juice-shop}"
LOG_FILE="/tmp/juice-shop-log-collector.log"

echo "[$(date)] Starting Docker log collector for $CONTAINER_NAME" >> $LOG_FILE

# Check if container exists
if ! docker ps --filter "name=$CONTAINER_NAME" --format "{{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
    echo "[$(date)] ERROR: Container $CONTAINER_NAME not found" >> $LOG_FILE
    exit 1
fi

echo "[$(date)] Collecting logs from container: $CONTAINER_NAME" >> $LOG_FILE
echo "[$(date)] Sending to Wazuh: $WAZUH_HOST:$WAZUH_PORT" >> $LOG_FILE

# Function to send UDP message
send_to_wazuh() {
    local message="$1"
    exec 3<>/dev/udp/$WAZUH_HOST/$WAZUH_PORT
    echo -n "$message" >&3
    exec 3>&-
}

# Stream logs from container and send to Wazuh via syslog
docker logs -f --timestamps=true $CONTAINER_NAME 2>&1 | while IFS= read -r line; do
    if [ -n "$line" ]; then
        # Format: YYYY-MM-DDTHH:MM:SS.NNNNNNZ <actual_log_message>
        # Extract just the log message part (after the timestamp)
        message=$(echo "$line" | sed 's/^[^ ]* //')
        
        # Send to Wazuh manager via UDP syslog
        send_to_wazuh "$message" 2>/dev/null
        
        # Also log locally
        echo "[$(date)] $message" >> $LOG_FILE
    fi
done

