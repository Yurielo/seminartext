# Dependency and model profiles

Each profile is intentionally isolated. The canonical mapping of profile names,
supported Python versions, lock files, model identities, and offline policy is
in [`dependency_profiles.json`](dependency_profiles.json).

Reconstruct a profile without touching the system interpreter:

```bash
python3.14 -m venv .venv-seminartext-dev
. .venv-seminartext-dev/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

Use the same pattern with `requirements-core.txt`, `requirements-alignment.txt`
(Python 3.13 only), or `requirements-treeseg.txt`. The `.lock` files under
`dependencies/locks/` are the reviewed exact-version constraints used for
reproduction and drift checks. No command in this repository installs or
upgrades global packages.

Run read-only diagnostics from the repository root:

```bash
./scripts/seminartext-dependencies doctor
./scripts/seminartext-dependencies doctor --profile alignment_whisperx --json
./scripts/seminartext-dependencies model --path /path/to/model.bin
./scripts/seminartext-dependencies ollama
```

The alignment model must use the recorded Hugging Face revision and SHA-256.
Set `HF_HOME` to a controlled cache root and set `HF_HUB_OFFLINE=1` for offline
runs; a missing cache is reported, never silently downloaded. Ollama evidence
must resolve `bge-m3:latest` to the recorded digest before it is accepted.

Optional real integration checks are deliberately outside the fast suite:

```bash
./scripts/seminartext-optional-smoke
```

The script performs imports and local-service/model preflight only when the
corresponding optional profile is available. It never installs dependencies.
