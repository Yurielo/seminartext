import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from seminartext_modules.owned_tmp import APP

ROOT = Path(__file__).resolve().parents[1]


class CLIContainmentTests(unittest.TestCase):
    def test_actual_queue_list_and_argument_error_cycles_leave_no_owned_tmp(self):
        with tempfile.TemporaryDirectory() as fixture:
            base = Path(fixture).resolve()
            source = base / 'lecture.wav'
            source.write_bytes(b'fixture')
            tools = base / 'bin'
            tools.mkdir()
            for tool in ['ffmpeg','ffprobe','whisper-cli']:
                executable=tools/tool
                executable.write_text('#!/bin/sh\nexit 0\n')
                executable.chmod(0o755)
            model=base/'model.bin';model.write_bytes(b'fixture')
            env = {**os.environ, 'SEMINARTEXT_OWNED_TMP_BASE': str(base), 'SEMINARTEXT_OUTPUT': str(base/'output'), 'SEMINARTEXT_HEADLESS':'1', 'PATH':str(tools)+os.pathsep+os.environ['PATH'], 'SEMINARTEXT_MODEL':str(model), 'SEMINARTEXT_VAD_MODEL':str(model)}
            for args,code in [(['--list',str(source)],0),(['--not-a-real-option'],2)]*3:
                result=subprocess.run([str(ROOT/'seminartext'),*args],env=env,capture_output=True,text=True)
                self.assertEqual(result.returncode,code,result.stderr)
                ns=base/f'{APP}-owned-v2-{os.getuid()}'
                self.assertEqual([p for p in ns.iterdir() if not p.name.startswith('.')],[])
            self.assertEqual(source.read_bytes(),b'fixture')
