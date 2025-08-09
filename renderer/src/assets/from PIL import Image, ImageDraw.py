from PIL import Image, ImageDraw
from math import hypot

# --- Field + Dead Ball + Padding Specs ---
pitch_length = 100
pitch_width = 70
deadball_length = 15
padding = 3

# Canvas dimensions
field_total_length = pitch_length + 2 * deadball_length
field_total_width = pitch_width
canvas_length = field_total_length + 2 * padding
canvas_width = field_total_width + 2 * padding

# Drawing scale
scale = 10  # pixels per meter
img_width = int(canvas_length * scale)
img_height = int(canvas_width * scale)

# Create image
img = Image.new("RGB", (img_width, img_height), "green")
draw = ImageDraw.Draw(img)

# Coordinate converter
def m2px(x_m, y_m):
    x_px = int((x_m + padding) * scale)
    y_px = img_height - int((y_m + padding) * scale)
    return x_px, y_px

# Rectangle helper
def draw_rect_m(x0, y0, x1, y1, **kwargs):
    p0 = m2px(min(x0, x1), max(y0, y1))
    p1 = m2px(max(x0, x1), min(y0, y1))
    draw.rectangle([p0, p1], **kwargs)

# Dashed line drawing (same style for all)
def draw_dashed_line(x0, y0, x1, y1, dash_length=12, gap_length=8, width=2, fill="white"):
    total_length = hypot(x1 - x0, y1 - y0)
    dx = x1 - x0
    dy = y1 - y0
    num_dashes = int(total_length // (dash_length + gap_length))
    
    for i in range(num_dashes + 1):
        start_frac = i * (dash_length + gap_length) / total_length
        end_frac = min(start_frac + dash_length / total_length, 1.0)
        x_start = x0 + dx * start_frac
        y_start = y0 + dy * start_frac
        x_end = x0 + dx * end_frac
        y_end = y0 + dy * end_frac
        draw.line([(x_start, y_start), (x_end, y_end)], fill=fill, width=width)

# Main coordinates
pitch_x0 = deadball_length
pitch_x1 = deadball_length + pitch_length
pitch_origin_x = pitch_x0

# Draw pitch
draw_rect_m(pitch_x0, 0, pitch_x1, pitch_width, outline="white", width=3)
draw_rect_m(0, 0, deadball_length, pitch_width, outline="white", width=2)
draw_rect_m(pitch_x1, 0, field_total_length, pitch_width, outline="white", width=2)

# Vertical full pitch markings
for x in [22, 50, 78]:
    px = pitch_x0 + x
    draw.line([m2px(px, 0), m2px(px, pitch_width)], fill="white", width=2)

# Center spot
center = m2px(pitch_x0 + 50, pitch_width / 2)
r = 4
draw.ellipse([center[0] - r, center[1] - r, center[0] + r, center[1] + r], fill="white")

# --- Dashed Lines ---

# Vertical dashed lines (X fixed)
dashed_x_lines = [5, 40, 60, 95]
for x in dashed_x_lines:
    full_x = pitch_origin_x + x
    x_px0, y_px0 = m2px(full_x, 2.5)
    x_px1, y_px1 = m2px(full_x, pitch_width)
    draw_dashed_line(x_px0, y_px0, x_px1, y_px1, dash_length=scale*5, gap_length=scale*5, width=2)

# Horizontal dashed lines (Y fixed, broken segments only)
# --- Horizontal short dashed segments ONLY at vertical marker locations ---
dashed_y_lines = [5, 15, 55, 65]
marker_x_lines = [7.5, 22, 40, 50, 60, 78, 92.5]
segment_half = 2.5  # 5m total segment

for y in dashed_y_lines:
    for x in marker_x_lines:
        full_x0 = pitch_origin_x + (x - segment_half)
        full_x1 = pitch_origin_x + (x + segment_half)
        y_px = m2px(0, y)[1]
        x_px0 = m2px(full_x0, 0)[0]
        x_px1 = m2px(full_x1, 0)[0]
        draw.line([(x_px0, y_px), (x_px1, y_px)], fill="white", width=2)

# --- Goalposts ---
post_offset = 3
post_thickness = 3

def draw_posts_at(x_m):
    y1 = (pitch_width / 2) - post_offset
    y2 = (pitch_width / 2) + post_offset
    x_px, y_px1 = m2px(x_m, y1)
    _,    y_px2 = m2px(x_m, y2)

    # Vertical post
    draw.line([(x_px, y_px1), (x_px, y_px2)], fill="black", width=post_thickness)

    # Thin crossbar
    draw.line([(x_px, y_px1), (x_px, y_px2)], fill="black", width=2)

    # End circles
    circle_radius = 4
    for y_px in [y_px1, y_px2]:
        draw.ellipse(
            [(x_px - circle_radius, y_px - circle_radius), (x_px + circle_radius, y_px + circle_radius)],
            fill="black"
        )

# Draw posts
draw_posts_at(deadball_length)
draw_posts_at(deadball_length + pitch_length)

# Save image
img.save("rugby_pitch_dashed_styled_correct.png")
