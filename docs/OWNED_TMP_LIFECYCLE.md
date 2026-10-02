# Owned TMP lifecycle audit / fixture evidence

This task performs no existing TMP mass cleanup, runtime replacement or persistent
artifact deletion. The audit starts from verified origin/main. System TMP is
read only; tests allocate small new isolated fixtures only.

## Lifecycle and classes

| Producer | Class | Success / failure | Interruption / crash |
|---|---|---|---|
| CLI input/topic/project queues (`mktemp -t`) | owned ephemeral | supervisor-owned TMPDIR; normal local cleanup plus final root cleanup | independent supervisor survives local RETURN/INT/TERM trap changes; exact leased root recovery after crash |
| Subtitle burning/watermark staging (`mktemp -d`) | owned ephemeral | same supervisor; includes normalization/ffmpeg error paths | terminate only owned process group, then remove exact owned workspace |
| CLI subprocess tool scratch | owned ephemeral | inherited TMPDIR/TMP/TEMP inside run workspace | supervised process group + lease + open-file inspection |
| Full/focused pytest and Integrity subprocesses | owned ephemeral | CI and documented `scripts/seminartext-owned-run` wrapper | controlled signals and next-start recovery |
| Frozen Issue #45 matplotlib scratch | ephemeral inside owned runner | original TemporaryDirectory plus outer run cleanup | runner handles interruption/import error without changing hash-locked adapter bytes |
| Research venv / NLTK dependencies | persistent explicit environment/cache | reproducibility recipe now uses `.venv-issue45` / explicit cache | never runtime TMP or automatic deletion candidates |
| Transcript outputs/audio chunks/project checkpoints/deploy backups/evidence | persistent or workflow-owned project staging | existing project lifecycle retained | no generic project cleanup, no Dataset/Gold/semantic mutation |

The hash-locked historical adapter remains unchanged. Always execute test/build/
render/research commands via `scripts/seminartext-owned-run`; unsupported raw
ad-hoc developer commands cannot promise controlled interruption cleanup.
Runtime deploy/backup/rollback includes the new helper; no actual deploy occurs
in this task. Missing helper fails closed rather than launching unbounded CLI.

## Ownership authority and bound

Private per-user namespace, random workspace UUID, schema/app/namespace token,
exact canonical path and device/inode receipt; private directory owner/mode;
non-following lease and marker reads. A PID/lease/open-file check retains active
or uninspectable objects. Recovery considers only entries in this authenticated
namespace, never a global prefix/age search. Legacy unknown objects are not
adopted. Missing lsof, malformed receipts and substitutions retain fail closed.
At 32 retained/live/unknown workspace slots, new work fails closed rather than
creating another workspace. Completed cycles leave no run directories/data;
constant small namespace metadata remains. This is a workspace count guard,
not a size cap for a legitimately active task or explicitly retained evidence.
SIGKILL cannot execute finally; the next safe launch performs owned recovery.

## Controlled test matrix

Fixture subprocesses allocate 8 KiB payloads. Tests cover context error/cancel,
SIGINT/SIGTERM, killed supervisor with live surviving leased worker, later stale
recovery, unknown names, symlinks/substituted inode/marker, busy foreign FD,
unavailable lsof, repeated success/failure cycles, and exhausted namespace.
Eight alternating success/failure cycles: owned before 0 directories / 0 payload
bytes; after every cycle 0 / 0. Actual CLI entrypoint success/invalid-input cycles
are also checked. No full model/application candidate is built.

## Audited source locations

All matches below were examined. Atomic persistent writes and historical retained
evidence are distinguished above; imports alone do not allocate TMP. Test
fixture TemporaryDirectory uses are contained by the canonical test runner.

```text
dependencies/check_profiles.py:13:import subprocess
dependencies/check_profiles.py:117:            completed = subprocess.run(
dependencies/check_profiles.py:125:        except (OSError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
seminartext:515:  q="$(mktemp -t seminartext_queue.XXXXXX)"
seminartext:519:import subprocess
seminartext:558:        r = subprocess.run(
seminartext:1575:      subtitle_tmp="$(mktemp -d "${TMPDIR:-/tmp}/seminartext-subtitles.XXXXXX")"
seminartext:1698:    subtitle_tmp="$(mktemp -d "${TMPDIR:-/tmp}/seminartext-subtitles.XXXXXX")"
seminartext:3758:  queue="$(mktemp -t seminartext_topics_project.XXXXXX)"
seminartext:4669:  queue="$(mktemp -t seminartext_project.XXXXXX)"
seminartext:4934:import subprocess
seminartext:4973:        result = subprocess.run(command, text=True, capture_output=True, check=False)
seminartext:4987:        result = subprocess.run(
integrity/process.py:3:import subprocess
integrity/process.py:10:) -> subprocess.CompletedProcess[str]:
integrity/process.py:11:    return subprocess.run(
seminartext_modules/seminartext_translate.py:5:import subprocess
seminartext_modules/seminartext_translate.py:20:    p = subprocess.run(["ollama", "run", MODEL], input=prompt, text=True,
integrity/runner.py:6:import subprocess
integrity/runner.py:78:        probe = subprocess.run(
integrity/checks/runtime_truth.py:5:import subprocess
integrity/checks/runtime_truth.py:136:            smoke = subprocess.run(
integrity/checks/runtime_truth.py:154:        except (OSError, subprocess.SubprocessError) as exc:
seminartext_modules/owned_tmp.py:16:import subprocess
seminartext_modules/owned_tmp.py:18:import tempfile
seminartext_modules/owned_tmp.py:74:        result = subprocess.run([tool, "-nP", "-F", "p", "+D", str(path)], capture_output=True, text=True, timeout=5)
seminartext_modules/owned_tmp.py:75:    except (OSError, subprocess.TimeoutExpired):
seminartext_modules/owned_tmp.py:84:    base = Path(base or os.environ.get(f"{APP.upper()}_OWNED_TMP_BASE") or tempfile.gettempdir()).resolve()
seminartext_modules/owned_tmp.py:236:        child = subprocess.Popen(command, env=env, start_new_session=True, pass_fds=(workspace._lease,))
seminartext_modules/owned_tmp.py:252:                    except subprocess.TimeoutExpired:
analysis/external_topic_baselines/run_baseline_challenge.py:20:import tempfile
analysis/external_topic_baselines/run_baseline_challenge.py:295:    temporary_mpl = tempfile.TemporaryDirectory(prefix="seminartext-issue45-mpl-")
analysis/gold_expansion_v2/prepare_gold_expansion_v2.py:12:import subprocess
analysis/gold_expansion_v2/prepare_gold_expansion_v2.py:96:    output = subprocess.check_output(
seminartext_modules/seminartext_topics.py:5:import subprocess
seminartext_modules/seminartext_topics.py:424:        p = subprocess.run(
seminartext_modules/seminartext_topics.py:434:    except subprocess.TimeoutExpired:
```
