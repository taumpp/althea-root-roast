"""Source selection and proportional placement for introduction backgrounds."""

ASSET_ROOT = 'locale/common/ui/intro_background/'
BACKGROUND_SIZES = ((1920, 1080), (2560, 1440), (3840, 2160))
GIANT_MARK = ASSET_ROOT + 'giant_mark_700x980.png'


def get_background_spec(screen_width, screen_height):
	width, height = max(1, int(screen_width)), max(1, int(screen_height))
	source_width, source_height = BACKGROUND_SIZES[-1]
	for candidate_width, candidate_height in BACKGROUND_SIZES:
		if width <= candidate_width and height <= candidate_height:
			source_width, source_height = candidate_width, candidate_height
			break
	scale = max(float(width) / source_width, float(height) / source_height)
	return {
		'image': ASSET_ROOT + 'atmosphere_%dx%d.png' % (source_width, source_height),
		'width': source_width, 'height': source_height, 'scale': scale,
		'x': int((width - source_width * scale) / 2.0),
		'y': int((height - source_height * scale) / 2.0),
	}


def get_logo_spec(screen_width, screen_height):
	width, height = max(1, int(screen_width)), max(1, int(screen_height))
	if height >= 1000:
		logo_width, logo_height = 469, 481
	elif height >= 800:
		logo_width, logo_height = 352, 361
	else:
		logo_width, logo_height = 235, 241
	scale = min(1.0, float(max(1, width - 48)) / logo_width,
		float(max(1, height - 180)) / logo_height)
	return {
		'image': ASSET_ROOT + 'loading_logo_%dx%d.png' % (logo_width, logo_height),
		'width': logo_width, 'height': logo_height, 'scale': scale,
		'x': int((width - logo_width * scale) / 2.0),
		'y': max(0, int((height - logo_height * scale) / 2.0 - min(40, height // 20))),
	}


def apply_spec(image_box, spec):
	image_box.LoadImage(spec['image'])
	image_box.SetScale(spec['scale'], spec['scale'])
	# Screen artwork uses absolute cover offsets in every locale. A legacy
	# UIScript can otherwise leave right-aligned positioning on the widget.
	align_left = getattr(image_box, 'SetWindowHorizontalAlignLeft', None)
	if align_left:
		align_left()
	image_box.SetPosition(spec['x'], spec['y'])
	filter_setter = getattr(image_box, 'SetLinearFiltering', None)
	if filter_setter:
		filter_setter(True)


def apply_background(image_box, screen_width, screen_height):
	apply_spec(image_box, get_background_spec(screen_width, screen_height))
