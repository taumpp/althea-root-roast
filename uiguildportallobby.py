# -*- coding: utf-8 -*-
"""Lobby of the guild portal (owner 12. 10. 2026): a guild finds the portal, the portal is locked to that guild for
10 minutes, at least 3 members with level 75+ join, the leader or the council (Vůdce / Rada, the ranks of the guild
window) starts the entry and every joined member is moved into the crypt.

Built ONLY from the R1 components of the guild window (root/uiguildv2widgets.py, the approved R1 market layout of
root/uiguildv2r1.py): Canvas.shell = uir1.Chrome (frame, Cinzel header with the vein, the X), uir1.Frame "panel"
for the content panel, the band surface of the guild content panel, Canvas.gauge (the R1 red gauge of the guild
level), Canvas.table_header + ScrollList (the member table with uir1.ScrollBar), Canvas.button (uir1.Button
primary) and Canvas.action (R1Action = uir1.Button secondary), lock_image (the padlock of the locked guild
features) and the guild palette / fonts. Nothing is drawn by this module itself. "Starý vzhled" draws the same page
code with the old guild art (the primitives switch on uiguildv2widgets.R1).

Server -> client (quest cmdchat, root/game.py serverCommandList -> PortalController):
  GuildPortalQuest <questIndex>
  GuildPortalLobby <portalId> <element> <mapIndex> <channel> <lockLeftSec> <joined> <need> <canJoin> <isJoined>
                   <canStart> <pids|-> <guildName_with_underscores>
  GuildPortalLobbyOpen
  GuildPortalPopup <element> <finderName> <joined> <need> <lockLeftSec> <canJoin>
  GuildPortalLobbyClose <STARTED|FAILED|EXPIRED|TAKEN>
  guild_portal_cmd            -> net.SendQuestInputStringPacket("<JOIN|LEAVE|START|OPEN>#<portalId>")
Client -> server: a button stores the pending action and calls event.QuestButtonClick(questIndex), exactly like the
dungeon rejoin offer (game.py __DungeonRejoinRespond / __DungeonRejoinQuestCMD).

<pids> is a comma list of the joined members; an entry may be "pid" or "pid:mapIndex:channel" (where the member is,
the column "Kde je"). The names, levels, ranks and the online flag come from the client guild model
(guildv2model.Model of the guild window); an unknown PID is shown as "?"."""
import app
import fontconfig
import ui

try:
    import uir1         # the R1 look of the guild primitives (uiguildv2widgets.R1); measured text widths
except Exception:
    uir1 = None

import uiguildv2widgets as widgets
from uiguildv2widgets import (Canvas, ScrollList, INK, DIM, GOLD, GREEN, MUTED, ROLE_CAPTION, lock_image, px, span)

MIN_LEVEL = 75
ELEMENTS = ((u"Ledový", u"ledový", u"Ledový živelný golem"), (u"Ohnivý", u"ohnivý", u"Ohnivý živelný golem"),
    (u"Zemní", u"zemní", u"Zemní živelný golem"))
ACTIONS = ("JOIN", "LEAVE", "START", "OPEN")
CLOSE_REASONS = {"STARTED": u"Vstup do krypty byl spuštěn.", "FAILED": u"Vstup do krypty se nepodařil.",
    "EXPIRED": u"Lobby portálu vypršelo, portál je znovu volný.", "TAKEN": u"Portál už drží jiný cech."}
ROLES = (u"Vůdce", u"Rada", u"Člen")
PENDING_TIMEOUT = 5.0

# Layout in the design units of the guild window (uiguildv2widgets.SCALE): the window is 760 x 522 units = 593 x 407 px.
WIDTH, HEIGHT = 760, 522
PANEL_X, PANEL_Y = 18, 46
PAD = 16
BAND_H = 40
SURFACE, EDGE = 0xff161516, 0xff2c2829          # the band surface of the guild content panel (uiguildv2r1)
ROW = 36
VISIBLE_ROWS = 5
LOCKED_TEXT = u"Zamčeno – potřebuješ úroveň %d" % MIN_LEVEL


