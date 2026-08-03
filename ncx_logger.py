"""
NosTale Discord Logger Standalone
==============================================

Must be run as Administrator (WinDivert requires it).

Install dependencies:
    pip install pydivert noscrypto requests psutil
"""

import time
import psutil
import pydivert
import requests
from datetime import datetime, timedelta
from noscrypto import Client

# ── CONFIG ────────────────────────────────────────────────────────────────────

GAME_EXE = "NostaleClientX.exe"

DISCORD_WEBHOOK_URL = ""

TS_WEBHOOK_URL = ""

ITEM_API_BASE = "https://itempicker.atlagaming.eu/api/items"

LOG_FILE = "packets.log"

# ── FAIRY ITEM IDs ────────────────────────────────────────────────────────────
# Only treated as fairies when e_info type field == 4

FAIRY_VNUMS = {
    800, 801, 802, 803, 804, 920, 425,
    254, 255, 256, 274, 275, 278, 277,
    987, 988, 989, 993,
    4803, 4802, 4804, 4805, 4801, 4800, 4799, 4798, 4807, 4806, 4808, 4809,
    7157,
    4980, 4981, 4983, 4984, 8672, 8673, 8674, 8675,
}

# ── STATE ─────────────────────────────────────────────────────────────────────

ITEM_CACHE = {}

# If the exact same full packet string arrives again within 0.5s, drop it.
_last_packet_str  = None
_last_packet_time = 0.0

# ── RARITY SETTINGS ───────────────────────────────────────────────────────────

RARITY_NAMES = {
    0: "0",
    1: "1 (Useful)",
    2: "2 (Good)",
    3: "3 (High Quality)",
    4: "4 (Excellent)",
    5: "5 (Ancient)",
    6: "6 (Mysterious)",
    7: "7 (Legendary)",
    8: "8 (Phenomenal)"
}

RARITY_COLORS = {
    0: 0xFFFFFF,
    1: 0xC0BDFC,
    2: 0x72FF85,
    3: 0x91CDFF,
    4: 0x0EF902,
    5: 0xF8E2B3,
    6: 0xFEDD02,
    7: 0xB2F304,
    8: 0xFF5E00
}

DEFAULT_ITEM_COLOR = 0x9B59B6
FAIRY_COLOR        = 0xFFB6C1
SPECIALIST_COLOR   = 0xF1C40F

# ── SHELL CATEGORY GROUPS ─────────────────────────────────────────────────────

WEAPON_CATEGORIES = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12}
ARMOR_CATEGORIES  = {13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24}

# ── SHELL GRADE MAPPINGS ──────────────────────────────────────────────────────

SHELL_GRADES = {
    1: "C",  2: "B",  3: "A",  4: "S",
    5: "C",  6: "B",  7: "A",  8: "S",
    9: "C",  10: "B", 11: "A", 12: "S",
    13: "C", 14: "B", 15: "A", 16: "S",
    17: "C", 18: "B", 19: "A", 20: "S",
    21: "C", 22: "B", 23: "A", 24: "S",
}

FAIRY_GRADES = {
    1: "C",
    2: "C",
    3: "B",
    4: "A",
    5: "S",
    15: "S",
}

# ── EFFECT TABLES ─────────────────────────────────────────────────────────────

