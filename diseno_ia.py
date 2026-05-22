import subprocess
import os
import re
try:
    import ollama
except ImportError:
    ollama = None

# Configuración de archivos
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

def run_magick(command):
    """Ejecuta comandos de ImageMagick y maneja errores."""
    try:
        subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error ejecutando: {command}")
        print(f"Detalle: {e.stderr}")
        return False
    return True

def vectorizar_logo():
    """Convierte el logo rasterizado en un vector SVG real usando Potrace."""
    print("Intentando vectorizar logo para calidad infinita...")
    temp_bmp = "temp_logo.bmp"
    run_magick(f"magick {logo_limpio} -threshold 50% -flip {temp_bmp}")
    try:
        # Ejecución silenciosa de potrace
        subprocess.run(f"potrace {temp_bmp} -s -o {logo_vector}", shell=True, check=True, capture_output=True)
        print(f"Efectivo: Vector SVG generado: {logo_vector}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Aviso: Potrace no detectada. Omitiendo generación de SVG.")
    finally:
        if os.path.exists(temp_bmp):
            os.remove(temp_bmp)

def aplicar_nitidez_hd(input_file, output_file, resize_val=None):
    """
    Restauración de la técnica de Super-Sampling estable: 
    Upscale Bicubic -> Downscale Lanczos -> Adaptive Sharpen.
    """
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

def ejecutar_todo():
    if not os.path.exists(logo):
        print("Error: No encuentro 'logo.png'.")
        return

    print("\n--- INICIANDO PRODUCCION MRY (ULTRA HD & VECTOR EDITION) ---")

    # 1. IA: Analizar colores del logo
    print("Consultando paleta de colores a gemma4:31b-cloud...")
    prompt = "Mi logo tiene colores naranja, azul y blanco. Devuelve ÚNICAMENTE una lista de 5 códigos HEX separados por espacios (ej: #FF5733 #0000FF ...). No escribas introducciones ni explicaciones."
    
    try:
        if ollama is None:
            raise ImportError("ollama no disponible")
        response = ollama.chat(model='gemma4:31b-cloud', messages=[
            {'role': 'user', 'content': prompt}
        ])
        content = response['message']['content'].strip()
        colores = re.findall(r'#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})', content)
        if not colores:
            colores = ["#FF8C00", "#0000FF", "#FFFFFF", "#FFA500", "#ADD8E6"]
        else:
            print(f"Colores extraídos: {colores}")
    except Exception:
        print("Aviso: no se pudo consultar Ollama. Usando paleta por defecto.")
        colores = ["#FF8C00", "#0000FF", "#FFFFFF", "#FFA500", "#ADD8E6"]

    # 2. Procesamiento Ultra HD
    print("Procesando imágenes con reconstrucción de bordes...")

    # A) Limpieza Profunda y Creación de Margen (Sin recortar al ras)
    # Eliminamos -trim y añadimos un borde transparente para que el logo respire
    run_magick(
        f"magick {logo} -filter Lanczos -resize {UPSCALE_BASE} "
        f"-fuzz {WHITE_FUZZ} -transparent white "
        f"-channel A -blur 0x0.5 -morphology Erode Disk:1 +channel "
        f"-bordercolor none -border {BORDE_HD} "
        f"-define png:compression-level=9 {logo_limpio}"
    )

    # B) Vectorización
    vectorizar_logo()

    # C) Logos Sólidos Transparentes HD
    print("Generando versiones sólidas transparentes...")
    # Negro Puro HD
    run_magick(f"magick {logo_limpio} -channel RGB -evaluate multiply 0 logo_negro_temp.png")
    aplicar_nitidez_hd("logo_negro_temp.png", "logo_negro_transparente.png")
    
    # Blanco Puro HD
    run_magick(f"magick {logo_limpio} -channel RGB -evaluate multiply 0 -negate logo_blanco_temp.png")
    aplicar_nitidez_hd("logo_blanco_temp.png", "logo_blanco_transparente.png")
    
    if os.path.exists("logo_negro_temp.png"): os.remove("logo_negro_temp.png")
    if os.path.exists("logo_blanco_temp.png"): os.remove("logo_blanco_temp.png")

    # D) Muestras de color HEX
    for i, color in enumerate(colores):
        hex_color = color if color.startswith('#') else f"#{color}"
        run_magick(
            f"magick -size {MUESTRA_COLOR_SIZE} xc:\"{hex_color}\" "
            f"-define png:compression-level=9 color_{i+1}.png"
        )

    # E) Formato WebP (Ultra Lossless)
    run_magick(
        f"magick {logo_limpio} -quality {WEBP_QUALITY} "
        f"-define webp:lossless=true -define webp:method=6 "
        f"-define webp:exact=true logo_web.webp"
    )

    # F) Escala de grises HD
    run_magick(f"magick {logo_limpio} -grayscale Rec709Luma -contrast-stretch 0.15x0.15% logo_bn_temp.png")
    aplicar_nitidez_hd("logo_bn_temp.png", "logo_bn.png")
    if os.path.exists("logo_bn_temp.png"): os.remove("logo_bn_temp.png")

    # G) Icono 512px Super-Sampled
    aplicar_nitidez_hd(logo_limpio, "logo_icono.png", ICONO_SIZE)

    # H) Instagram 1080px Super-Sampled
    run_magick(
        f"magick {logo_limpio} -filter Lanczos -antialias -resize {INSTA_SIZE} "
        f"-background white -gravity center -extent {INSTA_SIZE} logo_insta_temp.png"
    )
    aplicar_nitidez_hd("logo_insta_temp.png", "logo_insta.png")
    if os.path.exists("logo_insta_temp.png"): os.remove("logo_insta_temp.png")

    # I) Marca de agua Ultra HD
    if os.path.exists(imagen_a_procesar):
        # Pre-procesamos el logo la marca de agua para que sea nítido
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
        if os.path.exists("marca_temp.png"): os.remove("marca_temp.png")
    
    print("\n--- PRODUCCION FINALIZADA CON EXITO (CALIDAD INFINITA) ---")
    print("Entregables: logo_vector.svg, Logos B/N Transparentes, Icono HD, Insta HD y Marca de Agua Nítida.")

if __name__ == "__main__":
    ejecutar_todo()
