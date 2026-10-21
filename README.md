# seminartext
SeminarText 4.0 — seminar processing, transcription, topic analysis and knowledge extraction pipeline

## Operating model

The project operating model is documented in
[`DEVELOPMENT_WORKFLOW.md`](DEVELOPMENT_WORKFLOW.md). Future Issues should state
their human-gate classification: `AUTO`, `DOMAIN_REVIEW`, `DOMAIN_AUTHORING`, or
`LOCAL_ACTION`.

## Codex GitHub workflow

Local Codex work should use GitHub Issues and Pull Requests directly, without
manual copy/paste of issue text or PR reports through the user.

### One-time local setup

Install and authenticate GitHub CLI for the `Yurielo` account:

```bash
gh auth login
gh auth setup-git
```

Do not store GitHub tokens, passwords, SSH keys, or credential output in this
repository.

### Verification

From the repository root, verify that private GitHub access and HTTPS git
credentials work without interactive prompts:

```bash
gh auth status
gh issue view 3 --repo Yurielo/seminartext
git fetch origin
gh pr list --repo Yurielo/seminartext
```

The final branch push for a task is the push-capability check for that task.

### YouTube downloads

`project-transcribe` downloads YouTube audio through the installed `yt-dlp`.
SeminarText uses conservative retry options when the first download attempt
fails. If YouTube still returns an authorization or HTTP 403 error for a video
that is available in your local browser session, run the command with browser
cookies enabled:

```bash
SEMINARTEXT_YTDLP_COOKIES_FROM_BROWSER=chrome seminartext project-transcribe "$HOME/Documents/seminartext_projects/И Цзин" --only video_001
```

Use the browser name/profile accepted by `yt-dlp --cookies-from-browser` for
your local setup.

### Объединённая чистая расшифровка локальной сессии

Когда несколько локальных audio/video-файлов являются частями одной записи,
добавьте к обычной обработке `--combined-clear`:

```bash
seminartext project-transcribe "/путь/к/проекту" --combined-clear
```

SeminarText сохраняет отдельные расшифровки каждой части и дополнительно
создаёт `transcript/combined_clear.txt`. Локальные источники сортируются
хронологически: embedded creation date медиа, затем macOS birth time, затем
mtime как fallback (inode `ctime` не используется). При равной дате порядок
детерминирован: filename, затем source_id. Это derived artifact с provenance в
`transcript/combined_clear_manifest.json`, а не новый source of truth.

Для читаемого файла с границами частей, filename и разрешённой датой используйте
`--combined-with-sources`; он также создаёт чистый `combined_clear.txt`.
Если creation dates утрачены или неверны, проверьте metadata исходных файлов:
текущая реализация использует `creation_date`; контракты `filename`,
`selection_order` и `manual` оставлены для будущего выбора порядка.

### Групповая расшифровка папок и выбранных файлов

`group` принимает в одном вызове любые сочетания папок и конкретно выбранных
аудио/видеофайлов. Папки сканируются рекурсивно. По умолчанию постоянная
папка группы создаётся как `group/` рядом с первым источником; для повторного
пополнения группы из разных папок задайте её явно через `--output`:

```bash
seminartext group "/путь/к/папке"
seminartext group "выбранная запись 1.ogg" "выбранная запись 2.mp4"
seminartext group "/папка" "/путь/к/выбранной записи.m4a" \
  --output "/путь/к/постоянной-группе"
```

Источники внутри группы добавляются ссылками, без копирования больших медиа.
Идентичные файлы определяются по SHA-256, поэтому повтор с другим именем или
из другой папки не получает отдельную расшифровку. Для предварительной
проверки используйте `--list`; `--force` запускает повторную расшифровку всех
уникальных источников группы. Итоговый машинный текст находится в
`transcript/combined_clear.txt`, а вариант с границами источников — в
`transcript/combined_clear_with_sources.txt`; provenance сохраняется в
`transcript/combined_clear_manifest.json`.

### Task workflow

For each GitHub Issue:

1. Read the Issue directly with `gh issue view ISSUE --repo Yurielo/seminartext`.
2. Start from an up-to-date `main` branch.
3. Create a dedicated branch for the Issue.
4. Implement only the requested scope.
5. Run the relevant tests and verification commands.
6. Commit only files that belong to the Issue.
7. Push the branch to `origin`.
8. Open a Pull Request against `main` with `gh pr create`.
9. Do not merge the PR from local Codex.

ChatGPT/Product Owner reviews the PR through GitHub and either requests changes
or merges it.

### Safety

- Do not change product code for setup-only workflow issues.
- Do not change Topic Engine logic or benchmark data unless an Issue explicitly
  requires it.
- Do not expose credentials in logs, documentation, commits, PR descriptions, or
  comments.

## Project Knowledge bridge

The bounded project bridge composes retained source-scoped Canonical Evidence,
validates explicitly authored semantic records, compiles Canonical Knowledge
v1, and produces a deterministic Obsidian derived view:

```bash
seminartext project-obsidian-export PROJECT \
  --knowledge-input PROJECT/knowledge_input.json \
  --destination /path/to/vault \
  --dry-run
```

The accepted Topic origins are `verified_manual`, `gold`, and explicitly marked
`semi_automatic`. The command does not generate or semantically accept Topics,
Concepts, Relations, or review decisions. Remove `--dry-run` only after reviewing the
plan. Generated paths are managed by a hash manifest; user-owned collisions and
changed managed files fail closed. Optional source resolution is supplied with
`--source-resolver FILE`; canonical notes retain source identity and report the
resolver state without embedding machine-local paths.

The input schema is
[`schemas/project_knowledge_input_v1.schema.json`](schemas/project_knowledge_input_v1.schema.json).
Issue #104 fixture validation is not a real full-seminar Issue #68 run and does
not make the bridge production-ready.
