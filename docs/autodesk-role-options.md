# Autodesk ACC — "Role" Dropdown Options

- **Control type**: custom dropdown (non-native `<select>`), React component with `role='option'` ARIA attributes
- **Source**: probed via DevTools Console (`document.querySelectorAll("[role='option']")`)
- **Total options**: 20 (ISO 19650 role / discipline classification)

| # | Code | Name |
|---|------|------|
| 1 | A | architect |
| 2 | B | building surveyor |
| 3 | C | civil engineer |
| 4 | D | drainage, highways engineer |
| 5 | E | electrical engineer |
| 6 | F | facilities manager |
| 7 | G | geographical and land surveyor |
| 8 | H | heating and ventilation designer (deprecated) |
| 9 | I | interior designer |
| 10 | K | client |
| 11 | L | landscape architect |
| 12 | M | mechanical engineer |
| 13 | P | public health engineer |
| 14 | Q | quantity surveyor |
| 15 | S | structural engineer |
| 16 | T | town and country planner |
| 17 | W | contractor |
| 18 | X | subcontractor |
| 19 | Y | specialist designer |
| 20 | Z | general (non-disciplinary) |

## Notes

- Option text renders with the code and name concatenated (e.g. `Aarchitect`) — prefer substring matching over exact matches in assertions.
- One entry is marked **(deprecated)** (`H` — heating and ventilation designer); it may still appear in the list, so avoid asserting on its absence.
- The letter codes are not continuous (J, N, O, R, U, V are not used) — they follow the ISO 19650 role classification, not alphabetical completeness.
- This classification may evolve — assert on count + spot-check key entries rather than hard-coding the full list.
