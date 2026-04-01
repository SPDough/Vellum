# Lockfile Decision

## Current decision
For the frontend, treat:
- `frontend/package-lock.json`

as the authoritative lockfile.

## Why
During the Vellum frontend cleanup and refinement pass:
- installs were run inside `frontend/`
- the local dependency state was updated there
- the root `package-lock.json` appears stale relative to active frontend work

## Recommended follow-up
To remove Next.js lockfile warnings, remove or archive:
- `../package-lock.json`

once you confirm the root repo is not intentionally using that lockfile for a separate install boundary.

## Current caution
Because this repo may still have root-level package manager history, do not blindly delete the root lockfile without a quick repo-level sanity check.
