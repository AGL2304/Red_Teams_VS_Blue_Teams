# Blue Team Wazuh SIEM/XDR Setup - Complete Guide

## ✅ Deployment Status

All Wazuh components are successfully deployed and operational:

### Running Services
- **Wazuh Manager**: `single-node-wazuh.manager-1` (Running - Healthy)
- **Wazuh Indexer**: `single-node-wazuh.indexer-1` (Running - Healthy)  
- **Wazuh Dashboard**: `single-node-wazuh.dashboard-1` (Running)
- **Juice Shop**: `juice-shop` (Running on port 3000)

---

## 🔌 Connection Details

### Wazuh Dashboard
- **URL**: https://localhost:443 or https://localhost/ (if using standard HTTPS)
- **Username**: `admin`
- **Password**: `SecretPassword`
- **Certificate**: Self-signed (ignore browser warning)

### Wazuh REST API
- **URL**: `https://localhost:55000`
- **Username**: `wazuh-wui`
- **Password**: `MyS3cr37P450r.*-`

### Wazuh Manager
- **Address**: `127.0.0.1`
- **Agent Port**: `1514/TCP` and `1515/TCP`
- **Syslog Port**: `514/UDP`

### Juice Shop Vulnerable Application
- **URL**: `http://localhost:3000`

---

## 📊 Configured Detection Rules

Custom Wazuh rules have been created to detect:

### Rule Set (Rule IDs 100101-100120)

| Rule ID | Rule Name | Severity | Pattern |
|---------|-----------|----------|---------|
| 100101  | Brute Force Attack | Level 7 | Multiple failed login attempts |
| 100102  | Admin Panel Access | Level 6 | `/admin` or `/rest/admin/*` endpoints |
| 100103  | SQL Injection | Level 8 | SQL keywords: `UNION`, `DROP`, `INSERT`, etc. |
| 100104  | Path Traversal | Level 6 | `../` or URL encoded variants |
| 100105  | XSS Injection | Level 6 | Script tags and event handlers |
| 100106  | API Enumeration | Level 5 | High-frequency `/api/*` requests |
| 100107  | IDOR (ID enumeration) | Level 6 | Rapid sequential resource ID access |
| 100108  | Weak Passwords | Level 5 | Common password attempts |
| 100109  | File Upload Exploit | Level 6 | Suspicious file extension attempts |
| 100110  | Debug Info Disclosure | Level 5 | Access to debug/info endpoints |
| 100111  | Blind SQL Injection | Level 7 | `SLEEP()` or `BENCHMARK()` functions |
| 100112  | Malicious JSON Payload | Level 6 | Exec/system commands in JSON |
| 100113  | Command Injection | Level 7 | Shell metacharacters and commands |
| 100114  | Session Fixation | Level 5 | Session cookie manipulation |
| 100115  | 2FA/OTP Bypass | Level 6 | Rapid verification attempts |
| 100116  | XXE Injection | Level 7 | XML External Entity patterns |
| 100117  | CSRF Bypass | Level 4 | Missing/invalid CSRF tokens |
| 100118  | HTTP Smuggling | Level 6 | Conflicting HTTP headers |
| 100119  | Prototype Pollution | Level 6 | `__proto__` or `constructor` keywords |
| 100120  | Directory Listing | Level 4 | Enabled directory enumerate |
| 100201  | Critical Attack | Level 9 | Aggregated high-severity attacks |

**Rules Location**: `/tmp/wazuh-docker/single-node/config/wazuh_cluster/etc/rules/local_rules.xml`

---

## 🛡️ Active Response Configuration

**Brute Force Response**:
- **Trigger**: Rule 100101 (10 failed attempts within 120 seconds)
- **Action**: Block source IP using `iptables` for 300 seconds (5 minutes)
- **Log**: `/var/ossec/logs/active-responses.log`

---

## 📝 Log Collection

### Method 1: Syslog Integration
Send Docker/application logs to Wazuh syslog port (514/UDP):
```bash
# Example
echo "Your log message" | nc -u 127.0.0.1 514
```

### Method 2: Docker Log Collector Script
```bash
# Start the Docker log collection service
bash ~/Desktop/M1/U2/M1PPAW/Red_Teams_VS_Blue_Teams/Blue_Team/scripts/docker-log-collector.sh
```

### Method 3: Direct Docker Integration
The Wazuh manager can directly read Docker container logs from:
- `/var/lib/docker/containers/*/*-json.log`

---

## 🚀 Blue Team Monitoring Script

### Starting the Monitor
```bash
# Basic usage
python3 ~/Desktop/M1/U2/M1PPAW/Red_Teams_VS_Blue_Teams/Blue_Team/scripts/monitor.py

# With custom parameters
python3 monitor.py --host 127.0.0.1 --port 55000 \
  --username wazuh-wui --password "MyS3cr37P450r.*-" \
  --log-file ~/Desktop/M1/U2/M1PPAW/Red_Teams_VS_Blue_Teams/Blue_Team/logs/alerts.log \
  --poll-interval 10
```

### Features
- ✅ Real-time alert monitoring from Wazuh API
- ✅ Color-coded severity levels in terminal display
- ✅ Automatic BOLA (Broken Object Level Authorization) detection
- ✅ JSON-formatted alert logging to file
- ✅ 30-second BOLA detection window with 3+ unique ID threshold


### Alert Log Format
```json
{
  "timestamp": "2026-04-17T10:30:00Z",
  "rule_id": "100103",
  "severity": "HIGH",
  "description": "SQL Injection attack pattern detected",
  "source_ip": "192.168.1.100",
  "agent": "docker-host",
  "full_alert": {...}
}
```

