# Rapport de test d’intrusion — Phase de reconnaissance et d’énumération

## Projet : Red Team vs Blue Team — Application e-commerce

## Cible : OWASP Juice Shop

---

## 1. Introduction

Ce document présente les travaux de reconnaissance et d’énumération réalisés sur l’application OWASP Juice Shop dans un contexte de test en boîte noire. L’objectif de cette phase est d’identifier la surface d’attaque, les composants exposés et les premières failles potentielles exploitables.

---

## 2. Identification de la cible

* URL cible : [http://127.0.0.1:3000](http://127.0.0.1:3000)
* Type : Application web e-commerce
* Contexte : Environnement volontairement vulnérable basé sur les vulnérabilités OWASP Top 10

---

## 3. Identification technologique (Fingerprinting)

### Outil utilisé

* whatweb

### Commande exécutée

```bash
whatweb http://127.0.0.1:3000
```

### Résultat obtenu

```
HTTP 200 OK
HTML5
Script[module]
X-Frame-Options: SAMEORIGIN
```

### Analyse

L’application repose sur une architecture moderne de type Single Page Application. La présence de modules JavaScript suggère l’utilisation probable d’un framework frontend tel qu’Angular.

Le header X-Frame-Options est correctement configuré, ce qui limite les attaques de type clickjacking. Toutefois, plusieurs mécanismes de sécurité essentiels ne sont pas présents.

### Points faibles identifiés

* Absence de Content-Security-Policy (CSP)
* Absence de Strict-Transport-Security (HSTS)

### Conclusion

La configuration de sécurité HTTP est partielle et pourrait être renforcée afin de limiter certains vecteurs d’attaque côté client.

---

## 4. Découverte des ressources (énumération de répertoires)

### Outil utilisé

* gobuster

### Difficulté rencontrée

L’application retourne un code HTTP 200 pour des routes inexistantes, ce qui est caractéristique des applications SPA. Cela rend l’énumération classique inefficace.

### Solution appliquée

Filtrage basé sur la taille des réponses :

```bash
gobuster dir -u http://127.0.0.1:3000 \
-w /usr/share/wordlists/dirb/common.txt \
--exclude-length 75002
```

### Résultats pertinents

| Endpoint    | Code | Observation              |
| ----------- | ---- | ------------------------ |
| /ftp        | 200  | Répertoire accessible    |
| /promotion  | 200  | Contenu public           |
| /robots.txt | 200  | Fichier de configuration |
| /rest       | 500  | Endpoint API             |
| /api        | 500  | Endpoint API             |

### Analyse

Le répertoire /ftp est directement accessible sans authentification. Les endpoints /rest et /api retournent des erreurs serveur, indiquant leur existence et leur rôle probable dans le backend.

---

## 5. Analyse du fichier robots.txt

### Commande exécutée

```bash
curl http://127.0.0.1:3000/robots.txt
```

### Résultat

```
Disallow: /ftp
```

### Analyse

Le fichier robots.txt tente de dissimuler le répertoire /ftp aux moteurs de recherche. Toutefois, ce mécanisme n’apporte aucune protection réelle.

### Conclusion

Le répertoire est accessible publiquement malgré son exclusion, ce qui constitue une mauvaise pratique de sécurité.

---

## 6. Accès à un répertoire sensible

### Accès direct

[http://127.0.0.1:3000/ftp](http://127.0.0.1:3000/ftp)

### Fichiers identifiés

* incident-support.kdbx
* coupons_2013.md.bak
* package.json.bak
* encrypt.pyc
* announcement_encrypted.md

### Analyse

Plusieurs fichiers sensibles sont exposés, notamment :

* fichiers de sauvegarde (.bak)
* base de mots de passe (format KeePass)
* fichiers internes de l’application

### Impact

L’accès à ces fichiers peut permettre :

* la récupération d’informations sensibles
* la préparation d’attaques hors ligne

---

## 7. Exfiltration de données

### Commande exécutée

```bash
curl http://127.0.0.1:3000/ftp/incident-support.kdbx -o incident.kdbx
```

### Résultat

Le fichier KeePass a été téléchargé avec succès.

### Analyse

Ce type de fichier contient généralement des identifiants et mots de passe sensibles.

---

## 8. Analyse des mécanismes de filtrage

### Comportement observé

Le serveur limite l’accès à certains fichiers avec le message :

```
Only .md and .pdf files are allowed
```

### Tests réalisés

* Tentative de contournement via null byte : échec
* Manipulation d’extensions : échec

### Analyse

Le mécanisme de filtrage est présent mais mal implémenté, car des fichiers sensibles restent accessibles.

---

## 9. Analyse des erreurs serveur

### Commande exécutée

```bash
curl http://127.0.0.1:3000/rest
```

### Résultat

Erreur 500 avec affichage de la stack trace.

### Informations révélées

* Framework utilisé : Express
* Chemins internes exposés : /build/routes/fileServer.js

### Impact

Ces informations facilitent la compréhension de l’architecture interne et peuvent être exploitées pour affiner les attaques.

---

## 10. Tentative d’attaque sur la base KeePass

### Extraction du hash

```bash
keepass2john incident.kdbx > hash.txt
```

### Attaque par dictionnaire

```bash
john --wordlist=/usr/share/wordlists/rockyou.txt hash.txt
```

### Résultat

Aucun mot de passe trouvé.

### Analyse

Le mot de passe utilisé est suffisamment robuste pour résister à une attaque par dictionnaire standard.

---

## 11. Analyse des fichiers récupérés

Les fichiers acquisitions.md et legal.md contiennent uniquement du contenu générique sans valeur exploitable.

Le fichier suspicious_errors.yml révèle des erreurs internes déjà observées, confirmant l’exposition d’informations sensibles.

---

## 12. Conclusion

Cette phase a permis d’identifier plusieurs failles importantes :

* Accès non autorisé à des fichiers sensibles
* Exposition d’informations internes via les erreurs serveur
* Mauvaise implémentation des contrôles d’accès

Ces vulnérabilités offrent des opportunités d’exploitation significatives et justifient une analyse approfondie des mécanismes d’authentification et des APIs backend.

---

## 13. Découverte d'un endpoint administratif sensible

### Endpoint identifié

Un endpoint administratif sensible a été identifié :

```
/rest/admin/application-configuration
```

### Analyse du contrôle d'accès

Ce dernier est accessible sans authentification ni contrôle d'accès approprié.

### Données exposées

L'appel à cet endpoint retourne la configuration complète de l'application, incluant :

* Paramètres internes du serveur
* URLs et environnements de développement
* Identifiants liés à des services externes (OAuth)
* Données sensibles liées aux utilisateurs (ex : réponses à des questions de sécurité)

### Impact

Un attaquant non authentifié peut accéder à des informations critiques, facilitant :

* La cartographie de l'infrastructure
* L'exploitation d'autres vulnérabilités
* La compromission de comptes utilisateurs

### Classification

Cette vulnérabilité correspond à un défaut de contrôle d'accès critique (Broken Access Control).

---

## 14. Prochaines étapes

Les étapes suivantes consisteront à approfondir l'analyse des endpoints backend, notamment pour identifier d'autres failles de contrôle d'accès et explorer les données obtenues via `/rest/admin/application-configuration`.

---
