"""
scripts/generate_icons.py - Generador de logo e íconos para Montu.
Genera con Pillow:
  - assets/icon.png (1024x1024 con squircle para macOS / general)
  - assets/icon.icns (usando iconutil de macOS)
  - assets/icon.ico (Windows con múltiples capas 16, 32, 48, 64, 128, 256)
  - assets/logo.png (isotipo limpio con fondo transparente para UI y splash)
"""

import os
import shutil
import subprocess
from PIL import Image, ImageDraw


def create_base_logo(size=2048, transparent_bg=False):
    """
    Crea una 'M' estilizada geométrica con estética Dark Finance:
    - Esmeralda (#059669 / #10B981) para la parte izquierda/central
    - Ámbar (#E3B368) para el vértice ascendente derecho (simbolizando USD y COP)
    - Fondo oscuro redondeado (#111827 / #0B0F17) o transparente
    """
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    margin = int(size * 0.08)
    corner_radius = int(size * 0.22)

    if not transparent_bg:
        # Fondo oscuro squircle con borde sutil
        bg_rect = [margin, margin, size - margin, size - margin]
        draw.rounded_rectangle(bg_rect, radius=corner_radius, fill="#0F172A", outline="#1E293B", width=int(size * 0.015))

    # Coordenadas geométricas de la 'M'
    # Centro y proporciones
    left_x = int(size * 0.24)
    mid_left_x = int(size * 0.41)
    center_x = int(size * 0.50)
    mid_right_x = int(size * 0.59)
    right_x = int(size * 0.76)

    top_y = int(size * 0.28)
    bottom_y = int(size * 0.72)
    center_y = int(size * 0.52)
    stroke_w = int(size * 0.09)

    # Colores de marca
    c_emerald = (5, 150, 105, 255)    # #059669
    c_emerald_light = (16, 185, 129, 255) # #10B981
    c_amber = (227, 179, 104, 255)    # #E3B368

    # Trazo 1: Columna vertical izquierda (Esmeralda)
    draw.line([(left_x, bottom_y), (left_x, top_y)], fill=c_emerald, width=stroke_w)
    draw.ellipse([left_x - stroke_w//2, top_y - stroke_w//2, left_x + stroke_w//2, top_y + stroke_w//2], fill=c_emerald)
    draw.ellipse([left_x - stroke_w//2, bottom_y - stroke_w//2, left_x + stroke_w//2, bottom_y + stroke_w//2], fill=c_emerald)

    # Trazo 2: Diagonal descendente izquierda -> centro (Esmeralda brillante)
    draw.line([(left_x, top_y), (center_x, center_y)], fill=c_emerald_light, width=stroke_w)
    draw.ellipse([center_x - stroke_w//2, center_y - stroke_w//2, center_x + stroke_w//2, center_y + stroke_w//2], fill=c_emerald_light)

    # Trazo 3: Diagonal ascendente centro -> derecha (Ámbar)
    draw.line([(center_x, center_y), (right_x, top_y)], fill=c_amber, width=stroke_w)

    # Trazo 4: Columna vertical derecha (Ámbar)
    draw.line([(right_x, top_y), (right_x, bottom_y)], fill=c_amber, width=stroke_w)
    draw.ellipse([right_x - stroke_w//2, top_y - stroke_w//2, right_x + stroke_w//2, top_y + stroke_w//2], fill=c_amber)
    draw.ellipse([right_x - stroke_w//2, bottom_y - stroke_w//2, right_x + stroke_w//2, bottom_y + stroke_w//2], fill=c_amber)

    # Pequeño acento joya en el vértice central (punto de unión de los dos mundos)
    core_dot_r = int(stroke_w * 0.28)
    draw.ellipse([center_x - core_dot_r, center_y - core_dot_r, center_x + core_dot_r, center_y + core_dot_r], fill="#FFFFFF")

    return img


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    assets_dir = os.path.join(base_dir, "assets")
    os.makedirs(assets_dir, exist_ok=True)

    print("🎨 Generando ícono base a alta resolución (2048px)...")
    icon_master = create_base_logo(size=2048, transparent_bg=False)
    icon_1024 = icon_master.resize((1024, 1024), Image.Resampling.LANCZOS)

    # 1. assets/icon.png (1024x1024)
    icon_png_path = os.path.join(assets_dir, "icon.png")
    icon_1024.save(icon_png_path, format="PNG")
    print(f"✅ Guardado: {icon_png_path}")

    # 2. assets/logo.png (fondo transparente para UI / barra lateral)
    logo_master = create_base_logo(size=1024, transparent_bg=True)
    logo_512 = logo_master.resize((512, 512), Image.Resampling.LANCZOS)
    logo_png_path = os.path.join(assets_dir, "logo.png")
    logo_512.save(logo_png_path, format="PNG")
    print(f"✅ Guardado: {logo_png_path}")

    # 3. assets/icon.ico (Windows multicapa)
    ico_path = os.path.join(assets_dir, "icon.ico")
    icon_1024.save(
        ico_path,
        format="ICO",
        sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    )
    print(f"✅ Guardado: {ico_path}")

    # 4. assets/icon.icns (macOS usando iconutil)
    icns_path = os.path.join(assets_dir, "icon.icns")
    if shutil.which("iconutil"):
        print("🍏 Generando assets/icon.icns con iconutil...")
        iconset_dir = os.path.join(assets_dir, "icon.iconset")
        os.makedirs(iconset_dir, exist_ok=True)

        sizes_table = [
            ("icon_16x16.png", 16),
            ("icon_16x16@2x.png", 32),
            ("icon_32x32.png", 32),
            ("icon_32x32@2x.png", 64),
            ("icon_128x128.png", 128),
            ("icon_128x128@2x.png", 256),
            ("icon_256x256.png", 256),
            ("icon_256x256@2x.png", 512),
            ("icon_512x512.png", 512),
            ("icon_512x512@2x.png", 1024),
        ]

        for filename, px_size in sizes_table:
            resized = icon_1024.resize((px_size, px_size), Image.Resampling.LANCZOS)
            resized.save(os.path.join(iconset_dir, filename), format="PNG")

        cmd = ["iconutil", "-c", "icns", iconset_dir, "-o", icns_path]
        subprocess.run(cmd, check=True)
        shutil.rmtree(iconset_dir, ignore_errors=True)
        print(f"✅ Guardado: {icns_path}")
    else:
        print("⚠️ iconutil no encontrado, omitiendo generación de .icns.")

    print("\n🎉 Generación de activos de marca completada con éxito.")


if __name__ == "__main__":
    main()
