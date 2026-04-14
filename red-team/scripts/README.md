# Red Team Exploitation Toolkit - OWASP Juice Shop

## Overview

Complete Python-based Red Team exploitation toolkit for security testing and vulnerability assessment. These scripts target OWASP Juice Shop vulnerabilities including Broken Access Control, XSS, SQL Injection, and IDOR.

**Total Code Size:** 1200+ lines of Python  
**Test Coverage:** End-to-end exploitation automation  
**Reports Generated:** JSON-based findings with evidence collection

---

## Scripts Included

### 1. **01_enum_api.py** - API Enumeration & Discovery
**Purpose:** Discover and map all API endpoints

**Features:**
- Brute force endpoint discovery
- HTTP method testing (GET, POST, PUT, DELETE)
- Authentication requirement detection
- Response analysis and classification
- CSV/JSON export
- Rate limiting bypass attempts

**Usage:**
```bash
python3 01_enum_api.py -u http://127.0.0.1:3000 -d 0.1
python3 01_enum_api.py --url http://target.com --export both
```

**Output:**
- `api_enum_results_*.json` - Detailed endpoint mapping
- `api_enum_results_*.csv` - Spreadsheet format
- `enum_api.log` - Execution log

**Lines of Code:** ~280

---

### 2. **02_exploit_broken_access_control.py** - Broken Access Control Exploitation
**Purpose:** Exploit Broken Access Control (BAC) vulnerabilities

**Key Targets:**
- `/rest/admin/application-configuration` (primary target)
- Admin endpoints
- User resource endpoints

**Features:**
- Unauthenticated access testing
- Sensitive data extraction
- IDOR vulnerability detection
- Authentication bypass techniques (8+ variants)
- HTTP method override testing
- Configuration data parsing and IOC generation

**Usage:**
```bash
python3 02_exploit_broken_access_control.py
python3 02_exploit_broken_access_control.py -u http://target.com -t 15
```

**Output:**
- `admin_config_*.json` - Extracted admin configuration
- `bac_exploitation_report_*.json` - Detailed findings
- `exploit_bac.log` - Execution log

**Lines of Code:** ~380

---

### 3. **03_exploit_xss.py** - XSS Vulnerability Testing
**Purpose:** Detect and exploit XSS vulnerabilities

**Attack Types:**
- Reflected XSS
- Stored XSS
- DOM-based XSS
- Attribute-based XSS

**Payloads:** 30+ XSS payload variants including:
- Script tags
- Event handlers (onerror, onload, etc.)
- SVG-based payloads
- Encoded variants
- Case variations

**Parameters Tested:** search, q, query, keyword, name, message, comment, text, content, etc.

**Usage:**
```bash
python3 03_exploit_xss.py
python3 03_exploit_xss.py --reflected  # Only test reflected
python3 03_exploit_xss.py --stored     # Only test stored
```

**Output:**
- `xss_findings_*.json` - Vulnerability details
- Evidence of XSS payload reflection
- `exploit_xss.log` - Execution log

**Lines of Code:** ~340

---

### 4. **04_exploit_sql_injection.py** - SQL Injection Testing
**Purpose:** Detect and exploit SQL injection vulnerabilities

**Injection Types:**
- Basic SQL injection (error-based)
- Time-based blind SQLi
- UNION-based SQLi
- Boolean-based blind SQLi
- NoSQL injection
- Authentication bypass via SQLi

**Payload Sets:**
- 10 basic SQLi payloads
- 7 time-based payloads
- 5 error-based payloads
- 4 boolean-based payloads
- 5 NoSQL payloads

**Detection Methods:**
- SQL error message detection
- Response time analysis
- Response size anomaly detection
- Pattern matching

**Usage:**
```bash
python3 04_exploit_sql_injection.py
python3 04_exploit_sql_injection.py --basic
python3 04_exploit_sql_injection.py --time-based
python3 04_exploit_sql_injection.py --union
```

**Output:**
- `sqli_findings_*.json` - Detected SQLi vulnerabilities
- `exploit_sqli.log` - Execution log

**Lines of Code:** ~380

---

### 5. **05_exploit_idor.py** - Insecure Direct Object Reference Testing
**Purpose:** Detect and exploit IDOR vulnerabilities

**Attack Vectors:**
- Sequential ID enumeration
- Parameter tampering
- User ID enumeration
- Horizontal privilege escalation
- Authorization bypass

**Common Endpoints Tested:**
- `/rest/user/{id}` and variants
- `/rest/orders/{id}`
- `/rest/products/{id}`
- `/rest/reviews/{id}`
- `/rest/basket/{id}`
- Admin endpoints with ID manipulation

**ID Ranges:** 1-50 (configurable)

**Usage:**
```bash
python3 05_exploit_idor.py
python3 05_exploit_idor.py -u http://target.com -t 20
```

**Output:**
- `idor_findings_*.json` - IDOR vulnerabilities
- `idor_evidence_*.json` - Extracted data per ID
- `exploit_idor.log` - Execution log

**Lines of Code:** ~380

---

### 6. **master_exploit.py** - Master Orchestration
**Purpose:** Coordinate all exploitation tools

