---
name: logo-brand-processor
description: Use this skill when the user wants to clean a logo, remove white background, extract a real color palette, generate transparent PNG variants, icon, Instagram version, WebP, grayscale version, vector attempt, or watermark a photo using any logo file and optional photo input.
---

# Logo Brand Processor

Use this skill for reusable logo processing workflows.

## Inputs

- A logo image, usually PNG, JPG, or WEBP
- An optional photo for watermarking
- An optional output prefix

## Default execution

Run:

```powershell
python .\scripts\diseno_ia.py --logo .\logo.png --foto .\tu_foto.jpg
```

If no photo is needed:

```powershell
python .\scripts\diseno_ia.py --logo .\logo.png
```

If the user wants separated outputs:

```powershell
python .\scripts\diseno_ia.py --logo .\mi_logo.png --foto .\mi_foto.jpg --prefijo cliente1
```

## Workflow

1. Verify the logo file exists.
2. Run the bundled script with the provided logo and optional photo.
3. Return the generated files with their final names.
4. If `ollama` is unavailable, rely on image-based palette extraction and built-in fallback colors.
5. If `potrace` is unavailable, continue without SVG output.

## Outputs

For a logo named `mi_logo.png`, expected outputs are:

- `mi_logo_transparente.png`
- `mi_logo_negro_transparente.png`
- `mi_logo_blanco_transparente.png`
- `mi_logo_bn.png`
- `mi_logo_icono.png`
- `mi_logo_insta.png`
- `mi_logo_web.webp`
- `mi_logo_vector.svg` when `potrace` is available
- `mi_logo_foto_con_marca.jpg` when a photo is provided

## Notes

- Prefer passing explicit file paths instead of renaming user files.
- This skill is intended to be portable across Codex-like agents.
- For Claude or other agents that use repository instructions, mirror the behavior from `CLAUDE.md` or `AGENTS.md` in this folder.
