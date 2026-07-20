# Workflow Duplication Fix

## Problem
The workflows were running twice because both `ci-cd.yml` and `pylint.yml` were triggered on pushes to the same branches.

## Root Cause
- `ci-cd.yml` triggers on pushes to `main` and `develop` branches
- `pylint.yml` was triggering on ALL pushes (including `main` and `develop`)
- This caused both workflows to run simultaneously when pushing to `main` or `develop`

## Solution
Modified `pylint.yml` to only trigger on:
- Pull requests to `main` and `develop` branches
- Pushes to branches OTHER than `main` and `develop`

## Result
- No more duplicate workflow runs
- `ci-cd.yml` handles comprehensive testing and linting for `main`/`develop` branches
- `pylint.yml` provides additional pylint analysis for feature branches and pull requests
- More efficient use of GitHub Actions resources

## Workflow Triggers Summary

### ci-cd.yml
- ✅ Push to `main` branch
- ✅ Push to `develop` branch  
- ✅ Pull requests to `main` branch

### pylint.yml (after fix)
- ✅ Pull requests to `main` branch
- ✅ Pull requests to `develop` branch
- ✅ Push to feature branches (any branch except `main`/`develop`)
- ❌ Push to `main` branch (avoided duplication)
- ❌ Push to `develop` branch (avoided duplication)