# GitHub Copilot Instructions for fmu-sim2seis

## Project overview

`fmu-sim2seis` is a Python package in the Equinor FMU (Fast Model Update) ecosystem.
It orchestrates seismic forward modelling, depth conversion, relative seismic inversion,
and observed-data processing as ERT forward-model steps.

Key namespaces: `fmu.sim2seis.seismic_fwd`, `fmu.sim2seis.seismic_inversion`,
`fmu.sim2seis.observed_data`, `fmu.sim2seis.map_attributes`, `fmu.sim2seis.cleanup`.

## Technology stack

- **Python ≥ 3.11**; supports 3.11, 3.12, 3.13
- **Pydantic v2** for all configuration validation (`BaseModel`, `model_validator`,
  `field_validator`, `ValidationInfo`)
- **ERT** (`ert.shared.plugins.plugin_manager`) for forward-model integration;
  `ForwardModelStepPlugin` with `validate_pre_experiment` and
  `validate_pre_realization_run` hooks
- **xtgeo** for grid and surface I/O
- **fmu-pem**, **fmu-dataio**, **fmu-config**, **fmu-tools** as sibling FMU libraries
- **seismic-forward** and **si4ti** as external seismic simulation tools
- **Ruff** for linting and formatting (configured in `pyproject.toml`)
- **pytest** for testing; test data lives under `tests/data/`

## Repository layout

```
src/fmu/sim2seis/
    utilities/          # shared helpers, pydantic config models, YAML reader
    forward_models/     # ERT ForwardModelStepPlugin registrations
    hook_implementations/  # ERT plugin entry-point
    seismic_fwd/        # seismic forward modelling logic
    seismic_inversion/  # relative acoustic impedance inversion
    observed_data/      # observed seismic data processing
    map_attributes/     # amplitude / relai attribute map extraction
    cleanup/            # post-run clean-up
tests/
    data/               # test fixtures (YAML configs, XML model files, roff grids)
.github/
    workflows/
        linting.yml          # ruff format --check && ruff check
        build_test_deploy.yml  # pytest + wheel build + GitHub Pages
```

## Coding conventions

- All configuration is validated through pydantic models in
  `src/fmu/sim2seis/utilities/sim2seis_config_validation.py`.
- Use `Path` (not `DirectoryPath` / `FilePath`) for path fields; move existence
  checks into `model_validator(mode="after")` methods so they can be gated by
  validation context.
- The `read_yaml_file` function in `get_yaml_file.py` is the single entry-point
  for loading and validating YAML configuration. Always thread `validation_context`
  (a `dict`) through both `Sim2SeisPaths.model_validate` and
  `Sim2SeisConfig.model_validate` calls.
- `SkipJsonSchema[...]` is used for fields that should be hidden from the
  user-facing JSON schema (default-only or internal fields).

## ERT validation lifecycle

ERT calls two hooks before a run:

| Hook | When called | Directories available |
|---|---|---|
| `validate_pre_experiment` | once, before any realization dirs are created | config dir only |
| `validate_pre_realization_run` | per realization, after runpath is created | full runpath |

Pass `pre_experiment=True` to `read_yaml_file` inside `validate_pre_experiment`.
This causes all pydantic validators to skip **realization-specific** path checks
(output dirs, PEM dirs, seismic cube dirs) while still validating files that live
in the shared config tree:

- `sim2seis/model/*.xml` (stack models, twt model) — resolved against `config_dir_sim2seis`
- `sim2seis/model/<attribute_map_definition>.yml` — resolved against `config_dir_sim2seis`
- `sim2seis/input/pem/*.roff` (WebvizMap grid files) — resolved via `grid_dir`
  anchored to `config_dir_sim2seis`

## Pre-commit checklist

Before every `git commit`:

1. **Ruff check**: `.venv/bin/ruff check <changed files>`
2. **Ruff format**: `.venv/bin/ruff format <changed files>`
3. **Tests**: `pytest tests/` (or the specific test file)

This shell uses **tcsh**. Important tcsh limitations:
- No heredoc (`<<EOF`) and no multi-line quoted strings — write long strings to a
  file with `create_file`, then reference the file (e.g. `git commit -F <file>`).
- `rm` is aliased to `rm -i`; use `\rm` to skip confirmation prompts.
- Remove all temporary files (commit messages, scripts) immediately after use with
  `\rm <file>`.
- `ruff` is not on `PATH`; invoke it as `.venv/bin/ruff`.

## Commit style

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(scope): short imperative summary

Body explaining *what* and *why*, not *how*.
Bullet list of per-file or per-class changes where helpful.
```

Common types: `fix`, `feat`, `refactor`, `test`, `chore`, `docs`.
Scope examples: `validation`, `ert`, `seismic_fwd`, `observed_data`.

Use atomic commits — one logical change per commit.

## Testing guidelines

- Test data is under `tests/data/`; use the `data_dir` / `testdata` fixtures
  from `conftest.py` to access it.
- For `pre_experiment` tests: copy only the shared config tree to `tmp_path`
  (model YAML + XML files, input grid roff files); do **not** create realization
  output directories.
- Assert both the positive case (`pre_experiment=True` succeeds) and the negative
  case (`pre_experiment=False` raises).
- After a `pre_experiment=True` call, assert that config-resident paths
  (e.g. `stack_models` values, `twt_model`) are absolute and point to existing files.
