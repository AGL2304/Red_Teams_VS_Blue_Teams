#!/usr/bin/env python3
"""
Red Team - Phase 1: Reconnaissance & Enumeration
Targets: Juice Shop (3000), VAmPI (5000), crAPI (8888)

Usage:
    python3 01_recon.py
    python3 01_recon.py --target juiceshop
    python3 01_recon.py --target vampi
    python3 01_recon.py --target crapi
"""

import requests
import json
import argparse
import sys
import time
from datetime import datetime

# ─── Colors ───────────────────────────────────────────────────────────────────
RED    = "\033[91m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
BLUE   = "\033[94m"
CYAN   = "\033[96m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

def banner():
    print(f"""{RED}
██████╗ ███████╗██████╗     ████████╗███████╗ █████╗ ███╗   ███╗
██╔══██╗██╔════╝██╔══██╗    ╚══██╔══╝██╔════╝██╔══██╗████╗ ████║
██████╔╝█████╗  ██║  ██║       ██║   █████╗  ███████║██╔████╔██║
██╔══██╗██╔══╝  ██║  ██║       ██║   ██╔══╝  ██╔══██║██║╚██╔╝██║
██║  ██║███████╗██████╔╝       ██║   ███████╗██║  ██║██║ ╚═╝ ██║
╚═╝  ╚═╝╚══════╝╚═════╝        ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝
{RESET}{YELLOW}Phase 1 — Recon & Enumeration | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RESET}
""")

# ─── Target Definitions ───────────────────────────────────────────────────────
TARGETS = {
    "juiceshop": {
        "name": "OWASP Juice Shop",
        "base_url": "http://localhost:3000",
        "type": "webapp",
        "endpoints": [
            "/",
            "/api/Products",
            "/api/Users",
            "/api/Feedbacks",
            "/api/BasketItems",
            "/api/Addresss",
            "/api/SecurityQuestions",
            "/api/Quantitys",
            "/api/Deliverys",
            "/api/Recycles",
            "/rest/user/login",
            "/rest/user/registration",
            "/rest/user/whoami",
            "/rest/basket/1",
            "/rest/products/search?q=",
            "/rest/admin/application-version",
            "/rest/admin/application-configuration",
            "/ftp/",
            "/b2b/v2/orders",
            "/.well-known/security.txt",
            "/metrics",
            "/socket.io/",
        ],
    },
    "vampi": {
        "name": "VAmPI",
        "base_url": "http://localhost:5000",
        "type": "rest_api",
        "endpoints": [
            "/",
            "/ui/",
            "/openapi.json",
            "/users/v1",
            "/users/v1/register",
            "/users/v1/login",
            "/users/v1/admin",
            "/users/v1/me",
            "/books/v1",
            "/books/v1/b1",
        ],
    },
    "crapi": {
        "name": "crAPI",
        "base_url": "http://localhost:8888",
        "type": "microservices",
        "endpoints": [
            "/",
            "/api/health",
            "/identity/api/auth/signup",
            "/identity/api/auth/login",
            "/identity/api/v2/user/dashboard",
            "/identity/api/v2/user/login-with-token",
            "/identity/api/v2/vehicle/vehicles",
            "/community/api/v2/community/posts/recent",
            "/community/api/v2/community/posts/popular",
            "/workshop/api/mechanic",
            "/workshop/api/shop/products",
            "/workshop/api/shop/orders",
            "/workshop/api/shop/orders/all",
        ],
    },
}

# ─── HTTP Session ─────────────────────────────────────────────────────────────
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (RedTeam-Recon/1.0)",
    "Accept": "application/json, text/html, */*",
})

# ─── Helpers ──────────────────────────────────────────────────────────────────
def info(msg):    print(f"{BLUE}[*]{RESET} {msg}")
def success(msg): print(f"{GREEN}[+]{RESET} {msg}")
def warn(msg):    print(f"{YELLOW}[!]{RESET} {msg}")
def error(msg):   print(f"{RED}[-]{RESET} {msg}")

def probe_endpoint(base_url, path, timeout=5):
    url = base_url.rstrip("/") + path
    try:
        r = session.get(url, timeout=timeout, allow_redirects=True)
        return {
            "url": url,
            "status": r.status_code,
            "length": len(r.content),
            "content_type": r.headers.get("Content-Type", ""),
            "server": r.headers.get("Server", ""),
            "interesting": extract_interesting(r),
        }
    except requests.exceptions.ConnectionError:
        return {"url": url, "status": "CONN_ERR", "length": 0,
                "content_type": "", "server": "", "interesting": []}
    except requests.exceptions.Timeout:
        return {"url": url, "status": "TIMEOUT", "length": 0,
                "content_type": "", "server": "", "interesting": []}

