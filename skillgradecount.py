"""The grade count of the character window's skill cells, drawn above the cell's cover button.

The engine writes the count of a skill cell (CSlotWindow::SetSlotCountNew: "17", "m3", "g1", "p1", "s") in the
taskbar digits at the cell's bottom-right corner from the slot window's OnRender. The skill page gives every skill
cell a cover button (SetCoverButton: the V31 cell frame, an opaque 3 px graphite border), which is a CHILD window of
the slot window, so it is rendered after OnRender, over the digits: on Postava -> Schopnosti the grade of the skills
and the standard skills is covered (tester 2026-10-09: "Pomoc draka G1" on Buffy, nothing on Schopnosti). The Buffi
cells (uicharacterbuff) have no cover button and show the engine digits.

GradeCounts repeats the engine count of each cell with an engine number line (ui.NumberLine: the same taskbar digits,
right-aligned, at the engine's own position) on a layer that is a later sibling of the slot window, so it is drawn
after the slot window and its cover buttons. The engine count itself stays set exactly as before (Starý vzhled and R1
alike); the layer only puts the same digits on top.
"""
import ui

CELL = 32                       # ITEM_WIDTH / ITEM_HEIGHT of CSlotWindow
COUNT_RIGHT = CELL - 4          # CSlotWindow::OnRender: x + width * 32 - 4, right-aligned
COUNT_TOP = CELL - 12 + 2       # CSlotWindow::OnRender: y + height * 32 - 12 + 2
SAGE_GRADE = 4                  # the engine writes "s" without a level


def CountText(grade, count):
    """The text the engine writes for SetSlotCountNew(grade, count) ('' = no count)."""
    grade, count = int(grade), int(count)
    if count <= 0:
        return ''
    if grade == 0:
        return '%d' % count
    if grade in (1, 2, 3):
        return '%s%d' % ('mgp'[grade - 1], count)
    if grade == SAGE_GRADE:
        return 's'
    return ''


class GradeCounts(object):
    """The counts of one slot window (by slot index), on a layer above it in the same parent."""

    def __init__(self, parent, slots):
        """parent: the window the slot window lies in (Skill_Page); the layer is created after the slot window."""
        self.slots = slots
        self.lines = {}
        self.texts = {}
        self.layer = ui.Window()
        self.layer.SetParent(parent)
        self.layer.AddFlag('not_pick')
        self.Sync()

    def Set(self, index, grade, count):
        self._Show(index, CountText(grade, count))

    def SetCount(self, index, count):
        """SetSlotCount: the plain number."""
        self._Show(index, CountText(0, count))

    def Clear(self, index):
        self._Show(index, '')

    def Text(self, index):
        return self.texts.get(index, '')

    def _Show(self, index, text):
        line = self.lines.get(index)
        if not text:
            self.texts.pop(index, None)
            if line is not None:
                line.Hide()
            return
        position = self.slots.GetSlotLocalPosition(index)
        if position is None:
            return
        if line is None:
            line = ui.NumberLine()
            line.SetParent(self.layer)
            line.AddFlag('not_pick')
            line.SetHorizontalAlignRight()
            self.lines[index] = line
        line.SetPosition(position[0] + COUNT_RIGHT, position[1] + COUNT_TOP)
        line.SetNumber(text)
        line.Show()
        self.texts[index] = text

    def Sync(self):
        """The layer follows the slot window: its place, size and visibility."""
        x, y = self.slots.GetLocalPosition()
        self.layer.SetPosition(x, y)
        self.layer.SetSize(self.slots.GetWidth(), self.slots.GetHeight())
        if self.slots.IsShow():
            self.layer.Show()
        else:
            self.layer.Hide()

    def Destroy(self):
        for line in self.lines.values():
            line.Hide()
        self.lines = {}
        self.texts = {}
        self.layer.Hide()
        self.slots = None
