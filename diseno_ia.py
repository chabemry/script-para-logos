import argparse
import os
import re
import subprocess
from collections import Counter

try:
    import ollama
except ImportError:
    ollama = None

# Configuracion por defecto
DEFAULT_LOGO = "logo.png"
DEFAULT_FOTO = "tu_foto.jpg"
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


def parse_args():
    parser = argparse.ArgumentParser(
        description="Procesa cualquier logo para generar variantes en alta resolucion."
    )
    parser.add_argument(
        "--logo",
        default=DEFAULT_LOGO,
        help="Ruta del logo principal. Por defecto usa logo.png",
    )
    parser.add_argument(
        "--foto",
        default=DEFAULT_FOTO,
        help="Ruta opcional de la foto para aplicar marca de agua. Por defecto usa tu_foto.jpg",
    )
    parser.add_argument(
        "--prefijo",
        default="",
        help="Prefijo opcional para los archivos generados.",
    )
    return parser.parse_args()


def construir_salidas(logo_path, prefijo=""):
    base_name = os.path.splitext(os.path.basename(logo_path))[0]
    slug = re.sub(r"[^A-Za-z0-9_-]+", "_", base_name).strip("_").lower() or "logo"
    if prefijo:
        slug = f"{prefijo}_{slug}"

    return {
        "slug": slug,
        "logo_limpio": f"{slug}_transparente.png",
        "logo_vector": f"{slug}_vector.svg",
        "logo_negro": f"{slug}_negro_transparente.png",
        "logo_blanco": f"{slug}_blanco_transparente.png",
        "logo_bn": f"{slug}_bn.png",
        "logo_icono": f"{slug}_icono.png",
        "logo_insta": f"{slug}_insta.png",
        "logo_web": f"{slug}_web.webp",
        "foto_con_marca": f"{slug}_foto_con_marca.jpg",
        "marca_temp": f"{slug}_marca_temp.png",
        "temp_bmp": f"{slug}_temp_logo.bmp",
        "logo_bn_temp": f"{slug}_bn_temp.png",
        "logo_insta_temp": f"{slug}_insta_temp.png",
        "logo_negro_temp": f"{slug}_negro_temp.png",
        "logo_blanco_temp": f"{slug}_blanco_temp.png",
    }


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


def vectorizar_logo(logo_limpio, logo_vector, temp_bmp):
    """Convierte el logo rasterizado en un SVG usando Potrace si esta disponible."""
    print("Intentando vectorizar logo para calidad infinita...")
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


def obtener_paleta_logo(logo_path):
    print("Extrayendo paleta real desde el logo...")
    colores = extraer_paleta_desde_logo(logo_path)
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
    args = parse_args()
    logo = args.logo
    imagen_a_procesar = args.foto
    salidas = construir_salidas(logo, args.prefijo)
    logo_limpio = salidas["logo_limpio"]
    logo_vector = salidas["logo_vector"]

    if not os.path.exists(logo):
        print(f"Error: No encuentro el logo '{logo}'.")
        return

    print("\n--- INICIANDO PRODUCCION MRY (ULTRA HD & VECTOR EDITION) ---")

    colores = obtener_paleta_logo(logo)

    print("Procesando imagenes con reconstruccion de bordes...")
    run_magick(
        f"magick {logo} -filter Lanczos -resize {UPSCALE_BASE} "
        f"-fuzz {WHITE_FUZZ} -transparent white "
        f"-channel A -blur 0x0.5 -morphology Erode Disk:1 +channel "
        f"-bordercolor none -border {BORDE_HD} "
        f"-define png:compression-level=9 {logo_limpio}"
    )

    vectorizar_logo(logo_limpio, logo_vector, salidas["temp_bmp"])

    print("Generando versiones solidas transparentes...")
    run_magick(f"magick {logo_limpio} -channel RGB -evaluate multiply 0 {salidas['logo_negro_temp']}")
    aplicar_nitidez_hd(salidas["logo_negro_temp"], salidas["logo_negro"])

    run_magick(f"magick {logo_limpio} -channel RGB -evaluate multiply 0 -negate {salidas['logo_blanco_temp']}")
    aplicar_nitidez_hd(salidas["logo_blanco_temp"], salidas["logo_blanco"])

    if os.path.exists(salidas["logo_negro_temp"]):
        os.remove(salidas["logo_negro_temp"])
    if os.path.exists(salidas["logo_blanco_temp"]):
        os.remove(salidas["logo_blanco_temp"])

    for i, color in enumerate(colores):
        hex_color = color if color.startswith("#") else f"#{color}"
        run_magick(
            f'magick -size {MUESTRA_COLOR_SIZE} xc:"{hex_color}" '
            f"-define png:compression-level=9 color_{i+1}.png"
        )

    run_magick(
        f"magick {logo_limpio} -quality {WEBP_QUALITY} "
        f"-define webp:lossless=true -define webp:method=6 "
        f"-define webp:exact=true {salidas['logo_web']}"
    )

    run_magick(f"magick {logo_limpio} -grayscale Rec709Luma -contrast-stretch 0.15x0.15% {salidas['logo_bn_temp']}")
    aplicar_nitidez_hd(salidas["logo_bn_temp"], salidas["logo_bn"])
    if os.path.exists(salidas["logo_bn_temp"]):
        os.remove(salidas["logo_bn_temp"])

    aplicar_nitidez_hd(logo_limpio, salidas["logo_icono"], ICONO_SIZE)

    run_magick(
        f"magick {logo_limpio} -filter Lanczos -antialias -resize {INSTA_SIZE} "
        f"-background white -gravity center -extent {INSTA_SIZE} {salidas['logo_insta_temp']}"
    )
    aplicar_nitidez_hd(salidas["logo_insta_temp"], salidas["logo_insta"])
    if os.path.exists(salidas["logo_insta_temp"]):
        os.remove(salidas["logo_insta_temp"])

    if os.path.exists(imagen_a_procesar):
        run_magick(
            f"magick {logo_limpio} -filter Lanczos -resize {WATERMARK_SCALE} "
            f"-channel A -blur 0x0.35 +channel "
            f"-unsharp 0x0.4+0.4+0.02 {salidas['marca_temp']}"
        )
        run_magick(
            f"magick {imagen_a_procesar} {salidas['marca_temp']} -gravity southeast -geometry +20+20 "
            f"-compose dissolve -define compose:args=60 -composite "
            f"-quality {JPEG_QUALITY} -sampling-factor 4:4:4 {salidas['foto_con_marca']}"
        )
        if os.path.exists(salidas["marca_temp"]):
            os.remove(salidas["marca_temp"])

    print("\n--- PRODUCCION FINALIZADA CON EXITO (CALIDAD INFINITA) ---")
    print(f"Logo procesado: {logo}")
    if os.path.exists(imagen_a_procesar):
        print(f"Foto procesada: {imagen_a_procesar}")
    print(f"Prefijo de salida: {salidas['slug']}")
    print("Entregables: paleta real del logo, PNG transparentes, WebP, icono, Insta y marca de agua.")


if __name__ == "__main__":
    ejecutar_todo()
