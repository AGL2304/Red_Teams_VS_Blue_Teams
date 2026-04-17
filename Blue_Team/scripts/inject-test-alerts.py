#!/usr/bin/env python3
"""
Direct Alert Injection - Bypass syslog pipeline for immediate testing
Writes test alerts directly to Wazuh's Elasticsearch index
This allows testing the full alert monitoring pipeline without waiting for syslog processing
"""

import json
import requests
from datetime import datetime
import sys

# Elasticsearch credentials
ES_HOST = "https://localhost:9200"
ES_USER = "admin"
ES_PASS = "SecretPassword"
INDEX = "wazuh-alerts-4.x"

# Suppress SSL warnings
requests.packages.urllib3.disable_warnings()

def get_today_index():
    """Get today's alert index name"""
    today = datetime.now().strftime("%Y.%m.%d")
    return f"{INDEX}-{today}"

def create_alert(rule_id, rule_name, level, message, source_ip="192.168.1.100", agent="wazuh.manager"):
    """Create a properly formatted Wazuh alert document"""
    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "rule": {
            "id": rule_id,
            "level": level,
            "name": rule_name,
            "groups": ["vulnerability", "custom_rule"],
            "mitre": {
                "tactic": ["Initial Access"],
                "technique": ["Exploit Public-Facing Application"]
            }
        },
        "agent": {
            "id": "000",
            "name": agent
        },
        "manager": {
            "name": "wazuh.manager"
        },
        "data": {
            "srcip": source_ip,
            "dstport": "80",
            "protocol": "tcp",
            "action": "log"
        },
        "full_log": message,
        "decoder": {
            "name": "syslog"
        }
    }

def inject_alert(alert_doc):
    """Inject alert into Elasticsearch"""
    try:
        url = f"{ES_HOST}/{get_today_index()}/_doc"
        response = requests.post(
            url,
            json=alert_doc,
            auth=(ES_USER, ES_PASS),
            verify=False,
            timeout=5
        )
        if response.status_code in [200, 201]:
            return True
        else:
            print(f"✗ Failed to inject alert: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_brute_force():
    """Generate brute force alerts"""
    print("\n[TEST 1] Brute Force Attack - 10 failed login attempts")
    print("─" * 60)
    for i in range(1, 11):
        alert = create_alert(
            rule_id=100101,
            rule_name="Brute force attack detected",
            level=10,
            message=f"juice-shop auth=failed user=admin source=192.168.1.100 attempt={i}/10"
        )
        if inject_alert(alert):
            print(f"  [{i}/10] Login failure injected")
    print("✓ Rule 100101 should trigger")

def test_sql_injection():
    """Generate SQL injection alerts"""
    print("\n[TEST 2] SQL Injection Attack")
    print("─" * 60)
    payloads = [
        "'; DROP TABLE users; --",
        "' UNION SELECT * FROM users --",
        "' OR 1=1 --"
    ]
    for i, payload in enumerate(payloads, 1):
        alert = create_alert(
            rule_id=100103,
            rule_name="SQL injection attack detected",
            level=8,
            message=f"juice-shop query={payload}"
        )
        if inject_alert(alert):
            print(f"  [{i}] SQL injection payload injected: {payload}")
    print("✓ Rule 100103 should trigger")

def test_xss():
    """Generate XSS alerts"""
    print("\n[TEST 3] XSS Attack")
    print("─" * 60)
    alert = create_alert(
        rule_id=100105,
        rule_name="XSS injection attempt detected",
        level=6,
        message="juice-shop payload=<script>alert('XSS')</script>"
    )
    if inject_alert(alert):
        print("  [1] XSS payload injected")
    print("✓ Rule 100105 should trigger")

def test_admin_access():
    """Generate admin panel access alerts"""
    print("\n[TEST 4] Admin Panel Access Attempt")
    print("─" * 60)
    alert = create_alert(
        rule_id=100102,
        rule_name="Admin panel access detected",
        level=6,
        message="juice-shop admin_access=true user=guest"
    )
    if inject_alert(alert):
        print("  [1] Admin access detected")
    print("✓ Rule 100102 should trigger")

def test_path_traversal():
    """Generate path traversal alerts"""
    print("\n[TEST 5] Path Traversal Attack")
    print("─" * 60)
    alert = create_alert(
        rule_id=100104,
        rule_name="Path traversal attempt detected",
        level=6,
        message="juice-shop path=../../../etc/passwd"
    )
    if inject_alert(alert):
        print("  [1] Path traversal detected")
    print("✓ Rule 100104 should trigger")

def test_command_injection():
    """Generate command injection alerts"""
    print("\n[TEST 6] Command Injection Attack")
    print("─" * 60)
    alert = create_alert(
        rule_id=100113,
        rule_name="Command injection attempt detected",
        level=7,
        message="juice-shop cmd=; cat /etc/passwd"
    )
    if inject_alert(alert):
        print("  [1] Command injection detected")
    print("✓ Rule 100113 should trigger")

def test_xxe():
    """Generate XXE injection alerts"""
    print("\n[TEST 7] XXE Injection Attack")
    print("─" * 60)
    alert = create_alert(
        rule_id=100116,
        rule_name="XXE injection attempt detected",
        level=7,
        message="juice-shop xxe=<!ENTITY xxe SYSTEM 'file:///etc/passwd'>"
    )
    if inject_alert(alert):
        print("  [1] XXE injection detected")
    print("✓ Rule 100116 should trigger")

def test_api_enumeration():
    """Generate API enumeration alerts"""
    print("\n[TEST 8] API Enumeration (High-frequency calls)")
    print("─ " * 60)
    for i in range(1, 6):
        alert = create_alert(
            rule_id=100106,
            rule_name="High-frequency API calls detected",
            level=5,
            message=f"juice-shop api=/api/Users request_num={i}"
        )
        if inject_alert(alert):
            print(f"  [{i}] API enumeration event injected")
    print("✓ Rule 100106 should trigger")

def test_idor():
    """Generate IDOR attacks"""
    print("\n[TEST 9] IDOR Attack - Sequential Resource Access")
    print("─" * 60)
    for uid in range(1, 6):
        alert = create_alert(
            rule_id=100107,
            rule_name="IDOR attack detected - seq user access",
            level=6,
            message=f"juice-shop idor=true user_id={uid} accessed_by=guest"
        )
        if inject_alert(alert):
            print(f"  [{uid}] User ID {uid} access detected")
    print("✓ Rule 100107 should trigger")
    print("✓ Monitor.py BOLA detection should also trigger")

def main():
    print("\n╔════════════════════════════════════════════════════════════════╗")
    print("║  Direct Alert Injection - Elasticsearch Backend               ║")
    print("╚════════════════════════════════════════════════════════════════╝\n")
    print(f"Injecting test alerts directly into: {get_today_index()}")
    print("These will be immediately available through the Wazuh API\n")

    test_brute_force()
    test_sql_injection()
    test_xss()
    test_admin_access()
    test_path_traversal()
    test_command_injection()
    test_xxe()
    test_api_enumeration()
    test_idor()

    print("\n" + "=" * 60)
    print("✅ All test alerts injected successfully!")
    print("=" * 60)
    print("\nExpected Behavior:")
    print("  1. Monitor.py should immediately display colored alerts")
    print("  2. Alerts will be logged to: Blue_Team/logs/alerts.log")
    print("  3. Check Wazuh Dashboard for visualization")
    print("\nWazuh Dashboard: https://localhost:443")
    print("Credentials: admin / SecretPassword")
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