def extract_interesting(response):
    """Pick out juicy things from a response."""
    notes = []
    text = response.text.lower()

    if response.status_code == 200:
        notes.append("OPEN")
    if response.status_code == 401:
        notes.append("AUTH_REQUIRED")
    if response.status_code == 403:
        notes.append("FORBIDDEN")
    if response.status_code in [500, 502, 503]:
        notes.append("SERVER_ERROR")

    # Look for interesting content patterns
    for keyword in ["password", "token", "secret", "admin", "key", "api_key",
                    "authorization", "bearer", "jwt", "email", "username"]:
        if keyword in text:
            notes.append(f"CONTAINS_{keyword.upper()}")

    # Check for common security headers
    headers = {k.lower(): v for k, v in response.headers.items()}
    missing = []
    for h in ["x-frame-options", "x-content-type-options",
              "content-security-policy", "strict-transport-security"]:
        if h not in headers:
            missing.append(h)
    if missing:
        notes.append(f"MISSING_HEADERS:{','.join(missing)}")

    return notes

def status_color(code):
    if code == 200:       return f"{GREEN}{code}{RESET}"
    if code in [301,302]: return f"{CYAN}{code}{RESET}"
    if code == 401:       return f"{YELLOW}{code}{RESET}"
    if code == 403:       return f"{YELLOW}{code}{RESET}"
    if code == 404:       return f"{RESET}{code}{RESET}"
    if str(code).startswith("5"): return f"{RED}{code}{RESET}"
    return f"{RESET}{code}{RESET}"

# ─── Core Recon Functions ─────────────────────────────────────────────────────
def check_target_alive(target_key):
    t = TARGETS[target_key]
    info(f"Checking {t['name']} at {t['base_url']} ...")
    try:
        r = session.get(t["base_url"], timeout=5)
        success(f"{t['name']} is UP — HTTP {r.status_code}")
        return True
    except Exception as e:
        error(f"{t['name']} is DOWN — {e}")
        return False

def enumerate_endpoints(target_key):
    t = TARGETS[target_key]
    print(f"\n{BOLD}{CYAN}{'─'*60}{RESET}")
    print(f"{BOLD}  Enumerating: {t['name']} ({t['type']}){RESET}")
    print(f"{BOLD}{CYAN}{'─'*60}{RESET}")

    results = []
    for path in t["endpoints"]:
        result = probe_endpoint(t["base_url"], path)
        code = result["status"]
        length = result["length"]
        notes = result["interesting"]

        # Print the result
        status_str = status_color(code) if isinstance(code, int) else f"{RED}{code}{RESET}"
        notes_str  = f"{YELLOW} [{', '.join(notes)}]{RESET}" if notes else ""
        print(f"  {status_str}  {result['url']:<60}  {length:>6}B{notes_str}")

        results.append(result)
        time.sleep(0.1)  # be gentle

    return results

def get_juiceshop_products():
    """Fetch and display Juice Shop product list — useful for injection targets."""
    print(f"\n{BOLD}  Juice Shop — Product Catalog (injection targets){RESET}")
    print(f"  {'─'*55}")
    try:
        r = session.get("http://localhost:3000/api/Products", timeout=5)
        if r.status_code == 200:
            products = r.json().get("data", [])[:10]
            for p in products:
                pid  = p.get("id", "?")
                name = p.get("name", "?")
                print(f"  {GREEN}[ID:{pid:>3}]{RESET} {name}")
            success(f"Found {len(products)} products (showing first 10)")
        else:
            warn(f"Got HTTP {r.status_code}")
    except Exception as e:
        error(f"Could not fetch products: {e}")

def get_vampi_openapi():
    """Parse VAmPI OpenAPI spec and list all endpoints."""
    print(f"\n{BOLD}  VAmPI — OpenAPI Endpoint Map{RESET}")
    print(f"  {'─'*55}")
    try:
        r = session.get("http://localhost:5000/openapi.json", timeout=5)
        if r.status_code == 200:
            spec = r.json()
            paths = spec.get("paths", {})
            for path, methods in paths.items():
                for method in methods.keys():
                    print(f"  {CYAN}{method.upper():<7}{RESET} {path}")
            success(f"Parsed {len(paths)} paths from OpenAPI spec")
        else:
            warn(f"Got HTTP {r.status_code}")
    except Exception as e:
        error(f"Could not fetch OpenAPI spec: {e}")

