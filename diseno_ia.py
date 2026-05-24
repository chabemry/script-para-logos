import os
import re
import subprocess
from collections import Counter

try:
    import ollama
except ImportError:
    ollama = None

# Configuracion de archivos
logo = "logo.png"
logo_limpio = "logo_transparente.png"
imagen_a_procesar = "tu_foto.jpg"
logo_vector = "logo_vector.svg"
UPSCALE_BASE = "400%"
BORDE_HD = "200x200"
MUESTRA_COLOR_SIZE = "1200x1200"
ICONO_SIZE = "2048x2048"
INSTA_SIZE = "2160x2160"
WATERMARK_SCALE = "25%"
WEBP_QUALITY = 100
JPEG_QUALITY = 95
WHITE_FUZZ = "18%"
DEFAULT_PALETTE = ["#0D284D", "#263C5D", "#3193CF", "#F86908", "#DDAB66"]


def run_magick(command):
    """Ejecuta comandos de ImageMagick y maneja errores."""
    try:
        subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"Error ejecutando: {command}")
        print(f"Detalle: {e.stderr}")
        return False
    return True


def rgb_a_hex(r, g, b):
    return f"#{r:02X}{g:02X}{b:02X}"


def brillo_aproximado(r, g, b):
    return (0.299 * r) + (0.587 * g) + (0.114 * b)


def extraer_paleta_desde_logo(input_file, max_colors=5):
    """
    Extrae una paleta real desde el logo usando ImageMagick.
    Filtra blancos y grises del fondo y prioriza azules, naranjas y dorados.
    """
    try:
        cmd = f'magick "{input_file}" -alpha off -resize 25% -colors 24 -unique-colors txt:-'
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError:
        return []

    familias = {
        "azul_oscuro": [],
        "azul_claro": [],
        "naranja": [],
        "dorado": [],
        "otros": [],
    }
    for line in result.stdout.splitlines():
        match = re.search(r"\((\d+),(\d+),(\d+)\)\s+#([A-Fa-f0-9]{6})", line)
        if not match:
            continue

        r, g, b = map(int, match.groups()[:3])
        brillo = brillo_aproximado(r, g, b)
        variacion = max(r, g, b) - min(r, g, b)

        if brillo > 235:
            continue
        if variacion < 18 and brillo > 80:
            continue

        score = variacion
        color_hex = rgb_a_hex(r, g, b)

        if b > r and b > g:
            score += 120
            if brillo < 95:
                familias["azul_oscuro"].append((score, color_hex))
            else:
                familias["azul_claro"].append((score, color_hex))
            continue

        if r > 200 and g > 90 and b < 80:
            score += 110
            familias["naranja"].append((score, color_hex))
            continue

        if r > 170 and g > 140 and b < 130:
            score += 90
            familias["dorado"].append((score, color_hex))
            continue

        familias["otros"].append((score, color_hex))

    paleta = []
    usados = Counter()
    orden_preferido = ["azul_oscuro", "azul_claro", "naranja", "dorado", "otros"]
    for familia in orden_preferido:
        for _, color in sorted(familias[familia], reverse=True):
            if usados[color]:
                continue
            paleta.append(color)
            usados[color] += 1
            break

    if len(paleta) < max_colors:
        resto = []
        for familia in orden_preferido:
            resto.extend(sorted(familias[familia], reverse=True))
        for _, color in resto:
            if usados[color]:
                continue
            paleta.append(color)
            usados[color] += 1
            if len(paleta) == max_colors:
                break

    paleta = paleta[:max_colors]
    return paleta


def vectorizar_logo():
    """Convierte el logo rasterizado en un SVG usando Potrace si esta disponible."""
    print("Intentando vectorizar logo para calidad infinita...")
    temp_bmp = "temp_logo.bmp"
    run_magick(f"magick {logo_limpio} -threshold 50% -flip {temp_bmp}")
    try:
        subprocess.run(
            f"potrace {temp_bmp} -s -o {logo_vector}",
            shell=True,
            check=True,
            capture_output=True,
            text=True,
        )
        print(f"SVG generado: {logo_vector}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Aviso: Potrace no detectada. Omitiendo generacion de SVG.")
    finally:
        if os.path.exists(temp_bmp):
            os.remove(temp_bmp)


def aplicar_nitidez_hd(input_file, output_file, resize_val=None):
    """Escalado suave para preservar bordes limpios sin crear halos fuertes."""
    if resize_val:
        cmd = (
            f"magick {input_file} -filter Lanczos -resize 200% "
            f"-filter Lanczos -antialias -resize {resize_val} "
            f"-channel A -blur 0x0.35 +channel "
            f"-unsharp 0x0.5+0.6+0.02 {output_file}"
        )
    else:
        cmd = (
            f"magick {input_file} -channel A -blur 0x0.35 +channel "
            f"-unsharp 0x0.4+0.5+0.02 {output_file}"
        )
    run_magick(cmd)


