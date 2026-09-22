# Autodesk ACC — Classification Dropdown Options (VIRTUALIZED — INCOMPLETE)

> ⚠️ This control uses **virtual scrolling**: only ~11 options are rendered in the DOM at any moment.
> The full option list is **not yet captured** — the table below is an observed sample only.

- **Field name**: Classification
- **Control type**: custom dropdown (non-native `<select>`), React component with `role='option'` ARIA attributes, **virtualized list**
- **Total options**: **unknown (≥ 11, likely much larger)** — the codes belong to the Uniclass `SL_90` spaces/locations classification
- **Capture method for the full list** (pending): DevTools scroll-and-collect script, or the underlying API response (Network tab)

## Observed Sample (11 of N — not the complete list)

| # | Code | Name |
|---|------|------|
| 1 | SL_90_60_74 | Roof voids |
| 2 | SL_90_90 | Plant and control spaces |
| 3 | SL_90_90_01 | Access floor voids |
| 4 | SL_90_90_08 | Boiler rooms |
| 5 | SL_90_90_13 | Ceiling voids |
| 6 | SL_90_90_15 | Control rooms |
| 7 | SL_90_90_32 | Furnace rooms |
| 8 | SL_90_90_42 | Incinerator rooms |
| 9 | SL_90_90_48 | Lift machine rooms |
| 10 | SL_90_90_63 | Plant enclosures |
| 11 | SL_90_90_64 | Plant rooms |

## Selection

- ✅ **Confirmed strategy:** the dropdown accepts **direct text input** — type `Ac_05` (or any code) and select the matching option; no scrolling through the virtualized list is required.

## Assertion Guidance

- ❌ **Do NOT assert an exact count or a full-list comparison** against UI reads — the virtualized DOM never contains the complete list.
- ✅ Safe strategies for this control:
  - **Min-count + spot checks**: assert `count >= 11` and key entries exist (e.g. `any("Plant rooms" in o for o in options)`).
  - **Search/filter behavior**: type a filter keyword (e.g. "Plant") and assert every visible option matches it — more stable than full-list assertions on virtualized controls.
  - **API-level verification**: if the underlying API is accessible, assert against the API response instead of the UI.
- Capture the full list once via the scroll-and-collect script, then update this document and re-evaluate the assertion strategy.
