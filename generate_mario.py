import os
import json
import math
import urllib.request


def fetch_contributions(username, token):
    query = """
    query($userName:String!) {
      user(login: $userName){
        contributionsCollection {
          contributionCalendar {
            weeks {
              contributionDays {
                contributionLevel
              }
            }
          }
        }
      }
    }
    """
    req = urllib.request.Request(
        'https://api.github.com/graphql',
        data=json.dumps({'query': query, 'variables': {'userName': username}}).encode('utf-8'),
        headers={'Authorization': f'Bearer {token}'}
    )
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            return data['data']['user']['contributionsCollection']['contributionCalendar']['weeks']
    except Exception as e:
        print(f"Error fetching data from GitHub API: {e}")
        return []


def draw_sprite(name, pixels, colors, scale, is_def=True):
    svg = [f'    <g id="{name}">'] if is_def else ['    <g>']
    for y_idx, row_str in enumerate(pixels):
        for x_idx, char in enumerate(row_str):
            if char in colors:
                px = x_idx * scale
                py = y_idx * scale
                svg.append(f'      <rect x="{px:.1f}" y="{py:.1f}" width="{scale}" height="{scale}" fill="{colors[char]}" />')
    svg.append('    </g>')
    return "\n".join(svg)


# ---------- helper untuk menghitung panjang lintasan ----------
def quad_point(p0, c, p1, t):
    u = 1 - t
    return (u * u * p0[0] + 2 * u * t * c[0] + t * t * p1[0],
            u * u * p0[1] + 2 * u * t * c[1] + t * t * p1[1])


def quad_length(p0, c, p1, t_max=1.0, steps=24):
    length, prev = 0.0, p0
    for i in range(1, steps + 1):
        pt = quad_point(p0, c, p1, t_max * i / steps)
        length += math.dist(prev, pt)
        prev = pt
    return length


def clamp01(v):
    return max(0.0, min(1.0, v))


