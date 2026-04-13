# Daily Log - M1PPAW Projet 2 Red/Blue Team - Jour 1
**Date :** 13/04/2026
**Durée :** 7h
**Objectif du jour :** Setup environnement + première reconnaissance

---

## Setup Environnement

### Configuration Machine
- **OS :** Windows 10 (26200.8037)
- **RAM :** 7.5GB
- **Docker :** v29.0.1
- **WSL2 :** activé (backend Docker)

### Outils Installés
- [x] Docker Desktop 29.0.1 (testé avec `docker --version`)
- [x] Python 3.14.0 (testé avec `python --version`)
- [x] Juice Shop déployé sur http://localhost:3000
- [x] Elasticsearch 8.13.0 (port 9200)
- [x] Kibana 8.13.0 (port 5601)
- [x] Filebeat 8.13.0 (collecte logs Juice Shop)
- [x] Logstash 8.13.0
- [x] Installation de Burn Suite
- [x] Scripts de monitoring et d'alertes + generation de rapport d'incident
- [x] Développer scripts Python d'énumération automatisée
- [x] Création de règles de détection KQL dans Kibana
- [x] Création de dashboard Kibana


### Problèmes Rencontrés
- Port 3000 déjà occupé → solution : `docker rm juice-shop` puis relance sur port 3001
- Wazuh incompatible ARM64 → solution : ELK Stack seul suffisant
- Image Wazuh 5.0.0 inexistante → solution : downgrade vers 4.7.4

---

## Première Reconnaissance Juice Shop

### Technologies détectées
- Frontend : Angular
- Backend : Node.js
- Base de données : SQLite
- 100+ challenges de sécurité intégrés

### Prochaines étapes Jour 2
1. Audit OWASP Top 10 sur Juice Shop avec Burp Suite
2. Création de règles de détection avancée (force brute)

---

## Time Tracking
- Setup Docker + conteneurs : 3h
- Configuration ELK Stack : 2h
- Tests et validation : 1h
- Documentation : 1h
**Total :** 7h