def obtener_paleta_logo():
    print("Extrayendo paleta real desde el logo...")
    colores = extraer_paleta_desde_logo(logo)
    if colores:
        print(f"Colores detectados desde el logo: {colores}")
        return colores

    print("Aviso: no se pudo extraer la paleta del logo.")
    print("Intentando consulta asistida con Ollama...")
    prompt = "Mi logo tiene colores naranja, azul y blanco. Devuelve UNICAMENTE una lista de 5 codigos HEX separados por espacios."
    try:
        if ollama is None:
            raise ImportError("ollama no disponible")
        response = ollama.chat(
            model="gemma4:31b-cloud",
            messages=[{"role": "user", "content": prompt}],
        )
        content = response["message"]["content"].strip()
        colores = [f"#{c}" for c in re.findall(r"#?([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})", content)]
        if colores:
            print(f"Colores sugeridos por Ollama: {colores}")
            return colores[:5]
    except Exception:
        pass

    print("Aviso: usando paleta por defecto optimizada para el logo.")
    return DEFAULT_PALETTE.copy()


def ejecutar_todo():
    if not os.path.exists(logo):
        print("Error: No encuentro 'logo.png'.")
        return

    print("\n--- INICIANDO PRODUCCION MRY (ULTRA HD & VECTOR EDITION) ---")

    colores = obtener_paleta_logo()

    print("Procesando imagenes con reconstruccion de bordes...")
    run_magick(
        f"magick {logo} -filter Lanczos -resize {UPSCALE_BASE} "
        f"-fuzz {WHITE_FUZZ} -transparent white "
        f"-channel A -blur 0x0.5 -morphology Erode Disk:1 +channel "
        f"-bordercolor none -border {BORDE_HD} "
        f"-define png:compression-level=9 {logo_limpio}"
    )

    vectorizar_logo()

    print("Generando versiones solidas transparentes...")
    run_magick(f"magick {logo_limpio} -channel RGB -evaluate multiply 0 logo_negro_temp.png")
    aplicar_nitidez_hd("logo_negro_temp.png", "logo_negro_transparente.png")

    run_magick(f"magick {logo_limpio} -channel RGB -evaluate multiply 0 -negate logo_blanco_temp.png")
    aplicar_nitidez_hd("logo_blanco_temp.png", "logo_blanco_transparente.png")

    if os.path.exists("logo_negro_temp.png"):
        os.remove("logo_negro_temp.png")
    if os.path.exists("logo_blanco_temp.png"):
        os.remove("logo_blanco_temp.png")

    for i, color in enumerate(colores):
        hex_color = color if color.startswith("#") else f"#{color}"
        run_magick(
            f'magick -size {MUESTRA_COLOR_SIZE} xc:"{hex_color}" '
            f"-define png:compression-level=9 color_{i+1}.png"
        )

    run_magick(
        f"magick {logo_limpio} -quality {WEBP_QUALITY} "
        f"-define webp:lossless=true -define webp:method=6 "
        f"-define webp:exact=true logo_web.webp"
    )

    run_magick(f"magick {logo_limpio} -grayscale Rec709Luma -contrast-stretch 0.15x0.15% logo_bn_temp.png")
    aplicar_nitidez_hd("logo_bn_temp.png", "logo_bn.png")
    if os.path.exists("logo_bn_temp.png"):
        os.remove("logo_bn_temp.png")

    aplicar_nitidez_hd(logo_limpio, "logo_icono.png", ICONO_SIZE)

    run_magick(
        f"magick {logo_limpio} -filter Lanczos -antialias -resize {INSTA_SIZE} "
        f"-background white -gravity center -extent {INSTA_SIZE} logo_insta_temp.png"
    )
    aplicar_nitidez_hd("logo_insta_temp.png", "logo_insta.png")
    if os.path.exists("logo_insta_temp.png"):
        os.remove("logo_insta_temp.png")

    if os.path.exists(imagen_a_procesar):
        run_magick(
            f"magick {logo_limpio} -filter Lanczos -resize {WATERMARK_SCALE} "
            f"-channel A -blur 0x0.35 +channel "
            f"-unsharp 0x0.4+0.4+0.02 marca_temp.png"
        )
        run_magick(
            f"magick {imagen_a_procesar} marca_temp.png -gravity southeast -geometry +20+20 "
            f"-compose dissolve -define compose:args=60 -composite "
            f"-quality {JPEG_QUALITY} -sampling-factor 4:4:4 foto_con_marca.jpg"
        )
        if os.path.exists("marca_temp.png"):
            os.remove("marca_temp.png")

    print("\n--- PRODUCCION FINALIZADA CON EXITO (CALIDAD INFINITA) ---")
    print("Entregables: paleta real del logo, PNG transparentes, WebP, icono, Insta y marca de agua.")


if __name__ == "__main__":
    ejecutar_todo()