def generate_mario_github_svg(filename="mario_contribution.svg"):
    username = os.environ.get("GITHUB_ACTOR", "User")
    token = os.environ.get("GITHUB_TOKEN")

    weeks_data = fetch_contributions(username, token) if token else []

    # --- LEVEL SETTINGS ---
    cell_size = 10
    gap = 4
    step = cell_size + gap
    cols = len(weeks_data) if weeks_data else 53
    rows = 7
    dur = 20  # durasi animasi (detik)

    grid_x_offset = 40
    top_padding = 40

    flag_x = grid_x_offset + (cols * step) + 15
    castle_x = flag_x + 35

    width = castle_x + 80
    height = top_padding + (rows * step) + 40
    ground_y = top_padding + (rows * step)

    level_map = {
        'NONE': 'empty', 'FIRST_QUARTILE': 'lvl1',
        'SECOND_QUARTILE': 'lvl2', 'THIRD_QUARTILE': 'lvl3', 'FOURTH_QUARTILE': 'lvl4'
    }

    # SVG Wrapper
    svg_elements = [
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">',
        '  <style>',
        '    .bg { fill: #87CEEB; }',
        '    .lvl1 { fill: #0e4429; rx: 2; ry: 2; stroke: #000; stroke-width: 0.5; }',
        '    .lvl2 { fill: #006d32; rx: 2; ry: 2; stroke: #000; stroke-width: 0.5; }',
        '    .lvl3 { fill: #26a641; rx: 2; ry: 2; stroke: #000; stroke-width: 0.5; }',
        '    .lvl4 { fill: #39d353; rx: 2; ry: 2; stroke: #000; stroke-width: 0.5; }',
        '    .ground { fill: #c84c0c; }',
        '    .ground-top { fill: #000000; }',
        '  </style>',
        '  <defs>'
    ]

    # Sprite Art
    mario_pixels = [
        "  RRRRR     ", " RRRRRRRRR  ", " BBSSSO     ", " BOSSSOOOO  ",
        " BOSSSOOOO  ", "  BOOOOO    ", "  RROORR    ", " RRROORRR   ",
        " RRROORRRR  ", " SSRRRRYSS  ", " SSS  SSS   ", "BBBB  BBBB  "
    ]
    cloud_pixels = ["      WWWW      ", "   WWWWWWWWWW   ", " WWWWWWWWWWWWWW ", " WWWWWWWWWWWWWW "]
    bush_pixels = ["      GGGG      ", "   GGGGGGGGGG   ", " GGGGGGGGGGGGGG ", " GGGGGGGGGGGGGG "]
    coin_pixels = ["  YYYY  ", " YYOOYY ", " YOOOOY ", " YOOOOY ", " YYOOYY ", "  YYYY  "]

    mario_colors = {'R': '#e52521', 'S': '#ffcca6', 'B': '#8B4513', 'O': '#2038ec', 'Y': '#f8d820'}

    svg_elements.append(draw_sprite("mario", mario_pixels, mario_colors, 1.2))
    svg_elements.append(draw_sprite("cloud", cloud_pixels, {'W': '#FFFFFF'}, 2.0))
    svg_elements.append(draw_sprite("bush", bush_pixels, {'G': '#00A800'}, 2.0))
    svg_elements.append(draw_sprite("coin", coin_pixels, {'Y': '#f8d820', 'O': '#d8a000'}, 1.2))
    svg_elements.append('  </defs>')

    # Sky & Scenery
    svg_elements.append('  <rect width="100%" height="100%" class="bg" />')
    for i in range(4):
        svg_elements.append(f'  <use href="#cloud" x="0" y="{10 if i % 2 == 0 else 30}">')
        svg_elements.append(f'    <animate attributeName="x" from="{width}" to="-100" dur="{40 + (i * 5)}s" repeatCount="indefinite" />')
        svg_elements.append('  </use>')

    # Ground & Bushes
    svg_elements.append(f'  <rect x="0" y="{ground_y}" width="{width}" height="{height - ground_y}" class="ground" />')
    svg_elements.append(f'  <rect x="0" y="{ground_y}" width="{width}" height="2" class="ground-top" />')
    for i in range(10):
        svg_elements.append(f'  <use href="#bush" x="{i * 120 + 30}" y="{ground_y - 8}" />')

    # Start Pipe
    pipe_x, pipe_top = 10, ground_y - 30
    svg_elements.append(f'  <rect x="{pipe_x}" y="{pipe_top}" width="24" height="30" fill="#00A800" stroke="#000"/>')
    svg_elements.append(f'  <rect x="{pipe_x - 2}" y="{pipe_top}" width="28" height="10" fill="#00A800" stroke="#000"/>')

    # --- PATHFINDING + BRICK PLACEMENT (sinkron dengan panjang lintasan) ---
    mario_height = 14
    path_d = f"M {pipe_x + 4} {ground_y} L {pipe_x + 4} {pipe_top - mario_height} "
    cur = (pipe_x + 4, pipe_top - mario_height)
    dist = ground_y - cur[1]          # jarak tempuh Mario sejauh ini
    coin_events = []                  # (x, y, jarak)
    brick_events = []                 # (x, y, jarak)
    last_brick_x = -999

    for col, week in enumerate(weeks_data):
        highest_block_row = rows      # default: berdiri di tanah kalau minggu kosong
        col_x = grid_x_offset + col * step
        week_coins = []

        for row, day in enumerate(week.get('contributionDays', [])):
            lvl = level_map.get(day.get('contributionLevel', 'NONE'), 'empty')
            block_y = top_padding + row * step
            if lvl == 'empty':
                continue  # kotak kosong tidak digambar sama sekali
            svg_elements.append(
                f'  <rect x="{col_x}" y="{block_y}" width="{cell_size}" '
                f'height="{cell_size}" class="{lvl}" />'
            )
            highest_block_row = min(highest_block_row, row)
            if lvl == 'lvl4':
                week_coins.append((col_x, block_y - 12))

        target = (col_x, (top_padding + highest_block_row * step) - mario_height)
        should_jump = (col % 4 == 2) or abs(target[1] - cur[1]) > 12

        if should_jump:
            ctrl = ((cur[0] + target[0]) / 2, min(cur[1], target[1]) - 40)
            apex = quad_point(cur, ctrl, target, 0.5)
            apex_dist = dist + quad_length(cur, ctrl, target, 0.5)
            dist += quad_length(cur, ctrl, target)
            path_d += f" Q {ctrl[0]:.1f} {ctrl[1]:.1f} {target[0]} {target[1]} "
            # bata tepat di atas kepala Mario saat titik tertinggi lompatan,
            # jaga jarak antar bata supaya tidak menumpuk
            if apex[0] - last_brick_x >= 60:
                brick_events.append((apex[0] + 7 - 9, apex[1] - 20, apex_dist))
                last_brick_x = apex[0]
        else:
            dist += math.dist(cur, target)
            path_d += f" L {target[0]} {target[1]} "

        for cx, cy in week_coins:
            coin_events.append((cx, cy, dist))   # koin diambil saat Mario tiba di kolom ini
        cur = target

    # End path: lompat ke tiang -> meluncur turun -> jalan ke kastil
    flag_top = top_padding - 10
    jump_end = (flag_x - 4, flag_top + 10)
    ctrl = (cur[0] + 10, cur[1] - 20)
    dist += quad_length(cur, ctrl, jump_end)
    d_grab = dist
    path_d += f" Q {ctrl[0]} {ctrl[1]} {jump_end[0]} {jump_end[1]} "

    slide_end = (flag_x - 4, ground_y - mario_height)
    dist += math.dist(jump_end, slide_end)
    d_slide_end = dist
    path_d += f" L {slide_end[0]} {slide_end[1]} "

    castle_end = (castle_x + 15, ground_y - mario_height)
    dist += math.dist(slide_end, castle_end)
    path_d += f" L {castle_end[0]} {castle_end[1]} "
    total = max(1.0, dist)

    # BATA (dengan animasi "kepentok" saat Mario lewat)
    for bx, by, d in brick_events:
        t = clamp01(d / total)
        t1, t2 = min(t + 0.008, 0.995), min(t + 0.016, 0.999)
        svg_elements.append('  <g>')
        svg_elements.append(
            f'    <animateTransform attributeName="transform" type="translate" '
            f'values="0,0; 0,0; 0,-5; 0,0; 0,0" keyTimes="0;{t:.4f};{t1:.4f};{t2:.4f};1" '
            f'dur="{dur}s" repeatCount="indefinite" />'
        )
        svg_elements.append(
            f'    <rect x="{bx:.1f}" y="{by:.1f}" width="18" height="18" '
            f'fill="#C84C0C" stroke="#6B2608" stroke-width="1.5" />'
            f'<path d="M {bx:.1f} {by + 9:.1f} H {bx + 18:.1f} '
            f'M {bx + 9:.1f} {by:.1f} V {by + 9:.1f} '
            f'M {bx + 4.5:.1f} {by + 9:.1f} V {by + 18:.1f} '
            f'M {bx + 13.5:.1f} {by + 9:.1f} V {by + 18:.1f}" '
            f'stroke="#6B2608" stroke-width="1" fill="none" />'
        )
        svg_elements.append('  </g>')

    # KOIN
    for cx, cy, d in coin_events:
        t = clamp01(d / total)
        t_end = min(1.0, t + 0.02)
        svg_elements.append(f'  <g transform="translate({cx}, {cy})">')
        svg_elements.append('    <g>')
        svg_elements.append(f'      <animateTransform attributeName="transform" type="translate" values="0,0; 0,0; 0,-20; 0,-20" keyTimes="0;{t:.4f};{t_end:.4f};1" dur="{dur}s" repeatCount="indefinite" />')
        svg_elements.append(f'      <animate attributeName="opacity" values="1;1;0;0" keyTimes="0;{t:.4f};{t_end:.4f};1" dur="{dur}s" repeatCount="indefinite" />')
        svg_elements.append('      <use href="#coin" x="0" y="0" />')
        svg_elements.append('    </g>')
        svg_elements.append('  </g>')

    # TIANG & BENDERA (turun pas Mario meluncur)
    t_flag = clamp01(d_grab / total)
    t_flag_end = clamp01(d_slide_end / total)

    svg_elements.append(f'  <rect x="{flag_x}" y="{flag_top}" width="3" height="{ground_y - flag_top}" fill="#FFF" stroke="#000" stroke-width="0.5"/>')
    svg_elements.append(f'  <circle cx="{flag_x + 1.5}" cy="{flag_top}" r="4" fill="#f8d820" stroke="#000"/>')
    svg_elements.append('  <g>')
    svg_elements.append(f'    <animateTransform attributeName="transform" type="translate" values="0,0; 0,0; 0,{ground_y - flag_top - 15}; 0,{ground_y - flag_top - 15}" keyTimes="0;{t_flag:.4f};{t_flag_end:.4f};1" dur="{dur}s" repeatCount="indefinite" />')
    svg_elements.append(f'    <polygon points="{flag_x-15},{flag_top+5} {flag_x},{flag_top+5} {flag_x},{flag_top+15}" fill="#00A800" stroke="#000"/>')
    svg_elements.append('  </g>')

    # ATTACH MARIO
    svg_elements.append(f'  <path id="parkour-path" d="{path_d}" fill="none" stroke="none" />')
    svg_elements.append('  <use href="#mario">')
    svg_elements.append(f'    <animateMotion dur="{dur}s" repeatCount="indefinite"><mpath href="#parkour-path"/></animateMotion>')
    svg_elements.append('  </use>')

    # FOREGROUND CASTLE (Drawn AFTER Mario to hide him inside the door)
    castle_y = ground_y - 40
    svg_elements.append('  <!-- Castle Foreground -->')
    svg_elements.append(f'  <path d="M {castle_x} {ground_y} L {castle_x} {castle_y} L {castle_x+10} {castle_y} L {castle_x+10} {castle_y+10} L {castle_x+20} {castle_y+10} L {castle_x+20} {castle_y} L {castle_x+30} {castle_y} L {castle_x+30} {castle_y+10} L {castle_x+40} {castle_y+10} L {castle_x+40} {castle_y} L {castle_x+50} {castle_y} L {castle_x+50} {ground_y} Z" fill="#c84c0c" stroke="#000" stroke-width="1" />')
    svg_elements.append(f'  <path d="M {castle_x+15} {ground_y} L {castle_x+15} {ground_y-20} A 10 10 0 0 1 {castle_x+35} {ground_y-20} L {castle_x+35} {ground_y} Z" fill="#000" />')

    # LEVEL CLEAR TEXT (muncul setelah bendera turun)
    t_text = min(t_flag_end, 0.95)
    t_text_a = min(t_text + 0.01, 0.97)
    t_text_b = min(t_text + 0.02, 0.975)
    svg_elements.append(f'  <text x="{flag_x - 70}" y="{top_padding - 10}" fill="#f8d820" font-family="monospace" font-weight="bold" font-size="16" stroke="#000" stroke-width="1" opacity="0">')
    svg_elements.append('    LEVEL CLEAR!')
    svg_elements.append(f'    <animate attributeName="opacity" values="0;0;1;1;0" keyTimes="0;{t_text:.4f};{t_text_a:.4f};0.98;1" dur="{dur}s" repeatCount="indefinite" />')
    svg_elements.append(f'    <animateTransform attributeName="transform" type="translate" values="0,10; 0,10; 0,0; 0,0" keyTimes="0;{t_text:.4f};{t_text_b:.4f};1" dur="{dur}s" repeatCount="indefinite" />')
    svg_elements.append('  </text>')

    svg_elements.append('</svg>')

    with open(filename, "w") as f:
        f.write("\n".join(svg_elements))
    print(f"Successfully generated Interactive {filename}!")


if __name__ == "__main__":
    generate_mario_github_svg()
