# Rapport Blue Team — Sécurisation OWASP Juice Shop
**Date :** 15–16 avril 2026  
**Environnement :** Juice Shop v6.2.0-SNAPSHOT · Docker · localhost:3000  
**WAF :** Nginx + ModSecurity · localhost:8081  
**Équipe :** Blue Team  

---

## Executive Summary

Suite à l'audit Red Team (J1–J3) ayant identifié **5 vulnérabilités critiques/hautes**, nous avons implémenté une défense en profondeur couvrant les couches WAF, SIEM et hardening applicatif.

La validation Purple Team (script `purple_team_validation.py`) a produit un score de **56 % (9/16 tests réussis)**. Ce score reflète un premier niveau de défense fonctionnel sur les vecteurs XSS et l'authentification, mais révèle des lacunes importantes sur le rate limiting, certaines règles SQLi, et la gestion des faux positifs.

| Métrique | Avant | Après (mesuré) |
|---|---|---|
| Score CVSS moyen | 9.2 / 10 | ~5.8 / 10 (partiel) |
| Attaques bloquées (Purple Team) | 0 % | **56 % (9/16)** |
| Faux positifs WAF | — | **2 détectés** |
| Header CSP | Absent | **Absent — à corriger** |
| Rate limiting actif | Non | **Non — à corriger** |

---

## 1. Vulnérabilités traitées — État réel

### 🔴 VULN-01 — SQLi UNION sur `/rest/products/search`

La concaténation directe du paramètre `q` dans la requête SQLite permettait un dump complet de la base (22 utilisateurs, hashes MD5, réponses de sécurité).

**Correction déployée :** règle WAF `WAF-001` ciblant les patterns `UNION SELECT`, `sqlite_master`, `'))`.

**Résultat Purple Team : ✗ FAIL — HTTP 0 au lieu de 403/400**  
→ La règle WAF-001 ne bloque pas encore le payload UNION SELECT sur cet endpoint. Le trafic passe sans interception. La correction est déclarée mais non effective en production.

**Action corrective requise :** vérifier que la règle ModSecurity est bien chargée et que le proxy écoute sur `:8081` pour cet endpoint spécifiquement.

---

### 🔴 VULN-02 — SQLi time-based via RANDOMBLOB

Payload de type time-based blind utilisant `RANDOMBLOB(500000000/2)` pour confirmer l'injection.

**Correction déployée :** règle WAF `WAF-005` ciblant `RANDOMBLOB`.

**Résultat Purple Team : ✗ FAIL — HTTP 0 au lieu de 403/400**  
→ La règle n'est pas active ou le proxy ne route pas correctement ce type de requête.

---

### 🔴 VULN-02b — SQLi Login Bypass sur `/rest/user/login`

L'injection `email'--` court-circuitait la vérification du mot de passe.

**Résultat Purple Team : ✅ PASS — HTTP 403 (bloqué)**  
→ Seul vecteur SQLi correctement bloqué. La règle WAF-002 fonctionne sur l'endpoint de login.  
→ Confirmé sans WAF : HTTP 200 (bypass réussi) — le WAF est bien nécessaire ici.

---

### 🟠 VULN-03 — IDOR sur `/api/Users/{id}` et `/rest/basket/{id}`

Tout utilisateur authentifié pouvait lire le profil et le panier d'un autre utilisateur par ID incrémental.

**Correction déployée :** rate limiting agressif sur ces endpoints + logging SIEM.

**Résultat Purple Team : non testé directement dans ce script**  
→ Le rate limiting global est confirmé **inactif** (voir BLOC 5). La protection IDOR par rate limiting n'est donc pas effective.  
→ La correction applicative (vérification `token.userId === requestedId`) reste recommandée et non implémentée.

---

### 🟠 VULN-04 — Null Byte Bypass sur `/ftp/`

Le double encodage `%2500` contournait le filtre d'extension `.md/.pdf`.

**Correction déployée :** règle WAF `WAF-003` rejetant `%25` dans les chemins `/ftp/`.

**Résultat Purple Team : ✗ FAIL — HTTP 200 au lieu de 403/400**  
→ Le payload `%2500` passe sans blocage. La règle WAF-003 n'est pas effective.  
→ Le trafic légitime `.md` passe correctement (✅ HTTP 200) — la règle est donc absente plutôt que mal configurée.

---

### 🟠 VULN-05 — XSS Stocké sur `/rest/products/{id}/reviews`

Injection de balises `<script>` permettant le vol de token JWT via `localStorage.getItem("token")`. Démontré en live : payload injecté, token admin exfiltré vers serveur attaquant, session hijacking confirmé.

**Correction déployée :** règle WAF `WAF-004` bloquant les balises HTML dans PUT/POST vers `/reviews`.

**Résultat Purple Team :**
- ✅ PASS — `<script>fetch(...)</script>` bloqué (HTTP 403)
- ✅ PASS — payload `onerror` bloqué (HTTP 403)
- ✗ FAIL — **Faux positif** : review légitime bloquée (HTTP 403 au lieu de 200)

→ La règle XSS est trop agressive : elle bloque le trafic légitime. À affiner avec une whitelist ou un pattern plus précis.

---

## 2. Architecture de défense déployée

```
Internet / Attaquant
        │
        ▼