def clock(seconds):
    seconds = max(0, int(seconds + 0.999))
    return "%d:%02d" % (seconds // 60, seconds % 60)


def _int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def element(index):
    index = _int(index)
    return ELEMENTS[index] if 0 <= index < len(ELEMENTS) else (u"?", u"?", u"?")


def map_name(index):
    try:
        import localeInfo
        name = getattr(localeInfo, "MINIMAP_ZONE_NAME_DICT_BY_IDX", {}).get(int(index))
        if name:
            return name
    except Exception:
        pass
    return u"mapa %s" % index


def parse_pids(text):
    """'1,2:408:1' -> [(1, None, None), (2, 408, 1)]; '-' or '' -> []."""
    result = []
    if not text or text == "-":
        return result
    for entry in text.split(","):
        parts = entry.split(":")
        pid = _int(parts[0], -1)
        if pid <= 0:
            continue
        where = (_int(parts[1]), _int(parts[2])) if len(parts) >= 3 else (None, None)
        result.append((pid,) + where)
    return result


def players(n):
    """Czech plural of "hráč": 1 hráč, 2-4 hráči, 0 and 5+ hráčů."""
    return u"hráč" if n == 1 else (u"hráči" if 2 <= n <= 4 else u"hráčů")


def joined_verb(n):
    """Agreement with "hráč": bude připojen 1 hráč, budou připojeni 2-4 hráči, bude připojeno 5+ hráčů."""
    return u"bude připojen" if n == 1 else (u"budou připojeni" if 2 <= n <= 4 else u"bude připojeno")


def parse_lobby(portal, elem, map_index, channel, left, joined, need, can_join, is_joined, can_start, pids, guild):
    """The fields of GuildPortalLobby as a state dict (None when a number is broken)."""
    try:
        state = dict(portal=int(portal), element=int(elem), map=int(map_index), channel=int(channel),
            left=max(0, int(left)), joined=max(0, int(joined)), need=max(1, int(need)), can_join=int(can_join) == 1,
            is_joined=int(is_joined) == 1, can_start=int(can_start) == 1)
    except (TypeError, ValueError):
        return None
    state["pids"] = parse_pids(pids)
    state["guild"] = (guild or "").replace("_", " ")
    return state


class GuildMembers(object):
    """Member lookup in the client guild model (root/guildv2model.py, filled by the guild window's snapshots):
    pid -> (name, level, rank, online). ``source`` returns the guildv2model.Model (or None); ``refresh`` asks the
    guild window for a snapshot when the model is still empty (the guild window was never opened)."""

    def __init__(self, source, refresh=None):
        self.source, self.refresh = source, refresh

    def Refresh(self):
        if self.refresh and not self.rows():
            try:
                self.refresh()
            except Exception:
                pass

    def model(self):
        try:
            return self.source()
        except Exception:
            return None

    def rows(self):
        model = self.model()
        if model is None:
            return []
        try:
            import guildv2model as m
            return list(model.rows(m.MEMBER))
        except Exception:
            return []

    def viewer(self):
        model = self.model()
        try:
            import guildv2model as m
            return model.row(m.CAPABILITY)[0][9] if model is not None else 0
        except Exception:
            return 0

    def get(self, pid):
        for values, name, body in self.rows():
            if values[0] == pid:
                return (name or "?", values[2], values[1], bool(values[7]))
        return None


def member_rows(state, members):
    """The table rows: the joined members first (state "joined"), then the other online members of the guild model
    ("invited", or "low" under MIN_LEVEL). Row = (pid, name, rank or None, level or None, where, status)."""
    rows, seen = [], set()
    for pid, where_map, where_channel in state.get("pids", ()):
        seen.add(pid)
        info = members.get(pid)
        where = (u"%s · kanál %d" % (map_name(where_map), where_channel)) if where_map else \
            (u"online" if info and info[3] else u"?")
        if info is None:
            rows.append((pid, u"?", None, None, where, "joined"))
        else:
            rows.append((pid, info[0], info[2], info[1], where, "joined"))
    others = []
    for values, name, body in members.rows():
        pid, rank, level, online = values[0], values[1], values[2], values[7]
        if pid in seen or not online:
            continue
        others.append((pid, name or u"?", rank, level, u"online", "invited" if level >= MIN_LEVEL else "low"))
    others.sort(key=lambda row: (row[5] != "invited", row[2], row[1]))
    return rows + others


STATUS = {"joined": (u"připojen", GREEN), "invited": (u"pozvánka odeslána", DIM), "low": (u"úroveň pod %d" % MIN_LEVEL,
    MUTED)}


class GuildPortalLobbyWindow(Canvas):
    """The lobby window. SetState(dict of parse_lobby) fills it; SetEvent(action, callback) for "JOIN", "LEAVE",
    "START" (the X / Zavřít only hide the window)."""

    def __init__(self, members=None):
        Canvas.__init__(self, None, 0, 0, WIDTH, HEIGHT)
        self.AddFlag("movable")
        self.AddFlag("float")
        self.members = members or GuildMembers(lambda: None)
        self.events = {}
        self.state = None
        self.deadline = 0.0
        self.pending = False
        self.pending_since = 0.0
        self.shown_second = None
        self.scroll = None
        self.offset = 0
        self.unresolved = False
        self.model_size = 0
        self.rendered_at = 0.0
        self.timer_value = None
        self.start_button = self.join_button = self.second_button = None
        self.shell(WIDTH, HEIGHT, u"Cechovní portál", ui.__mem_func__(self.Close))
        content_w = WIDTH - 2 * PANEL_X
        panel_h = HEIGHT - PANEL_Y - 18
        self.content_frame = None
        if widgets.R1:
            self.content_frame = self.keep(widgets.uir1.Frame(self, px(PANEL_X), px(PANEL_Y), span(PANEL_X, content_w),
                span(PANEL_Y, panel_h), "panel"))
        else:
            self.panel(PANEL_X, PANEL_Y, content_w, panel_h)
        self.pixel_bar(px(PANEL_X) + 2, px(PANEL_Y) + 2, span(PANEL_X, content_w) - 4, span(PANEL_Y, BAND_H) - 2, SURFACE)
        self.pixel_bar(px(PANEL_X) + 2, px(PANEL_Y + BAND_H), span(PANEL_X, content_w) - 4, 1, EDGE)
        self.band = Canvas(self, PANEL_X, PANEL_Y, content_w, BAND_H)
        self.band.Show()
        self.body = Canvas(self, PANEL_X + PAD, PANEL_Y + BAND_H + 12, content_w - 2 * PAD, panel_h - BAND_H - 24)
        self.body.Show()
        self.SetCenterPosition()
        self.Hide()

    # ------------------------------------------------------------------ API
    def SetEvent(self, action, callback):
        self.events[action] = callback

    def SetState(self, state, now=None):
        self.state = dict(state) if state else None
        if self.state:
            self.deadline = (app.GetTime() if now is None else now) + self.state["left"]
        self.pending = False
        self.render()

    def Remaining(self):
        return max(0.0, self.deadline - app.GetTime()) if self.state else 0.0

    def Open(self):
        self.render()
        self.Show()
        self.SetTop()

    def Close(self):
        self.Hide()

    def OnPressEscapeKey(self):
        self.Close()
        return True

    def OnUpdate(self):
        if not self.state:
            return
        if self.pending and app.GetTime() - self.pending_since > PENDING_TIMEOUT:
            self.pending = False
            self.render()
            return
        if self.unresolved and app.GetTime() - self.rendered_at > 2.0:
            self.rendered_at = app.GetTime()
            if len(self.members.rows()) != self.model_size:
                self.render()       # the guild model (names, levels) arrived meanwhile
                return
        second = int(self.Remaining() + 0.999)
        if second != self.shown_second:
            self.shown_second = second
            if self.timer_value is not None:
                self.timer_value.SetText(clock(self.Remaining()))

    def Destroy(self):
        self.events = {}
        self.band.Destroy()
        self.body.Destroy()
        Canvas.Destroy(self)

    # ------------------------------------------------------------------ actions
    def act(self, action):
        if self.pending or not self.state:
            return False
        callback = self.events.get(action)
        if not callback:
            return False
        self.pending, self.pending_since = True, app.GetTime()
        self.render()
        callback()
        return True

    # ------------------------------------------------------------------ frame
    def render(self):
        self.offset = self.scroll.offset if self.scroll else 0
        self.band.clear()
        self.body.clear()
        self.scroll = None
        self.timer_value = None
        state = self.state
        if not state:
            self.title_line.SetText(u"Cechovní portál")
            self.body.text(0, 4, u"Lobby portálu není otevřené.", self.body.design_width, DIM)
            return
        names = element(state["element"])
        self.title_line.SetText(u"Cechovní portál – %s" % names[0])
        self.render_band(state)
        self.render_summary(state, names)
        self.render_members(state)
        self.render_actions(state)

    def render_band(self, state):
        band = self.band
        w = band.design_width
        band.text(PAD, 10, state["guild"] or u"Lobby", w // 2, GOLD, fontconfig.ROLE_LARGE_BOLD)
        band.text(w - PAD, 10, u"Připraveno %d / %d" % (state["joined"], state["need"]), w // 2 - PAD,
            GREEN if state["joined"] >= state["need"] else INK, fontconfig.ROLE_CONTROL, "right")

    def render_summary(self, state, names):
        body = self.body
        w = body.design_width
        lead = body.text(0, 0, u"Portál drží váš cech ještě", 0, INK, fontconfig.ROLE_CONTROL)
        after = int(lead.GetTextSize()[0] / widgets.SCALE) + 8
        self.timer_value = body.text(after, 0, clock(self.Remaining()), 80, GOLD, fontconfig.ROLE_CONTROL)
        self.shown_second = int(self.Remaining() + 0.999)
        body.text(w, 2, u"potřeba %d %s úr. %d+" % (state["need"], players(state["need"]), MIN_LEVEL), 320, DIM,
            ROLE_CAPTION, "right")
        body.gauge(0, 32, w, state["joined"], state["need"])
        golem = names[2] + (u" %d" % state["strength"] if state.get("strength") else u"")
        body.text(0, 52, u"Uvnitř: %s · %s, kanál %d · do krypty jen členové s úrovní %d+" % (golem,
            map_name(state["map"]), state["channel"], MIN_LEVEL), w, DIM, ROLE_CAPTION)

    def grid(self, w):
        """x and alignment of the columns Člen, Úr., Kde je, Stav (header and rows)."""
        return ((12, "left"), (int(w * 0.40), "right"), (int(w * 0.45), "left"), (w - 12, "right"))

    def render_members(self, state):
        body = self.body
        w = body.design_width
        top = 88
        body.table_header(0, top, w)
        grid = self.grid(w - 16)
        for label, (x, align) in zip((u"Člen", u"Úr.", u"Kde je", u"Stav"), grid):
            body.text(x, top + 8, label, 160, DIM, ROLE_CAPTION, align)
        rows = member_rows(state, self.members)
        self.model_size = len(self.members.rows())
        self.unresolved = any(row[1] == u"?" for row in rows) or not self.model_size
        self.rendered_at = app.GetTime()
        own = self.members.viewer()

        def draw(canvas, row, y, width):
            pid, name, rank, level, where, status = row
            (nx, na), (lx, la), (wx, wa), (sx, sa) = self.grid(width)
            active = status != "low"
            color = GOLD if pid == own else (INK if active else MUTED)
            line = canvas.text(nx, y + 7, name, lx - nx - 110, color, fontconfig.ROLE_CONTROL)
            if rank is not None and 0 <= rank < len(ROLES):
                after = nx + int(line.GetTextSize()[0] / widgets.SCALE) + 10
                canvas.text(after, y + 9, ROLES[rank], max(10, lx - after - 70), DIM if active else MUTED,
                    ROLE_CAPTION)
            canvas.text(lx, y + 7, str(level) if level is not None else u"?", 80, INK if active else MUTED, align=la)
            canvas.text(wx, y + 8, where, sx - wx - 150, DIM if active else MUTED, ROLE_CAPTION)
            text, tint = STATUS[status]
            canvas.text(sx, y + 8, text, 170, tint, ROLE_CAPTION, sa)
        self.scroll = body.keep(ScrollList(body, 0, top + 34, w, VISIBLE_ROWS * ROW, rows, ROW, draw, self.offset))
        if not rows:
            body.text(12, top + 46, u"V lobby zatím nikdo není.", w, MUTED)

    def note(self, state):
        if not state["is_joined"]:
            if state["can_join"]:
                return u"Připojit se jde odkudkoli, k portálu není třeba běžet."
            return u"Do krypty smí jen členové s úrovní %d a vyšší." % MIN_LEVEL
        if state["can_start"]:
            return u"Všichni připojení se po spuštění přesunou do krypty naráz."
        if state["joined"] < state["need"]:
            return u"Vstup spustí Vůdce nebo Rada, až %s aspoň %d %s." % (joined_verb(state["need"]), state["need"],
                players(state["need"]))
        return u"Vstup spouští Vůdce nebo Rada."

    def render_actions(self, state):
        body = self.body
        w = body.design_width
        y = 88 + 34 + VISIBLE_ROWS * ROW + 8
        body.rule(0, y, w)
        body.text(0, y + 12, self.note(state), w, DIM, ROLE_CAPTION)
        y += 44
        ready = not self.pending
        if state["is_joined"]:
            label = u"Spustit vstup"
            if state["joined"] < state["need"]:
                label += u" (%d/%d)" % (state["joined"], state["need"])
            self.start_button = body.button(label, w - 170 - 14 - 250, y, lambda: self.act("START"),
                state["can_start"] and ready, width=250,
                tooltip=None if state["can_start"] else u"Spouští Vůdce nebo Rada, aspoň %d připojení" % state["need"])
            self.second_button = body.action(u"Odejít z lobby", w - 170, y, lambda: self.act("LEAVE"), ready,
                width=170, height=32)
            self.join_button = None
            return
        self.start_button = None
        if state["can_join"]:
            self.join_button = body.button(u"Připojit se", w - 170 - 14 - 250, y, lambda: self.act("JOIN"), ready,
                width=250)
        else:
            self.join_button = None
            locked_text(body, w - 170 - 24 - 400, y, 400, right=True)
        self.second_button = body.action(u"Zavřít", w - 170, y, ui.__mem_func__(self.Close), True, width=170,
            height=32)


def locked_text(canvas, x, y, width, right=False):
    """The locked join: the padlock of the guild's locked features and the dimmed text in the place of the button
    (centred on the button height); ``right`` = the text ends at x + width (next to the button on its right)."""
    if not right:
        canvas.keep(lock_image(canvas, px(x + 4), px(y + 9)))
        return canvas.text(x + 26, y + 6, LOCKED_TEXT, width - 26, MUTED, fontconfig.ROLE_CONTROL)
    line = canvas.text(x + width, y + 6, LOCKED_TEXT, width - 26, MUTED, fontconfig.ROLE_CONTROL, "right")
    start = x + width - int(line.GetTextSize()[0] / widgets.SCALE)
    canvas.keep(lock_image(canvas, px(start - 22), px(y + 9)))
    return line


class GuildPortalPopup(Canvas):
    """The short notice when the portal is found (as the guild invitation dialog): "<finder> našel cechovní portál
    (<element>). Lobby X/3 · zbývá M:SS", Připojit se / Později (Později only hides it); a member under the level
    sees the locked text instead of Připojit se."""

    W, H = 480, 214
    TOP = 40

    def __init__(self):
        Canvas.__init__(self, None, 0, 0, self.W, self.H)
        self.AddFlag("float")
        self.AddFlag("movable")
        self.on_join = None
        self.deadline = 0.0
        self.state = None
        self.shown_second = None
        self.shell(self.W, self.H, u"Cechovní portál", ui.__mem_func__(self.Close))
        # below the header row: the whole header drags the popup (the content never covers it)
        self.content = Canvas(self, 0, self.TOP, self.W, self.H - self.TOP)
        self.content.Show()
        self.SetCenterPosition()
        self.Hide()

    def SetJoinEvent(self, callback):
        self.on_join = callback

    def SetState(self, state, now=None):
        """state: element, finder, joined, need, left, can_join."""
        self.state = dict(state)
        self.deadline = (app.GetTime() if now is None else now) + self.state["left"]
        self.render()

    def Update(self, joined, need, left, can_join):
        if self.state:
            self.state.update(joined=joined, need=need, left=left, can_join=can_join)
            self.SetState(self.state)

    def Remaining(self):
        return max(0.0, self.deadline - app.GetTime())

    def counter(self):
        return u"Lobby %d/%d · zbývá %s" % (self.state["joined"], self.state["need"], clock(self.Remaining()))

    def render(self):
        c = self.content
        c.clear()
        s = self.state
        w = self.W
        t = -self.TOP
        c.text(w // 2, t + 46, u"%s našel cechovní portál (%s)." % (s["finder"], element(s["element"])[1]), w - 48, INK,
            fontconfig.ROLE_CONTROL, "center")
        self.counter_line = c.text(w // 2, t + 78, self.counter(), w - 48, GOLD, fontconfig.ROLE_CONTROL, "center")
        c.text(w // 2, t + 110, u"Do krypty jen členové cechu s úrovní %d+." % MIN_LEVEL, w - 48, DIM, ROLE_CAPTION,
            "center")
        if s["can_join"]:
            self.join_button = c.button(u"Připojit se", 24, t + 158, ui.__mem_func__(self.join), width=250)
        else:
            self.join_button = None
            locked_text(c, 24, t + 158, 270)
        self.later_button = c.action(u"Později", w - 174, t + 158, ui.__mem_func__(self.Close), width=150, height=28)
        self.shown_second = int(self.Remaining() + 0.999)

    def join(self):
        if self.on_join and self.state and self.state["can_join"]:
            self.Close()
            self.on_join()

    def Open(self):
        self.Show()
        self.SetTop()

    def Close(self):
        self.Hide()

    def OnPressEscapeKey(self):
        self.Close()
        return True

    def OnUpdate(self):
        if not self.state:
            return
        second = int(self.Remaining() + 0.999)
        if second != self.shown_second:
            self.shown_second = second
            self.counter_line.SetText(self.counter())

    def Destroy(self):
        self.on_join = None
        self.content.Destroy()
        Canvas.Destroy(self)


class PortalController(object):
    """The client side of the guild portal lobby for root/game.py: keeps the quest index, the last lobby state, the
    pending action, the window and the popup. ``send_quest_click(index)`` = event.QuestButtonClick,
    ``send_input(text)`` = net.SendQuestInputStringPacket, ``members`` = GuildMembers, ``notify(text)`` = chat."""

    def __init__(self, send_quest_click, send_input, members, notify=None):
        self.send_quest_click, self.send_input, self.notify = send_quest_click, send_input, notify
        self.members = members
        self.quest_index = None
        self.state = None
        self.pending = ""
        self.window = None
        self.popup = None
        self.popup_shown = False
        self.strength = 0

    # ------------------------------------------------------------------ server -> client
    def Quest(self, index):
        index = _int(index, None)
        if index is not None:
            self.quest_index = index

    def Golem(self, strength):
        """GuildPortalGolem <75|90> (server 12. 10.), sent before GuildPortalLobby; older servers never send it."""
        self.strength = _int(strength, 0)
        if self.state:
            self.state["strength"] = self.strength
            if self.window:
                self.window.SetState(self.state)

    def Lobby(self, *fields):
        state = parse_lobby(*fields)
        if state is None:
            return
        state["strength"] = self.strength
        self.state = state
        if self.window:
            self.window.SetState(state)
        if self.popup and self.popup.IsShow():
            self.popup.Update(state["joined"], state["need"], state["left"], state["can_join"])

    def Open(self):
        if not self.state:
            return False
        self.members.Refresh()
        window = self.lobby_window()
        window.SetState(self.state)
        window.Open()
        return True

    def Popup(self, elem, finder, joined, need, left, can_join):
        if self.popup_shown:
            return False
        self.popup_shown = True
        popup = self.popup_window()
        popup.SetState(dict(element=_int(elem), finder=(finder or u"?").replace("_", " "), joined=_int(joined),
            need=max(1, _int(need, 3)), left=max(0, _int(left)), can_join=_int(can_join) == 1))
        popup.Open()
        return True

    def Close(self, reason=""):
        if self.window:
            self.window.Close()
            self.window.SetState(None)
        if self.popup:
            self.popup.Close()
        self.state = None
        self.pending = ""
        self.popup_shown = False
        text = CLOSE_REASONS.get(reason)
        if text and self.notify:
            self.notify(text)

    def Command(self):
        """guild_portal_cmd: the server asks for the pending action; always answers (empty = nothing pending)."""
        command, self.pending = self.pending, ""
        self.send_input(command)
        return command

    # ------------------------------------------------------------------ client -> server
    def Request(self, action):
        if action not in ACTIONS or self.quest_index is None or not self.state:
            return False
        self.pending = "%s#%d" % (action, self.state["portal"])
        self.send_quest_click(self.quest_index)
        return True

    # ------------------------------------------------------------------ windows
    def lobby_window(self):
        if not self.window:
            self.window = GuildPortalLobbyWindow(self.members)
            for action in ("JOIN", "LEAVE", "START"):
                self.window.SetEvent(action, lambda a=action: self.Request(a))
        return self.window

    def popup_window(self):
        if not self.popup:
            self.popup = GuildPortalPopup()
            self.popup.SetJoinEvent(lambda: self.Request("JOIN"))
        return self.popup

    def Destroy(self):
        if self.window:
            self.window.Destroy()
        if self.popup:
            self.popup.Destroy()
        self.window = self.popup = None
        self.send_quest_click = self.send_input = self.notify = None
