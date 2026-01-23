import os
import requests
import json
import subprocess

# --- CONFIGURATION ---
SHELLY_IP = "192.168.1.50"  # Remplacez par l'IP de votre prise
DISCORD_WEBHOOK_URL = "VOTRE_URL" # Votre URL
MSG_ID_FILE = "./discord_msg_id.txt"

# --- LOGIQUE DE BATTERIE ---
def get_battery_info():
    # Récupère le % via la commande upower
    cmd = "upower -i $(upower -e | grep 'BAT') | grep percentage | awk '{print $2}' | tr -d '%'"
    percent = int(subprocess.check_output(cmd, shell=True).decode().strip())
    return percent

def get_logic(percent):
    if percent >= 60:
        return None, 0, "OFF"
    elif 50 <= percent <= 59:
        return [0, 100, 0], 15, "VERT"   # RGB, Minutes, Nom
    elif 40 <= percent <= 49:
        return [100, 100, 0], 30, "JAUNE"
    elif 30 <= percent <= 39:
        return [100, 50, 0], 45, "ORANGE"
    else:
        return [100, 0, 0], 60, "ROUGE"

# --- ACTIONS ---
def control_shelly(color_rgb, minutes):
    if color_rgb is None:
        # Éteindre la prise et la LED
        requests.get(f"http://{SHELLY_IP}/rpc/Switch.Set?id=0&on=false")
    else:
        # 1. Changer la couleur de la LED (Gen 3)
        payload = {
            "id": 0,
            "config": {"leds": {"mode": "switch", "colors": {"switch:0": {"on": {"rgb": color_rgb}, "off": {"rgb": [0,0,0]}}}}}
        }
        requests.post(f"http://{SHELLY_IP}/rpc/PLUGS_UI.SetConfig", json=payload)
        
        # 2. Allumer la prise avec un timer (Auto-off après X secondes)
        seconds = minutes * 60
        requests.get(f"http://{SHELLY_IP}/rpc/Switch.Set?id=0&on=true&toggle_after={seconds}")

def update_discord(percent, status, minutes):
    # Gestion de l'ancien message
    if os.path.exists(MSG_ID_FILE):
        with open(MSG_ID_FILE, "r") as f:
            old_id = f.read().strip()
            requests.delete(f"{DISCORD_WEBHOOK_URL}/messages/{old_id}")

    # Création du nouveau message
    emoji = "🔋" if percent > 60 else "⚠️"
    content = (
        f"**Rapport Batterie Serveur**\n"
        f"{emoji} Niveau : `{percent}%`\n"
        f"🔴 Statut : `{status}`\n"
        f"⏳ Recharge : `{minutes} min`"
    )
    
    res = requests.post(f"{DISCORD_WEBHOOK_URL}?wait=true", json={"content": content})
    if res.status_code == 200:
        with open(MSG_ID_FILE, "w") as f:
            f.write(res.json()['id'])

# --- EXECUTION ---
if __name__ == "__main__":
    p = get_battery_info()
    rgb, mins, label = get_logic(p)
    control_shelly(rgb, mins)
    update_discord(p, label, mins)