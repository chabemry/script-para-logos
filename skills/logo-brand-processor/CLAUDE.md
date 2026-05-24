# Logo Brand Processor

Use this workflow when the user wants to process a logo into clean deliverables.

## Trigger

Use when the user asks to:

- clean a logo
- remove the white background
- extract palette colors
- generate PNG/WebP/icon/Instagram versions
- create grayscale or black/white variants
- add the logo as a watermark to a photo

## Command

Run the bundled script:

```powershell
python .\scripts\diseno_ia.py --logo <logo_path> --foto <photo_path> --prefijo <optional_prefix>
```

Examples:

```powershell
python .\scripts\diseno_ia.py --logo .\logo.png
python .\scripts\diseno_ia.py --logo .\mi_logo.png --foto .\producto.jpg
python .\scripts\diseno_ia.py --logo .\mi_logo.png --foto .\producto.jpg --prefijo cliente1
```

## Behavior

- Extract the real palette from the logo image first.
- Continue even if `ollama` is missing.
- Continue even if `potrace` is missing.
- Return final generated filenames to the user.
