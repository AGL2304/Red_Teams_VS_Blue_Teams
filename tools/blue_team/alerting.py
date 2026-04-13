#!/usr/bin/env python3
"""
=============================================================================
Blue Team Alerting - M1PPAW Projet 2
=============================================================================
Description : Système d'alerting automatisé - sauvegarde et scoring des
              alertes de sécurité détectées sur OWASP Juice Shop
Auteur      : [Marc]
Date        : 13/04/2026
Version     : 1.0
Standards   : CVSS 3.1, MITRE ATT&CK, ISO 27035
=============================================================================
"""

import json
import os
import datetime
import requests
from collections import defaultdict

# =============================================================================
# CONFIGURATION
# =============================================================================

ES_HOST = "http://localhost:9200"
ES_INDEX = "juice-shop-logs-*"
ALERTS_FILE = "alerts.json"
REPORT_FILE = "incident_report.txt"

# Scoring CVSS simplifié par type d'attaque
CVSS_SCORES = {
    "SQL_INJECTION":     9.8,   # Critical
    "XSS":               7.2,   # High
    "BRUTE_FORCE":       6.5,   # Medium
    "PATH_TRAVERSAL":    8.1,   # High
    "COMMAND_INJECTION": 9.9,   # Critical
}

# Mapping MITRE ATT&CK
MITRE_MAPPING = {
    "SQL_INJECTION":     "T1190 - Exploit Public-Facing Application",
    "XSS":               "T1059 - Command and Scripting Interpreter",
    "BRUTE_FORCE":       "T1110 - Brute Force",
    "PATH_TRAVERSAL":    "T1083 - File and Directory Discovery",
    "COMMAND_INJECTION": "T1059 - Command and Scripting Interpreter",
}

# Patterns de détection
ATTACK_PATTERNS = {
    "SQL_INJECTION": [
        "SELECT", "UNION", "DROP", "INSERT",
        "UPDATE", "OR 1=1", "--", "xp_cmdshell"
    ],
    "XSS": [
        "<script>", "javascript:", "onerror=",
        "alert(", "document.cookie", "eval("
    ],
    "PATH_TRAVERSAL": [
        "../", "..\\", "/etc/passwd", "%2e%2e"
    ],
    "BRUTE_FORCE": [
        "401", "403", "Invalid password",
        "Authentication failed"
    ]
}


# =============================================================================
# GESTION DES ALERTES
# =============================================================================

