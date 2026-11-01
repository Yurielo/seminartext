"""Deterministic synthetic producer boundaries; these tests perform no inference."""
import copy
import hashlib
import io
import json
from pathlib import Path

import pytest

from seminartext_modules import media_to_review as intake
from seminartext_modules import media_alignment as alignment
from seminartext_modules import evidence_foundation as foundation
from seminartext_modules import automatic_topic_review as auto


def write_manifest(tmp_path, count=1, separate=False):
    entries=[]
    projects={}
    for index in range(count):
        project=tmp_path/(f'project-{index}' if separate else 'project')
        project.mkdir(exist_ok=True)
        media=project/f'sample-{index}.wav'; media.write_bytes(b'RIFF synthetic media '+bytes([index]))
        source_id=f'video_{index+1:03d}'
        projects.setdefault(project,[]).append(dict(source_id=source_id,type='local',file=media.name,title=f'Synthetic {index}',order=index+1,duration_seconds=5))
        entries.append(dict(id=f'selected-{index}',project=str(project),source_id=source_id,media=str(media)))
    for project, sources in projects.items():
        (project/'sources.json').write_text(json.dumps(dict(schema_version=1,videos=sources,documents=[])))
    payload=dict(artifact_type=intake.ARTIFACT,schema_version=intake.VERSION,entries=entries)
    path=tmp_path/'manifest.json';path.write_bytes(intake.review.canonical_bytes(payload))
    return path, entries


def transport(request, timeout=3):
    if isinstance(request,str):
        return io.BytesIO(auto.json_bytes(dict(models=[dict(name=auto.MODEL,digest='a'*64)])))
    data=json.loads(request.data)
    response={'boundaries':[1]} if 'boundaries' in data['format']['properties'] else dict(title='Синтетическая учебная тема',summary='Описание синтетического источника.')
    return io.BytesIO(auto.json_bytes(dict(message=dict(content=json.dumps(response,ensure_ascii=False)))))


