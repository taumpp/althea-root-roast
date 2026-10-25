"""Local item-to-render-target policy, shared by shop clicks and hints."""

TYPE_WEAPON = 1
TYPE_ARMOR = 2
TYPE_HAIR = 3
TYPE_ACCE = 4
TYPE_SHINING_WEAPON = 5
TYPE_SHINING_ARMOR = 6
TYPE_MODEL = 20

# (item type, subtype, render type, model value slot or None for equipment)
PREVIEW_RULES = (
    ("ITEM_TYPE_COSTUME", "COSTUME_TYPE_BODY", TYPE_ARMOR, None),
    ("ITEM_TYPE_COSTUME", "COSTUME_TYPE_HAIR", TYPE_HAIR, None),
    ("ITEM_TYPE_COSTUME", "COSTUME_TYPE_WEAPON", TYPE_WEAPON, None),
    ("ITEM_TYPE_COSTUME", "COSTUME_TYPE_ACCE", TYPE_ACCE, None),
    ("ITEM_TYPE_COSTUME", "COSTUME_TYPE_ACCE_SKIN", TYPE_ACCE, None),
    ("ITEM_TYPE_COSTUME", "COSTUME_TYPE_EFFECT_WEAPON", TYPE_SHINING_WEAPON, None),
    ("ITEM_TYPE_COSTUME", "COSTUME_TYPE_EFFECT_ARMOR", TYPE_SHINING_ARMOR, None),
    ("ITEM_TYPE_COSTUME", "COSTUME_TYPE_MOUNT", TYPE_MODEL, 1),
    ("ITEM_TYPE_COSTUME", "COSTUME_TYPE_PET", TYPE_MODEL, 0),
    ("ITEM_TYPE_PET", "PET_UPBRINGING", TYPE_MODEL, 0),
)


def Resolve(item, vnum):
    """Return (render type, equipment VNUM/model race), or (0, 0).

    A growth seal shows its base model. Eggs, bags and pet consumables do
    not describe a standalone model and must not interpret value0 as a race.
    Leave the caller's item selected, including rejected items.
    """
    item.SelectItem(vnum)
    itemType, subType = item.GetItemType(), item.GetItemSubType()
    for typeName, subName, renderType, valueSlot in PREVIEW_RULES:
        if (itemType == getattr(item, typeName, None)
                and subType == getattr(item, subName, None)):
            model = vnum if valueSlot is None else item.GetValue(valueSlot)
            if model > 0:
                return renderType, model
            break
    return 0, 0
