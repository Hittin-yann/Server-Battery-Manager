import os
import requests
import subprocess

# --- CONFIGURATION ---
SHELLY_IP = "192.168.1.50"
DISCORD_WEBHOOK_URL = "VOTRE_URL"
MSG_ID_FILE = "./discord_msg_id.txt"

# --- PARAMÈTRE PHYSIQUE ---
CHARGER_WATTAGE = 45  # Puissance nominale du chargeur (Watts)
TARGET_PERCENT = 75   # Seuil d'arrêt de la charge (%)
EFFICIENCY = 0.8      # Rendement estimé du circuit de charge (80%)
TEMP_LIMIT = 75       # Seuil d'alerte surchauffe (°C)

# --- --- FONCTION GET --- ---
def get_sys_value(pattern):
    """ Récupère une valeur via upower (batterie, énergie, etc.) """
    try:
        cmd = f"upower -i $(upower -e | grep 'BAT') | grep -i '{pattern}' | head -n 1 | awk '{{print $2}}'"
        val = subprocess.check_output(cmd, shell=True).decode().strip()
        val = val.replace('%', '').replace(',', '.')
        return float(val) if val else 0.0
    except Exception as e:
        return 0.0

def get_real_consumption():
    """ 
    Calcule la puissance réelle en Watts.
    Si upower renvoie 0, on utilise la formule P = Tension (V) x Courant (A).
    """
    # 1. On tente d'abord la valeur standard
    val = get_sys_value("energy-rate:")
    
    # 2. Si la valeur est nulle (cas typique en charge), on calcule via le kernel
    if val <= 0.1:
        try:
            path = "/sys/class/power_supply/BAT0/"
            # Lecture de la tension (micro-volts) et du courant (micro-ampères)
            with open(path + "voltage_now", "r") as f:
                voltage = float(f.read()) / 1_000_000  # Conversion en Volts
            with open(path + "current_now", "r") as f:
                current = abs(float(f.read())) / 1_000_000  # Conversion en Ampères (valeur absolue)
            
            val = voltage * current  # Loi d'Ohm : P = U * I
        except:
            val = 0.000
            
    return round(val, 3)

def get_temperature():
    """ Récupère la température du CPU via les fichiers système """
    try:
        with open("/sys/class/thermal/thermal_zone3/temp", "r") as f:
            return int(int(f.read()) / 1000)
    except:
        return 0

# --- FONCTION LOGIQUE DE CALCUL ---
def calculate_logic():
    # Récupération des données brutes
    percent = int(get_sys_value("percentage"))
    temp = get_temperature()
    energy_now = get_sys_value("energy:")
    energy_full = get_sys_value("energy-full:")
    
    # On utilise notre nouveau calcul dynamique pour la consommation
    power_draw = get_real_consumption()

    # 1. Vérification du pourcentage cible
    if percent >= TARGET_PERCENT:
        return 0, percent, temp, power_draw, None, "✅"

    # 2. Vérification de l'intégrité de la batterie
    if energy_full <= 0:
        return -1, percent, temp, power_draw, None, "ERREUR: Capacité batterie non lue"

    # 3. CALCUL DYNAMIQUE DU TEMPS DE RECHARGE
    # Énergie manquante en Watt-heures (Wh)
    energy_needed = ((TARGET_PERCENT / 100) * energy_full) - energy_now
    
    # Puissance réellement injectée dans la batterie :
    # (Puissance Chargeur * Rendement) - Consommation réelle du PC
    net_charge_power = (CHARGER_WATTAGE * EFFICIENCY) - power_draw

    # 4. Sécurité : Si le chargeur ne fournit pas assez de jus
    if net_charge_power <= 2:
        return -2, percent, temp, power_draw, None, "ERREUR: Puissance insuffisante"

    # 5. Calcul des minutes (Energie / Puissance * 60)
    raw_minutes = int((energy_needed / net_charge_power) * 60)
    minutes = int(round(raw_minutes / 5) * 5) # pas de 5 minutes
    minutes = max(minutes, 5) # Minimum 5 minutes pour protéger les relais du Shelly
    
    # 6. Détermination visuelle (LED Shelly et Discord)
    if percent <= 30:
        rgb, status = [100, 0, 0], "⚠️ 🔴"
    elif percent <= 50:
        rgb, status = [100, 50, 0], "🟠"
    else:
        rgb, status = [0, 100, 0], "🟢"
        
    return minutes, percent, temp, power_draw, rgb, status

# --- FONCTION SHELLY ---
def control_shelly(minutes, rgb):
    """ Pilote la prise Shelly (Couleur LED + Timer) """
    if minutes == 0 or rgb is None:
        requests.get(f"http://{SHELLY_IP}/rpc/Switch.Set?id=0&on=false")
    else:
        # Mise à jour de la couleur de la LED (Spécifique Gen 3)
        payload = {
            "id": 0,
            "config": {"leds": {"mode": "switch", "colors": {"switch:0": {"on": {"rgb": rgb}, "off": {"rgb": [0,0,0]}}}}}
        }
        try:
            requests.post(f"http://{SHELLY_IP}/rpc/PLUGS_UI.SetConfig", json=payload, timeout=5)
            # Allumage avec auto-off (toggle_after en secondes)
            requests.get(f"http://{SHELLY_IP}/rpc/Switch.Set?id=0&on=true&toggle_after={minutes * 60}", timeout=5)
        except:
            print("Erreur de communication avec le Shelly")

# --- FONCTION DISCORD ---
def update_discord(percent, minutes, temp, consumption, label):
    """ Envoie le rapport sur Discord et nettoie l'ancien message """
    if os.path.exists(MSG_ID_FILE):
        try:
            with open(MSG_ID_FILE, "r") as f:
                old_id = f.read().strip()
                requests.delete(f"{DISCORD_WEBHOOK_URL}/messages/{old_id}", timeout=5)
        except: pass

    temp_emoji = "🔥" if temp > TEMP_LIMIT else "❄️"

    content = (
        f"**📊 Rapport Serveur**\n"
        f"🔋 Batterie : `{percent}%` (Statut: {label})\n"
        f"{temp_emoji} Température : `{temp}°C`\n"
        f"⚡ Conso réelle : `{consumption} Watts`\n"
        f"⏱️ Charge prévue : `{minutes} min`"
    )
    
    try:
        res = requests.post(f"{DISCORD_WEBHOOK_URL}?wait=true", json={"content": content}, timeout=5)
        if res.status_code == 200:
            with open(MSG_ID_FILE, "w") as f:
                f.write(res.json()['id'])
    except:
        print("Erreur d'envoi Discord")

# --- MAIN ---
if __name__ == "__main__":
    mins, per, tmp, cons, rgb_color, status_label = calculate_logic()
    
    if mins < 0:
        # Cas d'erreur : on stoppe la charge par précaution
        control_shelly(0, None)
        update_discord(per, 0, tmp, cons, f"❌ {status_label}")
    else:
        control_shelly(mins, rgb_color)
        update_discord(per, mins, tmp, cons, status_label)