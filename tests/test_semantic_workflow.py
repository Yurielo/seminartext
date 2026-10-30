"""Synthetic source-bound product CLI lifecycle; no model or real domain review."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

import pytest

from seminartext_modules import semantic_workflow as workflow
from seminartext_modules import reviewed_knowledge_admission as admission

ROOT = Path(__file__).resolve().parents[1]
CASES = json.loads((ROOT / "tests/fixtures/semantic_workflow/cases.json").read_text())


def fixture(root, case=CASES[0]):
    root.mkdir()
    # Only reuse schema scaffolding from the existing controlled fixture.
    # No original text, semantic Topics, Gold, IDs or source hashes survive.
    bundle = json.loads((ROOT / "tests/fixtures/canonical_evidence_v1/valid_bundle.json")
                        .read_text().replace("stress_code", case["id"]))
    for key in ("topics", "benchmark_segments", "evidence_refs"):
        bundle[key] = []
    bundle["sources"] = bundle["sources"][:1]
    source = bundle["sources"][0]
    bundle["project"]["title"] = case["id"]
    source["title"] = case["id"] + " synthetic source"
    source_bytes = ("SYNTHETIC SOURCE ONLY: " + case["text"]).encode()
    source["content_sha256"] = workflow.sha(source_bytes)
    revision = bundle["transcript_revisions"][0]
    revision.update(canonical_text=case["text"], text_sha256=workflow.sha(case["text"].encode()),
                    authority="candidate", lifecycle_status="active", revision_kind="asr",
                    transcript_provenance={"origin": "machine_generated", "method": "synthetic fixture; no ASR executed",
                        "verification_state": "machine_unverified", "verification_ranges": [], "reviewer": None})
    for alignment in bundle["alignment_runs"]:
        alignment.update(source_content_sha256=source["content_sha256"], transcript_text_sha256=revision["text_sha256"])
    position = 0
    for word, text in zip(bundle["words"], case["text"].split()):
        word.update(text=text, normalized_text=None, char_start=position, char_end=position+len(text))
        position += len(text)+1
    cue = bundle["cues"][0]
    cue.update(text=case["text"], char_end=len(case["text"]))
    first, last = bundle["words"][:2]
    fragment = {"id": "fragment_"+case["id"], "source_id": source["id"],
                "transcript_revision_id": revision["id"], "word_start_id": first["id"], "word_end_id": last["id"],
                "quote": case["text"][:last["char_end"]], "locator": {"type":"time_interval",
                    "start_seconds":first["start_seconds"], "end_seconds":last["end_seconds"]},
                "review_decision_provenance": {"actor_type":"system_validator", "authority":"NONAUTHORITATIVE_MACHINE_DERIVED"}}
    if case["precision"] == "cue":
        fragment.pop("word_start_id"); fragment.pop("word_end_id")
        fragment.update(cue_start_id=cue["id"], cue_end_id=cue["id"], quote=cue["text"], locator=cue["source_locator"])
    evidence_bytes = admission.canonical_bytes(bundle)
    fragments = {"schema_version":"1.0.0", "artifact_type":admission.MACHINE_DERIVED_RESULT_TYPE,
        "artifact_id":"machine_"+case["id"], "canonical_evidence":{"artifact_id":bundle["artifact_id"],"sha256":workflow.sha(evidence_bytes)},
        "fragment_lineage":[fragment], "semantic_knowledge":[{"fragment_refs":[fragment["id"]],
            "provenance":{"boundary_authority":"MACHINE_DERIVED","semantic_authority":"NONE"}}],
        "application_status":"MACHINE_DERIVED", "provenance":fragment["review_decision_provenance"]}
    fragments_bytes = admission.canonical_bytes(fragments)
    ev = admission._span(fragment, bundle)
    notebook = admission.canonical_bytes({"notebook_id":"notebook_"+case["id"], "fixture_only":True})
    runtime = b"Synthetic Integra-compatible producer identity; NOT executable/model output."
    common = {"status":"PROVISIONAL","version":1,"evidence_refs":[ev["id"]],
              "provenance":{"origin":"derived","source_artifact_id":"proposals_"+case["id"]}}
    records = []
    for index in range(4):
        records.append(("concepts",{**common,"id":f"concept_{case['id']}_{index}","preferred_label":case["label"]+str(index),
            "aliases":[],"description":"Synthetic proposal","scope":"source-bound","topic_refs":[],
            "created_from":[ev["id"]],"supersedes":[],"redirects":[]}))
    records += [("topics",{**common,"id":"topic_"+case["id"],
        "seminar_id":"seminar_"+workflow.sha(bundle["project"]["id"].encode()),
        "source_scope":{"source_ids":[source["id"]],"transcript_revision_ids":[revision["id"]]},
        "title":case["id"],"summary":"Synthetic test topic","concept_refs":[]}),
        ("relations",{**common,"id":"relation_"+case["id"],"source_concept_id":records[0][1]["id"],
            "target_concept_id":records[1][1]["id"],"relation_type":"associated_with"})]
    proposals = [{"id":"proposal_"+record["id"],"entity_kind":kind,"operation":"CREATE","record":record,
        "fragment_refs":[{"id":fragment["id"],"sha256":admission.digest(fragment)}],"before_sha256":None,
        "review_status":"REVIEW_REQUIRED","generation_provenance":{"method":"prepared synthetic fixture, not inference",
        "producer_sha256":workflow.sha(runtime)}} for kind,record in records]
    package = {"schema_version":"1.0.0","artifact_type":"seminartext.reviewed_knowledge_proposals",
        "artifact_id":"proposals_"+case["id"],"contract":{"id":admission.CONTRACT_ID,"sha256":admission.CONTRACT_SHA256},
        "producer":{"component_id":"integra","runtime_id":"synthetic_fixture_producer","runtime_sha256":workflow.sha(runtime)},
        "source_binding":{"project_id":bundle["project"]["id"],"source_id":source["id"],
            "source_revision_sha256":source["content_sha256"],"source_sha256":source["content_sha256"],
            "transcript_revision_id":revision["id"],"transcript_sha256":revision["text_sha256"],"evidence_sha256":workflow.sha(evidence_bytes)},
        "k1_binding":{"artifact_id":fragments["artifact_id"],"sha256":workflow.sha(fragments_bytes),
            "notebook_id":"notebook_"+case["id"],"notebook_sha256":workflow.sha(notebook),"review_state":admission.MACHINE_DERIVED_REVIEW_STATE},
        "parent_revision_sha256":None,"proposals":proposals}
    payloads = dict(evidence=evidence_bytes,fragments=fragments_bytes,source=source_bytes,
                    notebook=notebook,producer_runtime=runtime,proposals=admission.canonical_bytes(package))
    paths = {}
    for role,payload in payloads.items():
        paths[role]=root/(role+".json");paths[role].write_bytes(payload)
    return paths,package


def cli(*args, ok=True):
    env = dict(os.environ, SEMINARTEXT_PYTHON=sys.executable, PYTHONDONTWRITEBYTECODE="1")
    result = subprocess.run([str(ROOT/"seminartext"),"project-semantic-workflow",*map(str,args)],
                            env=env,capture_output=True,text=True)
    assert (result.returncode == 0) == ok, result.stdout+result.stderr
    return json.loads(result.stdout) if ok and not str(args[0]) in {"inspect"} else result


def prepare_cli(run, paths):
    args = ["prepare",run]
    for role,path in paths.items():args.extend(["--"+role.replace("_","-"),path])
    return cli(*args)


def submission(package, actions=None, selected=None):
    chosen = package["proposals"] if selected is None else [package["proposals"][i] for i in selected]
    choices = [{"proposal_id":p["id"],"proposal_sha256":admission.digest(p),"action":(actions or {}).get(p["id"],"ACCEPT"),
                "reason":"EXPLICIT SYNTHETIC TEST ONLY", "timestamp":"2026-10-30T12:00:00Z"} for p in chosen]
    return {"schema_version":"1.0.0","package_id":package["artifact_id"],"package_sha256":admission.digest(package),
        "reviewer":{"actor_type":"human_domain_reviewer","actor_id":"synthetic_test_reviewer"},
        "explicit_confirmation":True,"confirmed_proposal_ids":sorted(c["proposal_id"] for c in choices),"decisions":choices}


def inventory(root):
    return {str(p.relative_to(root)):workflow.sha(p.read_bytes()) for p in root.rglob("*") if p.is_file()}


@pytest.mark.parametrize("case", CASES, ids=lambda c:c["id"])
def test_fresh_cli_full_lifecycle_and_deferred_reopening(tmp_path, case):
    paths,package=fixture(tmp_path/"source",case); before=inventory(tmp_path/"source"); run=tmp_path/"workflow"
    initial=prepare_cli(run,paths)
    assert initial["status"]=="REVIEW_REQUIRED" and initial["decisions"]==0 and initial["canonical_entity_count"]==0
    initial_state=json.loads(next(run.glob("*.json")).read_bytes())["state"]
    assert initial_state["choices"]=={} and initial_state["reviewer"] is None and initial_state["result"] is None
    assert prepare_cli(run,paths)==initial
    assert cli("status",run)==initial
    rendered=cli("inspect",run).stdout
    assert case["text"].split()[0] in rendered and "issue_68" not in rendered
    cli("apply",run,ok=False)
    first=submission(package,selected=[0]);path=tmp_path/"submission.json";path.write_bytes(admission.canonical_bytes(first))
    cli("submit",run,"--decisions",path)
    assert len(cli("status",run)["pending"])==5
    after_first=inventory(run);cli("submit",run,"--decisions",path);assert inventory(run)==after_first
    actions={package["proposals"][2]["id"]:"REJECT",package["proposals"][3]["id"]:"DEFER"}
    full=submission(package,actions);path.write_bytes(admission.canonical_bytes(full))
    cli("submit",run,"--decisions",path);applied=cli("apply",run)
    assert applied["canonical_entity_count"]==4 and len(applied["deferred"])==1
    assert cli("validate",run)==applied
    result=cli("result",run);assert result["source_evidence"]["evidence"][0]["precision"]==("CUE_RANGE" if case["precision"]=="cue" else "WORD_RANGE")
    snapshots=inventory(run);cli("apply",run);assert inventory(run)==snapshots
    reopened=cli("next-round",run);assert reopened["decisions"]==0 and len(reopened["pending"])==1
    after_reopen=inventory(run);assert cli("next-round",run)==reopened;assert inventory(run)==after_reopen
    proposal_id=reopened["pending"][0]
    args=("decide",run,"--proposal",proposal_id,"--action","ACCEPT","--reason","Synthetic deferred re-review",
          "--reviewer","synthetic_test_reviewer","--confirm-package-sha256",reopened["package_sha256"])
    cli(*args);after_decide=inventory(run);cli(*args);assert inventory(run)==after_decide
    cli("apply",run);new=cli("result",run)
    assert new["parent_revision_sha256"]==result["revision_sha256"]
    assert len(new["canonical_knowledge"]["concepts"])==3
    assert all(inventory(run)[path]==hash_ for path,hash_ in snapshots.items())
    assert inventory(tmp_path/"source")==before


@pytest.mark.parametrize("role",workflow.ROLES)
def test_current_inputs_are_rechecked_without_mutation(tmp_path,role):
    paths,_=fixture(tmp_path/"source");run=tmp_path/"workflow";prepare_cli(run,paths);before=inventory(run)
    paths[role].write_bytes(paths[role].read_bytes()+b" ")
    for command in ("status","inspect","apply","validate"):
        cli(command,run,ok=False)
    assert inventory(run)==before


@pytest.mark.parametrize("mutation",["duplicate","unknown","stale","unconfirmed","system","bad_edit","bad_action"])
def test_invalid_submission_is_atomic(tmp_path,mutation):
    paths,package=fixture(tmp_path/"source");run=tmp_path/"workflow";prepare_cli(run,paths);before=inventory(run)
    batch=submission(package)
    if mutation=="duplicate":batch["decisions"].append(batch["decisions"][0])
    elif mutation=="unknown":batch["decisions"][0]["proposal_id"]="unknown_proposal"
    elif mutation=="stale":batch["package_sha256"]="f"*64
    elif mutation=="unconfirmed":batch["explicit_confirmation"]=False
    elif mutation=="system":batch["reviewer"]["actor_type"]="system_validator"
    elif mutation=="bad_edit":batch["decisions"][0].update(action="EDIT",edited_fields={"id":"forged_id"})
    else:batch["decisions"][0]["action"]="ACCEPT_LINK"
    path=tmp_path/"batch.json";path.write_bytes(admission.canonical_bytes(batch));cli("submit",run,"--decisions",path,ok=False)
    assert inventory(run)==before


def test_interrupted_publication_and_concurrent_writer(tmp_path):
    paths,package=fixture(tmp_path/"source");run=tmp_path/"workflow";workflow.prepare(run,paths);before=inventory(run)
    with workflow.locked(run) as root:
        state,number,previous=workflow.load(root)
        updated=workflow.submit(state,submission(package))
        with patch.object(admission.os,"link",side_effect=OSError("simulated interrupted publication")):
            with pytest.raises(OSError):workflow.append(root,updated,number,previous)
        cli("status",run,ok=False)
    assert inventory(run)==before
    path=tmp_path/"decisions.json";path.write_bytes(admission.canonical_bytes(submission(package)))
    cli("submit",run,"--decisions",path);cli("apply",run);assert cli("validate",run)["status"]=="APPLIED"


def test_invalid_prepare_missing_and_unsupported_inputs(tmp_path):
    paths,package=fixture(tmp_path/"source");run=tmp_path/"workflow"
    package["schema_version"]="99";paths["proposals"].write_bytes(admission.canonical_bytes(package))
    args=["prepare",run]
    for role,path in paths.items():args.extend(["--"+role.replace("_","-"),path])
    cli(*args,ok=False);assert not run.exists()
    paths["evidence"].unlink();cli(*args,ok=False);assert not run.exists()


def test_conflicting_decisions_and_valid_empty_result(tmp_path):
    paths,package=fixture(tmp_path/"source");run=tmp_path/"workflow";prepare_cli(run,paths)
    batch=submission(package,{p["id"]:"REJECT" for p in package["proposals"]})
    path=tmp_path/"batch.json";path.write_bytes(admission.canonical_bytes(batch));cli("submit",run,"--decisions",path)
    before=inventory(run);batch["decisions"][0]["action"]="ACCEPT";path.write_bytes(admission.canonical_bytes(batch))
    cli("submit",run,"--decisions",path,ok=False);assert inventory(run)==before
    assert cli("apply",run)["canonical_entity_count"]==0
    assert cli("validate",run)["status"]=="APPLIED"


def test_edit_preserves_identity_and_source_wording(tmp_path):
    paths,package=fixture(tmp_path/"source");run=tmp_path/"workflow";prepare_cli(run,paths)
    batch=submission(package)
    batch["decisions"][0].update(action="EDIT",edited_fields={"preferred_label":"Reviewed synthetic label"})
    path=tmp_path/"batch.json";path.write_bytes(admission.canonical_bytes(batch));cli("submit",run,"--decisions",path)
    cli("apply",run);result=cli("result",run)
    concept=next(c for c in result["canonical_knowledge"]["concepts"] if c["id"]==package["proposals"][0]["record"]["id"])
    assert concept["preferred_label"]=="Reviewed synthetic label"
    assert result["source_evidence"]["evidence"][0]["quote"]=="Planets orbit"


def test_source_change_before_commit_and_lost_response_retry(tmp_path):
    paths,package=fixture(tmp_path/"source");run=tmp_path/"workflow";workflow.prepare(run,paths)
    with workflow.locked(run) as root:
        state,number,previous=workflow.load(root);updated=workflow.submit(state,submission(package))
        original=paths["source"].read_bytes();paths["source"].write_bytes(b"changed")
        before=inventory(run)
        with pytest.raises(ValueError,match="stale source"):workflow.append(root,updated,number,previous)
        assert inventory(run)==before
        paths["source"].write_bytes(original)
        writer=admission.persist_revision
        def lost_response(*args):
            writer(*args)
            raise OSError("simulated lost response after atomic commit")
        with patch.object(admission,"persist_revision",side_effect=lost_response):
            with pytest.raises(OSError):workflow.append(root,updated,number,previous)
    assert cli("status",run)["pending"]==[]
    before=inventory(run);path=tmp_path/"batch.json";path.write_bytes(admission.canonical_bytes(submission(package)))
    cli("submit",run,"--decisions",path);assert inventory(run)==before


@pytest.mark.parametrize("damage",["json","version","duplicate","quote","producer","symlink"])
def test_prepare_rejects_invalid_or_fabricated_inputs(tmp_path,damage):
    paths,package=fixture(tmp_path/"source");run=tmp_path/"workflow"
    if damage=="json":paths["proposals"].write_text("{")
    elif damage=="version":
        package["schema_version"]="2.0.0";paths["proposals"].write_bytes(admission.canonical_bytes(package))
    elif damage=="duplicate":
        package["proposals"].append(package["proposals"][0]);paths["proposals"].write_bytes(admission.canonical_bytes(package))
    elif damage=="producer":
        package["producer"]["component_id"]="seminartext";paths["proposals"].write_bytes(admission.canonical_bytes(package))
    elif damage=="symlink":
        link=tmp_path/"linked";link.symlink_to(paths["source"]);paths["source"]=link
    else:
        f=json.loads(paths["fragments"].read_bytes());f["fragment_lineage"][0]["quote"]="invented quotation"
        paths["fragments"].write_bytes(admission.canonical_bytes(f))
    with pytest.raises((ValueError,KeyError)):workflow.prepare(run,paths)
    assert not run.exists()


def test_corrupt_history_never_reports_old_success(tmp_path):
    paths,_=fixture(tmp_path/"source");run=tmp_path/"workflow";prepare_cli(run,paths)
    snapshot=next(run.glob("*.json"));snapshot.write_bytes(snapshot.read_bytes()+b"garbage")
    cli("status",run,ok=False)


def test_submission_requires_json_object_without_traceback(tmp_path):
    paths,package=fixture(tmp_path/"source");run=tmp_path/"workflow";prepare_cli(run,paths)
    before=inventory(run);path=tmp_path/"batch.json"
    path.write_text(json.dumps(list(submission(package))))
    failed=cli("submit",run,"--decisions",path,ok=False)
    assert json.loads(failed.stderr)["status"]=="INVALID_OR_UNAVAILABLE"
    assert inventory(run)==before
