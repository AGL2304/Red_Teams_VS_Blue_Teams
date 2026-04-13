#!/usr/bin/env python3
"""
=============================================================================
Blue Team Monitor - M1PPAW Projet 2
=============================================================================
Description : Script de monitoring et détection d'attaques en temps réel
              sur OWASP Juice Shop via Elasticsearch
Auteur      : [Marc]
Date        : 13/04/2026
Version     : 1.0
Standards   : OWASP, NIST Cybersecurity Framework, MITRE ATT&CK
=============================================================================
"""

import requests
import json
import time
import datetime
import sys
from collections import defaultdict

# =============================================================================
# CONFIGURATION
# =============================================================================

ES_HOST = "http://localhost:9200"
ES_INDEX = "juice-shop-logs-*"
REFRESH_INTERVAL = 30  # secondes entre chaque analyse
ALERT_THRESHOLD_401 = 10  # nb de 401 avant alerte brute force
ALERT_THRESHOLD_500 = 5   # nb de 500 avant alerte
ALERT_THRESHOLD_SQL = 3   # nb de tentatives SQLi avant alerte

# Patterns de détection OWASP Top 10
ATTACK_PATTERNS = {
    "SQL_INJECTION": [
        "SELECT", "UNION", "DROP", "INSERT", "UPDATE",
        "OR 1=1", "' OR '", "--", "/*", "xp_cmdshell"
    ],
    "XSS": [
        "<script>", "javascript:", "onerror=", "onload=",
        "alert(", "document.cookie", "<img src=", "eval("
    ],
    "PATH_TRAVERSAL": [
        "../", "..\\", "/etc/passwd", "C:\\Windows",
        "%2e%2e", "%252e%252e"
    ],
    "COMMAND_INJECTION": [
        "; ls", "| cat", "& whoami", "; rm -rf",
        "$(", "`cmd`", "| nc "
    ],
    "BRUTE_FORCE": [
        "401", "403", "Invalid password",
        "Authentication failed", "Too many requests"
    ]
}

# =============================================================================
# FONCTIONS UTILITAIRES
# =============================================================================

def print_banner():
    """Affiche la bannière du script."""
    banner = """
    ╔══════════════════════════════════════════════════════════╗
    ║          BLUE TEAM MONITOR - M1PPAW 2026                ║
    ║          Détection d'attaques en temps réel             ║
    ║          OWASP Juice Shop via Elasticsearch             ║
    ╚══════════════════════════════════════════════════════════╝
    """
    print(banner)


