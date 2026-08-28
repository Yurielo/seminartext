# Bounded Obsidian Knowledge Prototype

This directory contains the disposable derived Markdown view for Issue #51.
Canonical Evidence and the accepted Golden Seminar Knowledge Slice remain the
only authoritative inputs.

## Rebuild

From the repository root:

```bash
python3 analysis/obsidian_knowledge_prototype/export_obsidian_vault.py \
  --slice analysis/golden_knowledge_slice/golden_knowledge_slice.json \
  --canonical analysis/word_timeline_mvp/canonical_evidence_bundle.json \
  --output analysis/obsidian_knowledge_prototype/vault \
  --manifest analysis/obsidian_knowledge_prototype/export_manifest.json
```

The exporter verifies the frozen Golden Slice SHA-256, the canonical bundle
SHA-256, bounded entity counts, canonical Evidence quotes/Word ranges/time
locators, provisional Concept statuses and symmetric Topic/Concept references.
It then overwrites the same stable-ID filenames. It refuses to delete unmanaged
Markdown.

The vault has no plugin dependency. Frontmatter is emitted as a JSON mapping,
which is also valid YAML 1.2. Filenames make navigation convenient but are not
canonical identity; every note carries its stable ID and source artifact hash.

Open `vault/00_START_HERE.md` first. Product Review instructions are generated
at `vault/PRODUCT_OWNER_REVIEW_GUIDE.md`.
