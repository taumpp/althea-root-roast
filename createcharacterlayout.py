"""Native component geometry for character creation; no account state."""


def get_layout(screen_width, screen_height):
	width, height = int(screen_width), int(screen_height)
	if width >= 1440 and height >= 1080:
		profile, scale, base_height = "full", 1.0, 1080
		row_width, row_height, detail_width = 430, 88, 390
	elif width >= 1200 and height >= 900:
		profile, scale, base_height = "medium", 5.0 / 6.0, 900
		row_width, row_height, detail_width = 358, 73, 325
	else:
		profile, scale, base_height = "compact", 2.0 / 3.0, 600
		row_width, row_height, detail_width = 220, 58, 260
	compact = profile == "compact"
	margin = min(int(width * 0.05), max(24, (width - 752) // 2)) if compact else int(width * 0.05)
	gap = 24 if compact else int(round(48 * scale))
	detail_x = margin + row_width + gap
	render_x = detail_x + detail_width + (24 if compact else int(round(34 * scale)))
	extra = max(0, height - base_height)
	def y(value):
		return int(round(value + extra * float(value) / base_height))
	def p(value):
		return int(round(value * scale))
	if compact:
		sections = {
			"title": (116, 20),
			"gender_label": (154, 16), "gender": (176, 32),
			"shape_label": (220, 16), "shape": (242, 32),
			"stats_label": (286, 16), "stats": (308, 40),
			"name_label": (360, 16), "name": (382, 34), "create": (432, 52),
		}
		row_top, row_pitch, logo_y, phase_y, job_y = 156, 64, 20, 108, 136
	else:
		sections = {name: (p(top), p(size)) for name, top, size in (
			("title", 224, 32),
			("gender_label", 278, 20), ("gender", 306, 42),
			("shape_label", 380, 20), ("shape", 410, 42),
			("stats_label", 490, 20), ("stats", 528, 60),
			("name_label", 632, 20), ("name", 660, 58), ("create", 750, 78),
		)}
		row_top, row_pitch, logo_y, phase_y, job_y = p(260), p(94), p(56), p(180), p(230)
	sections = {name: (y(top), size) for name, (top, size) in sections.items()}
	face_scale = 0.72 if compact else scale
	face_size = int(43 * face_scale)
	return {
		"profile": profile, "scale": scale, "sections": sections,
		"rail": (margin, y(row_top), row_width, row_pitch * 4 + row_height),
		"row_height": row_height, "row_pitch": row_pitch,
		"portrait": {"scale": face_scale, "size": face_size,
			"x": 12 if compact else p(22), "y": (row_height - face_size) // 2},
		"detail": (detail_x, sections["title"][0], detail_width, sections["create"][0] + sections["create"][1] - sections["title"][0]),
		"render": (render_x, y(116 if compact else p(150)), max(1, width - margin - render_x), max(1, height - y(116 if compact else p(150)) - p(105))),
		"logo": (margin, y(logo_y)), "phase": (margin, y(phase_y)), "job_label": (margin, y(job_y)),
		"back": (margin, height - p(45) - p(60), p(120), p(45)),
		"choice_size": (125, 32) if compact else (p(185), p(42)),
	}
