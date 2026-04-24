# AGENTS

## PLAN AND ASK BEFORE DO
CRITICAL: NEVER EVER DO ANY ACTION READING, MODIFYING OR RUNNING without explaining the plan
Each set of intended actions needs to be explained in the format:
I understood that <YOUR ANALYSIS> so that i plan to <GOALS YOU PURSUE> by <ACTIONS TO BE CONFIRMED> estimating <# of ITEMS> <ITEMS> to be worked on. confirm with go!
YOU WILL NEVER PROCEED WITHOUT POSITIVE CONFIRMATION by go!

## Efficiency
* Do NOT do unneeded file lookups based on guessing or assuming typos.
* Do NOT use TodoWrite for tasks with fewer than 4 steps.
* Do NOT read files you already have contents for.
* Keep summaries to 2-3 lines max unless asked for detail.
* Minimize tool calls. Batch parallel calls. Avoid redundant calls.

## SECURITY
CRITICAL: NEVER leak credentials, passwords, hashes, internal hostnames, IPs, or any infrastructure details to public platforms (GitHub, Discourse, etc.). Firing offense.

## Project: pyExpireBackups
Automated cleanup and expiration of backup files based on age and retention rules.
- Version: 0.1.3
- Python: >=3.10
- License: Apache-2.0
- Source: https://github.com/WolfgangFahl/pyExpireBackups

## Structure
```
expirebackups/
  __init__.py        # version string
  version.py         # Version class (name, description, version, date)
  expire.py          # all core logic and CLI entry point
tests/
  testexpirebackups.py  # unittest-based tests
scripts/
  blackisort, doc, install, release, test  # shell helper scripts
```

## Key Classes (expire.py)
- `BackupFile` — wraps a file path with age, size, modification date; can delete itself
- `ExpirationRule` — one retention rule (frequency in days, min files to keep)
- `Expiration` — holds 4 rules: daily(1d), weekly(7d), monthly(28d), yearly(364d); applies them in order
- `ExpireBackups` — main driver: scans `rootPath` for files matching `baseName`/`ext`, applies expiration, optionally deletes

## CLI
Entry point: `expirebackups` (mapped to `expirebackups.expire:main`)
Key flags: `--rootPath`, `--baseName`, `--ext`, `--days`, `--weeks`, `--months`, `--years`, `--minFileSize`, `-f` (force delete), `--createTestFiles`

## Testing
```bash
python -m pytest tests/
# or
scripts/test
```

## Build & Release
```bash
scripts/install   # install locally
scripts/release   # publish
scripts/blackisort # format with black + isort
scripts/doc       # generate docs
```