WEAPON_SHELL_EFFECTS = {
    1:  ("Enhanced Damage", False),
    2:  ("Increased Damage", True),
    3:  ("Minor Bleeding", True),
    4:  ("Bleeding", True),
    5:  ("Heavy Bleeding", True),
    6:  ("Blackout", True),
    7:  ("Freeze", True),
    8:  ("Deadly Blackout", True),
    9:  ("Increased Damage to Plants", True),
    10: ("Increased Damage to Animals", True),
    11: ("Increased Damage to Monsters", True),
    12: ("Increased Damage to Undead", True),
    13: ("Increased Damage to Kovolts, Catsies und Bushtails", True),
    15: ("(Except sticks) Increased Chance of Critical Hit", True),
    16: ("(Except sticks) Increased Critical Damage", True),
    17: ("(Sticks only) Undisturbed When Casting Spells", True),
    18: ("Increased fire element", False),
    19: ("Increased water element", False),
    20: ("Increased light element", False),
    21: ("Increased shadow element", False),
    22: ("Increases all elements", False),
    23: ("Reduced MP Consumption", True),
    24: ("HP-Recovery per Kill", False),
    25: ("MP-Recovery per Kill", False),
    26: ("Increased SL Damage Stats", False),
    27: ("Increased SL Defense Stat", False),
    28: ("Increased SL Property Stat", False),
    29: ("Increased SL Energy Stat", False),
    30: ("Increased Overall SL Stat", False),
    31: ("(Main weapon only) Gain More Gold", True),
    32: ("(Main weapon only) Increased combat EXP", True),
    33: ("(Main weapon only) Increased job EXP", True),
    34: ("Increased Damage in PvP", True),
    35: ("Reduces opponents defence power in PvP", True),
    36: ("Reduced Enemy Fire Resistance in PvP", False),
    37: ("Reduced Enemy Water Resistance in PvP", False),
    38: ("Reduced Enemy Light Resistance in PvP", False),
    39: ("Reduced Enemy Shadow Resistance in PvP", False),
    40: ("Reduced All Enemy Resistances in PvP", False),
    43: ("Reduced Enemy Mana in PvP by X per Hit", False),
}

ARMOR_SHELL_EFFECTS = {
    1:  ("Erhöhte Nahangriffsverteidigung", False),
    2:  ("Erhöhte Fernangriffsverteidigung", False),
    3:  ("Erhöhte Magieverteidigung", False),
    4:  ("Erhöht alle Verteidigungen", True),
    5:  ("Reduziert die Chance auf Leichte Blutung", True),
    6:  ("Reduziert die Chance auf Blutung und Leichte Blutung", True),
    8:  ("Reduziert die Chance auf alle Blutungen", True),
    9:  ("Reduziert die Chance auf alle Blackouts", True),
    10: ("Reduziert die Chance auf Hand des Todes", True),
    11: ("Reduziert die Chance auf Frost", True),
    12: ("Reduziert die Chance auf Erblindung", True),
    15: ("Reduziert die Chance auf Schock", True),
    18: ("Erhöht die HP-Erholungsrate beim Ausruhen", True),
    20: ("Erhöht die MP-Erholungsrate beim Ausruhen", True),
    21: ("Erhöht die natürliche MP-Erholungsrate", True),
    22: ("Regeneriert HP: 20% von x% des erlittenen Schadens", True),
    23: ("Verringert die Chance, einen kritischen Treffer zu erhalten", True),
    24: ("Erhöht die Feuerresistenz um", False),
    25: ("Erhöht die Wasserresistenz um", False),
    26: ("Erhöht die Lichtresistenz um", False),
    27: ("Erhöht die Schattenresistenz um", False),
    30: ("Verringerter Produktionspunkte-Verbrauch", True),
    31: ("Erhalte mehr Minispiel-Belohnungen", True),
    32: ("Erhöhte Itemwiederherstellung", True),
    33: ("Erhöht alle Verteidigungen im PvP", True),
    34: ("Nahangriffe im PvP meiden", True),
    35: ("Fernangriffe im PvP meiden", True),
    36: ("Meidet magischen Schaden im PvP", True),
    37: ("Alle Angriffe im PvP meiden", True),
    38: ("Beschützt vor Mana-Schaden durch Skills", True),
}

FAIRY_SHELL_EFFECTS = {
    1:  ("Erhöht deine HP um", False),
    2:  ("Erhöht deine MP um", False),
    3:  ("Erhöht deine MP um", True),
    4:  ("Reduziert den erlittenen kritischen Schaden um", True),
    5:  ("Wahrsch., krit. Tref. zu erleiden ist um X verringert", True),
    6:  ("Erhöht alle Verteidigungen um", False),
    7:  ("Erhöht den kritischen Schaden um", True),
    8:  ("Erhöht den EXP Gewinn um", True),
    9:  ("Schlechte Effekte bis Lvl 4. verhindern", True),
    10: ("Reduziert den erlittenen Schaden im PvP um", True),
    11: ("Alle Verteidigungen erhöht um", True),
    12: ("Alle Elementresistenzen erhöht um", False),
    13: ("Erhöhte Heldenerfahrung um", True),
    14: ("Erhöht das Element der Fee um", False),
    15: ("Erhöht den Schaden", True),
    16: ("Erhöht die Wahrsch. eines kritischen Treffers um", True),
    17: ("Erhöht den Angriff", False),
}

