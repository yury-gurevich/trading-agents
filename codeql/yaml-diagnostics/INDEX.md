# YAML diagnostics pack -- folder map

This query pack holds local CodeQL diagnostics for tracked YAML content. Read this
before opening the individual `.ql` files.

| File | What it is |
| --- | --- |
| [qlpack.yml](qlpack.yml) | Pack manifest; depends on `codeql/python-all` because the Python extractor exposes YAML diagnostics for this repo |
| [yaml-diagnostics.qls](yaml-diagnostics.qls) | Query suite for this pack |
| [parse-errors.ql](parse-errors.ql) | Reports YAML parser errors in tracked configuration files |
| [unresolved-includes.ql](unresolved-includes.ql) | Reports YAML `!include` directives whose target file cannot be resolved |
| [codeql-pack.lock.yml](codeql-pack.lock.yml) | CodeQL dependency lockfile |

## Runtime note

`codeql/scripts/setup_codeql_local.ps1` currently creates and resolves the YAML
subdatabase but skips local YAML query execution on CodeQL 2.25.6 because the
finalized dataset is missing `yaml.dbscheme.stats`. The pack remains here as
the source of truth for those diagnostics.

Back to [CodeQL index](../INDEX.md).
