"""Catalog geometry; native listing indexes remain unchanged by presentation."""

BASE_ROW_HEIGHT = 51
SLOT_SIZE = 32


def RowHeight(itemHeight):
    return BASE_ROW_HEIGHT + (max(1, int(itemHeight)) - 1) * SLOT_SIZE


def PackRows(itemHeights, availableHeight, startIndex=0):
    """Pack one received batch in order, returning pages of (native index, y).

    Callers append pages for later batches instead of filling an already visited
    partial page. That keeps every newly received offer ahead of the Next button.
    """
    pages = []
    page = []
    y = 0
    for index, itemHeight in enumerate(itemHeights, startIndex):
        height = RowHeight(itemHeight)
        if page and y + height > availableHeight:
            pages.append(page)
            page = []
            y = 0
        page.append((index, y))
        y += height
    if page:
        pages.append(page)
    return pages
