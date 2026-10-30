"""Reproduce a pinned BookText -> Integra format gap with synthetic data only.

Run through scripts/seminartext-owned-run. This is audit evidence, not another
catalog implementation. Exact Git snapshots are extracted into the owned TMPDIR;
the supplied repositories, applications, and real source projects are not edited.
"""

from __future__ import annotations

import argparse
import io
import json
import os
from pathlib import Path
import subprocess
import tarfile
import tempfile


INTEGRA = "55141b8688996a4ba19f1cffb0930bb61a9561f6"
BOOKTEXT = "7219d0e6eee74c2c2f90e8cff6e9da624b6cb52a"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--integra-repo", required=True, type=Path)
    parser.add_argument("--booktext-repo", required=True, type=Path)
    args = parser.parse_args()
    if not os.environ.get("TMPDIR"):
        parser.error("run through scripts/seminartext-owned-run")
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    with tempfile.TemporaryDirectory(prefix="four-product-contract-") as temporary:
        root = Path(temporary)
        for name, repository, commit in (
            ("integra", args.integra_repo, INTEGRA),
            ("booktext", args.booktext_repo, BOOKTEXT),
        ):
            target = root / name
            target.mkdir()
            data = subprocess.check_output(["git", "-C", str(repository), "archive", commit])
            with tarfile.open(fileobj=io.BytesIO(data)) as archive:
                archive.extractall(target, filter="data")

        def run(name, *command):
            result = subprocess.run(command, cwd=root / name, env=env,
                                    check=True, capture_output=True, text=True)
            return result.stdout

        fixture = {
            "schema_version": "1.0", "artifact_type": "booktext.canonical_document",
            "document_id": "synthetic-document", "source_pages": [{"source_page": 1}],
            "blocks": [{"block_id": "block-1", "reading_order": 1, "type": "paragraph",
                        "text": "Synthetic source text.", "provenance": {"source_page": 1}}],
            "warnings": [],
        }
        source = root / "book_document.json"
        source.write_text(json.dumps(fixture), encoding="utf-8")
        before = source.read_bytes()
        validation = run("booktext", "python3", "-c",
                         "from tools.canonical_document import validate_document; "
                         "import json,sys; print(json.dumps(validate_document(json.load(open(sys.argv[1])))))",
                         str(source))
        if not json.loads(validation)["valid"]:
            raise RuntimeError("synthetic CDM is invalid at the pinned producer")
        command = ("python3", "-c",
                   "from scripts.seminar_library_preview import build; import sys,json; "
                   "print(json.dumps(build([('booktext',sys.argv[1])]),sort_keys=True))", str(source))
        first, second = run("integra", *command), run("integra", *command)
        catalog = json.loads(first)
        expected = "unsupported BookText package manifest version or type"
        if (catalog["summary"]["unsupported_manifests"] != 1 or catalog["projects"]
                or not any(expected in item for item in catalog["diagnostics"])):
            raise RuntimeError("expected pinned contract gap was not reproduced")
        if first != second or before != source.read_bytes():
            raise RuntimeError("non-deterministic catalog or source modification")
        print(json.dumps({"producer_validation": "PASS", "consumer": "UNSUPPORTED_VERSION_OR_TYPE",
                          "deterministic_same_paths": True, "source_unchanged": True,
                          "synthetic_only": True}, sort_keys=True))


if __name__ == "__main__":
    main()
