# Legacy Frontend Files

These files were moved out of the active TypeScript source tree into `frontend/legacy-src/`
as temporary migration leftovers from older SPA-oriented frontend paths.

## Files
- `../legacy-src/main.tsx`
- `../legacy-src/App.tsx`
- `../legacy-src/App.simple.tsx`
- `../legacy-src/App.auth.tsx`
- `../legacy-src/TestApp.tsx`
- `../legacy-src/debug.tsx`
- `../legacy-src/simple.js`

## Current rule
The canonical frontend runtime is the Next.js App Router under:
- `frontend/app/*`

These legacy files should not be used for new work.

## Deletion rule
Delete or archive them only after:
- import graph verification
- final runtime verification
- one deliberate cleanup pass
