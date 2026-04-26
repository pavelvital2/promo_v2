# Git Repository Prep Report

Дата: 2026-04-25
Роль: Git/repository preparation agent
Рабочий каталог: `/home/pavel/projects/promo_v2`

## Результат

- Локальный git-репозиторий инициализирован.
- Первый commit `221415f77a391314f9fc232a53d194c050563ffa` был отменён по уточнённому решению пользователя: коммит пока не делать.
- История commit удалена, файлы сохранены в рабочем дереве как untracked.
- Branch: `master`.
- GitHub remote не создавался и push не выполнялся.

Примечание: отчёт оставлен как файл в рабочем дереве; новый commit не создавался.

## .gitignore

`.gitignore` расширен для Django/PostgreSQL/deployment проекта.

Исключены:

- local env/config: `.env`, `.env.*`, кроме `.env.example`;
- virtualenv: `.venv/`, `venv/`, `env/`;
- Python cache/bytecode: `__pycache__/`, `*.py[cod]`;
- local DB/static/media output: `*.sqlite3`, `db.sqlite3`, `/staticfiles/`, `/collected_static/`, `/media/`, `media/uploads/`;
- test/lint/type caches: `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`, coverage output;
- node dependencies/logs: `node_modules/`, npm/yarn/pnpm debug logs;
- logs/temp/backups/dumps: `logs/`, `*.log`, `tmp/`, `temp/`, `backups/`, `*.dump`, `*.sql`;
- IDE/OS files: `.idea/`, `.vscode/`, swap files, `.DS_Store`, `Thumbs.db`.

Не исключены: `.env.example`, deploy examples, docs, scripts, source code.

## Secret Scan

Scope: intended tracked files from `git ls-files --others --exclude-standard` before commit.

Commands/pattern groups used:

- `SECRET_KEY|DJANGO_SECRET_KEY|PASSWORD|TOKEN|API_KEY|PRIVATE KEY|BEGIN ... PRIVATE KEY|AWS_ACCESS_KEY|AWS_SECRET|AKIA...|ghp_...|github_pat_...|xox...`
- URI credentials: `postgres://`, `postgresql://`, `mysql://`, `redis://`, `amqp://`, `mongodb://`, and `://user:password@...`
- local sensitive filenames: `.env`, `.env.*`, `*.pem`, `*.key`, `id_rsa`, `id_ed25519`, `*credentials*`

Findings:

- No real `.env` file found.
- No private key files found.
- No AWS access keys, GitHub tokens, Slack tokens, generic API keys, or token-shaped secrets found.
- No URI credentials found.
- `.env.example` contains placeholder/example values: `DJANGO_SECRET_KEY=change-me`, `POSTGRES_PASSWORD=postgres`.
- Docs and reports contain repeated example/local commands with `POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres`.
- `config/settings.py` contains dev fallback values for local bootstrap: `dev-only-insecure-bootstrap-secret`, `promo_v2`.
- Shell scripts reference `POSTGRES_PASSWORD` only as an environment variable and do not hardcode a production secret.

Conclusion: no production secret blocker found. Example credentials are present and classified as non-production examples.

## Commands Run

```bash
git rev-parse --is-inside-work-tree
ls -la
sed -n '1,220p' AGENTS.md
sed -n '1,220p' docs/README.md
sed -n '1,220p' docs/orchestration/AGENTS.md
sed -n '1,220p' docs/roles/READING_PACKAGES.md
sed -n '1,220p' .gitignore
find . -maxdepth 3 -type f
find . -maxdepth 4 \( -name '.env' -o -name '.env.*' -o -name '*.sqlite3' -o -name 'db.sqlite3' -o -name '*.pem' -o -name '*.key' -o -name 'id_rsa' -o -name 'id_ed25519' \)
git init
git ls-files --others --exclude-standard
git status --short --ignored
git ls-files --others --ignored --exclude-standard
rg secret/token/password/key patterns over intended tracked files
git add .
git status --short
git commit -m "Initial project implementation"
git rev-parse HEAD
git ls-files | wc -l
git status --short --branch
git log --oneline -3
git reset --mixed HEAD~1
git read-tree --empty
git update-ref -d HEAD
```

## Remaining Next Step

После отдельного задания оркестратора: создать первый commit, затем при отдельном задании создать GitHub repository, добавить remote, проверить `git status`, затем выполнить push нужной ветки. До такого задания remote не создавался, push не выполнялся.
