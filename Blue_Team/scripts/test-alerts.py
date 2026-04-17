#!/usr/bin/env python3
"""
Blue Team Test Alert Generator
Sends simulated attack events to Wazuh that match custom detection rules
"""

import socket
import time
import sys

def send_syslog(message, host="127.0.0.1", port=514):
    """Send syslog message to Wazuh manager"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(message.encode(), (host, port))
        sock.close()
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_brute_force():
    """Generate brute force attack alerts (Rule 100101)"""
    print("\n[TEST 1] Brute Force Attack - 10 failed login attempts")
    print("─" * 60)
    for i in range(1, 11):
        msg = f"juice-shop auth=failed user=admin source=192.168.1.100 attempt={i}/10"
        if send_syslog(msg):
            print(f"  [{i}/10] Login failure sent")
            time.sleep(0.1)
    print("✓ Rule 100101 should trigger (10 attempts in short timeframe)")

def test_sql_injection():
    """Generate SQL injection alerts (Rule 100103)"""
    print("\n[TEST 2] SQL Injection Attack")
    print("─" * 60)
    payloads = [
        "query='; DROP TABLE users; --",
        "query=' UNION SELECT * FROM users --",
        "query=' OR 1=1 --",
    ]
    for i, payload in enumerate(payloads, 1):
        msg = f"juice-shop security=sql_injection {payload}"
        if send_syslog(msg):
            print(f"  [{i}] SQL injection payload: {payload}")
            time.sleep(0.2)
    print("✓ Rule 100103 should trigger (SQL pattern detected)")

def test_xss_injection():
    """Generate XSS injection alerts (Rule 100105)"""
    print("\n[TEST 3] XSS Attack")
    print("─" * 60)
    msg = "juice-shop security=xss_injection payload=<script>alert('XSS')</script>"
    if send_syslog(msg):
        print("  [1] XSS payload: <script>alert('XSS')</script>")
    print("✓ Rule 100105 should trigger (XSS pattern detected)")

def test_admin_access():
    """Generate admin panel access alerts (Rule 100102)"""
    print("\n[TEST 4] Admin Panel Access Attempt")
    print("─" * 60)
    msg = "juice-shop endpoint=/rest/admin/application-configuration source=10.0.0.50"
    if send_syslog(msg):
        print("  [1] Admin panel access attempt detected")
    print("✓ Rule 100102 should trigger (admin endpoint access)")

def test_path_traversal():
    """Generate path traversal alerts (Rule 100104)"""
    print("\n[TEST 5] Path Traversal Attack")
    print("─" * 60)
    msg = "juice-shop security=path_traversal request=../../../etc/passwd"
    if send_syslog(msg):
        print("  [1] Path traversal: ../../../etc/passwd")
    print("✓ Rule 100104 should trigger (path traversal detected)")

def test_command_injection():
    """Generate command injection alerts (Rule 100113)"""
    print("\n[TEST 6] Command Injection Attack")
    print("─" * 60)
    msg = "juice-shop security=command_injection payload=; cat /etc/passwd"
    if send_syslog(msg):
        print("  [1] Command injection: ; cat /etc/passwd")
    print("✓ Rule 100113 should trigger (command injection detected)")

def test_xxe_injection():
    """Generate XXE injection alerts (Rule 100116)"""
    print("\n[TEST 7] XXE Injection Attack")
    print("─" * 60)
    msg = 'juice-shop security=xxe_injection payload=<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>'
    if send_syslog(msg):
        print("  [1] XXE payload detected")
    print("✓ Rule 100116 should trigger (XXE injection detected)")

def test_api_enumeration():
    """Generate API enumeration alerts (Rule 100106)"""
    print("\n[TEST 8] API Enumeration (High-frequency calls)")
    print("─" * 60)
    for i in range(1, 6):
        msg = f"juice-shop api_call=/api/Users call_num={i}"
        if send_syslog(msg):
            print(f"  [{i}] API request to /api/Users")
            time.sleep(0.05)
    print("✓ Rule 100106 should trigger (20+ API calls detected)")

def test_idor():
    """Generate IDOR attack alerts (Rule 100107)"""
    print("\n[TEST 9] IDOR Attack - Sequential Resource Access")
    print("─" * 60)
    for user_id in [1, 2, 3, 4, 5]:
        msg = f"juice-shop endpoint=/api/Users/{user_id} source=192.168.1.200"
        if send_syslog(msg):
            print(f"  [{user_id}] Accessing user resource ID: {user_id}")
            time.sleep(0.1)
    print("✓ Rule 100107 should trigger (IDOR pattern detected)")
    print("✓ Monitor.py BOLA detection should also trigger")

def main():
    print("╔════════════════════════════════════════════════════════════════╗")
    print("║   Blue Team Alert Generator - Wazuh Detection Testing         ║")
    print("╚════════════════════════════════════════════════════════════════╝")
    print("\nGenerating test alerts to match all custom detection rules...")
    print("Make sure monitor.py is running to capture these alerts!\n")

    try:
        test_brute_force()
        test_sql_injection()
        test_xss_injection()
        test_admin_access()
        test_path_traversal()
        test_command_injection()
        test_xxe_injection()
        test_api_enumeration()
        test_idor()

        print("\n" + "=" * 60)
        print("✅ All test alerts sent successfully!")
        print("=" * 60)
        print("\nExpected Behavior:")
        print("  1. Monitor.py should display colored alerts")
        print("  2. Alerts will be logged to: Blue_Team/logs/alerts.log")
        print("  3. Check Wazuh Dashboard for visualization")
        print("\nWazuh Dashboard: https://localhost:443")
        print("Credentials: admin / SecretPassword")
        print("\n" + "=" * 60 + "\n")

    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
    except Exception as e:
        print(f"\nError during testing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
