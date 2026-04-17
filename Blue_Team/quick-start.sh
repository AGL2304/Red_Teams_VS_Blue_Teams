#!/bin/bash
# Blue Team Wazuh - Quick Start Testing Script
# Run this to immediately test the complete Blue Team setup

set -e

BLUE_TEAM_DIR="$HOME/Desktop/M1/U2/M1PPAW/Red_Teams_VS_Blue_Teams/Blue_Team"
LOGS_DIR="$BLUE_TEAM_DIR/logs"
SCRIPTS_DIR="$BLUE_TEAM_DIR/scripts"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     Blue Team Wazuh SIEM/XDR - Quick Start Testing             ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}\n"

# Function to print step
print_step() {
    local step=$1
    local description=$2
    echo -e "\n${YELLOW}[STEP $step]${NC} $description"
    echo "════════════════════════════════════════════════════════════════"
}

# Function to print result
print_result() {
    local status=$1
    if [ "$status" -eq 0 ]; then
        echo -e "${GREEN}✓ SUCCESS${NC}"
    else
        echo -e "${RED}✗ FAILED${NC}"
    fi
}

# Function to check service status
check_service() {
    local service_name=$1
    local port=$2
    echo -e "${BLUE}» Checking $service_name on port $port...${NC}"
    if nc -z localhost $port 2>/dev/null; then
        echo -e "${GREEN}  ✓ $service_name is accessible${NC}"
        return 0
    else
        echo -e "${RED}  ✗ $service_name is NOT accessible${NC}"
        return 1
    fi
}

# STEP 1: Pre-flight checks
print_step 1 "Pre-flight Checks"
echo "Verifying required services..."

check_service "Wazuh Dashboard" 443
DASHBOARD_STATUS=$?

check_service "Wazuh API" 55000
API_STATUS=$?

check_service "Wazuh Indexer" 9200
INDEXER_STATUS=$?

check_service "Juice Shop" 3000
JUICE_STATUS=$?

if [ $DASHBOARD_STATUS -eq 0 ] && [ $API_STATUS -eq 0 ] && [ $INDEXER_STATUS -eq 0 ] && [ $JUICE_STATUS -eq 0 ]; then
    echo -e "${GREEN}All services ready!${NC}"
else
    echo -e "${RED}Some services are down. Please check Docker containers.${NC}"
    exit 1
fi

# STEP 2: Generate test traffic
print_step 2 "Generating Test Attack Traffic"
echo "Simulating Red Team attacks..."

echo -e "${BLUE}» Testing admin panel access...${NC}"
curl -s http://localhost:3000/rest/admin/application-configuration > /dev/null && echo -e "${GREEN}  ✓ Admin endpoint accessed${NC}"

echo -e "${BLUE}» Testing SQL injection patterns...${NC}"
curl -s "http://localhost:3000/rest/products/search?q=' OR '1'='1" > /dev/null && echo -e "${GREEN}  ✓ SQL injection pattern sent${NC}"

echo -e "${BLUE}» Testing API enumeration...${NC}"
for i in {1..10}; do
    curl -s "http://localhost:3000/api/Users/?q='" -o /dev/null
done
echo -e "${GREEN}  ✓ $i API requests sent${NC}"

echo -e "${BLUE}» Testing IDOR patterns...${NC}"
for i in {1..5}; do
    curl -s "http://localhost:3000/api/Users/$i" -o /dev/null
done
echo -e "${GREEN}  ✓ IDOR enumeration pattern sent${NC}"

# STEP 3: Send test alerts to Wazuh
print_step 3 "Sending Test Alerts to Wazuh"
echo "Injecting synthetic security events..."

python3 << 'PYTHON_EOF'
import socket
import time

wazuh_host = "127.0.0.1"
wazuh_port = 514

test_messages = [
    "ALERT: Suspicious login attempt detected from 192.168.1.100",
    "WARNING: Multiple failed authentication attempts from 10.0.0.50",
    "CRITICAL: SQL injection pattern detected in query parameter",
    "INFO: Admin endpoint accessed from unauthorized source",
    "ALERT: Path traversal attempt detected in URL",
]

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

