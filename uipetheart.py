"""Retired Pet Heart compatibility module; no UI or mutation entry remains."""
import ui

WindowDestroy = getattr(ui, "WindowDestroy", lambda function: function)


class PetHeartPage(ui.Window):
    """Old imports remain harmless during a rolling content update."""
    def __init__(self, parent):
        ui.Window.__init__(self)
        self.SetParent(parent)
        self.Hide()

    def Show(self):
        self.Hide()

    def Refresh(self):
        return

    @WindowDestroy
    def Destroy(self):
        self.Hide()