def get_crapi_vehicles_unauthenticated():
    """Test crAPI vehicle endpoint without auth — check for broken auth."""
    print(f"\n{BOLD}  crAPI — Unauthenticated Access Tests{RESET}")
    print(f"  {'─'*55}")
    test_endpoints = [
        "/identity/api/v2/vehicle/vehicles",
        "/workshop/api/shop/products",
        "/community/api/v2/community/posts/recent",
        "/workshop/api/shop/orders/all",
    ]
    for ep in test_endpoints:
        url = f"http://localhost:8888{ep}"
        try:
            r = session.get(url, timeout=5)
            color = GREEN if r.status_code == 200 else YELLOW
            print(f"  {color}[{r.status_code}]{RESET} {ep}")
            if r.status_code == 200:
                warn(f"    --> UNAUTHENTICATED ACCESS to {ep} !")
        except Exception as e:
            error(f"  Error hitting {ep}: {e}")

def save_findings(all_results):
    """Save all findings to a JSON report."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename  = f"recon_{timestamp}.json"
    try:
        with open(filename, "w") as f:
            json.dump(all_results, f, indent=2)
        success(f"Findings saved → {filename}")
    except Exception as e:
        error(f"Could not save findings: {e}")

# ─── Summary ──────────────────────────────────────────────────────────────────
def print_summary(all_results):
    print(f"\n{BOLD}{CYAN}{'═'*60}{RESET}")
    print(f"{BOLD}  RECON SUMMARY{RESET}")
    print(f"{BOLD}{CYAN}{'═'*60}{RESET}")

    open_endpoints   = []
    auth_endpoints   = []
    error_endpoints  = []
    interesting_hits = []

    for target_key, results in all_results.items():
        for r in results:
            if r["status"] == 200:
                open_endpoints.append(r["url"])
            elif r["status"] in [401, 403]:
                auth_endpoints.append(r["url"])
            elif isinstance(r["status"], int) and r["status"] >= 500:
                error_endpoints.append(r["url"])
            for note in r["interesting"]:
                if "CONTAINS_" in note or "MISSING_" in note:
                    interesting_hits.append((r["url"], note))

    print(f"\n  {GREEN}Open endpoints      :{RESET} {len(open_endpoints)}")
    print(f"  {YELLOW}Auth-protected      :{RESET} {len(auth_endpoints)}")
    print(f"  {RED}Server errors       :{RESET} {len(error_endpoints)}")
    print(f"  {CYAN}Interesting hits    :{RESET} {len(interesting_hits)}")

    if open_endpoints:
        print(f"\n  {GREEN}[OPEN ENDPOINTS]{RESET}")
        for ep in open_endpoints[:15]:
            print(f"    → {ep}")

    if interesting_hits:
        print(f"\n  {CYAN}[INTERESTING FINDINGS]{RESET}")
        for url, note in interesting_hits[:10]:
            print(f"    → {note:<40} {url}")

    print(f"\n{BOLD}{CYAN}{'═'*60}{RESET}")
    print(f"  Next step: run 02_auth_bruteforce.py")
    print(f"{BOLD}{CYAN}{'═'*60}{RESET}\n")

# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Red Team Phase 1 — Recon")
    parser.add_argument("--target", choices=["juiceshop", "vampi", "crapi", "all"],
                        default="all", help="Which target to scan")
    parser.add_argument("--save", action="store_true",
                        help="Save findings to JSON file")
    args = parser.parse_args()

    banner()

    targets_to_scan = (
        list(TARGETS.keys()) if args.target == "all"
        else [args.target]
    )

    # Liveness check
    print(f"{BOLD}[0] Liveness Check{RESET}")
    alive = {}
    for t in targets_to_scan:
        alive[t] = check_target_alive(t)

    # Endpoint enumeration
    print(f"\n{BOLD}[1] Endpoint Enumeration{RESET}")
    all_results = {}
    for t in targets_to_scan:
        if alive.get(t):
            all_results[t] = enumerate_endpoints(t)

    # Target-specific deep recon
    print(f"\n{BOLD}[2] Deep Recon{RESET}")
    if "juiceshop" in targets_to_scan and alive.get("juiceshop"):
        get_juiceshop_products()
    if "vampi" in targets_to_scan and alive.get("vampi"):
        get_vampi_openapi()
    if "crapi" in targets_to_scan and alive.get("crapi"):
        get_crapi_vehicles_unauthenticated()

    # Summary
    print_summary(all_results)

    # Save
    if args.save:
        save_findings(all_results)

if __name__ == "__main__":
    main()