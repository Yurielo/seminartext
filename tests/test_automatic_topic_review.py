"""Two synthetic sources. No real seminar, ASR or human verification is used."""
import argparse
import io
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest
from seminartext_modules import automatic_topic_review as auto

ROOT = Path(__file__).resolve().parents[1]
CASES = [('astronomy', 'Планеты вращаются вокруг далёкой звезды.'),
         ('botany', 'Корни растений впитывают воду почвы.')]


def fixture(root, case=CASES[0]):
    key, text = case
    root.mkdir(parents=True)
    bundle = json.loads((ROOT/'tests/fixtures/canonical_evidence_v1/valid_bundle.json').read_text().replace('stress_code', key))
    bundle['topics'] = []; bundle['benchmark_segments'] = []; bundle['evidence_refs'] = []
    bundle['project']['title'] = key+' synthetic'
    bundle['sources'] = bundle['sources'][:1]
    source = root/'synthetic-source.bin';source.write_text(text)
    src = bundle['sources'][0];src['content_sha256'] = auto.digest(source.read_bytes());src['title'] = key
    rev = bundle['transcript_revisions'][0]
    rev.update(canonical_text=text, text_sha256=auto.digest(text.encode()), revision_kind='asr', authority='candidate', lifecycle_status='active',
               transcript_provenance=dict(origin='machine_generated', method='synthetic fixture; no ASR performed',
                 verification_state='machine_unverified', verification_ranges=[], reviewer=None))
    offset=0
    for i,(w,token) in enumerate(zip(bundle['words'],text.split())):
        w.update(text=token,char_start=offset,char_end=offset+len(token),start_seconds=i*10,end_seconds=(i+1)*10,
                 alignment_status='aligned',qa_flags=[],confidence=None,
                 timing_provenance=dict(kind='forced_alignment',alignment_run_id=bundle['alignment_runs'][0]['id'],method=None))
        offset+=len(token)+1
    cue=bundle['cues'][0];cue.update(text=text,char_start=0,char_end=len(text),start_seconds=0,end_seconds=50)
    cue['source_locator'].update(start_seconds=0,end_seconds=50)
    for a in bundle['alignment_runs']:
        a.update(source_content_sha256=src['content_sha256'],transcript_text_sha256=rev['text_sha256'])
    (root/'evidence').mkdir();(root/'evidence/canonical_bundle.json').write_bytes(auto.json_bytes(bundle))
    return argparse.Namespace(command='generate',run=root/'run',project=root,source=source,
                               source_id=src['id'],revision_id=rev['id'])


def transport(request,timeout=3):
    if isinstance(request,str):
        return io.BytesIO(auto.json_bytes(dict(models=[dict(name=auto.MODEL,digest='a'*64)])))
    data=json.loads(request.data)
    response={'boundaries':[1]} if 'boundaries' in data['format']['properties'] else dict(title='Синтетическая учебная тема',summary='Описание синтетического источника.')
    return io.BytesIO(auto.json_bytes(dict(message=dict(content=json.dumps(response,ensure_ascii=False)))))


def cli(command,args,ok=True):
    result=subprocess.run([str(ROOT/'seminartext'),'project-topic-review',command,str(args.run)],
             env={**os.environ,'SEMINARTEXT_PYTHON':sys.executable,'PYTHONDONTWRITEBYTECODE':'1'},capture_output=True,text=True)
    assert (result.returncode==0)==ok,result.stderr
    return result


@pytest.mark.parametrize('case',CASES)
def test_generation_reopen_replay_exact_and_pending(tmp_path,monkeypatch,case):
    args=fixture(tmp_path/'project',case);original=args.source.read_bytes()
    monkeypatch.setattr(auto.urllib.request,'urlopen',transport)
    auto.execute(args)
    assert json.loads(cli('status',args).stdout)['decisions']==0
    assert 'machine_unverified' in cli('inspect',args).stdout
    before={p.name:p.read_bytes() for p in args.run.iterdir()}
    cli('replay',args);assert before=={p.name:p.read_bytes() for p in args.run.iterdir()}
    # Simulate interruption between producer completion and package publication.
    (args.run/'receipt.json').unlink();cli('status',args,False);cli('replay',args)
    assert before=={p.name:p.read_bytes() for p in args.run.iterdir()}
    assert args.source.read_bytes()==original
    assert 'issue_68' not in cli('inspect',args).stdout
    args.source.write_bytes(b'changed');cli('status',args,False)


@pytest.mark.parametrize('damage',['duplicate','unknown','json','timeout','fallback'])
def test_failed_producer_never_publishes_success(tmp_path,monkeypatch,damage):
    args=fixture(tmp_path/'project')
    def broken(request,timeout=3):
        if isinstance(request,str):return transport(request,timeout)
        if damage=='timeout':raise TimeoutError('synthetic timeout')
        if damage=='json':return io.BytesIO(b'{')
        boundaries={'duplicate':[1,1],'unknown':[999],'fallback':[]}[damage]
        return io.BytesIO(auto.json_bytes(dict(message=dict(content=json.dumps(dict(boundaries=boundaries))))))
    monkeypatch.setattr(auto.urllib.request,'urlopen',broken)
    with pytest.raises((ValueError,TimeoutError)):auto.execute(args)
    assert not (args.run/'receipt.json').exists()
    cli('status',args,False)
    # No automatic second inference after a failed/interrupted attempt.
    with pytest.raises(ValueError,match='new explicit run'):auto.execute(args)


def test_stale_response_corruption_and_unknown_contract(tmp_path,monkeypatch):
    args=fixture(tmp_path/'project');monkeypatch.setattr(auto.urllib.request,'urlopen',transport);auto.execute(args)
    (args.run/'call_0001.json').write_text('{}');cli('replay',args,False);cli('status',args,False)
    evidence=args.project/'evidence/canonical_bundle.json';doc=json.loads(evidence.read_bytes());doc['schema_version']='99'
    evidence.write_bytes(auto.json_bytes(doc));cli('status',args,False)


def test_unaligned_input_no_output(tmp_path):
    args=fixture(tmp_path/'project');path=args.project/'evidence/canonical_bundle.json';doc=json.loads(path.read_bytes())
    doc['words'][0]['start_seconds']=None;path.write_bytes(auto.json_bytes(doc))
    with pytest.raises(ValueError):auto.execute(args)
    assert not args.run.exists()
