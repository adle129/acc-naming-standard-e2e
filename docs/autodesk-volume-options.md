# Autodesk ACC — "Volume/System" Dropdown Options

- **Control type**: custom dropdown (non-native `<select>`), React component with `role='option'` ARIA attributes
- **Source**: probed via DevTools Console (`document.querySelectorAll("[role='option']")`)
- **Total options**: 2

| # | Code | Name |
|---|------|------|
| 1 | ZZ | all volumes/systems |
| 2 | XX | no volume/system applicable |

## Notes

- Option text renders with the code and name concatenated (e.g. `ZZall volumes/systems`) — prefer substring matching over exact matches in assertions.
- `ZZ` / `XX` follow the Uniclass convention for "general / none" entries (`Z` = general, `X` = not applicable).
- Only 2 options — a full-list assertion is safe here.
