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

Puedes usar los nombres por defecto:

```powershell
python .\diseno_ia.py
```

O pasar cualquier logo y cualquier foto:

```powershell
python .\diseno_ia.py --logo .\mi_logo.png --foto .\mi_foto.jpg
```

Tambien puedes agregar un prefijo para separar salidas:

```powershell
python .\diseno_ia.py --logo .\mi_logo.png --foto .\mi_foto.jpg --prefijo cliente1
```

Si no envias parametros, el script intentara usar:

- `logo.png`
- `tu_foto.jpg` (opcional)

## Salidas esperadas

- `<nombre_logo>_transparente.png`
- `<nombre_logo>_negro_transparente.png`
- `<nombre_logo>_blanco_transparente.png`
- `<nombre_logo>_bn.png`
- `<nombre_logo>_icono.png`
- `<nombre_logo>_insta.png`
- `<nombre_logo>_web.webp`
- `<nombre_logo>_foto_con_marca.jpg` si existe una foto
