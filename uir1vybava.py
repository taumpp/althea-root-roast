# -*- coding: utf-8 -*-
"""Shared pieces of the R1 look of the equipment windows (Talismany, Rychlá změna výbavy, Strom dovedností):

* DragHandle - the original title bar stays shown but draws nothing, so a drag on the R1 header moves the window
  exactly as today (the R1 header is not pickable, the title bar's 'attach' moves the window; the window flags do
  not change);
* ButtonAdapter - an R1 button standing in for an original ui.Button: the window keeps calling Enable / Disable /
  SetText / Show / Hide on what it holds, the adapter applies it to the R1 button AND to the hidden original, so the
  original is always current when the original look comes back. The state is never asked from the engine (the game
  EXE has no wndMgr.IsDisable).

docs/ALTHEA_R1_KIT.md
"""
TITLE_PARTS = ('imgLeft', 'imgCenter', 'imgRight', 'btnClose')


class DragHandle(object):
    """Hides the images, the close button and the title text of an original title bar; the bar stays shown."""

    def __init__(self, bar, extra=()):
        self.bar = bar
        self.parts = [getattr(bar, name, None) for name in TITLE_PARTS] + list(extra or ())
        self.parts = [part for part in self.parts if part is not None]
        self.shown = [part.IsShow() for part in self.parts]
        for part in self.parts:
            part.Hide()
        bar.Show()

    def Restore(self):
        for part, shown in zip(self.parts, self.shown):
            if shown:
                part.Show()
        self.parts, self.shown = [], []


class ButtonAdapter(object):
    """Stands in for an original button; unknown attributes come from the R1 button."""

    def __init__(self, original, button, enabled=True):
        self.__dict__['original'] = original
        self.__dict__['button'] = button
        self.__dict__['enabled'] = bool(enabled)
        if not enabled:
            button.Disable()

    def __getattr__(self, name):
        return getattr(self.__dict__['button'], name)

    def __setattr__(self, name, value):
        # attributes the window sets on its button (e.g. ToolTipText) go to the original
        setattr(self.__dict__['original'], name, value)

    def Enable(self):
        self.__dict__['enabled'] = True
        self.button.Enable()
        self.original.Enable()

    def Disable(self):
        self.__dict__['enabled'] = False
        self.button.Disable()
        self.original.Disable()

    def IsEnabled(self):
        return self.__dict__['enabled']

    def Show(self):
        self.button.Show()

    def Hide(self):
        self.button.Hide()

    def IsShow(self):
        return self.button.IsShow()

    def SetText(self, text):
        self.original.SetText(text)
        self.button.SetText(text)

    def GetText(self):
        return self.button.GetText()

    def SetEvent(self, event, *args):
        self.original.SetEvent(event, *args)
        self.button.SetEvent((lambda: event(*args)) if args else event)


def Swap(window, attr, original, button, enabled=True, hidden=False):
    """window.<attr> becomes an adapter of ``button`` for ``original`` (hidden); returns the adapter."""
    adapter = ButtonAdapter(original, button, enabled)
    if hidden:
        button.Hide()
    original.Hide()
    setattr(window, attr, adapter)
    return adapter


def Unswap(window, attr, adapter):
    """Puts the original button back on the window, shown if the R1 button was shown."""
    shown = adapter.button.IsShow()
    adapter.button.callback = None
    adapter.button.Hide()
    original = adapter.original
    if shown:
        original.Show()
    else:
        original.Hide()
    if getattr(window, attr, None) is adapter:
        setattr(window, attr, original)
    return original


def Fail(widgets):
    """Hides R1 widgets of a failed build."""
    for widget in widgets:
        if widget is None:
            continue
        try:
            widget.Hide()
        except Exception:
            pass

