---
description: Smoke-test every API key and secret in .env by running scripts/test-api-keys.ps1
---

# check-api Command

Run `pwsh scripts/test-api-keys.ps1` from the repo root and render the results as a markdown table.

## Steps

1. Run the script:
   ```
   pwsh scripts/test-api-keys.ps1
   ```
   Capture stdout and stderr together. If `pwsh` is not on PATH, try `~/pwsh/pwsh`.

2. If the script exits with "`.env` not found", stop and tell the user:
   > `.env` is missing — copy `.env.example` to `.env` and fill in your secrets, then run `/check-api` again.

3. Parse each output line. Lines follow one of two patterns:
   - `  OK  <label>  <detail>` — green / passing
   - `  --  <label>  <detail>` — yellow or red / failing

4. Render a markdown table:

   | Service | Detail | Status |
   |---|---|---|
   | `<label>` | `<detail>` | OK or FAIL |

   Use **OK** for lines that started with `OK`, **FAIL** for lines that started with `--`.

5. After the table, add a one-line summary: how many passed, how many failed.

## Rules

- Do not edit any files.
- Do not retry failed keys or attempt to diagnose individual failures unless the user asks.
- Output the table inline — never save it to a file.
