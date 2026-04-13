# Rapport d'Incident de Sécurité
## Ecole IT - M1 Cybersécurité

---

**Date de génération :** 13/04/2026 à 14:09:09
**Analyste :** [Marc]
**Classification :** CONFIDENTIEL
**Référence :** INC-202604131409

---


## 1. Executive Summary

**Période d'analyse :** 13/04/2026
**Analyste :** [Ton nom]
**Projet :** M1PPAW - Projet 2 Red/Blue Team

### Synthèse

Durant la période d'analyse, le système de monitoring Blue Team a détecté
**2 alertes de sécurité** sur l'infrastructure OWASP Juice Shop,
avec un score de risque global évalué à **100/100 (CRITIQUE)**.

| Indicateur | Valeur |
|---|---|
| Total logs analysés | 10,000 |
| Alertes générées | 2 |
| Alertes ouvertes | 2 |
| Score de risque | 100/100 |
| CVSS moyen | 8.15 |
| CVSS maximum | 9.8 |

### Niveau de risque global : CRITIQUE

Les principales menaces identifiées sont les injections SQL et les tentatives
de brute force, nécessitant une remédiation immédiate.

## 2. Findings Techniques

### 2.1 Tableau de synthèse

| # | Type d'attaque | Sévérité | CVSS | Occurrences | MITRE |
|---|---|---|---|---|---|
| 1 | SQL_INJECTION | 🔴 CRITICAL | 9.8 | 9 | T1190 - Exploit Public-Facing Application |
| 2 | BRUTE_FORCE | 🟡 MEDIUM | 6.5 | 6 | T1110 - Brute Force |

### 2.2 Détail des alertes

#### Alerte 1 — SQL_INJECTION

- **ID**         : `ALERT-20260413140559`
- **Timestamp**  : 2026-04-13T14:05:59.339311
- **Sévérité**   : 🔴 CRITICAL
- **CVSS**       : 9.8
- **MITRE**      : T1190 - Exploit Public-Facing Application
- **IP source**  : unknown
- **Occurrences**: 9
- **Statut**     : OPEN

**Détails :** 9 occurrences détectées dans les 5 dernières minutes

**Remédiation recommandée :**

```
1. Utiliser des requêtes paramétrées (prepared statements)
2. Valider et assainir tous les inputs utilisateur
3. Appliquer le principe du moindre privilège sur la DB
4. Activer un WAF avec règles anti-SQLi
```

#### Alerte 2 — BRUTE_FORCE

- **ID**         : `ALERT-20260413140559`
- **Timestamp**  : 2026-04-13T14:05:59.345389
- **Sévérité**   : 🟡 MEDIUM
- **CVSS**       : 6.5
- **MITRE**      : T1110 - Brute Force
- **IP source**  : unknown
- **Occurrences**: 6
- **Statut**     : OPEN

**Détails :** 6 occurrences détectées dans les 5 dernières minutes

**Remédiation recommandée :**

```
1. Implémenter un rate limiting sur les endpoints auth
2. Activer le verrouillage de compte après N tentatives
3. Mettre en place le MFA (Multi-Factor Authentication)
4. Bloquer les IPs suspectes via fail2ban ou WAF
```

## 3. Recommandations

### 3.1 Actions immédiates (< 24h)

- 🔴 **SQL_INJECTION** (CVSS 9.8) : Bloquer immédiatement et investiguer

### 3.2 Actions à court terme (< 1 semaine)

- ✅ Aucune alerte haute active

### 3.3 Améliorations long terme

- Mettre en place un programme de Bug Bounty
- Intégrer les tests de sécurité dans la CI/CD (DevSecOps)
- Former les développeurs aux bonnes pratiques OWASP
- Déployer un WAF (ModSecurity, Cloudflare) en production
- Planifier des audits de sécurité trimestriels

## 4. Annexes

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
| stderr | 116,941 |
| stdout | 32,186 |
| **Total** | **10,000** |

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
