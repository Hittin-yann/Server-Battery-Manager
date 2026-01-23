# 🔋 Server Battery Manager x Shelly Plug S Gen 3

Ce projet permet de piloter intelligemment une prise connectée **Shelly Plug S Gen 3** en fonction du niveau de batterie d'un serveur Ubuntu. Il ajuste la couleur de la LED de la prise, gère un temps de recharge automatique et notifie l'état sur **Discord** en nettoyant les anciens messages.

## 📋 Sommaire
1. [Fonctionnalités](#-fonctionnalités)
2. [Structure du Projet](#-structure-du-projet)
3. [Prérequis](#-prérequis)
4. [Installation](#-installation)
5. [Configuration](#-configuration)
6. [Automatisation (Cron)](#-automatisation-cron)

---

## 🚀 Fonctionnalités

- **Analyse de la batterie** : Récupération du pourcentage via `upower`.
- **Gestion Shelly Gen 3** : 
    - Contrôle des couleurs LED via RPC (HTTP).
    - Allumage avec minuteur de sécurité (`toggle_after`).
- **Logique de Charge** :
    - `> 60%` : Éteint (LED Off).
    - `50–59%` : 15 min (LED Verte 🟢).
    - `40–49%` : 30 min (LED Jaune 🟡).
    - `30–39%` : 45 min (LED Orange 🟠).
    - `< 30%`  : 60 min (LED Rouge 🔴).
- **Notification Discord** :
    - Envoi via Webhook.
    - Suppression automatique du message précédent pour garder un canal propre.

---

## 🏗 Structure du Projet

```text
./
├── battery_manager.py    # Script principal Python
├── discord_msg_id.txt    # Stocke l'ID du dernier message (généré auto)
└── README.md             # Documentation
```

## 🛠 Prérequis
- **Système** : Ubuntu (ou toute distro Linux avec `upower`).

- **Matériel** : Shelly Plug S Gen 3 (avec IP statique).

- **Python** : Version 3.x installée.

- **Dépendances :**

```Bash

pip install requests
```

## 📥 Installation
- **Cloner ou créer le dossier** :

```Bash

mkdir -p ~/scripts/battery-manager
cd ~/scripts/battery-manager
```

- **Créer le script** : Copiez le code Python fourni dans un fichier nommé `battery_manager.py`.

- **Rendre le script exécutable** :

```Bash

chmod +x battery_manager.py
```

## ⚙️ Configuration
Ouvrez `battery_manager.py` et modifiez la section `CONFIGURATION` :

```Python

SHELLY_IP = "192.168.1.50"          # IP de votre Shelly
DISCORD_WEBHOOK_URL = "VOTRE_URL"   # URL Webhook Discord
```

## 🕒 Automatisation (Cron)
Pour respecter la vérification **toutes les 2 heures à la minute 05** (ex: 11h20 -> 13h05), configurez le cron de l'utilisateur :

- Ouvrez l'éditeur cron :

```Bash

crontab -e
```

- Ajoutez la ligne suivante en bas du fichier :

```Extrait de code

5 */2 * * * /usr/bin/python3 /home/VOTRE_USER/scripts/battery-manager/battery_manager.py
```
*Note : Remplacez `VOTRE_USER` par votre nom d'utilisateur Linux.*

## 📊 Schéma Logique

| Batterie | Couleur LED | Temps Charge |
| -------- | ----------- | ------------ |
|   60% +  |   ⚪ Off   |     0 min    |
|  50-59%  |   🟢 Vert	|    15 min    |
|  40-49%  |  🟡 Jaune	|    30 min    |
|  30-39%  |  🟠 Orange	|    45 min    |
|  < 30%   |  🔴 Rouge	|    60 min    |

## 📝 Maintenance
**Logs** : Si vous souhaitez rediriger les erreurs vers un fichier log, modifiez le cron ainsi : ``5 */2 * * * python3 ...py >> /home/user/battery.log 2>&1``

**ID Discord** : Le fichier `discord_msg_id.txt` est créé automatiquement au premier lancement. S'il est supprimé, le script en créera simplement un nouveau sans supprimer le dernier message Discord existant.