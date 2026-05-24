# Logo Brand Processor

When a user asks to process a brand logo, use the bundled script in `scripts/diseno_ia.py`.

## Run

```powershell
python .\scripts\diseno_ia.py --logo <logo_path> --foto <photo_path> --prefijo <optional_prefix>
```

## Use this for

- logo cleanup
- transparent exports
- palette extraction
- icon generation
- Instagram exports
- WebP exports
- grayscale/solid variants
- watermarking a photo with a logo

## Constraints

- Prefer explicit file paths over renaming files.
- Do not fail just because `ollama` or `potrace` are unavailable.
- Surface final output filenames clearly.
