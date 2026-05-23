from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


WIDTH = 1200
HEIGHT = 630
ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "lp" / "assets" / "ogp.png"

FONT_CANDIDATES = [
    Path("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"),
    Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
    Path("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"),
]


def find_font() -> tuple[Path, bool]:
    for index, path in enumerate(FONT_CANDIDATES):
        if path.exists():
            return path, index < 2
    raise FileNotFoundError("No usable font found.")


def find_bold_font(font_path: Path, supports_japanese: bool) -> Path:
    if supports_japanese:
        return font_path

    bold_path = font_path.with_name("LiberationSans-Bold.ttf")
    if bold_path.exists():
        return bold_path
    return font_path


def font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size=size)


def hex_to_rgba(value: str, alpha: int = 255) -> tuple[int, int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4)) + (alpha,)


def add_radial_glow(image: Image.Image) -> None:
    glow = Image.new("RGBA", image.size, (0, 0, 0, 0))
    pixels = glow.load()
    cx, cy = 1000, 80
    radius = 400
    r, g, b, max_alpha = hex_to_rgba("#58d68d", int(255 * 0.15))

    for y in range(max(0, cy - radius), min(HEIGHT, cy + radius + 1)):
        for x in range(max(0, cx - radius), min(WIDTH, cx + radius + 1)):
            distance = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            if distance <= radius:
                strength = (1 - distance / radius) ** 2
                pixels[x, y] = (r, g, b, int(max_alpha * strength))

    image.alpha_composite(glow)


def draw_grid(draw: ImageDraw.ImageDraw) -> None:
    color = (255, 255, 255, int(255 * 0.025))
    for x in range(0, WIDTH + 1, 36):
        draw.line((x, 0, x, HEIGHT), fill=color, width=1)
    for y in range(0, HEIGHT + 1, 36):
        draw.line((0, y, WIDTH, y), fill=color, width=1)


def draw_spaced_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    text_font: ImageFont.FreeTypeFont,
    fill: str,
    spacing: int,
) -> None:
    x, y = xy
    for char in text:
        draw.text((x, y), char, font=text_font, fill=fill)
        bbox = draw.textbbox((x, y), char, font=text_font)
        x += bbox[2] - bbox[0] + spacing


def draw_code_segment(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    text: str,
    text_font: ImageFont.FreeTypeFont,
    fill: str,
) -> int:
    draw.text((x, y), text, font=text_font, fill=fill)
    bbox = draw.textbbox((x, y), text, font=text_font)
    return x + bbox[2] - bbox[0]


def draw_terminal(
    draw: ImageDraw.ImageDraw,
    mono_font: ImageFont.FreeTypeFont,
    supports_japanese: bool,
) -> None:
    x0, y0, x1, y1 = 720, 200, 1128, 430
    draw.rounded_rectangle(
        (x0, y0, x1, y1),
        radius=8,
        fill="#101418",
        outline="#27313a",
        width=1,
    )
    draw.rounded_rectangle((x0, y0, x1, y0 + 28), radius=8, fill="#151b21")
    draw.rectangle((x0, y0 + 20, x1, y0 + 28), fill="#151b21")

    for offset, color in zip((16, 32, 48), ("#ff5f57", "#febc2e", "#28c840")):
        cx = x0 + offset
        cy = y0 + 14
        draw.ellipse((cx - 5, cy - 5, cx + 5, cy + 5), fill=color)

    if supports_japanese:
        rows = [
            [("N10", "#58d68d"), (": 変数を初期化する", "#eef3f5")],
            [("N20", "#58d68d"), (": もし ", "#eef3f5"), ("[#100 GT 0]", "#f4b35e"), (" なら", "#eef3f5")],
            [("  ", "#eef3f5"), ("N30", "#58d68d"), (": 加工を開始する", "#eef3f5")],
            [("N40", "#58d68d"), (": プログラムを終了する", "#eef3f5")],
        ]
    else:
        rows = [
            [("N10", "#58d68d"), (": Initialize variables", "#eef3f5")],
            [("N20", "#58d68d"), (": If ", "#eef3f5"), ("[#100 GT 0]", "#f4b35e"), (" then", "#eef3f5")],
            [("  ", "#eef3f5"), ("N30", "#58d68d"), (": Start machining", "#eef3f5")],
            [("N40", "#58d68d"), (": End program", "#eef3f5")],
        ]

    y = y0 + 56
    for row in rows:
        x = x0 + 28
        for text, color in row:
            x = draw_code_segment(draw, x, y, text, mono_font, color)
        y += 40


def main() -> None:
    font_path, supports_japanese = find_font()
    bold_path = find_bold_font(font_path, supports_japanese)

    regular_22 = font(font_path, 22)
    regular_24 = font(font_path, 24)
    regular_36 = font(font_path, 36)
    bold_72 = font(bold_path, 72)
    mono_20 = font(font_path, 20)

    image = Image.new("RGBA", (WIDTH, HEIGHT), "#07090b")
    add_radial_glow(image)
    draw = ImageDraw.Draw(image, "RGBA")
    draw_grid(draw)

    if supports_japanese:
        badge = "v0.1.0 · 開発中"
        subtitle = "NCマクロを読めるフローチャートへ"
    else:
        badge = "v0.1.0 / IN DEVELOPMENT"
        subtitle = "NC macros into readable flowcharts"

    draw_spaced_text(draw, (72, 180), badge, regular_24, "#58d68d", spacing=2)
    draw.text((72, 230), "NC Macro Visualizer", font=bold_72, fill="#eef3f5")
    draw.text((72, 330), subtitle, font=regular_36, fill="#9caab2")
    draw.text(
        (72, 530),
        "henkikobo-cloud.github.io/nc-macro-visualizer",
        font=regular_22,
        fill="#58d68d",
    )
    draw_terminal(draw, mono_20, supports_japanese)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    image.convert("RGB").save(OUTPUT, format="PNG", optimize=True)

    language = "Japanese" if supports_japanese else "English fallback"
    print(f"Generated {OUTPUT} ({WIDTH}x{HEIGHT}, {language}, font={font_path})")


if __name__ == "__main__":
    main()
