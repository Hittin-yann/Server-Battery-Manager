# 🔋 Server Battery & Thermal Manager (Shelly Gen 3)
Ce projet permet de transformer une machine sous Ubuntu Server en un nœud auto-géré. Il optimise la santé de la batterie (maintien à 75%), surveille la température CPU en temps réel et pilote une prise intelligente **Shelly Plug S Gen 3**.

## 🚀 Points forts
- **Calcul Dynamique de Charge** : Le temps de recharge est calculé précisément selon la formule physique $T = \frac{E}{P}$ (Énergie manquante / Puissance nette disponible).

- **Mesure de Consommation Réelle** : Utilise la loi d'Ohm ($P=U×I$) via le kernel Linux pour obtenir les Watts exacts consommés par le PC, même pendant la recharge.

- **Sécurité Thermique "Deep Cool"** : Si le CPU dépasse **75°C**, le script éteint proprement le PC et programme son réveil automatique 30 minutes plus tard via `rtcwake`.

- **Auto-nettoyage Discord** : Supprime automatiquement le message précédent pour garder un canal de log propre.

- **Sécurité Fail-Safe** : En cas d'erreur de lecture des capteurs, la prise est coupée par précaution.

## 🏗 Structure du Projet
```Plaintext
./
├── battery_manager.py    # Script principal Python
├── discord_msg_id.txt    # Stocke l'ID du dernier message (auto-généré)
└── README.md             # Documentation
```

## 🛠 Prérequis
- **OS** : Ubuntu Server (avec `upower` installé).

- **Matériel** : Shelly Plug S Gen 3 (IP statique recommandée).

- **Python** : 3.x + bibliothèque `requests`.

```Bash
pip install requests
```

- **Permissions Sudoers** : Pour permettre l'extinction/réveil sans mot de passe :
    - Tapez `sudo visudo`
    - Ajoutez à la fin : `votre_utilisateur ALL=(ALL) NOPASSWD: /usr/sbin/rtcwake`.

## ⚙️ Configuration du Script
Modifie les constantes au début du fichier `battery_manager.py` pour les adapter à ton matériel :

```Python
CHARGER_WATTAGE = 45  # Puissance de ton chargeur original
TARGET_PERCENT = 75   # Seuil d'arrêt (recommandé pour la longévité)
EFFICIENCY = 0.8      # Rendement du circuit (80%)
TEMP_LIMIT = 75       # Alerte surchauffe
```

## 🕒 Automatisation (Cron)
Pour assurer une gestion fluide, le script est configuré pour s'exécuter toutes les heures paires à la minute 05 (ex: 00h05, 02h05, 04h05...).

1. Ouvrez l'éditeur cron :
```Bash
crontab -e
```

2. Ajoutez la ligne suivante (adaptez le chemin vers votre script) :
```Extrait de code
5 */2 * * * /usr/bin/python3 /home/VOTRE_USER/scripts/battery_manager.py
```

## 📊 Logique Visuelle (Shelly LED)
Le script ajuste la couleur de la LED circulaire de la prise Shelly selon l'état de la batterie :

|   Niveau   |  Couleur LED  |    Statut Discord    |
|:----------:|:-------------:|:---------------------|
|   < 30%    |   🔴 Rouge    |     ⚠️ Critique     |
| 31% - 50%  |	 🟠 Orange   | 	     🟠 Moyen      |
| 51% - 74%  |    🟢 Vert    |      🟢 Optimal     |
|    75% +	 |    ⚪ Off     |   ✅ Chargé / Repos |
| SURCHAUFFE |   🟣 Magenta  |   Shutdown (30 min) |

## 📝 Maintenance
- **Lecture Consommation** : Le script tente de lire `energy-rate` via upower, s'il est à 0 (cas fréquent en charge), il bascule sur le calcul `voltage_now * current_now` dans `/sys/class/power_supply/BAT0/`.

- **Température** : La cible est `thermal_zone3` (x86_pkg_temp) pour refléter la chaleur réelle du cœur processeur.

- **Test de réveil** : Pour tester la sécurité thermique manuellement : `sudo rtcwake -m off -s 60`. Le PC doit s'éteindre et se rallumer après une minute.

- **Relais** : Le temps de charge est arrondi par pas de 5 minutes pour éviter l'usure prématurée du relais de la prise Shelly.