┌───────────────┐
│  Nginx Proxy  │  ← WAF ModSecurity + règles custom
│  :8081        │  ← Rate limiting (configuré, non actif)
└───────┬───────┘
        │
        ▼
┌───────────────┐
│  Juice Shop   │  ← Headers sécurité partiels
│  :3000        │  ← CSP manquant
└───────┬───────┘
        │
        ▼
┌───────────────┐
│  ELK Stack    │  ← Ingestion logs WAF + app
│  :9200/:5601  │  ← Alertes temps réel
└───────────────┘
```

---

## 3. Résultats Purple Team — Détail complet

**Score global : 9/16 — 56 %**

### BLOC 1 : SQLi

| Test | Résultat | HTTP obtenu | Attendu |
|---|---|---|---|
| SQLi UNION search (WAF) | ✗ FAIL | 0 | 403/400/429 |
| SQLi time-based RANDOMBLOB (WAF) | ✗ FAIL | 0 | 403/400/429 |
| SQLi login bypass (WAF) | ✅ PASS | 403 | 403 |
| Sans WAF → login bypass | ✅ INFO | 200 | — |

### BLOC 2 : FTP Null Byte

| Test | Résultat | HTTP obtenu | Attendu |
|---|---|---|---|
| FTP null byte %2500 (WAF) | ✗ FAIL | 200 | 403/400/429 |
| FTP fichier .md légitime (WAF) | ✅ PASS | 200 | 200 |

### BLOC 3 : XSS Stocké

| Test | Résultat | HTTP obtenu | Attendu |
|---|---|---|---|
| XSS `<script>` dans review (WAF) | ✅ PASS | 403 | 403 |
| XSS `onerror` dans review (WAF) | ✅ PASS | 403 | 403 |
| Review légitime (WAF) | ✗ FAIL | 403 | 200 (faux positif) |

### BLOC 4 : Trafic légitime

| Test | Résultat | HTTP obtenu | Attendu |
|---|---|---|---|
| Recherche produit normale | ✅ PASS | 200 | 200 |
| Recherche avec apostrophe naturelle | ✗ FAIL | 500 | 200 (faux positif) |
| Page d'accueil | ✅ PASS | 200 | 200 |
| API produits | ✅ PASS | 200 | 200 |

### BLOC 5 : Rate Limiting

| Test | Résultat | Détail |
|---|---|---|
| 6 tentatives login rapides | ✗ FAIL | 0/6 requêtes bloquées |

### BLOC 6 : Headers de sécurité

| Header | Résultat | Valeur |
|---|---|---|
| X-Frame-Options | ✅ PASS | SAMEORIGIN |
| X-Content-Type-Options | ✅ PASS | nosniff |
| Content-Security-Policy | ✗ FAIL | Absent |

---

## 4. Analyse des échecs — Causes identifiées

### Rate Limiting inactif (BLOC 5)
Le module `limit_req` Nginx est configuré mais la zone n'est pas appliquée sur les bons `location` blocks. Résultat : 0/6 requêtes bloquées sur `/rest/user/login`. Correction : ajouter `limit_req zone=login burst=3 nodelay;` dans le block `location /rest/user/login`.

### SQLi UNION non bloqué (BLOC 1)
HTTP 0 indique que le proxy ne répond pas du tout — probable problème de routing ou de port. Le WAF sur `:8081` ne proxifie pas correctement les requêtes vers `/rest/products/search`. Vérifier la directive `proxy_pass` dans la config Nginx pour cet endpoint.

### Faux positif apostrophe (BLOC 4)
La règle anti-SQLi intercepte `q=it's` comme une tentative d'injection. Trop sensible. Solution : affiner le pattern pour exiger `'--`, `' OR`, `' UNION` plutôt que toute apostrophe isolée.

