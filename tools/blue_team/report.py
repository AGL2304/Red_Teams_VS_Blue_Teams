#!/usr/bin/env python3
"""
=============================================================================
Blue Team Report Generator - M1PPAW Projet 2
=============================================================================
Description : Génération automatique de rapports d'incident de sécurité
              conformes aux standards ISO 27035 et ANSSI
Auteur      : [Marc]
Date        : 13/04/2026
Version     : 1.0
Standards   : ISO 27035, ANSSI, OWASP, CVSS 3.1
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

ES_HOST        = "http://localhost:9200"
ES_INDEX       = "juice-shop-logs-*"
ALERTS_FILE    = "alerts.json"
REPORT_FILE    = "incident_report.md"
COMPANY_NAME   = "Ecole IT - M1 Cybersécurité"
ANALYST_NAME   = "[Ton nom]"
PROJECT        = "M1PPAW - Projet 2 Red/Blue Team"


# =============================================================================
# CHARGEMENT DES DONNÉES
# =============================================================================

def load_alerts():
    """
    Charge les alertes depuis le fichier JSON généré par alerting.py.

    Returns:
        list: Liste des alertes ou liste vide si fichier absent
    """
    if not os.path.exists(ALERTS_FILE):
        print(f"[!] Fichier {ALERTS_FILE} introuvable.")
        print("    Lancez d'abord alerting.py pour générer des alertes.")
        return []
    with open(ALERTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def get_log_stats():
    """
    Récupère les statistiques globales des logs depuis Elasticsearch.

    Returns:
        dict: Statistiques (total, par stream, période)
    """
    query = {
        "query": {"match_all": {}},
        "size": 0,
        "aggs": {
            "by_stream": {
                "terms": {"field": "stream"}
            },
            "over_time": {
                "date_histogram": {
                    "field": "@timestamp",
                    "calendar_interval": "day"
                }
            }
        }
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
            total = data.get("hits", {}).get("total", {}).get("value", 0)
            buckets = (data.get("aggregations", {})
                          .get("by_stream", {})
                          .get("buckets", []))
            stream_stats = {b["key"]: b["doc_count"] for b in buckets}
            return {"total": total, "by_stream": stream_stats}
    except Exception as e:
        print(f"[!] Erreur ES stats: {e}")

    return {"total": 0, "by_stream": {}}


# =============================================================================
# CALCULS ET STATISTIQUES
# =============================================================================

def compute_stats(alerts):
    """
    Calcule les statistiques globales à partir des alertes.

    Args:
        alerts (list): Liste des alertes

    Returns:
        dict: Statistiques agrégées
    """
    stats = {
        "total":       len(alerts),
        "open":        0,
        "by_severity": defaultdict(int),
        "by_type":     defaultdict(int),
        "avg_cvss":    0.0,
        "max_cvss":    0.0,
        "risk_score":  0.0,
    }

    cvss_values = []

    for alert in alerts:
        if alert.get("status") == "OPEN":
            stats["open"] += 1
        stats["by_severity"][alert.get("severity", "UNKNOWN")] += 1
        stats["by_type"][alert.get("attack_type", "UNKNOWN")] += 1
        cvss = alert.get("cvss_score", 0)
        cvss_values.append(cvss)

    if cvss_values:
        stats["avg_cvss"] = round(sum(cvss_values) / len(cvss_values), 2)
        stats["max_cvss"] = max(cvss_values)

    # Score de risque global normalisé sur 100
    if alerts:
        raw = sum(
            a.get("cvss_score", 0) * (1 + a.get("occurrences", 1) * 0.1)
            for a in alerts
        )
        stats["risk_score"] = round(min(100, raw / len(alerts) * 10), 2)

    return stats


def get_severity_emoji(severity):
    """
    Retourne l'emoji correspondant au niveau de sévérité.

    Args:
        severity (str): Niveau de sévérité

    Returns:
        str: Emoji
    """
    return {
        "CRITICAL": "🔴",
        "HIGH":     "🟠",
        "MEDIUM":   "🟡",
        "LOW":      "🟢",
    }.get(severity, "⚪")


# =============================================================================
# GÉNÉRATION DU RAPPORT
# =============================================================================

def generate_executive_summary(stats, log_stats):
    """
    Génère l'executive summary du rapport.

    Args:
        stats (dict): Statistiques des alertes
        log_stats (dict): Statistiques des logs

    Returns:
        str: Section executive summary en Markdown
    """
    risk_level = (
        "CRITIQUE" if stats["risk_score"] >= 80 else
        "ÉLEVÉ"    if stats["risk_score"] >= 60 else
        "MODÉRÉ"   if stats["risk_score"] >= 40 else
        "FAIBLE"
    )

    return f"""## 1. Executive Summary