@pytest.fixture
def producers(monkeypatch):
    counts=dict(asr=0,alignment=0)
    runtime=dict(interpreter='/synthetic/python',runtime={'python':'3.13.15','packages':{'whisperx':'3.8.6','torch':'2.8.0','torchaudio':'2.8.0','transformers':'4.57.6'}},model_sha256='a'*64)
    monkeypatch.setattr(intake,'prerequisites',lambda:dict(whisper_cli=True,ffmpeg=True,whisperx_3_8_6=True,alignment=runtime))
    monkeypatch.setattr(alignment,'discover',lambda:runtime)
    def asr(entry, work):
        counts['asr']+=1
        output=Path(entry['project'])/'transcript'/entry['source_id'];output.mkdir(parents=True)
        transcript=output/'transcript.txt';transcript.write_text('Альфа бета. Гамма дельта.\n')
        srt=output/'transcript.srt';srt.write_text('00:00:00,000 --> 00:00:02,000\nАльфа бета.\n\n00:00:02,000 --> 00:00:04,000\nГамма дельта.\n')
        completion=output/'.seminartext_completion.json';completion.write_text(json.dumps(dict(source={},configuration={})))
        return intake._receipt([transcript,srt,completion],configuration_env=intake._asr_environment(),completion=str(completion))
    def align(media, segments, output, identity, log):
        counts['alignment']+=1
        words=[dict(word=w,start=i,end=i+0.8,score=0.9) for i,w in enumerate(['Альфа','бета.','Гамма','дельта.'])]
        output.write_text(json.dumps(dict(artifact_type='issue_38_whisperx_existing_transcript_alignment',schema_version=1,invocation_role='alignment_only_no_asr',input=dict(audio_sha256=intake.digest(media),segments_sha256=intake.digest(segments)),environment=dict(python=identity['runtime']['python'],**identity['runtime']['packages']),runs=[dict(result=dict(word_segments=words),canonical_result_sha256=hashlib.sha256(json.dumps(dict(word_segments=words),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest())])))
    monkeypatch.setattr(intake,'transcribe',asr)
    monkeypatch.setattr(alignment,'produce',align)
    monkeypatch.setattr(intake.asr_completion,'verify_completion',lambda *a:(True,'fixture'))
    monkeypatch.setattr(auto.urllib.request,'urlopen',transport)
    return counts,runtime


@pytest.mark.parametrize('count,separate',[(1,False),(2,True),(2,False)])
def test_synthetic_orchestration_reopen_and_idempotent_resume(tmp_path,monkeypatch,producers,count,separate):
    counts,runtime=producers
    path,entries=write_manifest(tmp_path,count,separate)
    original={e['media']:Path(e['media']).read_bytes() for e in entries}
    directory=tmp_path/'intake'
    intake.prepare(directory,path)
    state=intake.run(directory)
    assert state['status']=='REVIEW_REQUIRED'
    assert counts==dict(asr=count,alignment=count)
    assert intake.status(directory)['status']=='REVIEW_REQUIRED'
    snapshots=list(directory.glob('state-*.json'))
    intake.run(directory)
    assert list(directory.glob('state-*.json'))==snapshots
    assert counts==dict(asr=count,alignment=count)
    for entry in state['entries']:
        project=Path(entry['project'])
        bundle=foundation.load_json(project/'evidence/canonical_bundle.json','bundle')
        assert foundation.validate_bundle(bundle)==[]
        revision=next(r for r in bundle['transcript_revisions'] if r['id']==entry['receipts']['evidence']['revision_id'])
        assert revision['transcript_provenance']['verification_state']=='machine_unverified'
        assert revision['authority']=='candidate'
        assert len([c for c in bundle['cues'] if c['transcript_revision_id']==revision['id']])==2
        package=json.loads((directory/'topic-review'/entry['id']/'review_package.json').read_bytes())
        assert package
    assert all(Path(p).read_bytes()==v for p,v in original.items())


def test_missing_runtime_has_specific_persistent_status(tmp_path,monkeypatch):
    path,_=write_manifest(tmp_path); directory=tmp_path/'intake';intake.prepare(directory,path)
    def absent():raise alignment.Unavailable('ALIGNMENT_RUNTIME_ABSENT','synthetic absent')
    monkeypatch.setattr(intake,'prerequisites',absent)
    assert intake.run(directory)['status']=='ALIGNMENT_RUNTIME_ABSENT'
    assert not (tmp_path/'project/transcript').exists()


def test_changed_media_manifest_registry_and_completed_artifacts_rejected(tmp_path,producers):
    path,entries=write_manifest(tmp_path);directory=tmp_path/'intake';intake.prepare(directory,path)
    media=Path(entries[0]['media']);media.write_bytes(b'changed')
    with pytest.raises(ValueError,match='selected media changed'):intake.run(directory)


def test_alignment_interruption_requires_explicit_retry(tmp_path,monkeypatch,producers):
    path,_=write_manifest(tmp_path);directory=tmp_path/'intake';intake.prepare(directory,path)
    original=alignment.produce
    def failure(*a):raise alignment.Unavailable('ALIGNMENT_EXECUTION_FAILURE','synthetic interruption')
    monkeypatch.setattr(alignment,'produce',failure)
    with pytest.raises(ValueError,match='failed'):intake.run(directory)
    monkeypatch.setattr(alignment,'produce',original)
    with pytest.raises(ValueError,match='failed'):intake.run(directory)
    state=intake.run(directory,retry='selected-0')
    assert state['status']=='REVIEW_REQUIRED'
    assert producers[0]==dict(asr=1,alignment=1)


def test_runtime_drift_corruption_and_lock_fail_closed(tmp_path,producers):
    path,entries=write_manifest(tmp_path);directory=tmp_path/'intake';intake.prepare(directory,path)
    intake.run(directory)
    producers[1]['runtime']['python']='3.14.6'
    with pytest.raises(ValueError,match='configuration changed'):intake.status(directory)
    producers[1]['runtime']['python']='3.13.15'
    with intake.batch.lock(directory):
        with pytest.raises(BlockingIOError):intake.run(directory)
    project=Path(entries[0]['project'])
    with intake.batch.lock(project/'evidence/media_review_lock'):
        with pytest.raises(BlockingIOError):intake.run(directory)
    (project/'transcript/video_001/transcript.srt').write_text('corrupt')
    with pytest.raises(ValueError,match='artifact changed'):intake.status(directory)


def test_positional_unaligned_repeat_never_moves_later_timing(tmp_path):
    cues=[dict(text='да да',start=0,end=2)]
    raw=dict(runs=[dict(result=dict(word_segments=[dict(word='да'),dict(word='да',start=1,end=1.5)]))])
    media=tmp_path/'sample.wav';media.write_bytes(b'fixture')
    srt=tmp_path/'transcript.srt';srt.write_text('fixture')
    (tmp_path/'transcript.txt').write_text('да да\n')
    words=alignment.project_output(raw,cues,{},media,srt)['words']
    mapped=foundation.map_words('да да',words)
    assert mapped[0] is None and mapped[1]['start']==1
    with pytest.raises(ValueError,match='preserve every'):foundation.map_words('да да',words[1:])


def test_runtime_selection_runs_selected_interpreter(tmp_path,monkeypatch):
    executable=tmp_path/'python';executable.write_text('fixture');executable.chmod(0o755)
    monkeypatch.setenv('SEMINARTEXT_ALIGNMENT_PYTHON',str(executable))
    seen=[]
    class Result:
        returncode=1;stdout='';stderr='wrong selected runtime'
    monkeypatch.setattr(alignment.subprocess,'run',lambda command,**kwargs:seen.append((command,kwargs)) or Result())
    with pytest.raises(alignment.Unavailable) as error:alignment.discover()
    assert error.value.code=='ALIGNMENT_RUNTIME_INCOMPATIBLE'
    assert seen[0][0][0]==str(executable)
    assert seen[0][1]['env']['HF_HUB_OFFLINE']=='1'


def test_native_srt_padding_preserves_exact_original_transcript(tmp_path,producers):
    srt=tmp_path/'transcript.srt'
    srt.write_text('00:00:00,000 --> 00:00:02,000\n Альфа бета.\n\n00:00:02,000 --> 00:00:04,000\n Гамма дельта.\n\n')
    cues=alignment.parse_srt(srt)
    assert [c['text'] for c in cues]==['Альфа бета.','Гамма дельта.']
    original='Альфа бета.\nГамма дельта.\n\n\n'
    transcript=tmp_path/'transcript.txt';transcript.write_text(original)
    media=tmp_path/'source.wav';media.write_bytes(b'fixture')
    raw=dict(runs=[dict(result=dict(segments=[dict(text=c['text'],words=[]) for c in cues]))])
    projected=alignment.project_output(raw,cues,{},media,srt)
    assert all(w['alignment_status']=='unaligned' for w in projected['words'])
    assert transcript.read_text()==original


@pytest.mark.parametrize('field',['manifest','registry'])
def test_manifest_and_registry_drift(tmp_path,producers,field):
    path,entries=write_manifest(tmp_path);directory=tmp_path/'intake';intake.prepare(directory,path)
    target=path if field=='manifest' else Path(entries[0]['project'])/'sources.json'
    target.write_bytes(target.read_bytes()+b' ')
    with pytest.raises(ValueError,match='changed'):intake.run(directory)


def test_stage_receipt_tampering_is_not_adopted(tmp_path,producers):
    path,_=write_manifest(tmp_path);directory=tmp_path/'intake';intake.prepare(directory,path);intake.run(directory)
    receipt=directory/'entries/selected-0/asr.json'
    value=json.loads(receipt.read_bytes());value['extra']='tampered';receipt.write_text(json.dumps(value))
    with pytest.raises(ValueError,match='stage receipt changed'):intake.run(directory)


def test_alignment_raw_commit_recovered_without_second_inference(tmp_path,monkeypatch,producers):
    path,_=write_manifest(tmp_path);directory=tmp_path/'intake';intake.prepare(directory,path)
    original=intake._save_receipt
    def interrupted(directory,entry,stage,receipt):
        if stage=='alignment':raise OSError('synthetic commit interruption')
        return original(directory,entry,stage,receipt)
    monkeypatch.setattr(intake,'_save_receipt',interrupted)
    with pytest.raises(ValueError):intake.run(directory)
    assert producers[0]['alignment']==1
    monkeypatch.setattr(intake,'_save_receipt',original)
    # Crash recovery reconciles the durable raw result without explicit inference retry.
    assert intake.run(directory,retry='selected-0')['status']=='REVIEW_REQUIRED'
    assert producers[0]['alignment']==1


def test_partial_evidence_import_is_mechanically_recovered(tmp_path,monkeypatch,producers):
    path,_=write_manifest(tmp_path);directory=tmp_path/'intake';intake.prepare(directory,path)
    original=foundation.atomic_write_json
    def interrupted(destination,value,**kwargs):
        if '/revisions/' in str(destination) and Path(destination).name=='canonical_bundle.json':
            raise OSError('synthetic import interruption')
        return original(destination,value,**kwargs)
    monkeypatch.setattr(foundation,'atomic_write_json',interrupted)
    with pytest.raises(ValueError):intake.run(directory)
    monkeypatch.setattr(foundation,'atomic_write_json',original)
    assert intake.run(directory,retry='selected-0')['status']=='REVIEW_REQUIRED'
    assert producers[0]==dict(asr=1,alignment=1)


@pytest.mark.parametrize('failure',['absent','mismatch'])
def test_cached_model_failure_distinction(tmp_path,monkeypatch,failure):
    executable=tmp_path/'python';executable.write_text('fixture')
    monkeypatch.setenv('SEMINARTEXT_ALIGNMENT_PYTHON',str(executable))
    monkeypatch.setenv('HF_HUB_CACHE',str(tmp_path/'hub'))
    pins=dict(line.strip().split('==') for line in (alignment.ROOT/'requirements-alignment.txt').read_text().splitlines() if '==' in line and not line.startswith('#'))
    class Result:
        returncode=0;stdout=json.dumps(dict(python='3.13.15',implementation='CPython',packages=pins));stderr=''
    monkeypatch.setattr(alignment.subprocess,'run',lambda *a,**k:Result())
    if failure=='mismatch':
        root=tmp_path/'hub/models--jonatasgrosman--wav2vec2-large-xlsr-53-russian/snapshots'/alignment.REVISION
        root.mkdir(parents=True)
        for name in ['config.json','preprocessor_config.json','special_tokens_map.json','vocab.json','pytorch_model.bin']:(root/name).write_text('fixture')
    with pytest.raises(alignment.Unavailable) as error:alignment.discover()
    expected='ALIGNMENT_MODEL_CACHE_ABSENT' if failure=='absent' else 'ALIGNMENT_MODEL_IDENTITY_MISMATCH'
    assert error.value.code==expected


@pytest.mark.parametrize('code',['ALIGNMENT_MODEL_LOAD_FAILURE','ALIGNMENT_EXECUTION_FAILURE'])
def test_worker_failure_is_reported_without_reclassification(tmp_path,monkeypatch,code):
    output=tmp_path/'raw.json'
    Path(str(output)+'.failure.json').write_text(json.dumps(dict(code=code,message='synthetic failure')))
    class Result:returncode=1
    monkeypatch.setattr(alignment.subprocess,'run',lambda *a,**k:Result())
    with pytest.raises(alignment.Unavailable) as error:
        alignment.produce(tmp_path/'media',tmp_path/'segments',output,dict(interpreter='/synthetic/python',snapshot='/synthetic/cache'),tmp_path/'log')
    assert error.value.code==code


def test_late_evidence_import_interruption_is_recovered(tmp_path,monkeypatch,producers):
    path,_=write_manifest(tmp_path);directory=tmp_path/'intake';intake.prepare(directory,path)
    original=foundation.atomic_write_json
    def interrupted(destination,value,**kwargs):
        if '/sources/' in str(destination) and Path(destination).name=='manifest.json':
            raise OSError('synthetic late import interruption')
        return original(destination,value,**kwargs)
    monkeypatch.setattr(foundation,'atomic_write_json',interrupted)
    with pytest.raises(ValueError):intake.run(directory)
    monkeypatch.setattr(foundation,'atomic_write_json',original)
    assert intake.run(directory,retry='selected-0')['status']=='REVIEW_REQUIRED'
    assert producers[0]==dict(asr=1,alignment=1)


def test_raw_input_provenance_mismatch_rejected(tmp_path,producers):
    media=tmp_path/'source';media.write_text('fixture')
    segments=tmp_path/'segments';segments.write_text('fixture')
    runtime=producers[1]
    raw=dict(artifact_type='issue_38_whisperx_existing_transcript_alignment',schema_version=1,invocation_role='alignment_only_no_asr',input=dict(audio_sha256='wrong',segments_sha256=intake.digest(segments)),environment=dict(python='3.13.15',**runtime['runtime']['packages']),runs=[dict(result={})])
    with pytest.raises(ValueError,match='input identity'):intake._validate_raw(raw,media,segments,runtime)


def test_failed_topic_explicit_retry_preserves_successful_children(tmp_path,monkeypatch,producers):
    path,_=write_manifest(tmp_path,2);directory=tmp_path/'intake';intake.prepare(directory,path)
    original=auto.generate; calls=[]
    def fail_second(items,run):
        calls.append(run.name)
        if run.name=='selected-1':raise ValueError('synthetic Topic failure')
        return original(items,run)
    monkeypatch.setattr(auto,'generate',fail_second)
    with pytest.raises(ValueError,match='Topic batch failed'):intake.run(directory)
    assert calls==['selected-0','selected-1']
    with pytest.raises(ValueError,match='failed'):intake.run(directory)
    assert calls==['selected-0','selected-1']
    def success(items,run):
        calls.append(run.name)
        return original(items,run)
    monkeypatch.setattr(auto,'generate',success)
    assert intake.run(directory,retry='selected-1')['status']=='REVIEW_REQUIRED'
    assert calls==['selected-0','selected-1','selected-1']
    assert producers[0]==dict(asr=2,alignment=2)
    assert intake.status(directory)['status']=='REVIEW_REQUIRED'


def test_raw_result_hash_is_validated(tmp_path,producers):
    media=tmp_path/'source';media.write_text('fixture')
    segments=tmp_path/'segments';segments.write_text('fixture')
    runtime=producers[1]
    raw=dict(artifact_type='issue_38_whisperx_existing_transcript_alignment',schema_version=1,invocation_role='alignment_only_no_asr',input=dict(audio_sha256=intake.digest(media),segments_sha256=intake.digest(segments)),environment=dict(python='3.13.15',**runtime['runtime']['packages']),runs=[dict(result={'tampered':True},canonical_result_sha256='0'*64)])
    with pytest.raises(ValueError,match='native result hash'):intake._validate_raw(raw,media,segments,runtime)
