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
    "READY_BIO": ("Můžeš znovu odevzdávat.", "You can submit again."),
    "READY_DUNGEON": ("Čekání na další vstup skončilo.", "The entry cooldown has ended."),
    "READY_SWITCHBOT": ("Požadované bonusy nalezeny.", "Requested bonuses found."),
    "SWITCHBOT_RESULT": (
        "Změna bonusů předmětu %s (slot %d) je hotová.",
        "Bonuschange of %s (Slot: %d) successfully finished."),
    "NAVIGATION": ("Upozornění", "Notifications"),
}


def Text(key):
    czech = app.GetLocalePath().replace("\\", "/").lower().endswith("/cz")
    return getattr(localeInfo, "SYSTEM_NOTIFY_" + key, _STRINGS[key][0 if czech else 1])


_SWITCHBOT_RESULT = r"Bonuschange of (.+) \(Slot: ([1-6])\) successfully finished\."


def _PlaceholderName(name):
    return not name.strip() or name.strip().lower() == "noname"


def WithClientItemName(message):
    """Use the client's own item name when the server sent its NoName placeholder.

    The game server names the item from its item_names tables; a VNUM missing
    there arrives as "NoName". The finished item is still in the
    Switchbot slot when the whisper arrives, so the client resolves the name
    the tooltip shows. Call this on receipt only: history keeps the result.
    """
    match = re.fullmatch(_SWITCHBOT_RESULT, message)
    if match is None or not _PlaceholderName(match.group(1)):
        return message
    try:
        import item
        import player
        vnum = player.GetItemIndex(player.SWITCHBOT, int(match.group(2)) - 1)
        if not vnum:
            return message
        item.SelectItem(vnum)
        name = item.GetItemName()
    except Exception:
        return message
    if not name or _PlaceholderName(name):
        return message
    return "Bonuschange of %s (Slot: %s) successfully finished." % (name, match.group(2))


def SwitchbotMessage(message):
    """Translate only the known result carried by a typed Switchbot whisper."""
    match = re.fullmatch(_SWITCHBOT_RESULT, message)
    if match is None:
        return message
    return Text("SWITCHBOT_RESULT") % (match.group(1), int(match.group(2)))
