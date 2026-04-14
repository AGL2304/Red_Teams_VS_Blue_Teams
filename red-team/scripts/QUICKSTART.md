# QUICK START GUIDE

## Red Team Exploitation Toolkit for OWASP Juice Shop

### ⚙️ Setup (1 minute)

```bash
# Install dependencies
pip install -r requirements.txt

# Make scripts executable
chmod +x *.py
```

---

### 🚀 Run All Exploits (15 minutes)

```bash
# Full exploitation campaign with master report
python3 master_exploit.py

# With custom target and timeout
python3 master_exploit.py -u http://target.com -t 20
```

**Output:** `master_exploitation_report_YYYYMMDD_HHMMSS.json`

---

### 🎯 Individual Modules

#### 1️⃣ Enumerate APIs
```bash
python3 01_enum_api.py
```
📊 Output: `api_enum_results_*.json`

#### 2️⃣ Exploit Broken Access Control
```bash
python3 02_exploit_broken_access_control.py
```
⚠️ Primary target: `/rest/admin/application-configuration`  
📊 Output: `bac_exploitation_report_*.json`

#### 3️⃣ Test XSS Vulnerabilities
```bash
python3 03_exploit_xss.py --reflected  # Reflected only
python3 03_exploit_xss.py --stored     # Stored only
python3 03_exploit_xss.py              # All types
```
📊 Output: `xss_findings_*.json`

#### 4️⃣ Test SQL Injection
```bash
python3 04_exploit_sql_injection.py --basic
python3 04_exploit_sql_injection.py --time-based
python3 04_exploit_sql_injection.py --union
```
📊 Output: `sqli_findings_*.json`

#### 5️⃣ Test IDOR Vulnerabilities
```bash
python3 05_exploit_idor.py
```
📊 Output: `idor_findings_*.json` + `idor_evidence_*.json`

---

### 📊 Example Outputs

**API Enumeration:**
```
[200] GET  /rest/products
[200] GET  /ftp
[500] GET  /rest/admin/users
[401] GET  /rest/user/profile
```

**Broken Access Control:**
```
✓ VULNERABILITY: /rest/admin/application-configuration accessible without auth!
✓ Data extracted: 2457 bytes
- Sensitive data found in response
- OAuth tokens exposed
```

**XSS:**
```
✓ REFLECTED XSS FOUND
  Endpoint: /search
  Parameter: q
  Payload: <img src=x onerror=alert("XSS")>
```

**SQL Injection:**
```
✓ SQL ERROR FOUND
  Payload: ' OR '1'='1
  Found error pattern: "SQL syntax error"
```

**IDOR:**
```
✓ IDOR FOUND - Different data retrieved
  Endpoint: /rest/user/2
  ID: 2
  Response: User profile data accessible
```

---

### 📈 Metrics

- **Total Lines of Code:** 1200+
- **Scripts Created:** 6
- **Payloads:** 80+
- **Endpoints Tested:** 40+
- **Import Statement:** `import requests` only
- **Documentation:** README.md + this guide

---

### 🔍 What Gets Tested

✅ API Endpoint Enumeration  
✅ Broken Access Control (BAC)  
✅ XSS (Reflected, Stored, DOM)  
✅ SQL Injection (Multiple types)  
✅ IDOR / Broken Authentication  
✅ Parameter Tampering  
✅ Authentication Bypass  
✅ Authorization Flaws  

---

### 📝 Expected Findings (OWASP Juice Shop)

From your current report, we'll target:

1. **Already Confirmed:**
   - ✅ Broken Access Control on `/rest/admin/application-configuration`
   - ✅ Exposed FTP files

2. **To Be Tested:**
   - 🎯 XSS via search/feedback endpoints
   - 🎯 SQL injection on product search
   - 🎯 IDOR on user/order endpoints
   - 🎯 Authentication bypass variants

---

### 🏃 Execution Timeline

**Phase 1: Enumeration (2 min)**
- Discover all endpoints
- Map authentication requirements

**Phase 2: Access Control (3 min)**
- Extract admin configuration
- Test IDOR vulnerabilities

**Phase 3: Web Exploitation (5 min)**
- Test XSS payloads
- Test SQL injection variants

**Phase 4: Reporting (5 min)**
- Aggregate findings
- Generate IOCs
- Create master report

**Total: ~15 minutes**

---

### 💾 Reports Generated

After `master_exploit.py`:

```
├── master_exploitation_report_YYYYMMDD_HHMMSS.json    [Master report]
├── api_enum_results_YYYYMMDD_HHMMSS.json              [API findings]
├── admin_config_YYYYMMDD_HHMMSS.json                  [Extracted config]
├── bac_exploitation_report_YYYYMMDD_HHMMSS.json        [BAC findings]
├── xss_findings_YYYYMMDD_HHMMSS.json                  [XSS findings]
├── sqli_findings_YYYYMMDD_HHMMSS.json                 [SQLi findings]
├── idor_findings_YYYYMMDD_HHMMSS.json                 [IDOR findings]
└── *.log                                               [Execution logs]
```

---

### 🎓 Learning Objectives Covered

✅ Red Team methodology (reconnaissance, exploitation, reporting)  
✅ OWASP Top 10 vulnerability testing  
✅ Python automation development  
✅ API security assessment  
✅ Web application penetration testing  
✅ Data exfiltration and evidence collection  
✅ Incident timeline reconstruction  

---

### ⚠️ Important Notes

1. **These tools are for authorized testing only**
2. Only use on systems you own or have permission to test
3. All tests are non-destructive (no data deletion)
4. Results are logged for audit purposes
5. Payloads are standard security testing variants

---

### 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| Connection failed | Check target URL and network |
| No findings | Try with `-d 0.05` for slower requests |
| Timeout errors | Increase with `-t 20` or `-t 30` |
| Import errors | Run `pip install -r requirements.txt` |
| Permission denied | Use `chmod +x *.py` |

---

### 📞 Next Steps

1. ✅ Review this guide
2. ✅ Run individual scripts to understand each
3. ✅ Run `master_exploit.py` for full assessment
4. ✅ Analyze findings in JSON reports
5. ✅ Use data for your project documentation

**Estimated total setup + execution: 20 minutes**

---

**Happy hunting! 🎯**

Generated: April 2024  
Version: 1.0