### Faux positif review légitime (BLOC 3)
La règle XSS bloque tout body contenant `<` ou `>`. Un texte comme `"Super produit < 10€"` serait bloqué. Solution : restreindre le pattern aux balises complètes (`<script`, `<img`, `onerror=`) plutôt qu'au caractère seul.

### CSP absent (BLOC 6)
L'en-tête `Content-Security-Policy` n'est pas ajouté par le proxy. Ajouter dans la config Nginx : `add_header Content-Security-Policy "default-src 'self'; script-src 'self'" always;`

---

## 5. Plan d'action correctif

### Priorité immédiate (avant prochaine session Purple Team)

| # | Action | Fichier à modifier | Impact |
|---|---|---|---|
| 1 | Activer rate limiting sur `/rest/user/login` | `nginx.conf` | Bloque brute force |
| 2 | Corriger routing proxy pour `/rest/products/search` | `nginx.conf` | Active WAF-001 |
| 3 | Ajouter header CSP | `nginx.conf` | Passe BLOC 6 |
| 4 | Affiner règle anti-apostrophe | `modsecurity.conf` | Élimine faux positif |
| 5 | Affiner règle XSS (pattern balise complète) | `modsecurity.conf` | Élimine faux positif review |

### Objectif score Purple Team après correction
Avec ces 5 corrections : **14/16 → 87 %**

---

## 6. Ce qui fonctionne — Points positifs

- **XSS Stored bloqué** sur les deux payloads testés (`<script>` et `onerror`) — la règle WAF-004 est la plus efficace du dispositif
- **Login bypass SQLi bloqué** — WAF-002 fonctionne correctement
- **Trafic légitime majoritairement préservé** — 3/4 tests passent sans faux positif
- **Headers X-Frame-Options et X-Content-Type-Options** présents et corrects
- **Architecture ELK** opérationnelle pour la corrélation des logs

---

## 7. Recommandations supplémentaires

**Court terme (0–30 j)**
- Remplacer le stockage JWT dans `localStorage` par un cookie `HttpOnly` — élimine définitivement le vecteur XSS token theft même si le WAF est contourné
- Activer `Secure` sur tous les cookies
- Corriger l'IDOR au niveau applicatif (`token.userId === requestedId`) — le WAF seul ne suffit pas

**Moyen terme (1–6 mois)**
- Migrer vers des requêtes préparées (ORM/Sequelize) pour éliminer la surface SQLi à la source
- Intégrer OWASP ZAP en mode CI/CD pour détection continue
- Tester les règles WAF avec une suite de régression à chaque modification

**Long terme**
- Pentest externe annuel
- Bug bounty (HackerOne / YesWeHack)
- Zero-trust réseau inter-services Docker (mTLS entre conteneurs)

---

*Rapport corrigé le 16/04/2026 — Blue Team · Red Team vs Blue Team CTF*  
*Score Purple Team mesuré : 9/16 (56 %) — Objectif post-correction : 14/16 (87 %)*
