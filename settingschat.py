# -*- coding: utf-8 -*-
"""Chat options of the settings window (settings v5, page "Chat a text"; 2026-10-05).

The compact chat (root/uicompactchat.py; the interface uses it whenever the EXE has chat.GetRecentMessages) keeps its
preferences in memory and saves the whole dict to UserData/compact_chat/<character>.json (debounced 0.3 s). The
settings window therefore changes them only through the LIVE chat window - writing the file would be overwritten:

  chat_font            prefs['font'] 12-18 px            chat.SetAppearance('font', n)
  chat_timestamps      prefs['timestamps']               chat.SetAppearance('timestamps', bool)
  chat_opacity         prefs['opacity'] 0-100 (typing)    chat.SetAppearance('opacity', n)
  chat_idle_opacity    prefs['idle_opacity'] 0-100       chat.SetAppearance('idle_opacity', n)
  chat_filter_<type>   prefs['tabs'][0]['filters']       the main tab "Vše" (types 1-7: local, party, guild, shout,
                                                         system, notices, dice; items / yang never arrive typed)
  pm_<key>             messengerHistory notification preference (badge, sound, toast, preview; native storage)

Without the compact chat (an old EXE) or the messenger history module the rows report unavailable and are disabled;
nothing else changes. What would need C++ or the server is listed in docs/SETTINGS_KIT_LOOK.md
(message types for trade / drops, native fade and line count, history above 300 lines).
"""
FILTER_TYPES = (1, 2, 3, 4, 5, 6, 7)
APPEARANCE = dict(chat_font='font', chat_timestamps='timestamps', chat_opacity='opacity',
                  chat_idle_opacity='idle_opacity')
PM_KEYS = dict(pm_badge='badge', pm_sound='sound', pm_toast='toast', pm_preview='preview')
FILTER_KEYS = dict(('chat_filter_%d' % index, index) for index in FILTER_TYPES)
DEFAULTS = dict(chat_font=13, chat_timestamps=1, chat_opacity=89, chat_idle_opacity=20,
                pm_badge=1, pm_toast=1, pm_sound=0, pm_preview=0)
DEFAULTS.update((key, 1) for key in FILTER_KEYS)
BOUNDS = dict(chat_opacity=(0, 100), chat_idle_opacity=(0, 100))
FONT_SIZES = tuple(range(12, 19))
KEYS = tuple(APPEARANCE) + tuple(FILTER_KEYS) + tuple(PM_KEYS)


def owns(key):
    return key in DEFAULTS


def _history():
    try:
        import messengerHistory
    except ImportError:
        return None
    return messengerHistory


class ChatOptions(object):
    """Reads and changes the chat options on the live chat window of the interface (interface_getter())."""

    def __init__(self, interface_getter, history=None):
        self.interface_getter = interface_getter
        self.history_getter = history or _history

    def chat(self):
        try:
            interface = self.interface_getter()
        except Exception:
            return None
        chat = getattr(interface, 'wndChat', None) if interface else None
        if chat is None or not hasattr(chat, 'SetAppearance') or not isinstance(getattr(chat, 'prefs', None), dict):
            return None
        return chat

    def history(self):
        history = self.history_getter()
        return history if history is not None and hasattr(history, 'SetNotificationPreference') else None

    def available(self, key):
        if key in PM_KEYS:
            return self.history() is not None
        return self.chat() is not None

    def get(self, key):
        try:
            if key in PM_KEYS:
                history = self.history()
                return int(bool(history.GetNotificationPreference(PM_KEYS[key]))) if history else DEFAULTS[key]
            chat = self.chat()
            if chat is None:
                return DEFAULTS[key]
            if key in FILTER_KEYS:
                return int(FILTER_KEYS[key] in chat.prefs['tabs'][0]['filters'])
            value = chat.prefs[APPEARANCE[key]]
            return int(bool(value)) if key == 'chat_timestamps' else int(value)
        except (KeyError, IndexError, TypeError, ValueError, AttributeError):
            return DEFAULTS[key]

    def set(self, key, value):
        """Apply one option; returns True when the live chat / history took it."""
        if key in PM_KEYS:
            history = self.history()
            if history is None:
                return False
            history.SetNotificationPreference(PM_KEYS[key], int(bool(value)))
            chat = self.chat()
            snapshot = getattr(chat, 'settings_notifications', None) if chat else None
            if isinstance(snapshot, dict):
                snapshot[PM_KEYS[key]] = bool(value)
            return True
        chat = self.chat()
        if chat is None:
            return False
        if key in FILTER_KEYS:
            selected = chat.prefs['tabs'][0]['filters']
            index = FILTER_KEYS[key]
            if bool(value) == (index in selected):
                return True
            selected.remove(index) if index in selected else selected.append(index)
            selected.sort()
            for method in ('QueuePreferences', 'RefreshTabs', 'Refresh'):
                if hasattr(chat, method):
                    getattr(chat, method)()
            return True
        if key == 'chat_timestamps':
            value = bool(value)
        elif key == 'chat_font':
            value = max(FONT_SIZES[0], min(FONT_SIZES[-1], int(value)))
        else:
            low, high = BOUNDS[key]
            value = max(low, min(high, int(round(value))))
        chat.SetAppearance(APPEARANCE[key], value)
        return True

    def reset(self, keys):
        for key in keys:
            if owns(key) and self.available(key) and self.get(key) != DEFAULTS[key]:
                self.set(key, DEFAULTS[key])