**Période d'analyse :** {datetime.datetime.now().strftime('%d/%m/%Y')}
**Analyste :** {ANALYST_NAME}
**Projet :** {PROJECT}

### Synthèse

Durant la période d'analyse, le système de monitoring Blue Team a détecté
**{stats['total']} alertes de sécurité** sur l'infrastructure OWASP Juice Shop,
avec un score de risque global évalué à **{stats['risk_score']}/100 ({risk_level})**.

| Indicateur | Valeur |
|---|---|
| Total logs analysés | {log_stats['total']:,} |
| Alertes générées | {stats['total']} |
| Alertes ouvertes | {stats['open']} |
| Score de risque | {stats['risk_score']}/100 |
| CVSS moyen | {stats['avg_cvss']} |
| CVSS maximum | {stats['max_cvss']} |

### Niveau de risque global : {risk_level}

Les principales menaces identifiées sont les injections SQL et les tentatives
de brute force, nécessitant une remédiation immédiate.
"""


def generate_technical_findings(alerts, stats):
    """
    Génère la section des findings techniques.

    Args:
        alerts (list): Liste des alertes
        stats (dict): Statistiques

    Returns:
        str: Section findings en Markdown
    """
    lines = ["## 2. Findings Techniques\n"]

    # Tableau de synthèse
    lines.append("### 2.1 Tableau de synthèse\n")
    lines.append("| # | Type d'attaque | Sévérité | CVSS | Occurrences | MITRE |")
    lines.append("|---|---|---|---|---|---|")

    for i, alert in enumerate(alerts, 1):
        emoji   = get_severity_emoji(alert.get("severity", ""))
        lines.append(
            f"| {i} "
            f"| {alert.get('attack_type', 'N/A')} "
            f"| {emoji} {alert.get('severity', 'N/A')} "
            f"| {alert.get('cvss_score', 'N/A')} "
            f"| {alert.get('occurrences', 'N/A')} "
            f"| {alert.get('mitre_technique', 'N/A')} |"
        )

    lines.append("")

    # Détail par alerte
    lines.append("### 2.2 Détail des alertes\n")

    for i, alert in enumerate(alerts, 1):
        emoji = get_severity_emoji(alert.get("severity", ""))
        lines += [
            f"#### Alerte {i} — {alert.get('attack_type', 'N/A')}",
            "",
            f"- **ID**         : `{alert.get('id', 'N/A')}`",
            f"- **Timestamp**  : {alert.get('timestamp', 'N/A')}",
            f"- **Sévérité**   : {emoji} {alert.get('severity', 'N/A')}",
            f"- **CVSS**       : {alert.get('cvss_score', 'N/A')}",
            f"- **MITRE**      : {alert.get('mitre_technique', 'N/A')}",
            f"- **IP source**  : {alert.get('source_ip', 'N/A')}",
            f"- **Occurrences**: {alert.get('occurrences', 'N/A')}",
            f"- **Statut**     : {alert.get('status', 'N/A')}",
            "",
            f"**Détails :** {alert.get('details', 'N/A')}",
            "",
            "**Remédiation recommandée :**",
            "",
            f"```",
            alert.get("remediation", "N/A"),
            "```",
            "",
        ]

    return "\n".join(lines)


def generate_recommendations(alerts):
    """
    Génère les recommandations prioritaires.

    Args:
        alerts (list): Liste des alertes

    Returns:
        str: Section recommandations en Markdown
    """
    critical = [a for a in alerts if a.get("severity") == "CRITICAL"]
    high     = [a for a in alerts if a.get("severity") == "HIGH"]

    lines = [
        "## 3. Recommandations\n",
        "### 3.1 Actions immédiates (< 24h)\n",
    ]

    if critical:
        for a in critical:
            lines.append(
                f"- 🔴 **{a['attack_type']}** (CVSS {a['cvss_score']}) : "
                f"Bloquer immédiatement et investiguer"
            )
    else:
        lines.append("- ✅ Aucune alerte critique active")

    lines += [
        "",
        "### 3.2 Actions à court terme (< 1 semaine)\n",
    ]

    if high:
        for a in high:
            lines.append(
                f"- 🟠 **{a['attack_type']}** : Corriger la vulnérabilité "
                f"et mettre à jour les règles WAF"
            )
    else:
        lines.append("- ✅ Aucune alerte haute active")

    lines += [
        "",
        "### 3.3 Améliorations long terme\n",
        "- Mettre en place un programme de Bug Bounty",
        "- Intégrer les tests de sécurité dans la CI/CD (DevSecOps)",
        "- Former les développeurs aux bonnes pratiques OWASP",
        "- Déployer un WAF (ModSecurity, Cloudflare) en production",
        "- Planifier des audits de sécurité trimestriels",
        "",
    ]

    return "\n".join(lines)


def generate_appendix(log_stats):
    """
    Génère les annexes techniques du rapport.

    Args:
        log_stats (dict): Statistiques des logs

    Returns:
        str: Section annexes en Markdown
    """
    return f"""## 4. Annexes

