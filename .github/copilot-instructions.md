# GitHub Copilot Instructions for fmu-sim2seis

## Project overview

`fmu-sim2seis` is a Python package in the Equinor FMU (Fast Model Update) ecosystem.
It orchestrates seismic forward modelling, depth conversion, relative seismic inversion,
and observed-data processing as ERT forward-model steps.

Key namespaces: `fmu.sim2seis.seismic_fwd`, `fmu.sim2seis.seismic_inversion`,
`fmu.sim2seis.observed_data`, `fmu.sim2seis.map_attributes`, `fmu.sim2seis.cleanup`.

## Technology stack

- **Python ≥ 3.11**; supports 3.11, 3.12, 3.13, 3.14
- **Pydantic v2** for all configuration validation (`BaseModel`, `model_validator`,
  `field_validator`, `ValidationInfo`)
- **ERT** (`ert.shared.plugins.plugin_manager`) for forward-model integration;
  `ForwardModelStepPlugin` with `validate_pre_realization_run` hook.
  (`validate_pre_experiment` is kept as a no-op stub on each step — see
  *ERT validation lifecycle* below for historical context.)
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


## Language

- The default languagage is British English. This includes:
  - chat
  - PR summary
  - code comments
  - documentation


## Python Library Standards

- **Public API Protection:** Ensure changes to public modules, classes, and functions maintain backward compatibility. Verify that internal-only helpers use a leading underscore (`_`).
- **Type Hints & Annotations:** Check that public functions and classes include precise type hints and that annotations align with the surrounding codebase standards.
- **Documentation & Docstrings:** Ensure new public APIs include clear docstrings documenting parameters, return values, and expected exceptions.
- **Idiomatic Python:** Flag anti-patterns or inefficient constructs (e.g., mutable default arguments, improper exception handling, or missing context managers for resource management).

## ERT validation lifecycle

ERT calls two hooks before a run:

| Hook | When called | Directories available |
|---|---|---|
| `validate_pre_experiment` | once, before any realization dirs are created | config dir only |
| `validate_pre_realization_run` | per realization, after runpath is created | full runpath |

**Deprecated / historical.** `validate_pre_experiment` is **no longer used** by
this package — each `ForwardModelStepPlugin` subclass keeps the method only as
a no-op stub (`pass`). Earlier revisions called `read_yaml_file(...,
pre_experiment=True)` from `SeismicForward.validate_pre_experiment` to catch
configuration errors before realization directories existed, and the
`pre_experiment` flag gated path-existence checks in the pydantic validators in
`sim2seis_config_validation.py`. Both the flag and the gating have been
removed; all validation now runs at `validate_pre_realization_run` time
(implicitly, via `read_yaml_file` called from each step's CLI entry point).
Do **not** reintroduce a `pre_experiment` parameter to `read_yaml_file` or a
`pre_experiment` key in the pydantic validation context.

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

## Pull request summaries

PR summaries (titles, descriptions, review comments) must be:

- **Brief** — no filler, no recap of obvious diff content.
- **Covering** — mention every user-visible change and any non-obvious
  rationale, so a reviewer can grasp the scope without reading every hunk.
- **Written in clear prose** — normal paragraphs must be complete grammatical
  sentences with an explicit subject and verb. Bullet items may be abbreviated
  (e.g. imperative or noun phrases) as long as they remain clear.
- **Written in Markdown** — use fenced code blocks for commands, paths, and
  identifiers; use short bullet lists for change inventories; use headings only
  when the PR spans multiple distinct areas.
- **Delivered as a Markdown code block** — output the entire PR summary wrapped
  in a fenced ```markdown code block so it can be copied verbatim into the PR
  description. Any fenced code blocks inside the summary must use a different
  fence length (e.g. ````) so the outer block is not broken.

## Testing guidelines

- Test data is under `tests/data/`; use the `data_dir` / `testdata` fixtures
  from `conftest.py` to access it.
- *(Historical, no longer applicable):* earlier revisions had dedicated
  `pre_experiment` tests that copied only the shared config tree to `tmp_path`
  and asserted both the positive (`pre_experiment=True` succeeds) and negative
  (`pre_experiment=False` raises) cases. These tests were removed together with
  the `pre_experiment` parameter — see *ERT validation lifecycle* above.

## Code review guidance

In principle, it should not be necessary to have several iterations on code review
unless the suggested fixes also include weak or erroneous code.

When performing a code review:

- Review all changed files systematically before reporting findings. Check correctness, 
  error handling, boundary conditions, security, compatibility, and regression-test 
  coverage.
- Inspect relevant callers, callees, and tests before claiming that changed code is 
  incorrect.
- Report actionable defects with a concrete failure scenario and explain the impact. 
  Avoid speculative issues and stylistic preferences unless they violate an explicit 
  repository convention.
- Validate suggested fixes against the surrounding implementation. Do not propose a 
  fix that introduces another defect or contradicts the documented requirements.
- Respect intentional design decisions documented in this repository. If a decision 
  is unsafe, explain the specific failure rather than merely recommending a different 
  approach.
- Consolidate findings with the same root cause rather than reporting multiple symptoms separately.
- Compare new comments with earlier comments on the same code. If an earlier suggestion 
  conflicts with the current one, thoroughly evaluate whether the new suggestion is needed.
- Review user feedback on earlier suggestions, especially suggestions that were downvoted.
- Check review summary, ensure that there are no "```" added, which disables rendering.

## Review completeness and stability

When reviewing a pull request, produce the most complete set of findings you can on the first pass.

- Treat each review as a comprehensive review of the current diff, not as a progressive discovery process.
- Surface all material findings that are observable from the changed code and immediately relevant surrounding context in the first review.
- Do not intentionally withhold findings for later iterations.
- On subsequent review rounds, only add new findings when they are caused by:
  - newly changed code,
  - newly added context, or
  - a prior finding being resolved in a way that introduces a different issue.
- Do not raise net-new findings on unchanged code if those findings were already discoverable in an earlier round.
- If a finding is deferred because it depends on missing context, say that explicitly.

In other words:

- first review: comprehensive findings for the PR's current state
- later reviews: deltas only

The goal is a stable review experience where authors can trust that unchanged code will not accumulate avoidable new findings across iterations.

In fact:
- Missing an earlier-discoverable issue and surfacing it only in a later review on unchanged code should be treated as a review quality failure.
