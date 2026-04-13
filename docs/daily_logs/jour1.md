# Daily Log - Red Teams VS Blue Teams - Jour 1
**Date :** 2026-04-13
**Durée :** 7h
**Objectif :** Setup environnement + reconnaissance initiale

---

## 1. Environnement VM

| Paramètre | Valeur |
|-----------|--------|
| OS | Kali Linux 2024.x |
| RAM | 19 Go |
| CPU | 4 cœurs |
| Disque libre | 47 Go |
| Réseau | [NAT / Host-Only — à préciser] |

---

## 2. Cibles Déployées

| Application | Port | Statut | Type |
|-------------|------|--------|------|
| Application port 8080 | 8080 | ✅ Live | PHP / Apache |
| Juice Shop | 3000 | ✅ Live | Node.js / Angular |
| VAmPI | 5000 | ✅ Live | API REST Python |
| crAPI | 8888 | ✅ Live | API microservices |

---

## 3. Outils Installés et Validés

- [x] Burp Suite (natif Kali)
- [x] Gobuster 3.8.2
- [x] SQLMap
- [x] Nikto
- [x] Hydra
- [x] Nmap
- [x] Python3 + requests + beautifulsoup4
- [x] SecLists (wordlists)

---

## 4. Reconnaissance — Port 8080

### Commandes exécutées
```bash
gobuster dir -u http://localhost:8080 -w SecLists/Discovery/Web-Content/common.txt -o gobuster_results.txt
curl -s http://localhost:8080/php.ini
curl -s http://localhost:8080/.gitignore
curl -s http://localhost:8080/robots.txt
curl -I http://localhost:8080
```

### Résultats Gobuster

| Route | Code | Taille | Criticité |
|-------|------|--------|-----------|
| `php.ini` | 200 | 148B | 🔴 CRITIQUE |
| `.gitignore` | 200 | 57B | 🟠 HAUTE |
| `/config/` | 301 | - | 🟠 HAUTE |
| `/docs/` | 301 | - | 🟡 MOYENNE |
| `/external/` | 301 | - | 🟡 MOYENNE |
| `phpinfo.php` | 302→login | - | 🟡 MOYENNE |
| `robots.txt` | 200 | 26B | 🟢 INFO |
| `server-status` | 403 | - | 🟢 INFO |

### Découvertes critiques

**php.ini exposé (CRITIQUE)**
- Contenu : [à compléter après curl]
- Impact : Révèle la configuration PHP (extensions, chemins, options de sécurité)
- Référence : OWASP A05:2021 - Security Misconfiguration

**Dépôt Git potentiellement exposé**
- `.gitignore` accessible → tester `/.git/config`, `/.git/HEAD`
- Commande : `curl http://localhost:8080/.git/config`
- Impact potentiel : Accès au code source, historique des commits, secrets

**Répertoire /config/ accessible**
- Contenu : [à compléter après exploration]
- Impact potentiel : Fichiers de configuration avec credentials

---

## 5. Next Steps — Jour 2 (priorités)

1. **Lire le contenu de php.ini** → identifier options dangereuses (allow_url_include, disable_functions)
2. **Tester l'exposition Git** → `curl http://localhost:8080/.git/config`
3. **Explorer /config/** → chercher des credentials en clair
4. **Lancer Nikto** → scan automatique des vulnérabilités
5. **Audit manuel login** → test SQLi sur formulaire de connexion, brute force

---

## 6. Time Tracking

| Activité | Temps |
|----------|-------|
| Setup et déploiement cibles | 2h |
| Clone repos (Juice Shop, VAmPI, crAPI) | 1h |
| Reconnaissance Gobuster | 30min |
| Documentation | 30min |
| **Total** | **4h** |

