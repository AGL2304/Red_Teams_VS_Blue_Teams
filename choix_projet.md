# Choix de Projet – M1PPAW
**Groupe :** Purple Team  
**Date :** 13 avril 2026  
**Encadrant :**  Jean-Louis Feuvrier LEWENDOWSKI  

---

## 1. Projet Choisi

**PROJET 2 – Red Team vs Blue Team : Audit d'application web e-commerce (SecureShop)**

---

## 2. Arguments Techniques Justifiant le Choix

### Argument 1 : Couverture complète de l'OWASP Top 10
L'application SecureShop est conçue pour embarquer des vulnérabilités intentionnelles couvrant les dix catégories de l'OWASP Top 10 (SQLi, XSS, CSRF, IDOR, file upload, etc.). Il permet d'aborder de façon systématique et exhaustive les classes de vulnérabilités les plus répandues en entreprise.

### Argument 2 : Approche Purple Team (attaque + défense)
Contrairement aux projets 1 et 3, ce projet couvre les deux facettes du métier de cybersécurité : la phase offensive (exploitation, chaining de vulnérabilités) **et** la phase défensive (déploiement d'un WAF, mise en place d'un SIEM avec la stack ELK, threat hunting). Cette dualité correspond directement aux profils "Purple Team" très demandés sur le marché.

### Argument 3 : Pertinence des outils avec l'écosystème professionnel
Les outils mobilisés (Burp Suite, SQLMap, Nikto, ELK Stack, Suricata) sont les standards de l'industrie. Ils sont utilisés quotidiennement dans les ESN de pentest, les équipes SOC et les cellules Purple Team. Cette mission constitue donc une préparation directe aux missions en entreprise et aux certifications GWAPT/eCPPT.

---

## 3. Risques Identifiés et Stratégies de Mitigation

| # | Risque | Impact | Mitigation |
|---|--------|--------|------------|
| 1 | **ELK Stack trop consommateur en ressources** – Elasticsearch peut faire crasher la VM si la RAM est insuffisante | Blocage complet de la phase Blue Team | Allouer au minimum 6 Go de RAM à la VM, utiliser des index Elasticsearch légers, ou remplacer temporairement par Grafana + Loki si nécessaire |
| 2 | **WAF bloquant les tests offensifs avant leur documentation** – Déployer trop tôt les contre-mesures peut empêcher la reproduction des PoC | Impossibilité de valider les vulnérabilités et de rédiger les rapports techniques | Respecter scrupuleusement le séquençage : Red Team **avant** Blue Team. Conserver un snapshot "pré-WAF" permettant de rejouer les exploits à tout moment |

---

## 4. Compétences Mobilisées

| Domaine | Compétences requises |
|---------|----------------------|
| Pentest Web | Injection SQL, XSS (stored/reflected/DOM), CSRF, IDOR, File Upload, session hijacking |
| Outils offensifs | Burp Suite (interception, Intruder, Repeater), SQLMap, Nikto, Gobuster |
| Scripting | Python pour automatisation des tests CSRF/IDOR |
| Blue Team / Défense | Configuration WAF (ModSecurity), IDS/IPS (Suricata), alertes SIEM |
| Analyse de logs | Stack ELK (Elasticsearch, Logstash, Kibana), création de dashboards |
| Forensics | Analyse de fichiers PCAP, corrélation d'événements |
| Documentation | Rédaction de rapports techniques et exécutifs au format OWASP/PTES |

---

## 5. Lacunes Identifiées

- **ELK Stack** : Configuration avancée de Logstash (pipelines, parseurs Grok) à approfondir
- **Suricata** : Écriture de règles de détection custom (syntaxe Snort/Suricata)
- **Chaining de vulnérabilités** : Combiner plusieurs vulnérabilités pour escalader les privilèges (technique avancée, temps d'apprentissage prévu en J3)
- **Bypass de WAF** : Techniques d'encodage, obfuscation de payloads (à étudier en parallèle des tests)



---

## 6. Estimation Macro du Planning

| Phase | Activités | % du temps | Jours |
|-------|-----------|------------|-------|
| Setup & Reconnaissance | Installation VM, outils, analyse initiale de SecureShop | 15 % | J1 |
| Audit offensif (Red Team) | Test OWASP Top 10, documentation des vulnérabilités, PoC | 35 % | J2 – J3 matin |
| Exploitation avancée | Chaining, privilege escalation, extraction de données | 15 % | J3 après-midi |
| Mise en place des défenses (Blue Team) | WAF, IDS, SIEM, threat hunting | 20 % | J4 |
| Consolidation & Rapports | Rapport technique, rapport exécutif, présentation | 15 % | J5 |

---

Purple Team - École IT
