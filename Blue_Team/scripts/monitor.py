#!/usr/bin/env python3
"""
Blue Team Wazuh Alert Monitor
Monitors Wazuh alerts in real-time, detects attack patterns, and logs security events.
Includes custom BOLA (Broken Object Level Authorization) detection.
"""

import requests
import json
import time
import sys
import os
from datetime import datetime, timedelta
from collections import defaultdict
from urllib3.exceptions import InsecureRequestWarning

# Suppress SSL warnings for self-signed certificates
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# ANSI Color codes for terminal output
class Colors:
    RESET = '\033[0m'
    CRITICAL = '\033[91m'    # Bright Red
    HIGH = '\033[38;5;208m'  # Orange
    MEDIUM = '\033[93m'      # Yellow
    LOW = '\033[92m'         # Green
    INFO = '\033[94m'        # Blue
    DEBUG = '\033[95m'       # Magenta
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class WazuhAlertMonitor:
    def __init__(self, wazuh_host="127.0.0.1", wazuh_port="55000", 
                 username="wazuh-wui", password="MyS3cr37P450r.*-",
                 log_file=None):
        self.wazuh_host = wazuh_host
        self.wazuh_port = wazuh_port
        self.base_url = f"https://{wazuh_host}:{wazuh_port}"
        self.username = username
        self.password = password
        self.session = None
        self.log_file = log_file or os.path.expanduser("~/Desktop/M1/U2/M1PPAW/Red_Teams_VS_Blue_Teams/Blue_Team/logs/alerts.log")
        self.last_alert_id = 0
        self.bola_window = defaultdict(list)  # Track BOLA pattern: {user: [resource_id, timestamp]}
        self.alert_cache = set()  # Cache to avoid duplicate processing
        
        # Create log directory if it doesn't exist
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        
    def authenticate(self):
        """Authenticate with Wazuh API"""
        try:
            print(f"{Colors.INFO}[*] Connecting to Wazuh API at {self.base_url}...{Colors.RESET}")
            response = requests.post(
                f"{self.base_url}/security/user/authenticate",
                auth=(self.username, self.password),
                verify=False,
                timeout=10
            )
            
            if response.status_code == 200:
                token = response.json().get('data', {}).get('token')
                if token:
                    self.session = requests.Session()
                    self.session.headers.update({'Authorization': f'Bearer {token}'})
                    print(f"{Colors.INFO}[+] Successfully authenticated to Wazuh API{Colors.RESET}")
                    return True
        except Exception as e:
            print(f"{Colors.CRITICAL}[!] Authentication failed: {e}{Colors.RESET}")
        
        return False
    
    def get_severity_color(self, level):
        """Return color based on alert severity level"""
        level = int(level) if isinstance(level, str) else level
        
        if level >= 12:
            return Colors.CRITICAL
        elif level >= 9:
            return Colors.HIGH
        elif level >= 6:
            return Colors.MEDIUM
        elif level >= 4:
            return Colors.LOW
        else:
            return Colors.INFO
    
    def get_severity_name(self, level):
        """Get severity name from level"""
        level = int(level) if isinstance(level, str) else level
        
        if level >= 12:
            return "CRITICAL"
        elif level >= 9:
            return "HIGH"
        elif level >= 6:
            return "MEDIUM"
        elif level >= 4:
            return "LOW"
        else:
            return "INFO"
    
    def fetch_alerts(self, limit=100):
        """Fetch recent alerts from Elasticsearch directly"""
        try:
            from datetime import datetime, timedelta
            
            # Query Elasticsearch directly for today's alerts
            today = datetime.now().strftime("%Y.%m.%d")
            index = f"wazuh-alerts-4.x-{today}"
            
            response = requests.get(
                f"https://localhost:9200/{index}/_search",
                auth=("admin", "SecretPassword"),
                json={
                    "size": limit,
                    "sort": [{"timestamp": {"order": "desc"}}],
                    "query": {"match_all": {}}
                },
                verify=False,
                timeout=10
            )
            
            if response.status_code == 200:
                hits = response.json().get('hits', {}).get('hits', [])
                # Convert Elasticsearch docs to alert format
                alerts = [hit['_source'] for hit in hits]
                return alerts
        except Exception as e:
            print(f"{Colors.INFO}[*] Note: Direct ES query failed, trying API: {e}{Colors.RESET}")
        
        # Fallback to API
        try:
            response = self.session.get(
                f"{self.base_url}/alerts",
                params={'limit': limit, 'sort': '-timestamp'},
                verify=False,
                timeout=10
            )
            if response.status_code == 200:
                return response.json().get('data', {}).get('affected_items', [])
        except:
            pass
        
        return []
    
    def detect_bola_pattern(self, alert):
        """
        Detect BOLA (Broken Object Level Authorization) patterns.
        BOLA = same user accessing 3+ different resource IDs in 30 seconds
        """
        try:
            # Extract relevant fields from alert  
            data = alert.get('data', {})
            
            # Look for patterns like /users/{id}, /products/{id}, etc.
            http_request = data.get('http', {}).get('request', {})
            url = http_request.get('url', '')
            
            source_ip = alert.get('agent', {}).get('ip_address', 'unknown')
            timestamp = alert.get('timestamp', datetime.now().isoformat())
            
            # Extract resource IDs from URL patterns
            import re
            resource_matches = re.findall(r'/(products|users|orders|reviews|comments)/(\d+)', url)
            
            if resource_matches:
                for resource_type, resource_id in resource_matches:
                    key = f"{source_ip}:{resource_type}"
                    current_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    
                    # Clean old entries outside the 30-second window
                    self.bola_window[key] = [
                        (rid, ts) for rid, ts in self.bola_window[key]
                        if (current_time - ts).total_seconds() <= 30
                    ]
                    
                    # Add current resource access
                    self.bola_window[key].append((resource_id, current_time))
                    
                    # Check if we have 3+ unique resource IDs in 30 seconds
                    unique_ids = set(rid for rid, _ in self.bola_window[key])
                    if len(unique_ids) >= 3:
                        return True, f"BOLA detected: {source_ip} accessed {len(unique_ids)} different {resource_type} IDs"
        except Exception as e:
            pass
        
        return False, ""
    
    def log_alert(self, alert, is_bola=False, bola_message=""):
        """Log alert to file"""
        try:
            timestamp = alert.get('timestamp', datetime.now().isoformat())
            rule_id = alert.get('rule', {}).get('id', 'N/A')
            rule_level = alert.get('rule', {}).get('level', 0)
            rule_desc = alert.get('rule', {}).get('description', 'Unknown')
            source_ip = alert.get('agent', {}).get('ip_address', 'Unknown')
            agent_name = alert.get('agent', {}).get('name', 'Unknown')
            
            log_entry = {
                'timestamp': timestamp,
                'rule_id': rule_id,
                'severity': self.get_severity_name(rule_level),
                'description': rule_desc,
                'source_ip': source_ip,
                'agent': agent_name,
                'full_alert': alert
            }
            
            if is_bola:
                log_entry['bola_alert'] = bola_message
            
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            print(f"{Colors.CRITICAL}[!] Error logging alert: {e}{Colors.RESET}")
    
    def print_alert(self, alert):
        """Print alert to terminal with color coding"""
        try:
            timestamp = alert.get('timestamp', 'N/A')
            rule_id = alert.get('rule', {}).get('id', 'N/A')
            rule_level = alert.get('rule', {}).get('level', 0)
            rule_desc = alert.get('rule', {}).get('description', 'Unknown')
            source_ip = alert.get('agent', {}).get('ip_address', 'Unknown')
            agent_name = alert.get('agent', {}).get('name', 'Unknown')
            
            # Check for BOLA pattern
            is_bola, bola_msg = self.detect_bola_pattern(alert)
            
            # Get color based on severity
            color = self.get_severity_color(rule_level)
            severity_name = self.get_severity_name(rule_level)
            
            # Print header
            print("\n" + "="*80)
            print(f"{color}{Colors.BOLD}[{timestamp}] {severity_name} ALERT (Rule: {rule_id}){Colors.RESET}")
            print("="*80)
            
            # Print details
            print(f"Description: {rule_desc}")
            print(f"Source IP:   {source_ip}")
            print(f"Agent:       {agent_name}")
            
            # Print BOLA detection if found
            if is_bola:
                print(f"{Colors.CRITICAL}{Colors.BOLD}⚠️  {bola_msg}{Colors.RESET}")
            
            # Log the alert
            self.log_alert(alert, is_bola, bola_msg)
            
        except Exception as e:
            print(f"{Colors.CRITICAL}[!] Error printing alert: {e}{Colors.RESET}")
    
    def run(self, poll_interval=10):
        """Main monitoring loop"""
        if not self.authenticate():
            return False
        
        print(f"{Colors.INFO}[*] Starting alert monitoring (poll interval: {poll_interval}s){Colors.RESET}")
        print(f"{Colors.INFO}[*] Logging alerts to: {self.log_file}{Colors.RESET}\n")
        
        try:
            while True:
                try:
                    alerts = self.fetch_alerts(limit=50)
                    
                    for alert in alerts:
                        alert_id = alert.get('id', '')
                        
                        # Skip if already processed
                        if alert_id in self.alert_cache:
                            continue
                        
                        # Add to cache and print
                        self.alert_cache.add(alert_id)
                        self.print_alert(alert)
                    
                    # Keep cache size reasonable
                    if len(self.alert_cache) > 1000:
                        self.alert_cache.clear()
                    
                    time.sleep(poll_interval)
                    
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"{Colors.CRITICAL}[!] Error in monitoring loop: {e}{Colors.RESET}")
                    time.sleep(poll_interval)
        
        except KeyboardInterrupt:
            pass
        
        print(f"\n{Colors.INFO}[*] Alert monitoring stopped{Colors.RESET}")
        return True

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Blue Team Wazuh Alert Monitor")
    parser.add_argument("--host", default="127.0.0.1", help="Wazuh manager host")
    parser.add_argument("--port", default="55000", help="Wazuh API port")
    parser.add_argument("--username", default="wazuh-wui", help="Wazuh API username")
    parser.add_argument("--password", default="MyS3cr37P450r.*-", help="Wazuh API password")
    parser.add_argument("--log-file", help="Alert log file path")
    parser.add_argument("--poll-interval", type=int, default=10, help="Poll interval in seconds")
    
    args = parser.parse_args()
    
    monitor = WazuhAlertMonitor(
        wazuh_host=args.host,
        wazuh_port=args.port,
        username=args.username,
        password=args.password,
        log_file=args.log_file
    )
    
    monitor.run(poll_interval=args.poll_interval)

if __name__ == "__main__":
    main()
