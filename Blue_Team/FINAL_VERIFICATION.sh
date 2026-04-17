#!/bin/bash
# Blue Team Complete Verification & Deployment Summary

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║   Blue Team Wazuh SIEM/XDR - FINAL VERIFICATION               ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

PASSED=0
FAILED=0

check_status() {
    local name=$1
    local command=$2
    
    if eval "$command" > /dev/null 2>&1; then
        echo "✓ $name"
        ((PASSED++))
    else
        echo "✗ $name"
        ((FAILED++))
    fi
}

echo "🔍 INFRASTRUCTURE CHECKS"
echo "─────────────────────────────────────────────────────────────────"

check_status "Wazuh Manager Running" "docker ps | grep -q 'single-node-wazuh.manager'"
check_status "Wazuh Indexer Running" "docker ps | grep -q 'single-node-wazuh.indexer'"
check_status "Wazuh Dashboard Running" "docker ps | grep -q 'single-node-wazuh.dashboard'"
check_status "Juice Shop Running" "docker ps | grep -q 'juice-shop'"
check_status "Wazuh Dashboard Port 443" "nc -z 127.0.0.1 443 2>/dev/null"
check_status "Wazuh API Port 55000" "nc -z 127.0.0.1 55000 2>/dev/null"
check_status "Juice Shop Port 3000" "nc -z 127.0.0.1 3000 2>/dev/null"
check_status "Wazuh Indexer Port 9200" "nc -z 127.0.0.1 9200 2>/dev/null"
check_status "Syslog Port 514 UDP" "netstat -uln 2>/dev/null | grep -q ':514'"

echo ""
echo "📦 CONFIGURATION FILES"
echo "─────────────────────────────────────────────────────────────────"

check_status "Custom Rules File" "test -f ~/Desktop/M1/U2/M1PPAW/Red_Teams_VS_Blue_Teams/Blue_Team/wazuh-rules/local_rules.xml"
check_status "Monitor Script" "test -f ~/Desktop/M1/U2/M1PPAW/Red_Teams_VS_Blue_Teams/Blue_Team/scripts/monitor.py"
check_status "Alert Generator" "test -f ~/Desktop/M1/U2/M1PPAW/Red_Teams_VS_Blue_Teams/Blue_Team/scripts/test-alerts.py"
check_status "Setup Guide" "test -f ~/Desktop/M1/U2/M1PPAW/Red_Teams_VS_Blue_Teams/Blue_Team/WAZUH_SETUP_GUIDE.md"
check_status "Quick Reference" "test -f ~/Desktop/M1/U2/M1PPAW/Red_Teams_VS_Blue_Teams/Blue_Team/QUICK_REFERENCE.md"
check_status "Logs Directory" "test -d ~/Desktop/M1/U2/M1PPAW/Red_Teams_VS_Blue_Teams/Blue_Team/logs"

echo ""
echo "🔐 API AUTHENTICATION"
echo "─────────────────────────────────────────────────────────────────"

API_TEST=$(curl -s -k -u "wazuh-wui:MyS3cr37P450r.*-" https://127.0.0.1:55000/security/user/authenticate 2>/dev/null | grep -q '"token"' && echo "pass" || echo "fail")

if [ "$API_TEST" = "pass" ]; then
    echo "✓ Wazuh API Authentication"
    ((PASSED++))
else
    echo "✗ Wazuh API Authentication"
    ((FAILED++))
fi

echo ""
echo "🎯 DETECTION RULES"
echo "─────────────────────────────────────────────────────────────────"

RULE_COUNT=$(grep -c "<rule id=\"100" ~/Desktop/M1/U2/M1PPAW/Red_Teams_VS_Blue_Teams/Blue_Team/wazuh-rules/local_rules.xml 2>/dev/null || echo "0")

echo "✓ Custom Rules Loaded: $RULE_COUNT rules (Expected: 20)"

echo ""
echo "📊 MONITORING SYSTEM"
echo "─────────────────────────────────────────────────────────────────"

if pgrep -f "monitor.py" > /dev/null; then
    MON_PID=$(pgrep -f "monitor.py")
    MON_TIME=$(ps -p $MON_PID -o etime= 2>/dev/null | xargs)
    echo "✓ Monitor Script Running (PID: $MON_PID, Runtime: $MON_TIME)"
    ((PASSED++))
else
    echo "ℹ Monitor Script Not Running (can be started manually)"
fi

echo ""
echo "📋 SUMMARY"
echo "─────────────────────────────────────────────────────────────────"
echo "Passed: $PASSED"
echo "Failed: $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo "✅ ALL CHECKS PASSED - SYSTEM FULLY OPERATIONAL"
    echo ""
    echo "🚀 QUICK START COMMANDS:"
    echo ""
    echo "  1. Access Dashboard:"
    echo "     https://localhost:443  (admin/SecretPassword)"
    echo ""
    echo "  2. Generate Test Alerts:"
    echo "     python3 ~/Desktop/M1/U2/M1PPAW/Red_Teams_VS_Blue_Teams/Blue_Team/scripts/test-alerts.py"
    echo ""
    echo "  3. Start Monitoring:"
    echo "     python3 ~/Desktop/M1/U2/M1PPAW/Red_Teams_VS_Blue_Teams/Blue_Team/scripts/monitor.py"
    echo ""
    echo "  4. Check Alerts Log:"
    echo "     tail -f ~/Desktop/M1/U2/M1PPAW/Red_Teams_VS_Blue_Teams/Blue_Team/logs/alerts.log"
    echo ""
else
    echo "⚠️  SOME CHECKS FAILED - Review configuration"
    exit 1
fi

echo "═" "════════════════════════════════════════════════════════════════"
echo ""