def print_alert(level, attack_type, details):
    """
    Affiche une alerte formatée avec niveau de criticité.
    
    Args:
        level (str): Niveau d'alerte (CRITICAL, HIGH, MEDIUM, LOW)
        attack_type (str): Type d'attaque détecté
        details (str): Détails de l'attaque
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    colors = {
        "CRITICAL": "\033[91m",  # Rouge
        "HIGH":     "\033[93m",  # Jaune
        "MEDIUM":   "\033[94m",  # Bleu
        "LOW":      "\033[92m",  # Vert
    }
    reset = "\033[0m"
    color = colors.get(level, reset)
    
    print(f"{color}[{timestamp}] [{level}] {attack_type}{reset}")
    print(f"  → {details}")
    print()


def check_elasticsearch():
    """
    Vérifie que Elasticsearch est accessible.
    
    Returns:
        bool: True si ES est accessible, False sinon
    """
    try:
        response = requests.get(f"{ES_HOST}/_cluster/health", timeout=5)
        if response.status_code == 200:
            print("[✓] Elasticsearch accessible")
            return True
        else:
            print(f"[✗] Elasticsearch répond avec le code {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("[✗] Impossible de contacter Elasticsearch")
        print(f"    Vérifiez que ES tourne sur {ES_HOST}")
        return False


def get_logs_last_minutes(minutes=5):
    """
    Récupère les logs des X dernières minutes depuis Elasticsearch.
    
    Args:
        minutes (int): Nombre de minutes à analyser
        
    Returns:
        list: Liste des documents de logs
    """
    query = {
        "query": {
            "range": {
                "@timestamp": {
                    "gte": f"now-{minutes}m",
                    "lte": "now"
                }
            }
        },
        "size": 1000,
        "_source": ["message", "@timestamp", "stream"]
    }
    
    try:
        response = requests.post(
            f"{ES_HOST}/{ES_INDEX}/_search",
            json=query,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            hits = data.get("hits", {}).get("hits", [])
            return hits
        else:
            print(f"[!] Erreur ES: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"[!] Erreur lors de la requête ES: {e}")
        return []


# =============================================================================
# FONCTIONS DE DÉTECTION
# =============================================================================

def detect_sql_injection(logs):
    """
    Détecte les tentatives d'injection SQL dans les logs.
    
    Args:
        logs (list): Liste des logs à analyser
        
    Returns:
        list: Liste des logs suspects avec le pattern détecté
    """
    suspicious = []
    
    for log in logs:
        message = log.get("_source", {}).get("message", "").upper()
        timestamp = log.get("_source", {}).get("@timestamp", "")
        
        for pattern in ATTACK_PATTERNS["SQL_INJECTION"]:
            if pattern.upper() in message:
                suspicious.append({
                    "timestamp": timestamp,
                    "pattern": pattern,
                    "message": log.get("_source", {}).get("message", "")[:200]
                })
                break
                
    return suspicious


def detect_xss(logs):
    """
    Détecte les tentatives de Cross-Site Scripting (XSS).
    
    Args:
        logs (list): Liste des logs à analyser
        
    Returns:
        list: Liste des logs suspects
    """
    suspicious = []
    
    for log in logs:
        message = log.get("_source", {}).get("message", "").lower()
        timestamp = log.get("_source", {}).get("@timestamp", "")
        
        for pattern in ATTACK_PATTERNS["XSS"]:
            if pattern.lower() in message:
                suspicious.append({
                    "timestamp": timestamp,
                    "pattern": pattern,
                    "message": log.get("_source", {}).get("message", "")[:200]
                })
                break
                
    return suspicious


def detect_brute_force(logs):
    """
    Détecte les tentatives de brute force via les codes 401/403.
    
    Args:
        logs (list): Liste des logs à analyser
        
    Returns:
        dict: Compteur de tentatives par IP
    """
    attempts = defaultdict(int)
    
    for log in logs:
        message = log.get("_source", {}).get("message", "")
        
        for pattern in ATTACK_PATTERNS["BRUTE_FORCE"]:
            if pattern in message:
                # Extraction IP si présente dans le message
                parts = message.split()
                for part in parts:
                    if part.count(".") == 3:  # Format IP basique
                        attempts[part] += 1
                        break
                else:
                    attempts["unknown"] += 1
                break
                
    return attempts


def detect_path_traversal(logs):
    """
    Détecte les tentatives de path traversal.
    
    Args:
        logs (list): Liste des logs à analyser
        
    Returns:
        list: Liste des logs suspects
    """
    suspicious = []
    
    for log in logs:
        message = log.get("_source", {}).get("message", "")
        timestamp = log.get("_source", {}).get("@timestamp", "")
        
        for pattern in ATTACK_PATTERNS["PATH_TRAVERSAL"]:
            if pattern in message:
                suspicious.append({
                    "timestamp": timestamp,
                    "pattern": pattern,
                    "message": message[:200]
                })
                break
                
    return suspicious


# =============================================================================
# FONCTION PRINCIPALE D'ANALYSE
# =============================================================================

def analyze_logs(logs):
    """
    Lance toutes les détections sur les logs récupérés.
    
    Args:
        logs (list): Liste des logs à analyser
    """
    print(f"\n[*] Analyse de {len(logs)} logs...")
    print("-" * 60)
    
    # Détection SQLi
    sqli = detect_sql_injection(logs)
    if len(sqli) >= ALERT_THRESHOLD_SQL:
        print_alert("CRITICAL", "SQL INJECTION",
                   f"{len(sqli)} tentatives détectées")
        for s in sqli[:3]:
            print(f"    Pattern: {s['pattern']} | {s['timestamp']}")
    elif len(sqli) > 0:
        print_alert("HIGH", "SQL INJECTION",
                   f"{len(sqli)} tentative(s) détectée(s)")
    
    # Détection XSS
    xss = detect_xss(logs)
    if len(xss) > 0:
        print_alert("HIGH", "XSS ATTEMPT",
                   f"{len(xss)} tentative(s) détectée(s)")
    
    # Détection Brute Force
    bf = detect_brute_force(logs)
    for ip, count in bf.items():
        if count >= ALERT_THRESHOLD_401:
            print_alert("CRITICAL", "BRUTE FORCE",
                       f"IP {ip} : {count} tentatives échouées")
        elif count >= 5:
            print_alert("MEDIUM", "BRUTE FORCE",
                       f"IP {ip} : {count} tentatives échouées")
    
    # Détection Path Traversal
    pt = detect_path_traversal(logs)
    if len(pt) > 0:
        print_alert("HIGH", "PATH TRAVERSAL",
                   f"{len(pt)} tentative(s) détectée(s)")
    
    # Résumé
    total_threats = len(sqli) + len(xss) + len(pt)
    print(f"\n[*] Résumé : {total_threats} menaces détectées")
    print(f"    SQLi: {len(sqli)} | XSS: {len(xss)} | Path Traversal: {len(pt)}")
    print("-" * 60)


# =============================================================================
# BOUCLE PRINCIPALE
# =============================================================================

def main():
    """Point d'entrée principal du script de monitoring."""
    print_banner()
    
    # Vérification ES
    if not check_elasticsearch():
        sys.exit(1)
    
    print(f"\n[*] Démarrage du monitoring (intervalle: {REFRESH_INTERVAL}s)")
    print("[*] Appuyez sur Ctrl+C pour arrêter\n")
    
    try:
        while True:
            print(f"\n{'='*60}")
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Analyse en cours...")
            
            # Récupération et analyse des logs
            logs = get_logs_last_minutes(minutes=5)
            analyze_logs(logs)
            
            print(f"\n[*] Prochaine analyse dans {REFRESH_INTERVAL}s...")
            time.sleep(REFRESH_INTERVAL)
            
    except KeyboardInterrupt:
        print("\n\n[*] Monitoring arrêté par l'utilisateur")
        sys.exit(0)


if __name__ == "__main__":
    main()