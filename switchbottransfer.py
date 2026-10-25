"""Confirmed switchbot-to-inventory handoff for the instant reroller."""
import app
import chat
import item
import localeInfo
import net
import player
import switchbot


def Fingerprint(window, cell):
    return (player.GetItemIndex(window, cell), player.GetItemCount(window, cell),
            tuple(player.GetItemMetinSocket(window, cell, i)
                  for i in range(player.METIN_SOCKET_MAX_NUM)),
            tuple(player.GetItemAttribute(window, cell, i)
                  for i in range(player.ATTRIBUTE_SLOT_MAX_NUM)))


def EmptyCell(vnum):
    # Native inventory pages are 5 columns; reserve every tile of tall items,
    # including clients which expose only the occupied item's anchor cell.
    pageSize = player.INVENTORY_PAGE_SIZE
    capacity = pageSize * player.INVENTORY_PAGE_COUNT
    occupied = set()
    for cell in range(capacity):
        existing = player.GetItemIndex(player.INVENTORY, cell)
        if existing:
            item.SelectItem(existing)
            width, height = item.GetItemSize()
            for dy in range(height):
                for dx in range(width):
                    occupied.add(cell + dy * 5 + dx)
    item.SelectItem(vnum)
    width, height = item.GetItemSize()
    for cell in range(capacity):
        local = cell % pageSize
        if local % 5 + width > 5 or local // 5 + height > pageSize // 5:
            continue
        if all(cell + dy * 5 + dx not in occupied
               for dy in range(height) for dx in range(width)):
            return cell
    return None


class Transfer(object):
    def __init__(self):
        self.Cancel()

    def Cancel(self):
        self.pending = None

    def Begin(self, slot):
        if self.pending is not None or not 0 <= slot < switchbot.SLOT_COUNT or switchbot.IsActive(slot):
            return False
        expected = Fingerprint(player.SWITCHBOT, slot)
        if not expected[0]:
            return False
        cell = EmptyCell(expected[0])
        if cell is None:
            chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.SHOP_INVENTORY_FULL)
            return False
        self.pending = (slot, cell, expected, app.GetTime() + 5.0)
        net.SendItemMovePacket(player.SWITCHBOT, slot, player.INVENTORY, cell, expected[1])
        return True

    def Poll(self):
        if self.pending is None:
            return None
        slot, cell, expected, deadline = self.pending
        if app.GetTime() >= deadline:
            self.Cancel()
            return None
        # Neither the move request nor source removal alone proves delivery.
        # Consume before SetTarget can issue a catalog request or refresh UI.
        if not player.GetItemIndex(player.SWITCHBOT, slot) and player.GetItemIndex(player.INVENTORY, cell):
            self.Cancel()
            if Fingerprint(player.INVENTORY, cell) == expected:
                return cell
        return None