---

## 🧪 Testing End-to-End

### 1. Generate Admin Page Access Alert
```bash
curl http://localhost:3000/rest/admin/application-configuration
```
*Expected*: Rule 100102 triggered

### 2. Generate SQL Injection Alert
```bash
curl "http://localhost:3000/rest/products/search?q=' OR '1'='1"
```
*Expected*: Rule 100103 triggered

### 3. Generate API Enumeration Alert
```bash
for i in $(seq 1 30); do 
  curl -s "http://localhost:3000/api/Users/?q='" -o /dev/null
done
```
*Expected*: Rule 100106 triggered (API enumeration)

### 4. Generate IDOR Detection Alert
```bash
for i in $(seq 1 5); do
  curl -s "http://localhost:3000/api/Users/$i" -o /dev/null
done
```
*Expected*: Rule 100107 triggered + BOLA detection in monitor.py

### 5. Generate Command Injection Alert
```bash
curl "http://localhost:3000/api/Products?search=;%20cat%20/etc/passwd"
```
*Expected*: Rule 100113 triggered

---

## 📈 Wazuh Dashboard Configuration

### Access Dashboard
1. Open `https://localhost:443` (or `https://localhost`)
2. Login with credentials:
   - Username: `admin`
   - Password: `SecretPassword`

### Create Custom Dashboard: "Red Team Detection Dashboard"

#### Panel 1: Security Events Over Time
- **Visualization Type**: Line Chart
- **X-Axis**: Timestamp
- **Y-Axis**: Count of events
- **Filter**: `rule.level >= 6`

#### Panel 2: Top Source IPs Triggering Alerts  
- **Visualization Type**: Horizontal Bar Chart
- **Metric**: Count
- **Bucket**: `agent.ip_address`
- **Limit**: Top 10

#### Panel 3: Alert Severity Distribution
- **Visualization Type**: Pie Chart
- **Bucket**: `rule.level`
- **Size**: Count

#### Panel 4: Events Per Container/Application
- **Visualization Type**: Bar Chart
- **X-Axis**: Container name
- **Y-Axis**: Count
- **Filter**: Docker logs

#### Panel 5: Latest Alerts Table
- **Columns**: Timestamp, Rule ID, Severity, Description, Source IP
- **Sort**: Timestamp descending
- **Row Limit**: 20

---

## 📂 File Structure

```
~/Desktop/M1/U2/M1PPAW/Red_Teams_VS_Blue_Teams/
├── Blue_Team/
│   ├── wazuh-rules/
│   │   └── local_rules.xml                    # Custom detection rules
│   ├── wazuh-config/
│   │   ├── rules/                            # Additional rule definitions
│   │   ├── certs/                            # SSL/TLS certificates
│   │   └── config/                           # Wazuh configuration files
│   ├── scripts/
│   │   ├── monitor.py                        # Blue Team alert monitor
│   │   ├── docker-log-collector.py          # Docker log collector (Python)
│   │   └── docker-log-collector.sh          # Docker log collector (Bash)
│   ├── logs/
│   │   ├── alerts.log                        # Monitor alert output
│   │   └── active_response.log              # Active response events
│   └── docker-compose-official.yml           # Original Wazuh config
│
├── juice-shop/                                # OWASP Juice Shop
├── wazuh-docker/single-node/                 # Wazuh deployment
└── ...
```

---

## 🔧 Troubleshooting

### Wazuh Dashboard Not Accessible
```bash
# Check if dashboard container is running
docker ps | grep wazuh.dashboard

# View logs
docker logs single-node-wazuh.dashboard-1 | tail -20

# Verify port binding
netstat -tlnp | grep 443
```

### Logs Not Appearing in Wazuh
1. Verify syslog port is listening: `netstat -uln | grep 514`
2. Check manager logs: `docker logs single-node-wazuh.manager-1`
3. Verify rules are loaded: Check `/tmp/wazuh-docker/single-node/config/wazuh_cluster/etc/rules/`

### Monitor Script Connection Issues
```bash
# Test API connectivity
curl -k -u "wazuh-wui:MyS3cr37P450r.*-" \
  https://localhost:55000/security/user/authenticate

# Check manager API port
netstat -tlnp | grep 55000
```

---

## 📋 Key Credentials Reference

| Service | Default User | Password |
|---------|--------------|----------|
| Wazuh Dashboard | admin | SecretPassword |
| Wazuh API | wazuh-wui | MyS3cr37P450r.*- |
| Wazuh Indexer | admin | admin |
| Wazuh Manager Agent Communication | N/A | Encrypted |

---

## 🎯 Next Steps for Red Team Testing

1. **Run Attack Simulations**: Execute the test commands above and monitor alerts
2. **Review Detected Patterns**: Check the monitor.py output and alerts.log
3. **Validate Active Response**: Verify IP blocking via `iptables` after brute force attempts
4. **Test Dashboard Visualizations**: Create custom searches and dashboards
5. **Generate Reports**: Export alerts from Wazuh dashboard for documentation

---

## 📚 References

- **Wazuh Documentation**: https://documentation.wazuh.com/
- **MITRE ATT&CK Framework**: https://attack.mitre.org/
- **OWASP Top 10**: https://owasp.org/www-project-top-ten/
- **CIS Benchmarks**: https://www.cisecurity.org/

---

Generated: 2026-04-17
Blue Team SIEM/XDR Configuration Complete ✅