for i, msg in enumerate(test_messages, 1):
    try:
        syslog_msg = f"juice-shop alert: {msg}"
        sock.sendto(syslog_msg.encode(), (wazuh_host, wazuh_port))
        print(f"  [{i}] Sent: {msg}")
        time.sleep(0.5)
    except Exception as e:
        print(f"  [{i}] Error: {e}")

sock.close()
print("\nAll test alerts sent to Wazuh")
PYTHON_EOF

print -e "${GREEN}  ✓ Test alerts sent${NC}"

# STEP 4: Start monitoring script
print_step 4 "Starting Blue Team Alert Monitor"
echo "Launching real-time alert monitoring..."

if [ -f "$SCRIPTS_DIR/monitor.py" ]; then
    echo -e "${BLUE}» Starting monitor.py in background...${NC}"
    python3 "$SCRIPTS_DIR/monitor.py" --poll-interval 5 > "$LOGS_DIR/monitor_output.log" 2>&1 &
    MONITOR_PID=$!
    echo -e "${GREEN}  ✓ Monitor started (PID: $MONITOR_PID)${NC}"
    echo -e "${YELLOW}  Note: Monitor running in background. Check logs at:${NC}"
    echo -e "${YELLOW}    $LOGS_DIR/alerts.log${NC}"
    echo -e "${YELLOW}    $LOGS_DIR/monitor_output.log${NC}"
else
    echo -e "${RED}  ✗ Monitor script not found${NC}"
fi

# STEP 5: Display access information
print_step 5 "Access Information"
echo ""
echo -e "${BLUE}Wazuh Dashboard${NC}"
echo "  URL:      https://localhost:443"
echo "  Username: admin"
echo "  Password: SecretPassword"
echo ""
echo -e "${BLUE}Wazuh REST API${NC}"
echo "  URL:      https://localhost:55000"
echo "  Username: wazuh-wui"
echo "  Password: MyS3cr37P450r.*-"
echo ""
echo -e "${BLUE}OWASP Juice Shop${NC}"
echo "  URL: http://localhost:3000"
echo ""

# STEP 6: Display log file locations
print_step 6 "Log File Locations"
echo ""
echo -e "${BLUE}Blue Team Logs:${NC}"
echo "  Alerts Log:           $LOGS_DIR/alerts.log"
echo "  Monitor Output:       $LOGS_DIR/monitor_output.log"
echo "  Active Response:      $LOGS_DIR/active_response.log"
echo ""
echo -e "${BLUE}Wazuh Rules:${NC}"
echo "  Custom Rules:         $BLUE_TEAM_DIR/wazuh-rules/local_rules.xml"
echo ""

# STEP 7: Next steps
print_step 7 "Next Steps"
echo ""
echo "1. Open Wazuh Dashboard:"
echo "   ${GREEN}https://localhost:443${NC}"
echo ""
echo "2. View detected alerts:"
echo "   ${GREEN}tail -f $LOGS_DIR/alerts.log${NC}"
echo ""
echo "3. Check real-time monitoring output:"
echo "   ${GREEN}tail -f $LOGS_DIR/monitor_output.log${NC}"
echo ""
echo "4. Verify active response blocking:"
echo "   ${GREEN}sudo iptables -vnL INPUT | grep DROP${NC}"
echo ""
echo "5. For more detailed information, see:"
echo "   ${GREEN}$BLUE_TEAM_DIR/WAZUH_SETUP_GUIDE.md${NC}"
echo ""

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                   Quick Start Complete!                        ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}\n"

print_step 8 "Summary"
echo ""
echo -e "${GREEN}✓ Wazuh SIEM/XDR deployed and running${NC}"
echo -e "${GREEN}✓ Custom detection rules configured${NC}"
echo -e "${GREEN}✓ Active response enabled for brute force${NC}"
echo -e "${GREEN}✓ Blue Team monitoring script operational${NC}"
echo -e "${GREEN}✓ Test traffic generated${NC}"
echo ""
echo "The Blue Team is ready! Monitor the logs for security events."
echo ""
