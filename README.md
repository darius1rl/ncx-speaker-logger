# NosTale Discord Logger ![speaker image](/img/speaker)

A standalone packet Logger for **NosTale** that captures trade chat and item links in real time and forwards them to a Discord channel via webhook.

---

## Features

- **sayt** - captures all global chat messages and posts them to Discord
- **sayitemt** - captures item links with full details:
  - Equipment with rarity, upgrade, champion level and shell effects
  - Fairies with element, %, upgrade and fairy-specific shell effects
  - Specialist cards (slinfo) with joblevel, upgrade, perfection and stat points
  - Specialist cards inside card holders
  - Non-equipment items (IconInfo)
- **Timespace alerts** - notifies a separate webhook when an Act 6 Timespace opens or is announced
- **Packet log** - all captured packets are written to `packets.log` for offline review and troubleshooting
- Duplicate / TCP retransmit protection - the same packet arriving twice within 0.5s is silently dropped
- Player names with special characters (`»`, `«`, `×`, `–` etc.) are preserved correctly
- Item names and icons fetched automatically from the [AtlaGaming Item API](https://itempicker.atlagaming.eu)

---

## Requirements

- Windows (WinDivert requires it)
- Python 3.10+
- **Must be run as Administrator**

---

## Installation

**1. Install Python**

Download and install Python 3.10 or newer from https://python.org/downloads.
Make sure to check **"Add Python to PATH"** during installation.

**2. Install dependencies**

Open Command Prompt as Administrator and run:

```
pip install pydivert noscrypto requests psutil
```

**3. Download the script**

Download `ncx_logger.py` from the [Releases](../../releases) page and place it in a folder of your choice, e.g. `C:\NosTaleLogger\`.

---

## Configuration

Open `ncx_logger.py` in a text editor and set the following values near the top of the file:

| Variable | Description |
|---|---|
| `GAME_EXE` | Name of the NosTale executable (default: `NostaleClientX.exe`) |
| `DISCORD_WEBHOOK_URL` | Webhook URL for item and chat notifications |
| `TS_WEBHOOK_URL` | Webhook URL for Act 6 Timespace alerts (can be the same as above) |

To create a Discord webhook: go to your channel → **Edit Channel** → **Integrations** → **Webhooks** → **New Webhook** → **Copy Webhook URL**.

---

## Usage

1. Start NosTale and log in with your character
2. Open Command Prompt **as Administrator**
3. Navigate to the script folder and run:

```
python ncx_logger.py
```

The script will automatically find the running game client, detect the server port and start capturing. Press `Ctrl+C` to stop cleanly.

---

## How It Works

NosTale traffic between the game client and server is encrypted. This tool uses [WinDivert](https://reqrypt.org/windivert.html) (via `pydivert`) to intercept inbound TCP packets at the network driver level, decrypts them using the [`noscrypto`](https://pypi.org/project/noscrypto/) library, and parses the relevant packet types. Packets are re-injected immediately so the game client receives everything normally - nothing is blocked or modified.

---

## Known Issues

- **Fairy Beads** are broken and not displayed correctly
- **Partners, Partner Specialists and Partner Card Holders** are not supported and will not be sent to Discord
- **Pets** are broken and may display as random unrelated items
- **Accessories** are broken and not displayed correctly
- **Limited items** show as missing (no name or icon available from the item API)
- **Some Fairy VNUMs** are not yet defined - unknown fairies will fall through to the generic item handler
- **Translation to English** is still ongoing - most labels and shell effect names are currently in German

---

## Shell Effects

Shell effects for weapons, armor and fairies are looked up from built-in tables. If an unknown effect ID is encountered it will be displayed as `Effekt <id>` so no data is silently lost. You can add missing entries to the `WEAPON_SHELL_EFFECTS`, `ARMOR_SHELL_EFFECTS` or `FAIRY_SHELL_EFFECTS` dictionaries in the script.

---

## Disclaimer

This tool passively reads network traffic produced by your own game client. It does not modify, inject or automate any game actions. Use at your own risk and in accordance with the game's terms of service.
