# Autodesk ACC — "Type" Dropdown Options

- **Control type**: custom dropdown (non-native `<select>`), React component with `role='option'` ARIA attributes
- **Source**: probed via DevTools Console (`document.querySelectorAll("[role='option']")`)
- **Total options**: 28 (ISO 19650 document type classification)

| # | Code | Name |
|---|------|------|
| 1 | AF | animation file (of a model) |
| 2 | BQ | bill of quantities |
| 3 | CA | calculations |
| 4 | CM | combined model (combined multidiscipline model) |
| 5 | CO | correspondence |
| 6 | CP | cost plan |
| 7 | CR | clash rendition |
| 8 | DB | database |
| 9 | DR | drawing rendition |
| 10 | FN | file note |
| 11 | HS | health and safety |
| 12 | IE | information exchange file |
| 13 | M2 | 2D model |
| 14 | M3 | 3D model |
| 15 | MI | minutes / action notes |
| 16 | MR | model rendition for other renditions |
| 17 | MS | method statement |
| 18 | PP | presentation |
| 19 | PR | programme |
| 20 | RD | room data sheet |
| 21 | RI | request for information |
| 22 | RP | report |
| 23 | SA | schedule of accommodation |
| 24 | SH | schedule |
| 25 | SN | snagging list |
| 26 | SP | specification |
| 27 | SU | survey |
| 28 | VS | visualization |

## Notes

- Option text renders with the code and name concatenated (e.g. `AFanimation file (of a model)`) — prefer substring matching over exact matches in assertions.
- This classification may evolve (new types can be added) — assert on count + spot-check key entries rather than hard-coding the full list.