### 4.1 Infrastructure de monitoring

| Composant | Version | Rôle |
|---|---|---|
| Elasticsearch | 8.13.0 | Stockage et indexation des logs |
| Kibana | 8.13.0 | Visualisation et dashboards |
| Filebeat | 8.13.0 | Collecte des logs Docker |
| OWASP Juice Shop | Latest | Application cible |

### 4.2 Statistiques des logs collectés

| Stream | Documents |
|---|---|
| stderr | {log_stats['by_stream'].get('stderr', 0):,} |
| stdout | {log_stats['by_stream'].get('stdout', 0):,} |
| **Total** | **{log_stats['total']:,}** |

### 4.3 Règles KQL utilisées

```kql
# Détection erreurs HTTP
message: *401* or message: *403* or message: *500*

# Détection SQLi
message: *SELECT* or message: *UNION* or message: *DROP*

# Détection XSS
message: *script* or message: *onerror* or message: *alert*

# Détection Path Traversal
message: *../* or message: */etc/passwd*
```

### 4.4 Références

- OWASP Top 10 : https://owasp.org/Top10
- MITRE ATT&CK : https://attack.mitre.org
- CVSS 3.1 : https://www.first.org/cvss
- ISO 27035 : Gestion des incidents de sécurité
- ANSSI : https://www.ssi.gouv.fr
"""


# =============================================================================
# ASSEMBLAGE ET EXPORT
# =============================================================================

def generate_full_report(alerts, stats, log_stats):
    """
    Assemble le rapport complet en Markdown.

    Args:
        alerts (list): Liste des alertes
        stats (dict): Statistiques
        log_stats (dict): Statistiques des logs

    Returns:
        str: Rapport complet en Markdown
    """
    header = f"""# Rapport d'Incident de Sécurité
## {COMPANY_NAME}

---

**Date de génération :** {datetime.datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}
**Analyste :** {ANALYST_NAME}
**Classification :** CONFIDENTIEL
**Référence :** INC-{datetime.datetime.now().strftime('%Y%m%d%H%M')}

---

"""
    sections = [
        header,
        generate_executive_summary(stats, log_stats),
        generate_technical_findings(alerts, stats),
        generate_recommendations(alerts),
        generate_appendix(log_stats),
    ]

    return "\n".join(sections)


def save_report(content):
    """
    Sauvegarde le rapport dans un fichier Markdown.

    Args:
        content (str): Contenu du rapport
    """
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[✓] Rapport sauvegardé : {REPORT_FILE}")


# =============================================================================
# POINT D'ENTRÉE
# =============================================================================

def main():
    """Point d'entrée principal du générateur de rapports."""
    print("\n" + "="*60)
    print("  BLUE TEAM REPORT GENERATOR - M1PPAW 2026")
    print("="*60)

    # Chargement des données
    print("\n[*] Chargement des alertes...")
    alerts = load_alerts()
    if not alerts:
        print("[!] Aucune alerte trouvée. Lancez alerting.py d'abord.")
        return

    print(f"[✓] {len(alerts)} alertes chargées")

    print("[*] Récupération des statistiques ES...")
    log_stats = get_log_stats()
    print(f"[✓] {log_stats['total']:,} logs analysés")

    # Calcul des stats
    stats = compute_stats(alerts)

    # Génération du rapport
    print("[*] Génération du rapport...\n")
    report = generate_full_report(alerts, stats, log_stats)

    # Sauvegarde
    save_report(report)

    # Résumé console
    print("\n" + "="*60)
    print("  RAPPORT GÉNÉRÉ AVEC SUCCÈS")
    print("="*60)
    print(f"  Alertes analysées : {stats['total']}")
    print(f"  Score de risque   : {stats['risk_score']}/100")
    print(f"  CVSS moyen        : {stats['avg_cvss']}")
    print(f"  Fichier           : {REPORT_FILE}")
    print("="*60)


if __name__ == "__main__":
    main()