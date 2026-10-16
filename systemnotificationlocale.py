"""UTF-8 fallbacks; locale tables may override SYSTEM_NOTIFY_* individually."""
import re
import app
import localeInfo

_STRINGS = {
    "TITLE": ("Systémové zprávy", "System messages"),
    "SETTINGS_TITLE": ("Nastavení upozornění", "Notification settings"),
    "WAY": ("Způsob upozornění", "Notification delivery"),
    "SYSTEM": ("Systém", "System"),
    "HUD_COLUMN": ("Odpočtové okno", "Countdown window"),
    "MESSAGE_COLUMN": ("Systémová zpráva", "System message"),
    "BIOLOG": ("Biolog", "Biologist"),
    "DUNGEONS": ("Dungeony", "Dungeons"),
    "SWITCHBOT": ("Switchbot", "Switchbot"),
    "BIO_HINT": ("Další odevzdání", "Next submission"),
    "DUNGEON_HINT": ("Další vstup", "Next entry"),
    "SWITCHBOT_HINT": ("Výsledek přepínání", "Switching result"),
    "ALARM_HINT": ("Biolog a dungeony: jen položky se zapnutým budíkem.",
                   "Biologist and dungeons: only entries with an enabled alarm."),
    "CANCEL": ("Zrušit", "Cancel"),
    "APPLY": ("Použít", "Apply"),
    "HISTORY": ("Historie zpráv", "Message history"),
    "MARK_ALL_READ": ("Přečíst vše", "Read all"),
    "OPEN": ("Otevřít", "Open"),
    "EMPTY": ("Žádné systémové zprávy", "No system messages"),
    "SETTINGS": ("Nastavení", "Settings"),
    "UNREAD": ("Nepřečtené zprávy: %d", "Unread messages: %d"),
    "BELL_HINT": ("Systémové zprávy (%d)", "System messages (%d)"),
    "SAVE_FAILED": ("Nastavení se nepodařilo uložit.", "Could not save settings."),
    "SLOT_FORMAT": ("Pozice %d", "Slot %d"),
    "READY_BIO": ("Můžete znovu odevzdávat.", "You can submit again."),
    "READY_DUNGEON": ("Čekání na další vstup skončilo.", "The entry cooldown has ended."),
    "READY_SWITCHBOT": ("Požadované bonusy nalezeny.", "Requested bonuses found."),
    "SWITCHBOT_RESULT": (
        "Přetáčení bonusů předmětu %s (pozice %d) bylo úspěšně dokončeno.",
        "Bonuschange of %s (Slot: %d) successfully finished."),
    "NAVIGATION": ("Upozornění", "Notifications"),
}


def Text(key):
    czech = app.GetLocalePath().replace("\\", "/").lower().endswith("/cz")
    return getattr(localeInfo, "SYSTEM_NOTIFY_" + key, _STRINGS[key][0 if czech else 1])


def SwitchbotMessage(message):
    """Translate only the known result carried by a typed Switchbot whisper."""
    match = re.fullmatch(r"Bonuschange of (.+) \(Slot: ([1-6])\) successfully finished\.", message)
    if match is None:
        return message
    return Text("SWITCHBOT_RESULT") % (match.group(1), int(match.group(2)))
