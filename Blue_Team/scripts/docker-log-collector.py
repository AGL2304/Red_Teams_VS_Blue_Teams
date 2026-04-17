#!/usr/bin/env python3
"""
Docker log collector for Wazuh integration.
Collects logs from running Docker containers and sends them to Wazuh manager via syslog.
"""

import docker
import json
import socket
import time
import sys
from datetime import datetime

class DockerLogCollector:
    def __init__(self, wazuh_manager_host="127.0.0.1", wazuh_manager_port=514, container_name="juice-shop"):
        self.client = docker.from_env()
        self.wazuh_host = wazuh_manager_host
        self.wazuh_port = wazuh_manager_port
        self.container_name = container_name
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.last_timestamp = None
        
    def get_container(self):
        """Get the target container"""
        try:
            return self.client.containers.get(self.container_name)
        except docker.errors.NotFound:
            print(f"[ERROR] Container '{self.container_name}' not found")
            return None
    
    def send_to_wazuh(self, message):
        """Send syslog formatted message to Wazuh manager"""
        try:
            timestamp = datetime.now().strftime("%b %d %H:%M:%S")
            hostname = "docker-host"
            syslog_msg = f"{timestamp} {hostname} docker[{self.container_name}]: {message}"
            self.socket.sendto(syslog_msg.encode('utf-8'), (self.wazuh_host, self.wazuh_port))
        except Exception as e:
            print(f"[ERROR] Failed to send message to Wazuh: {e}")
    
    def collect_logs(self):
        """Collect and stream logs from container"""
        container = self.get_container()
        if not container:
            sys.exit(1)
        
        print(f"[INFO] Starting log collection from container '{self.container_name}'")
        print(f"[INFO] Sending logs to Wazuh: {self.wazuh_host}:{self.wazuh_port}")
        
        try:
            # Get logs stream
            logs = container.logs(stream=True, follow=True, timestamps=True)
            
            for line in logs:
                try:
                    log_line = line.decode('utf-8').strip()
                    if log_line:
                        # Remove timestamp if present (format: YYYY-MM-DDTHH:MM:SS.xxxxxx...)
                        if log_line.startswith(('2026-', '2025-', '2024-')):
                            log_line = log_line.split() [1:] if ' ' in log_line else log_line
                            log_line = ' '.join(log_line) if isinstance(log_line, list) else log_line
                        
                        self.send_to_wazuh(log_line)
                        sys.stdout.flush()
                except Exception as e:
                    print(f"[ERROR] Failed to process log line: {e}")
                    
        except KeyboardInterrupt:
            print("\n[INFO] Log collection stopped by user")
        except Exception as e:
            print(f"[ERROR] Error during log collection: {e}")
        finally:
            self.socket.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Docker log collector for Wazuh")
    parser.add_argument("--wazuh-host", default="127.0.0.1", help="Wazuh manager host")
    parser.add_argument("--wazuh-port", type=int, default=514, help="Wazuh manager syslog port")
    parser.add_argument("--container", default="juice-shop", help="Docker container name to monitor")
    
    args = parser.parse_args()
    
    collector = DockerLogCollector(
        wazuh_manager_host=args.wazuh_host,
        wazuh_port=args.wazuh_port,
        container_name=args.container
    )
    collector.collect_logs()
