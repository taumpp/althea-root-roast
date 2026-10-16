def _footprint(cell, page_start, page_width, page_height,
		item_width, item_height):
	local = cell - page_start
	if local < 0 or local >= page_width * page_height:
		return None

	column = local % page_width
	row = local // page_width
	if column + item_width > page_width or row + item_height > page_height:
		return None

	return tuple(
		page_start + (row + dy) * page_width + column + dx
		for dy in range(item_height)
		for dx in range(item_width)
	)


def mark_occupied_cells(page_starts, page_width, page_height, dimensions_at):
	occupied = set()
	for page_start in page_starts:
		for local in range(page_width * page_height):
			cell = page_start + local
			dimensions = dimensions_at(cell)
			if not dimensions:
				continue

			width, height = dimensions
			cells = _footprint(
				cell, page_start, page_width, page_height, width, height
			)
			if cells:
				occupied.update(cells)
	return occupied


def plan_split_moves(source_count, chunk_size, source_cell, page_starts,
		page_width, page_height, item_width, item_height, occupied_cells):
	if source_count <= 1 or chunk_size <= 0 or chunk_size >= source_count:
		return [], 0
	if page_width <= 0 or page_height <= 0:
		return [], 0
	if item_width <= 0 or item_height <= 0:
		return [], 0

	required_moves = (source_count - 1) // chunk_size
	occupied = set(occupied_cells)
	moves = []

	for page_start in page_starts:
		for local in range(page_width * page_height):
			destination = page_start + local
			if destination == source_cell:
				continue

			cells = _footprint(
				destination, page_start, page_width, page_height,
				item_width, item_height
			)
			if not cells or any(cell in occupied for cell in cells):
				continue

			moves.append((destination, chunk_size))
			occupied.update(cells)
			if len(moves) == required_moves:
				return moves, required_moves

	return moves, required_moves
