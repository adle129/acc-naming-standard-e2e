# Autodesk ACC — "Level/Location" Dropdown Options

- **Control type**: custom dropdown (non-native `<select>`), React component with `role='option'` ARIA attributes
- **Source**: probed via DevTools Console (`document.querySelectorAll("[role='option']")`)
- **Total options**: 9

| # | Code | Name |
|---|------|------|
| 1 | ZZ | multiple levels/locations |
| 2 | XX | no level/location applicable |
| 3 | 00 | base level |
| 4 | 01 | level 01 |
| 5 | 02 | level 02 |
| 6 | M1 | mezzanine above level 01 |
| 7 | M2 | mezzanine above level 02 |
| 8 | B1 | basement level 1 |
| 9 | B2 | basement level 2 |

## Notes

- Option text renders with the code and name concatenated (e.g. `01level 01`) — prefer substring matching over exact matches in assertions.
- `ZZ` / `XX` follow the Uniclass convention for "general / none" entries (`Z` = general, `X` = not applicable).
- Numeric codes (`00`-`02`), mezzanine (`M1`/`M2`) and basement (`B1`/`B2`) codes follow a building-level numbering convention.
- Only 9 options — a full-list assertion is safe here.
