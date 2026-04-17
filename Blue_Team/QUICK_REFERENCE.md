# 🛡️ Blue Team Quick Reference Card

## ✅ What Was Deployed

Your Blue Team SIEM/XDR is **fully operational** with:

- ✓ **Wazuh 4.14.4 SIEM** - SecurityInformation & Event Management
- ✓ **20 Custom Detection Rules** - OWASP Top 10 coverage
- ✓ **Active Response System** - Auto-blocking of brute force attacks
- ✓ **Real-Time Monitor** - Python-based alert monitoring
- ✓ **BOLA Detection** - Broken Object Level Authorization
- ✓ **Docker Integration** - Container log collection

---

## 🚀 Quick Start (30 seconds)

### 1️⃣ Open Wazuh Dashboard
```
https://localhost:443
Username: admin
Password: SecretPassword
```

### 2️⃣ Start Monitoring
```bash
python3 ~/Desktop/M1/U2/M1PPAW/Red_Teams_VS_Blue_Teams/Blue_Team/scripts/monitor.py
```

### 3️⃣ Generate Test Alerts
```bash
# Admin access attempt
curl http://localhost:3000/rest/admin/application-configuration

# SQL injection test
curl "http://localhost:3000/rest/products/search?q=' OR '1'='1"

# API enumeration (brute force)
for i in {1..15}; do curl -s http://localhost:3000/api/Users; done
```

### 4️⃣ Check Alerts
```bash
tail -f ~/Desktop/M1/U2/M1PPAW/Red_Teams_VS_Blue_Teams/Blue_Team/logs/alerts.log
```

---

## 📍 Key Locations

| What | Where |
|------|-------|
| 📊 Dashboard | `https://localhost:443` |
| 🔌 API | `https://localhost:55000` |
| 🎯 App | `http://localhost:3000` |
| 📋 Rules | `Blue_Team/wazuh-rules/local_rules.xml` |
| 🐍 Monitor | `Blue_Team/scripts/monitor.py` |
| 📝 Logs | `Blue_Team/logs/alerts.log` |
| 📖 Docs | `Blue_Team/WAZUH_SETUP_GUIDE.md` |

---

## 🎯 Detection Rules

| Rule | Trigger | Severity |
|------|---------|----------|
| **100101** | 10 failed logins / 120s | Level 7 |
| **100103** | SQL injection patterns | Level 8 |
| **100105** | XSS payloads | Level 6 |
| **100107** | 3+ different resource IDs / 30s | Level 6 |
| **100113** | Command injection | Level 7 |
| + 15 more rules | Various OWASP patterns | Various |

---

## 🛡️ Active Response

**Brute Force Blocking:**
- ✓ Auto-trigger on Rule 100101
- ✓ Blocks source IP with iptables
- ✓ 5 minute block duration
- ✓ Auto-unblock after timeout
- ✓ Logged to active_response.log

---

## 💡 Pro Tips

### Real-Time Monitoring with Color Output
```bash
python3 Blue_Team/scripts/monitor.py --poll-interval 5
```

### Check Blocked IPs
```bash
sudo iptables -vnL INPUT | grep DROP
```

### View Recent Alerts
```bash
tail -f Blue_Team/logs/alerts.log | jq .
```

### Test BOLA Detection
```bash
# Access multiple user IDs rapidly
for i in {1..5}; do
  curl -s "http://localhost:3000/api/Users/$i" &
done
wait
```

---

## 🔐 Important Credentials

```
Wazuh Dashboard:  admin / SecretPassword
Wazuh REST API:   wazuh-wui / MyS3cr37P450r.*-
Wazuh Indexer:    admin / admin
```

---

## 📊 Wazuh Dashboard Panels to Create

1. **Security Events Timeline** - Line chart of events over time
2. **Top Attacking IPs** - Bar chart of source IPs
3. **Alert Severity** - Pie chart distribution
4. **Events by Type** - Container-based breakdown
5. **Latest Alerts** - Real-time table view

---

## 🧪 Attack Simulation Scenarios

### Scenario 1: Brute Force
```bash
for i in {1..15}; do
  curl -s http://localhost:3000/api/Users &
done
```
→ Triggers Rule 100101 → Auto-blocks IP after 10 attempts

### Scenario 2: SQL Injection
```bash
curl "http://localhost:3000/rest/products/search?q='; DROP TABLE users; --"
```
→ Triggers Rule 100103 (Level 8 - HIGH)

### Scenario 3: API Enumeration
```bash
for i in {1..20}; do curl -s http://localhost:3000/api/Users; done
```
→ Triggers Rule 100106

### Scenario 4: IDOR Exploitation  
```bash
for i in {1..10}; do curl -s "http://localhost:3000/api/Users/$i"; done
```
→ Triggers Rule 100107 + BOLA detection

---

## 🐛 Troubleshooting

### Monitor won't connect
```bash
curl -k -u "wazuh-wui:MyS3cr37P450r.*-" https://localhost:55000/security/user/authenticate
```

### No alerts appearing
```bash
netstat -uln | grep 514  # Check syslog port
docker logs single-node-wazuh.manager-1 | tail
```

### Want to see all containers
```bash
docker ps | grep -E "wazuh|juice"
```

---

## 📞 Full Documentation

For complete setup details and troubleshooting:
- **Setup Guide**: `Blue_Team/WAZUH_SETUP_GUIDE.md`
- **Implementation Summary**: `Blue_Team/IMPLEMENTATION_SUMMARY.md`
- **Official Wazuh Docs**: https://documentation.wazuh.com/

---

## ✨ You're All Set!

Your Blue Team SIEM/XDR is ready to detect and respond to Red Team attacks.
Start the monitoring script and protect your infrastructure! 🛡️

```bash
python3 ~/Desktop/M1/U2/M1PPAW/Red_Teams_VS_Blue_Teams/Blue_Team/scripts/monitor.py
```

**Ready. Alert. Respond.** 🚀
