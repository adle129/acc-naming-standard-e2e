# Autodesk ACC — "Status" Dropdown Options

- **Control type**: custom dropdown (non-native `<select>`), React component with `role='option'` ARIA attributes
- **Source**: probed via DevTools Console (`document.querySelectorAll("[role='option']")`)
- **Total options**: 24 (ISO 19650 status / suitability classification)

## Suitability statuses (S-codes)

| # | Code | Name |
|---|------|------|
| 1 | S0 | Initial status |
| 2 | S1 | Suitable for coordination |
| 3 | S2 | Suitable for information |
| 4 | S3 | Suitable for review and comment |
| 5 | S4 | Suitable for stage approval |
| 6 | S6 | Suitable for PIM authorization |
| 7 | S7 | Suitable for AIM authorization |

## Authorized and accepted (A-codes)

| # | Code | Name |
|---|------|------|
| 8 | A0 | Authorized and accepted for Strategy work stage |
| 9 | A1 | Authorized and accepted for Brief work stage |
| 10 | A2 | Authorized and accepted for Concept work stage |
| 11 | A3 | Authorized and accepted for Definition work stage |
| 12 | A4 | Authorized and accepted for Design work stage |
| 13 | A5 | Authorized and accepted for Construct and Commission work stage |
| 14 | A6 | Authorized and accepted for Handover and Close-out work stage |
| 15 | A7 | Authorized and accepted for Operation and End of life work stage |

## Partial sign-off (B-codes)

| # | Code | Name |
|---|------|------|
| 16 | B0 | Partial sign-off for Strategy work stage |
| 17 | B1 | Partial sign-off for Brief work stage |
| 18 | B2 | Partial sign-off for Concept work stage |
| 19 | B3 | Partial sign-off for Definition work stage |
| 20 | B4 | Partial sign-off for Design work stage |
| 21 | B5 | Partial sign-off for Construct and Commission work stage |
| 22 | B6 | Partial sign-off for Handover and Close-out work stage |
| 23 | B7 | Partial sign-off for Operation and End of life work stage |

## Record status

| # | Code | Name |
|---|------|------|
| 24 | CR | As constructed record document |

## Notes

- Option text renders with the code and name concatenated (e.g. `S0Initial status`) — prefer substring matching over exact matches in assertions.
- `S5` is not used (the S-codes skip from S4 to S6) — not a page bug, it follows the ISO 19650 classification.
- The A/B codes cover the same 8 lifecycle work stages (Strategy → Brief → Concept → Definition → Design → Construct and Commission → Handover and Close-out → Operation and End of life).
- This classification may evolve — assert on count + spot-check key entries rather than hard-coding the full list.