def load_alerts():
    """
    Charge les alertes existantes depuis le fichier JSON.
    
    Returns:
        list: Liste des alertes existantes
    """
    if os.path.exists(ALERTS_FILE):
        with open(ALERTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_alert(alert):
    """
    Sauvegarde une nouvelle alerte dans le fichier JSON.
    
    Args:
        alert (dict): Dictionnaire contenant les détails de l'alerte
    """
    alerts = load_alerts()
    alerts.append(alert)
    
    with open(ALERTS_FILE, "w", encoding="utf-8") as f:
        json.dump(alerts, f, indent=2, ensure_ascii=False)


def create_alert(attack_type, count, details, source_ip="unknown"):
    """
    Crée une alerte structurée avec scoring CVSS et mapping MITRE.
    
    Args:
        attack_type (str): Type d'attaque détectée
        count (int): Nombre d'occurrences
        details (str): Détails de l'attaque
        source_ip (str): IP source si disponible
        
    Returns:
        dict: Alerte structurée
    """
    timestamp = datetime.datetime.now().isoformat()
    cvss = CVSS_SCORES.get(attack_type, 5.0)
    mitre = MITRE_MAPPING.get(attack_type, "Unknown")
    
    # Calcul du niveau de criticité basé sur CVSS
    if cvss >= 9.0:
        severity = "CRITICAL"
    elif cvss >= 7.0:
        severity = "HIGH"
    elif cvss >= 4.0:
        severity = "MEDIUM"
    else:
        severity = "LOW"
    
    alert = {
        "id": f"ALERT-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}",
        "timestamp": timestamp,
        "attack_type": attack_type,
        "severity": severity,
        "cvss_score": cvss,
        "mitre_technique": mitre,
        "occurrences": count,
        "source_ip": source_ip,
        "details": details,
        "status": "OPEN",
        "remediation": get_remediation(attack_type)
    }
    
    return alert


def get_remediation(attack_type):
    """
    Retourne les recommandations de remédiation par type d'attaque.
    
    Args:
        attack_type (str): Type d'attaque
        
    Returns:
        str: Recommandations de remédiation
    """
    remediations = {
        "SQL_INJECTION": (
            "1. Utiliser des requêtes paramétrées (prepared statements)\n"
            "2. Valider et assainir tous les inputs utilisateur\n"
            "3. Appliquer le principe du moindre privilège sur la DB\n"
            "4. Activer un WAF avec règles anti-SQLi"
        ),
        "XSS": (
            "1. Encoder les outputs HTML (htmlspecialchars)\n"
            "2. Implémenter Content Security Policy (CSP)\n"
            "3. Valider et assainir les inputs côté serveur\n"
            "4. Utiliser des cookies HttpOnly et Secure"
        ),
        "BRUTE_FORCE": (
            "1. Implémenter un rate limiting sur les endpoints auth\n"
            "2. Activer le verrouillage de compte après N tentatives\n"
            "3. Mettre en place le MFA (Multi-Factor Authentication)\n"
            "4. Bloquer les IPs suspectes via fail2ban ou WAF"
        ),
        "PATH_TRAVERSAL": (
            "1. Valider et normaliser tous les chemins de fichiers\n"
            "2. Utiliser une whitelist des répertoires autorisés\n"
            "3. Exécuter l'application avec des permissions minimales\n"
            "4. Chrooted environment pour isoler les accès fichiers"
        ),
        "COMMAND_INJECTION": (
            "1. Éviter les appels système avec des inputs utilisateur\n"
            "2. Utiliser des APIs sécurisées plutôt que shell_exec\n"
            "3. Valider strictement tous les paramètres\n"
            "4. Sandboxer l'environnement d'exécution"
        )
    }
    return remediations.get(attack_type, "Analyser et corriger la vulnérabilité.")


# =============================================================================
# ANALYSE ET SCORING
# =============================================================================

def get_logs(minutes=5):
    """
    Récupère les logs récents depuis Elasticsearch.
    
    Args:
        minutes (int): Fenêtre temporelle en minutes
        
    Returns:
        list: Liste des logs
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
            return response.json().get("hits", {}).get("hits", [])
        return []
    except Exception as e:
        print(f"[!] Erreur ES: {e}")
        return []


def calculate_risk_score(alerts):
    """
    Calcule un score de risque global basé sur les alertes actives.
    
    Args:
        alerts (list): Liste des alertes
        
    Returns:
        float: Score de risque global (0-100)
    """
    if not alerts:
        return 0.0
    
    total_score = 0
    for alert in alerts:
        cvss = alert.get("cvss_score", 0)
        occurrences = alert.get("occurrences", 1)
        # Formule : CVSS * log(occurrences + 1) normalisé sur 100
        total_score += cvss * (1 + occurrences * 0.1)
    
    # Normalisation sur 100
    risk_score = min(100, total_score / len(alerts) * 10)
    return round(risk_score, 2)


def analyze_and_alert(logs):
    """
    Analyse les logs et génère les alertes correspondantes.
    
    Args:
        logs (list): Liste des logs à analyser
        
    Returns:
        list: Liste des nouvelles alertes générées
    """
    new_alerts = []
    detections = defaultdict(int)
    
    # Comptage des patterns détectés
    for log in logs:
        message = log.get("_source", {}).get("message", "")
        
        for attack_type, patterns in ATTACK_PATTERNS.items():
            for pattern in patterns:
                if pattern.lower() in message.lower():
                    detections[attack_type] += 1
                    break
    
    # Génération des alertes
    for attack_type, count in detections.items():
        if count > 0:
            alert = create_alert(
                attack_type=attack_type,
                count=count,
                details=f"{count} occurrences détectées dans les 5 dernières minutes"
            )
            save_alert(alert)
            new_alerts.append(alert)
            
            # Affichage console
            print(f"[ALERTE] {alert['severity']} | {attack_type}")
            print(f"  CVSS: {alert['cvss_score']} | MITRE: {alert['mitre_technique']}")
            print(f"  Occurrences: {count}")
            print(f"  ID: {alert['id']}")
            print()
    
    return new_alerts


def print_dashboard(alerts):
    """
    Affiche un dashboard textuel des alertes et du score de risque.
    
    Args:
        alerts (list): Liste de toutes les alertes
    """
    risk_score = calculate_risk_score(alerts)
    open_alerts = [a for a in alerts if a.get("status") == "OPEN"]
    
    print("\n" + "="*60)
    print("  BLUE TEAM DASHBOARD - RÉSUMÉ DES ALERTES")
    print("="*60)
    print(f"  Score de risque global : {risk_score}/100")
    print(f"  Alertes totales        : {len(alerts)}")
    print(f"  Alertes ouvertes       : {len(open_alerts)}")
    
    # Comptage par sévérité
    by_severity = defaultdict(int)
    for a in open_alerts:
        by_severity[a.get("severity", "UNKNOWN")] += 1
    
    print(f"\n  Par sévérité :")
    print(f"    🔴 CRITICAL : {by_severity['CRITICAL']}")
    print(f"    🟠 HIGH     : {by_severity['HIGH']}")
    print(f"    🟡 MEDIUM   : {by_severity['MEDIUM']}")
    print(f"    🟢 LOW      : {by_severity['LOW']}")
    print("="*60)


# =============================================================================
# POINT D'ENTRÉE
# =============================================================================

def main():
    """Point d'entrée principal du système d'alerting."""
    print("\n[*] Blue Team Alerting System démarré")
    print(f"[*] Fichier alertes : {ALERTS_FILE}")
    print("[*] Analyse des logs des 5 dernières minutes...\n")
    
    # Récupération et analyse des logs
    logs = get_logs(minutes=5)
    print(f"[*] {len(logs)} logs récupérés\n")
    
    # Génération des alertes
    new_alerts = analyze_and_alert(logs)
    
    # Chargement de toutes les alertes pour le dashboard
    all_alerts = load_alerts()
    print_dashboard(all_alerts)
    
    print(f"\n[✓] {len(new_alerts)} nouvelles alertes sauvegardées dans {ALERTS_FILE}")


if __name__ == "__main__":
    main()