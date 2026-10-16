import app
import chat
import exchange
import item
import localeInfo
import net
import player

# Right-click (the native "use slot" event) on an inventory item while a
# player-to-player exchange is open adds the whole item/stack to the first
# free trade position instead of using or equipping it.
#
# The released server (CExchange::AddItem) does not pick a position itself:
# it rejects any display position whose 1 x item-height column is occupied
# or outside its CGrid, including the community "-1"/255 shortcut. The
# client therefore mirrors the server grid (6 x 4 with the new exchange
# window, 4 x 3 otherwise; EXCHANGE_ITEM_MAX_NUM cells) and the server's
# row-major CGrid::FindBlank order. The server stays authoritative for
# antiflags, seals, locks and item ownership.

PENDING_SECONDS = 1.5

# display position -> (inventory slot, item height, expiry)
# A reply to ITEM_ADD arrives asynchronously; reserving the position briefly
# stops two quick right-clicks from requesting the same cell.
_pending = {}


def _Text(name, fallback):
	return getattr(localeInfo, name, fallback)


def _Info(message):
	chat.AppendChat(chat.CHAT_TYPE_INFO, message)


def Reset():
	_pending.clear()


def GetGridShape():
	total = int(getattr(exchange, "EXCHANGE_ITEM_MAX_NUM", 24))
	if getattr(app, "ENABLE_NEW_EXCHANGE_WINDOW", 0):
		columns = 6
	else:
		columns = 4

	if total <= 0 or total % columns:
		return (0, 0)

	return (columns, total // columns)


def FindFreeDisplayPosition(occupiedCells, columns, rows, height):
	if columns <= 0 or rows <= 0 or height <= 0 or height > rows:
		return -1

	for position in range(columns * rows):
		row = position // columns
		if row + height > rows:
			continue

		free = True
		for offset in range(height):
			if (position + offset * columns) in occupiedCells:
				free = False
				break

		if free:
			return position

	return -1


def _ItemHeight(vnum):
	item.SelectItem(vnum)
	try:
		(width, height) = item.GetItemSize()
	except Exception:
		return 1
	return max(1, int(height))


def _MarkCells(occupiedCells, position, height, columns):
	for offset in range(height):
		occupiedCells.add(position + offset * columns)


def _CollectOccupiedCells(columns, now):
	occupiedCells = set()
	for position in range(int(getattr(exchange, "EXCHANGE_ITEM_MAX_NUM", 0))):
		vnum = exchange.GetItemVnumFromSelf(position)
		if vnum:
			_MarkCells(occupiedCells, position, _ItemHeight(vnum), columns)
			_pending.pop(position, None)

	for position, (slotIndex, height, expiry) in list(_pending.items()):
		if expiry <= now:
			del _pending[position]
			continue
		_MarkCells(occupiedCells, position, height, columns)

	return occupiedCells


def _IsPending(slotIndex, now):
	for pendingSlot, height, expiry in _pending.values():
		if pendingSlot == slotIndex and expiry > now:
			return True
	return False


def IsExchangeOpen(interface):
	if not exchange.isTrading():
		return False

	dialog = getattr(interface, "dlgExchange", None) if interface else None
	if not dialog:
		return False

	try:
		return bool(dialog.IsShow())
	except Exception:
		return False


def _IsEquippedSlot(slotIndex):
	for name in ("IsEquipmentSlot", "IsCostumeSlot"):
		check = getattr(player, name, None)
		if check and check(slotIndex):
			return True
	return False


def _IsSealed(slotIndex):
	if not getattr(app, "ENABLE_SOUL_BIND_SYSTEM", 0):
		return False
	sealDate = player.GetItemSealDate(player.INVENTORY, slotIndex)
	return sealDate == -1 or sealDate > 0


def _IsAlreadyInTrade(interface, slotIndex, now):
	dialog = getattr(interface, "dlgExchange", None)
	listed = getattr(dialog, "ItemListIdx", None) or []
	return slotIndex in listed or _IsPending(slotIndex, now)


def TryAddInventoryItem(interface, slotIndex):
	"""Return True when the right-click was consumed by an open exchange.

	False leaves the caller's ordinary right-click behaviour untouched
	(no exchange open, equipped item, empty slot)."""
	if slotIndex is None or slotIndex < 0:
		return False

	if not IsExchangeOpen(interface):
		Reset()
		return False

	# Equipped items and costumes are never offered; keep their native
	# right-click. The server also refuses equipment positions.
	if _IsEquippedSlot(slotIndex):
		return False

	vnum = player.GetItemIndex(slotIndex)
	if not vnum:
		return False

	now = app.GetTime()

	if _IsAlreadyInTrade(interface, slotIndex, now):
		_Info(_Text("EXCHANGE_QUICK_ADD_ALREADY", "Tento předmět už je ve výměně."))
		return True

	if exchange.GetAcceptFromTarget():
		_Info(_Text("EXCHANGE_QUICK_ADD_PARTNER_ACCEPTED",
			"Protistrana už výměnu potvrdila, nyní nelze přidat předmět."))
		return True

	if player.IsAntiFlagBySlot(slotIndex, item.ANTIFLAG_GIVE) or _IsSealed(slotIndex):
		_Info(localeInfo.EXCHANGE_CANNOT_GIVE)
		return True

	(columns, rows) = GetGridShape()
	height = _ItemHeight(vnum)
	position = FindFreeDisplayPosition(
		_CollectOccupiedCells(columns, now), columns, rows, height)
	item.SelectItem(vnum)

	if position < 0:
		_Info(_Text("EXCHANGE_QUICK_ADD_NO_SPACE",
			"Ve výměně není pro tento předmět místo."))
		return True

	# Special inventories are cells of the INVENTORY window (same as the
	# existing drag and drop path); the whole stack is always offered.
	net.SendExchangeItemAddPacket(player.INVENTORY, slotIndex, position)
	_pending[position] = (slotIndex, height, now + PENDING_SECONDS)
	return True
