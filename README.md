# Script para logos

Script en Python para limpiar un logo, generar variantes en alta resolucion y crear entregables listos para uso web, redes y marca de agua.

## Archivo principal

- `diseno_ia.py`

## Requisitos

- Python
- ImageMagick (`magick`)
- Opcional: `ollama`
- Opcional: `potrace`

## Uso

Coloca en esta carpeta:

- `logo.png`
- `tu_foto.jpg` (opcional)

Luego ejecuta:

```powershell
python .\diseno_ia.py
```

## Salidas esperadas

- `logo_transparente.png`
- `logo_negro_transparente.png`
- `logo_blanco_transparente.png`
- `logo_bn.png`
- `logo_icono.png`
- `logo_insta.png`
- `logo_web.webp`
- `foto_con_marca.jpg` si existe `tu_foto.jpg`

