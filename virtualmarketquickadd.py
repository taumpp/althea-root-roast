"""Route an unmodified inventory right-click to the open "Můj obchod".

While the virtual market shows the owner tab of an open shop, a right-click on
an inventory item (special inventories included) offers it exactly like a drop
on the first free owner slot: the same checks and the same "Prodejní cena"
dialog. The window decides; False keeps the ordinary right-click (use / equip)
whenever the offer cannot be made (window closed, shop full, unsellable item).
Listing creation is the existing client packet; the server stays authoritative.
Shift + right-click offers the item at the price last used for it, without the
dialog (the dialog still opens when no price is remembered).
"""
import app


def TryAddInventoryItem(interface, cell, windowType=None):
    if any(app.IsPressed(key) for key in (app.DIK_LCONTROL, app.DIK_RCONTROL,
                                         app.DIK_LALT, app.DIK_RALT)):
        return False
    window = getattr(interface, 'wndVirtualMarket', None) if interface else None
    offer = getattr(window, 'QuickOfferInventoryItem', None) if window else None
    if not offer:
        return False
    shift = any(app.IsPressed(key) for key in (getattr(app, 'DIK_LSHIFT', None),
                                              getattr(app, 'DIK_RSHIFT', None)) if key is not None)
    args = (cell,) if windowType is None else (cell, windowType)
    return bool(offer(*args, usePreviousPrice=True) if shift else offer(*args))
