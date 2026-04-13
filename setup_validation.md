# Setup & Validation Environnement – M1PPAW Projet 2
**Groupe :** [Nom du groupe]  
**Date :** 13 avril 2026  
**Projet :** Red Team vs Blue Team – SecureShop

---

## Checklist Globale de Validation

> ✅ Coché = validé avec preuve (screenshot dans `evidence/setup/`)  
> ❌ Non coché = bloquant à résoudre avant de continuer

---

## 1. Machine Virtuelle Créée

| Paramètre | Valeur cible | Valeur réelle | Statut |
|-----------|-------------|---------------|--------|
| Hyperviseur | VMware / VirtualBox / KVM | [à compléter] | ☐ |
| Distribution | Kali Linux 2024.x | [à compléter] | ☐ |
| RAM allouée | ≥ 6 Go (ELK Stack) | [à compléter] | ☐ |
| CPU alloués | ≥ 2 cœurs | [à compléter] | ☐ |
| Espace disque | ≥ 40 Go | [à compléter] | ☐ |

**Commande de vérification :**
```bash
free -h          # Vérifier RAM disponible
nproc            # Vérifier nombre de cœurs
df -h /          # Vérifier espace disque
```

> 📸 Screenshot attendu : capture de `neofetch` ou `uname -a` + `free -h`

---

## 2. Snapshot "Clean Install" Fonctionnel

| Étape | Statut |
|-------|--------|
| Snapshot "Clean_Install" créé avant installation des outils | ☐ |
| Test de restauration effectué (retour au snapshot puis reprise) | ☐ |
| Snapshot "Post_Recon" créé après J1 | ☐ |

**Procédure VirtualBox :**
```bash
# Créer un snapshot depuis l'interface graphique
# Machine > Snapshots > Take Snapshot
# Nom recommandé : "Clean_Install_YYYYMMDD"
```

> 📸 Screenshot attendu : liste des snapshots dans l'interface de l'hyperviseur

---

## 3. Réseau Configuré en Isolation (Host-Only)

| Test | Résultat attendu | Résultat obtenu | Statut |
|------|-----------------|-----------------|--------|
| `ping -c 3 8.8.8.8` | **Échec** (timeout/unreachable) | [à compléter] | ☐ |
| `ping -c 3 google.com` | **Échec** (résolution DNS échoue) | [à compléter] | ☐ |
| `curl -s https://example.com` | **Échec** (connection refused) | [à compléter] | ☐ |
| Accès à SecureShop localhost | **Succès** (HTTP 200) | [à compléter] | ☐ |

**Configuration réseau VM :**
- Mode réseau : `Host-Only` (aucun accès Internet)
- Adresse IP de la VM : `192.168.56.x` (plage Host-Only typique)

```bash
ip a                        # Vérifier l'interface réseau
ping -c 3 8.8.8.8           # Doit échouer
curl http://localhost:8080  # Doit retourner le HTML de SecureShop
```

> ⚠️ **CRITIQUE** : Si le ping 8.8.8.8 réussit, l'isolation n'est pas en place. Ne pas analyser de malware ou lancer d'exploits dans cet état.

> 📸 Screenshot attendu : terminal montrant l'échec du ping et le succès du curl localhost

---

## 4. Outils Installés et Testés

### 4.1 Outils Red Team

| Outil | Version | Test de validation | Statut |
|-------|---------|-------------------|--------|
| Burp Suite Community | Dernière stable | Lancement + interception proxy sur Firefox | ☐ |
| SQLMap | ≥ 1.7 | `sqlmap --version` | ☐ |
| Nikto | ≥ 2.1 | `nikto -h localhost:8080 -maxtime 30s` | ☐ |
| Gobuster | ≥ 3.x | `gobuster version` | ☐ |
| Hydra | Inclus Kali | `hydra -h` | ☐ |
| Python 3 + requests | Python ≥ 3.10 | `python3 -c "import requests; print('OK')"` | ☐ |

```bash
# Installation si manquant
sudo apt update && sudo apt install -y burpsuite sqlmap nikto gobuster hydra python3-pip
pip3 install requests beautifulsoup4
```

### 4.2 Application Cible – SecureShop

| Test | Résultat attendu | Statut |
|------|-----------------|--------|
| `docker ps` montre les conteneurs actifs | SecureShop + DB running | ☐ |
| Navigateur → `http://localhost:8080` | Page d'accueil SecureShop visible | ☐ |
| Burp Suite intercepte une requête vers SecureShop | Requête visible dans l'onglet Proxy | ☐ |

```bash
# Déploiement SecureShop
git clone https://github.com/ecoleit-cyber/secureshop-vulnerable
cd secureshop-vulnerable
docker compose up -d
docker ps   # Vérifier les conteneurs
```

### 4.3 Stack Blue Team – ELK

| Composant | Port | Test | Statut |
|-----------|------|------|--------|
| Elasticsearch | 9200 | `curl http://localhost:9200` → réponse JSON | ☐ |
| Logstash | 5044 | `curl http://localhost:9600` → réponse JSON | ☐ |
| Kibana | 5601 | Navigateur → `http://localhost:5601` → UI visible | ☐ |

```bash
# Démarrage ELK via Docker
docker pull docker.elastic.co/elasticsearch/elasticsearch:8.11.0
docker pull docker.elastic.co/logstash/logstash:8.11.0
docker pull docker.elastic.co/kibana/kibana:8.11.0

# Vérification mémoire (ELK nécessite 6 Go minimum)
docker stats --no-stream
```

> 📸 Screenshot attendu : Kibana accessible sur localhost:5601 (page de login ou dashboard)

### 4.4 Capture Réseau

| Outil | Test | Statut |
|-------|------|--------|
| Wireshark / tcpdump | `sudo tcpdump -i lo port 8080 -c 5` capture des paquets | ☐ |

---

## 5. Structure du Projet

```
~/projet_m1ppaw/
├── docs/               # Documentation et notes
│   └── daily_logs/     # Logs quotidiens (jour1.md, jour2.md...)
├── tools/              # Scripts et outils custom (Python, Bash)
├── evidence/           # Preuves (screenshots, pcaps, logs)
│   └── setup/          # Screenshots de validation du setup
├── reports/            # Rapports intermédiaires et final
│   ├── rapport_technique.md
│   └── rapport_executif.md
└── artifacts/          # Exports (dumps, captures, payloads PoC)
```

**Commande de création :**
```bash
mkdir -p ~/projet_m1ppaw/{docs/daily_logs,tools,evidence/setup,reports,artifacts}
ls -la ~/projet_m1ppaw/
```

> 📸 Screenshot attendu : `tree ~/projet_m1ppaw` ou `ls -R ~/projet_m1ppaw`

---

## Récapitulatif Validation

| Point de contrôle | Statut |
|-------------------|--------|
| VM créée avec ressources suffisantes (≥ 6 Go RAM, ≥ 2 CPU) | ☐ |
| Snapshot "Clean_Install" créé et testé | ☐ |
| Réseau Host-Only – ping Internet = échec | ☐ |
| SecureShop accessible sur localhost:8080 | ☐ |
| Burp Suite intercepte le trafic HTTP | ☐ |
| ELK Stack démarré – Kibana accessible sur localhost:5601 | ☐ |
| Structure de dossiers créée | ☐ |
| Tous les outils Red Team installés et testés | ☐ |

**Validation complète atteinte le :** `___/___/2026 à ___h___`  
**Validé par :** [Nom du membre]

---

*Document rédigé dans le cadre du module M1PPAW – École IT*