UTILITY_SHELL_EFFECTS = {}

# ── HELPERS ───────────────────────────────────────────────────────────────────

def timestamp():
    return (datetime.utcnow() + timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")


def get_rarity_color(rarity):
    if rarity is None:
        return DEFAULT_ITEM_COLOR
    return RARITY_COLORS.get(rarity, DEFAULT_ITEM_COLOR)


def log_packet(data: str):
    line = f"[{timestamp()}] {data}\n"
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception as e:
        print(f"[Log] Failed to write: {e}")


def is_duplicate(data: str) -> bool:
    """
    Returns True if this exact packet string was already processed
    within the last 0.5 seconds, indicating a TCP retransmit duplicate.
    """
    global _last_packet_str, _last_packet_time
    now = time.monotonic()
    if data == _last_packet_str and (now - _last_packet_time) < 0.5:
        return True
    _last_packet_str  = data
    _last_packet_time = now
    return False


def discord_post(embed: dict, webhook_url: str = None):
    url = webhook_url or DISCORD_WEBHOOK_URL
    try:
        response = requests.post(url, json={"embeds": [embed]}, timeout=5)
        if response.status_code >= 400:
            print("[Discord ERROR]", response.status_code, response.text)
        response.raise_for_status()
    except Exception as e:
        print(f"[Discord FAIL] {e}")

# ── TIMESPACE ALERTS ──────────────────────────────────────────────────────────

def send_timespace_alert(map_id: int):
    embed = {
        "title": "🖤🪽 Es hat sich ein Timespace in Akt 6 Geöffnet!",
        "color": 0x000000,
        "image": {"url": f"https://itempicker.atlagaming.eu/api/maps/minimap/{map_id}"},
        "footer": {"text": timestamp()}
    }
    try:
        r = requests.post(TS_WEBHOOK_URL, json={"embeds": [embed]}, timeout=5)
        r.raise_for_status()
        print(f"[Timespace] Akt 6 TS | Map {map_id}")
    except Exception as e:
        print(f"[TS Discord FAIL] {e}")


def send_timespace_countdown_alert(map_id: int, minutes: int):
    embed = {
        "title": "⏰ Timespace Ankündigung",
        "description": f"In **{minutes} Minuten** öffnet sich ein Timespace in Akt 6",
        "color": 0x2B2B2B,
        "image": {"url": f"https://itempicker.atlagaming.eu/api/maps/minimap/{map_id}"},
        "footer": {"text": timestamp()}
    }
    try:
        r = requests.post(TS_WEBHOOK_URL, json={"embeds": [embed]}, timeout=5)
        r.raise_for_status()
        print(f"[Timespace Countdown] Map {map_id} in {minutes} min")
    except Exception as e:
        print(f"[TS Countdown FAIL] {e}")

# ── ITEM API ──────────────────────────────────────────────────────────────────

def get_item_data(vnum: int):
    if vnum in ITEM_CACHE:
        return ITEM_CACHE[vnum]
    try:
        r = requests.get(f"{ITEM_API_BASE}/data/{vnum}", timeout=5)
        if r.status_code != 200:
            return None
        data = r.json()
        ITEM_CACHE[vnum] = data
        return data
    except Exception as e:
        print(f"[ItemAPI] {e}")
        return None


def resolve_item_name(vnum: int):
    item = get_item_data(vnum)
    if not item:
        return f"Unknown Item ({vnum})"
    name = item.get("name")
    if isinstance(name, dict):
        return name.get("de") or name.get("en") or next((v for v in name.values() if v), f"Item {vnum}")
    if isinstance(name, str):
        return name
    return f"Unknown Item ({vnum})"


def get_icon(vnum: int):
    return f"{ITEM_API_BASE}/icon/{vnum}"

# ── PARSERS ───────────────────────────────────────────────────────────────────

def parse_sayt(packet: str):
    parts = packet.split(" ", 5)
    if len(parts) < 6:
        return None
    return {"player": parts[4], "message": parts[5]}


def parse_sayitemt(packet: str):
    """Parse the sayitemt prefix (before e_info / slinfo / IconInfo)."""
    parts = packet.split()
    try:
        item_id = int(parts[5])
        player  = parts[6]
        message_parts = []
        for part in parts[7:]:
            if part in ("e_info", "IconInfo", "slinfo"):
                break
            message_parts.append(part)
        return {"item_id": item_id, "player": player, "message": " ".join(message_parts)}
    except Exception as e:
        print(f"[Parser] sayitemt failed: {e}")
        return None


def parse_shell(shell_str: str, effect_table: dict):
    """
    Parse an equipment shell string: category.effect_id.value.upgrade
    e.g. '1.16.40.-2'
    """
    try:
        parts = shell_str.split(".")
        if len(parts) != 4:
            return None
        category  = int(parts[0])
        effect_id = int(parts[1])
        value     = int(parts[2])
        upgrade   = abs(int(parts[3]))
        grade = SHELL_GRADES.get(category, "?")
        effect_data = effect_table.get(effect_id)
        if effect_data:
            effect_name, uses_percent = effect_data
        else:
            effect_name = f"Effekt {effect_id}"
            uses_percent = False
        return {
            "grade": grade,
            "effect_name": effect_name,
            "value": value,
            "upgrade": upgrade,
            "uses_percent": uses_percent,
        }
    except Exception as e:
        print(f"[Shell Parser] Failed on '{shell_str}': {e}")
        return None


def parse_fairy_shell(shell_str: str):
    """
    Parse a fairy shell string: category.effect_id.value  (3 parts, no upgrade)
    """
    try:
        parts = shell_str.split(".")
        if len(parts) != 3:
            return None
        category  = int(parts[0])
        effect_id = int(parts[1])
        value     = int(parts[2])
        grade = FAIRY_GRADES.get(category, f"Cat{category}")
        effect_data = FAIRY_SHELL_EFFECTS.get(effect_id)
        if effect_data:
            effect_name, uses_percent = effect_data
        else:
            effect_name = f"Effekt {effect_id}"
            uses_percent = False
        return {
            "grade":        grade,
            "effect_name":  effect_name,
            "value":        value,
            "upgrade":      0,
            "uses_percent": uses_percent,
        }
    except Exception as e:
        print(f"[Fairy Shell Parser] Failed on '{shell_str}': {e}")
        return None


def parse_e_info(packet: str):
    """
    Parse a standard equipment e_info packet.
    Shell strings have 4 dot-separated parts: category.effect_id.value.upgrade
    """
    parts = packet.split()
    try:
        item_vnum = int(parts[2])
        rarity    = int(parts[3])
        upgrade   = int(parts[4])
        try:
            champion_level = int(parts[6])
        except (IndexError, ValueError):
            champion_level = 0

        shells = []
        for p in parts:
            if p.count(".") == 3:
                try:
                    category = int(p.split(".")[0])
                except Exception:
                    continue
                if category in WEAPON_CATEGORIES:
                    table = WEAPON_SHELL_EFFECTS
                elif category in ARMOR_CATEGORIES:
                    table = ARMOR_SHELL_EFFECTS
                else:
                    table = UTILITY_SHELL_EFFECTS
                shell = parse_shell(p, table)
                if shell:
                    shells.append(shell)

        return {
            "item_vnum": item_vnum,
            "rarity": rarity,
            "upgrade": upgrade,
            "champion_level": champion_level,
            "shells": shells,
        }
    except Exception as e:
        print(f"[Parser] e_info failed: {e} | {packet}")
        return None


def parse_fairy_e_info(packet: str):
    """
    Parse a fairy e_info packet (type field == 4).
    element=[3], pct=[4]
    Shells are 3-part: category.effect_id.value
    Upgrade is the integer directly before the first shell string (0 if no shells).
    """
    parts = packet.split()
    try:
        item_vnum = int(parts[2])
        element   = int(parts[3])
        fairy_pct = int(parts[4])

        dot_parts = [p for p in parts if p.count(".") == 2]
        upgrade = 0
        if dot_parts:
            first_idx = parts.index(dot_parts[0])
            try:
                upgrade = int(parts[first_idx - 1])
            except (ValueError, IndexError):
                upgrade = 0

        shells = [s for s in (parse_fairy_shell(p) for p in dot_parts) if s]

        return {
            "item_vnum": item_vnum,
            "element":   element,
            "fairy_pct": fairy_pct,
            "upgrade":   upgrade,
            "shells":    shells,
        }
    except Exception as e:
        print(f"[Parser] fairy e_info failed: {e}")
        return None


def parse_slinfo(packet: str):
    """
    [2] vnum, [4] joblevel, [28] upgrade, [36] perfection
    [37] atk, [38] def, [39] ele, [40] hp
    """
    parts = packet.split()
    try:
        return {
            "vnum":       int(parts[2]),
            "joblevel":   int(parts[4]),
            "upgrade":    int(parts[28]),
            "perfection": int(parts[36]),
            "atk":        int(parts[37]),
            "def":        int(parts[38]),
            "ele":        int(parts[39]),
            "hp":         int(parts[40]),
        }
    except Exception as e:
        print(f"[Parser] slinfo failed: {e} | {packet}")
        return None


def parse_cardholder_e_info(packet: str):
    """
    [4] sp_vnum, [5] joblevel, [8] upgrade
    [14] perfection, [19] atk, [20] def, [21] ele, [22] hp
    """
    parts = packet.split()
    try:
        return {
            "vnum":       int(parts[4]),
            "joblevel":   int(parts[5]),
            "upgrade":    int(parts[8]),
            "perfection": int(parts[14]) if len(parts) > 14 else 0,
            "atk":        int(parts[19]) if len(parts) > 19 else 0,
            "def":        int(parts[20]) if len(parts) > 20 else 0,
            "ele":        int(parts[21]) if len(parts) > 21 else 0,
            "hp":         int(parts[22]) if len(parts) > 22 else 0,
        }
    except Exception as e:
        print(f"[Parser] cardholder e_info failed: {e} | {packet}")
        return None

# ── ELEMENT NAMES ─────────────────────────────────────────────────────────────

ELEMENT_NAMES = {
    1: "🔥 Feuer",
    2: "💧 Wasser",
    3: "☀️ Licht",
    4: "🌑 Schatten",
}

def element_name(element_id: int) -> str:
    return ELEMENT_NAMES.get(element_id, f"Element {element_id}")

# ── FORMATTERS ────────────────────────────────────────────────────────────────

def shell_text(shells):
    if not shells:
        return "Keine"
    lines = []
    for shell in shells:
        value_text = str(shell["value"])
        if shell["uses_percent"]:
            value_text += "%"
        line = f"[{shell['grade']}] {shell['effect_name']}: {value_text}"
        if shell.get("upgrade", 0) > 0:
            line += f" (+{shell['upgrade']})"
        lines.append(line)
    return "\n".join(lines)[:1000]

# ── DISCORD SENDERS ───────────────────────────────────────────────────────────

def send_sayt(player: str, message: str):
    embed = {
        "title": f"📢 {player}",
        "description": str(message)[:4000],
        "color": 0x5865F2,
        "footer": {"text": timestamp()}
    }
    discord_post(embed)
    print(f"[Discord] SAYT | {player}")


def send_item(player, item_name, item_id, message, rarity=None, upgrade=0, champion_level=0, shells=None):
    cleaned_message = str(message).replace("|", " ").replace("{%s}", f"**{item_name}**")[:4000]
    fields = [{"name": "Item", "value": str(item_name), "inline": False}]
    if rarity is not None:
        fields.append({"name": "Rare", "value": RARITY_NAMES.get(rarity, str(rarity)), "inline": True})
    if upgrade > 0:
        fields.append({"name": "Upgrade", "value": f"+{upgrade}", "inline": True})
    if champion_level > 0:
        fields.append({"name": "Heldenlevel", "value": str(champion_level), "inline": True})
    if shells:
        fields.append({"name": "Muschel Effekte", "value": shell_text(shells), "inline": False})
    fields.append({"name": "Item ID", "value": str(item_id), "inline": False})
    embed = {
        "title": f"🛒 {player}",
        "description": cleaned_message,
        "color": get_rarity_color(rarity),
        "thumbnail": {"url": get_icon(item_id)},
        "fields": fields,
        "footer": {"text": timestamp()}
    }
    discord_post(embed)
    print(f"[Discord] ITEM | {player} | {item_name}")


def send_fairy(player, item_name, item_id, message, element, fairy_pct, upgrade, shells=None):
    cleaned_message = str(message).replace("|", " ").replace("{%s}", f"**{item_name}**")[:4000]
    fields = [
        {"name": "Fee",     "value": str(item_name),        "inline": False},
        {"name": "Element", "value": element_name(element), "inline": True},
        {"name": "Fee %",   "value": f"{fairy_pct}%",       "inline": True},
        {"name": "Upgrade", "value": f"+{upgrade}",         "inline": True},
    ]
    if shells:
        fields.append({"name": "Muschel Effekte", "value": shell_text(shells), "inline": False})
    fields.append({"name": "Item ID", "value": str(item_id), "inline": False})
    embed = {
        "title": f"🧚 {player}",
        "description": cleaned_message,
        "color": FAIRY_COLOR,
        "thumbnail": {"url": get_icon(item_id)},
        "fields": fields,
        "footer": {"text": timestamp()}
    }
    discord_post(embed)
    print(f"[Discord] FAIRY | {player} | {item_name} | {fairy_pct}% +{upgrade}")


def send_specialist(player, item_name, item_id, message, sp):
    cleaned_message = str(message).replace("|", " ").replace("{%s}", f"**{item_name}**")[:4000]
    fields = [
        {"name": "Spezialkarte", "value": str(item_name),         "inline": False},
        {"name": "Joblevel",     "value": str(sp["joblevel"]),    "inline": True},
        {"name": "Upgrade",      "value": f"+{sp['upgrade']}",    "inline": True},
        {"name": "Perfektion",   "value": f"{sp['perfection']}", "inline": True},
        {"name": "Angriff / Verteidigung / Element / HP",
         "value": f"{sp['atk']} / {sp['def']} / {sp['ele']} / {sp['hp']}",
         "inline": False},
        {"name": "Item ID",      "value": str(item_id),           "inline": False},
    ]
    embed = {
        "title": f"🃏 {player}",
        "description": cleaned_message,
        "color": SPECIALIST_COLOR,
        "thumbnail": {"url": get_icon(item_id)},
        "fields": fields,
        "footer": {"text": timestamp()}
    }
    discord_post(embed)
    print(f"[Discord] SP | {player} | {item_name} | Joblv{sp['joblevel']} +{sp['upgrade']} {sp['perfection']}%")

# ── PACKET HANDLER ────────────────────────────────────────────────────────────

def handle_recv(data: str):

    # ── ACT 6 TIMESPACE ──────────────────────────────────────────────────────
    if data.startswith("guri 34 "):
        parts = data.split()
        if len(parts) >= 3:
            try:
                send_timespace_alert(int(parts[2]))
            except Exception as e:
                print(f"[TS Parser] {e}")
        return

    # ── ACT 6 TIMESPACE COUNTDOWN ────────────────────────────────────────────
    if data.startswith("guri 32 "):
        parts = data.split()
        if len(parts) >= 4:
            try:
                send_timespace_countdown_alert(int(parts[3]), int(parts[2]))
            except Exception:
                pass
        return

    # ── SAYT ─────────────────────────────────────────────────────────────────
    if data.startswith("sayt "):
        if is_duplicate(data):
            return
        log_packet(data)
        parsed = parse_sayt(data)
        if parsed:
            send_sayt(parsed["player"], parsed["message"])
        return

    # ── SAYITEMT ─────────────────────────────────────────────────────────────
    if data.startswith("sayitemt "):
        if is_duplicate(data):
            return
        log_packet(data)

        # ── Equipment with e_info ─────────────────────────────────────────
        if " e_info " in data:
            say_part, e_part = data.split(" e_info ", 1)
            e_info_full = "e_info " + e_part
            e_parts     = e_info_full.split()
            say_data    = parse_sayitemt(say_part)
            if not say_data:
                return

            e_type = int(e_parts[1]) if len(e_parts) > 1 else -1

            if e_type == 7:
                sp = parse_cardholder_e_info(e_info_full)
                if not sp:
                    return
                send_specialist(
                    player=say_data["player"],
                    item_name=resolve_item_name(sp["vnum"]),
                    item_id=sp["vnum"],
                    message=say_data["message"],
                    sp=sp,
                )
                return

            if e_type == 4 and say_data["item_id"] in FAIRY_VNUMS:
                fairy = parse_fairy_e_info(e_info_full)
                if not fairy:
                    return
                send_fairy(
                    player=say_data["player"],
                    item_name=resolve_item_name(fairy["item_vnum"]),
                    item_id=fairy["item_vnum"],
                    message=say_data["message"],
                    element=fairy["element"],
                    fairy_pct=fairy["fairy_pct"],
                    upgrade=fairy["upgrade"],
                    shells=fairy["shells"],
                )
                return

            e_info = parse_e_info(e_info_full)
            if not e_info:
                return
            send_item(
                player=say_data["player"],
                item_name=resolve_item_name(e_info["item_vnum"]),
                item_id=e_info["item_vnum"],
                message=say_data["message"],
                rarity=e_info["rarity"],
                upgrade=e_info["upgrade"],
                champion_level=e_info["champion_level"],
                shells=e_info["shells"],
            )

        # ── Specialist card with slinfo ────────────────────────────────────
        elif " slinfo " in data:
            say_part, sl_part = data.split(" slinfo ", 1)
            say_data = parse_sayitemt(say_part)
            sp = parse_slinfo("slinfo " + sl_part)
            if not say_data or not sp:
                return
            send_specialist(
                player=say_data["player"],
                item_name=resolve_item_name(sp["vnum"]),
                item_id=sp["vnum"],
                message=say_data["message"],
                sp=sp,
            )

        # ── Non-equipment with IconInfo ────────────────────────────────────
        elif " IconInfo " in data:
            say_data = parse_sayitemt(data)
            if not say_data:
                return
            send_item(
                player=say_data["player"],
                item_name=resolve_item_name(say_data["item_id"]),
                item_id=say_data["item_id"],
                message=say_data["message"],
                rarity=None,
            )

# ── SNIFFER ───────────────────────────────────────────────────────────────────

def get_game_port() -> int | None:
    """Find the remote port the game client is connected to."""
    for proc in psutil.process_iter(["name", "pid"]):
        try:
            if not proc.info["name"]:
                continue
            if GAME_EXE.lower() not in proc.info["name"].lower():
                continue
            try:
                conns = proc.net_connections()
            except AttributeError:
                conns = proc.connections()
            for conn in conns:
                if conn.status == "ESTABLISHED" and conn.raddr:
                    print(f"[Sniffer] Found {GAME_EXE} -> {conn.raddr.ip}:{conn.raddr.port}")
                    return conn.raddr.port
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return None


def decrypt_server_packet(raw: bytes) -> list[str]:
    """Split raw TCP payload on 0xFF and decrypt each chunk."""
    results = []
    for chunk in raw.split(b"\xff"):
        if not chunk:
            continue
        try:
            decrypted = Client.WorldDecrypt(chunk)
            text = decrypted.decode("cp1252", errors="replace").strip()
            if text:
                results.append(text)
        except Exception:
            pass
    return results


def run():
    print(f"[Sniffer] Looking for {GAME_EXE}...")
    server_port = get_game_port()

    if not server_port:
        print(f"[Sniffer] Could not find {GAME_EXE} running with an active connection.")
        print("          Make sure the game is open and logged in, then run this script again.")
        return

    divert_filter = f"tcp.SrcPort == {server_port} and inbound"
    print(f"[Sniffer] Capturing inbound packets from port {server_port}...")
    print("[Sniffer] Press Ctrl+C to stop.\n")

    with pydivert.WinDivert(divert_filter) as w:
        for packet in w:
            w.send(packet)
            payload = packet.tcp.payload
            if not payload:
                continue
            for line in decrypt_server_packet(bytes(payload)):
                for packet_str in line.split("\n"):
                    packet_str = packet_str.strip()
                    if packet_str:
                        handle_recv(packet_str)


if __name__ == "__main__":
    run()