**Features:**
- Sequential execution of all 5 scripts
- Result aggregation and analysis
- IOC (Indicators of Compromise) generation
- Incident timeline reconstruction
- Comprehensive master report

**Usage:**
```bash
python3 master_exploit.py
python3 master_exploit.py -u http://target.com -t 15
```

**Output:**
- `master_exploitation_report_*.json` - Complete findings
- All individual tool outputs
- `master_exploit.log` - Master execution log

**Execution Time:** ~10-15 minutes (full test)

**Lines of Code:** ~280

---

## Installation & Requirements

### Python Version
- Python 3.7+

### Dependencies
```bash
pip install requests
```

### Optional (for enhanced output)
```bash
pip install colorama  # For colored output
```

---

## Quick Start

### 1. Basic Exploitation
```bash
cd scripts/
python3 01_enum_api.py -u http://127.0.0.1:3000
```

### 2. Target Specific Vulnerability
```bash
# Test Broken Access Control
python3 02_exploit_broken_access_control.py

# Test XSS only
python3 03_exploit_xss.py -u http://target.com

# Test SQL Injection
python3 04_exploit_sql_injection.py --basic

# Test IDOR
python3 05_exploit_idor.py
```

### 3. Full Exploitation Campaign
```bash
# Run all tests and generate master report
python3 master_exploit.py -u http://127.0.0.1:3000 -t 15
```

---

## Common Options

All tools accept:
```bash
-u, --url URL          Target URL (default: http://127.0.0.1:3000)
-t, --timeout SECONDS  Request timeout (default: 10)
-e, --export FORMAT    Export format: json, csv, both
```

---

## Output Files

### JSON Format
```json
{
  "timestamp": "2024-04-14T12:00:00",
  "target": "http://127.0.0.1:3000",
  "total_findings": 5,
  "vulnerabilities": [
    {
      "type": "broken_access_control",
      "endpoint": "/rest/admin/application-configuration",
      "status_code": 200,
      "requires_auth": false
    }
  ]
}
```

### Logs
- All scripts generate `.log` files with detailed execution information
- Logs show discovered vulnerabilities with timestamps
- Error messages and debugging information included

---

## Vulnerability Mapping

| Script | OWASP Top 10 | CVSS | Status |
|--------|--------------|------|--------|
| enum_api.py | A01:2021 - Information Disclosure | Medium | ✓ |
| broken_access_control.py | A01:2021 - Broken Access Control | Critical | ✓ |
| xss.py | A03:2021 - Injection | High | ✓ |
| sql_injection.py | A03:2021 - Injection | Critical | ✓ |
| idor.py | A01:2021 - Broken Access Control | High | ✓ |

---

## Example Findings

### Broken Access Control
```
Target: /rest/admin/application-configuration
Status: 200 OK
Auth Required: NO
Data Exposed:
- OAuth credentials
- Database connection strings
- Internal environment variables
- User security questions
```

### XSS
```
Endpoint: /search
Parameter: q
Payload: <img src=x onerror=alert("XSS")>
Result: REFLECTED
```

### SQL Injection
```
Endpoint: /products
Parameter: id  
Payload: ' OR '1'='1
Result: Basic SQLi + Time-based Blind SQLi
```

### IDOR
```
Endpoint: /rest/user/1 (accessible)
Endpoint: /rest/user/2 (accessible without auth)
Endpoint: /rest/user/3 (accessible without auth)
Pattern: Sequential ID enumeration vulnerability
```

---

## Report Aggregation

After running `master_exploit.py`:

```
EXPLOITATION SUMMARY
====================
Total Vulnerabilities: 47
API Endpoints Found: 23
Access Control Issues: 8
XSS Vulnerabilities: 12
SQL Injection Vulnerabilities: 3
IDOR Vulnerabilities: 9

IOCs Generated:
- Vulnerable endpoints: 23
- Vulnerable parameters: 15
- Attack patterns: 45
```

---

## Ethical Usage

⚠️ **IMPORTANT**

- Only use these tools on systems you own or have explicit written permission to test
- Unauthorized access to computer systems is illegal
- These tools are for educational and authorized security testing only
- Respect responsible disclosure practices

---

## Troubleshooting

### Connection Refused
```bash
# Verify target is running
curl http://127.0.0.1:3000

# Increase timeout if network is slow
python3 script.py -t 30
```

### No Findings
- Target may have security controls in place
- Try different payloads or parameters
- Check logs for error details

### Timeout Issues
- Reduce request volume with `-d` (delay) flag
- Increase timeout with `-t` option
- Check network connectivity

---

## Performance Tips

1. **Parallel Execution:** Run scripts in different terminals
2. **Delay Between Requests:** Use `-d 0.05` for faster enumeration (if allowed)
3. **Selective Testing:** Test specific vulnerability types only
4. **Result Caching:** Import results from previous runs

---

## Credits & References

- OWASP Testing Guide v4
- OWASP Top 10
- CWE/CVSS Standards
- PTES - Penetration Testing Execution Standard

---

## Support

For issues or questions:
1. Check execution logs (*.log files)
2. Review JSON report output
3. Verify target accessibility
4. Test with default parameters first

---

**Version:** 1.0  
**Last Updated:** April 2024  
**Framework:** Python 3.7+  
**License:** Educational Use

