#!/usr/bin/env python3
import argparse
import csv
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse, parse_qsl, urlunparse

# ----------------------------
# Redaction helpers
# ----------------------------

SENSITIVE_KV_KEYS = {
    "password", "pass", "passwd", "pwd",
    "token", "apikey", "api_key", "key",
    "service_role", "secret", "private_key"
}

def _redact_url(url: str) -> Tuple[str, bool, List[str]]:
    """Redact credentials and sensitive query params from a URL."""
    changed = False
    secret_fields: List[str] = []

    try:
        p = urlparse(url)
    except Exception:
        return (_redact_inline_secrets(url)[0], True, ["unknown"])

    netloc = p.netloc
    # Handle user:pass@
    if "@" in netloc:
        userinfo, hostpart = netloc.rsplit("@", 1)
        if ":" in userinfo:
            user, _pw = userinfo.split(":", 1)
            netloc = f"{user}:***REDACTED***@{hostpart}"
            changed = True
            secret_fields.append("url_password")
        else:
            netloc = p.netloc

    # Redact query params like ?password=...&token=...
    q = []
    for k, v in parse_qsl(p.query, keep_blank_values=True):
        lk = k.lower()
        if lk in SENSITIVE_KV_KEYS or any(s in lk for s in ["pass", "token", "secret", "key"]):
            q.append((k, "***REDACTED***"))
            changed = True
            secret_fields.append(f"query:{k}")
        else:
            q.append((k, v))
    query = "&".join([f"{k}={v}" for k, v in q])

    redacted = urlunparse((p.scheme, netloc, p.path, p.params, query, p.fragment))
    return redacted, changed, sorted(list(set(secret_fields)))


INLINE_SECRET_PATTERNS = [
    # password=foo, token: foo, api_key = foo
    re.compile(r'(?i)\b(password|passwd|pwd|token|api[_-]?key|service[_-]?role|secret|private[_-]?key)\b\s*[:=]\s*([^\s\'",)]+)'),
]

def _redact_inline_secrets(s: str) -> Tuple[str, bool, List[str]]:
    changed = False
    secret_fields: List[str] = []
    out = s

    for pat in INLINE_SECRET_PATTERNS:
        def repl(m):
            nonlocal changed, secret_fields
            changed = True
            secret_fields.append(m.group(1))
            return f"{m.group(1)}=***REDACTED***"
        out2 = pat.sub(repl, out)
        out = out2

    # Also redact common JWT-like blobs (very conservative)
    jwt_pat = re.compile(r'\beyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\b')
    if jwt_pat.search(out):
        out = jwt_pat.sub("***REDACTED***", out)
        changed = True
        secret_fields.append("jwt")

    return out, changed, sorted(list(set(secret_fields)))


def redact_text(s: str) -> Tuple[str, bool, List[str]]:
    # First redact URLs if present
    url_pat = re.compile(r'(?i)\b([a-z][a-z0-9+.-]*://[^\s\'")]+)')
    secret_fields: List[str] = []
    changed_any = False

    def url_repl(m):
        nonlocal changed_any, secret_fields
        u = m.group(1)
        ru, changed, fields = _redact_url(u)
        if changed:
            changed_any = True
            secret_fields.extend(fields)
        return ru

    out = url_pat.sub(url_repl, s)

    # Then redact inline secrets
    out2, changed2, fields2 = _redact_inline_secrets(out)
    if changed2:
        changed_any = True
        secret_fields.extend(fields2)

    return out2, changed_any, sorted(list(set(secret_fields)))


# ----------------------------
# Detection
# ----------------------------

URL_SCHEMES = {
    "postgres": "postgres",
    "postgresql": "postgres",
    "mysql": "mysql",
    "mariadb": "mysql",
    "mssql": "mssql",
    "sqlserver": "mssql",
    "redis": "redis",
    "mongodb": "mongo",
    "clickhouse": "clickhouse",
    "elasticsearch": "elasticsearch",
    "opensearch": "opensearch",
}

URL_REGEX = re.compile(
    r'(?i)\b('
    r'(?:postgres(?:ql)?|mysql|mariadb|mssql|sqlserver|redis|mongodb|clickhouse|elasticsearch|opensearch)'
    r')://[^\s\'")]+'
)

SQLITE_REGEX = re.compile(r'(?i)\bsqlite:///[^\s\'")]+|\b\w[\w./-]*\.sqlite3?\b')

SUPABASE_URL_REGEX = re.compile(r'(?i)\bhttps://[a-z0-9-]{10,}\.supabase\.co\b')

ENV_ASSIGN_REGEX = re.compile(r'^\s*(export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)\s*$')

KNOWN_ENV_KEYS = {
    "DATABASE_URL", "POSTGRES_URL", "PGHOST", "PGPORT", "PGDATABASE", "PGUSER", "PGPASSWORD",
    "DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD",
    "REDIS_URL", "MONGODB_URI", "CLICKHOUSE_URL", "SUPABASE_URL", "SUPABASE_DB_URL",
}

def strip_quotes(v: str) -> str:
    v = v.strip()
    if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
        return v[1:-1]
    return v

def detector_for_path(path: str) -> str:
    p = path.lower()
    name = os.path.basename(p)
    if name.startswith(".env") or name.endswith(".env"):
        return "env_file"
    if "docker-compose" in name or name.startswith("compose") or "/docker/" in p:
        return "docker_compose"
    if "/.github/workflows/" in p:
        return "ci"
    if "/k8s/" in p or "/kubernetes/" in p or "helm" in p or "/manifests/" in p:
        return "k8s_manifest"
    if name.endswith(".tf"):
        return "terraform"
    if "superset_config.py" in name or "superset" in p and name.endswith(".py"):
        return "superset_config"
    if "odoo" in p and (name.endswith(".conf") or "odoo.conf" in name):
        return "odoo_config"
    if name.endswith(".md"):
        return "docs"
    if name.endswith(".prisma"):
        return "prisma_schema"
    if name.endswith(".toml"):
        return "toml_config"
    if name.endswith(".json") or name.endswith(".yaml") or name.endswith(".yml") or name.endswith(".ini") or name.endswith(".cfg"):
        return "config"
    return "code_or_text"

def tags_for_path(path: str) -> List[str]:
    p = path.lower()
    tags: List[str] = []
    if "odoo" in p: tags.append("odoo")
    if "superset" in p: tags.append("superset")
    if "supabase" in p: tags.append("supabase")
    if "/.github/" in p or "/ci/" in p: tags.append("ci")
    if any(x in p for x in ["/prod", "production"]): tags.append("prod")
    if any(x in p for x in ["/staging", "stage"]): tags.append("staging")
    if any(x in p for x in ["/dev", "development", "local"]): tags.append("local")
    return sorted(list(set(tags)))

def datastore_type_from_scheme(scheme: str) -> str:
    scheme = scheme.lower()
    return URL_SCHEMES.get(scheme, "unknown")

def parse_db_url(url: str) -> Dict[str, Optional[str]]:
    p = urlparse(url)
    host = p.hostname
    port = str(p.port) if p.port else None
    user = p.username
    dbname = p.path.lstrip("/") if p.path else None
    ssl_mode = None
    for k, v in parse_qsl(p.query, keep_blank_values=True):
        if k.lower() in {"sslmode", "ssl"}:
            ssl_mode = v
    return {
        "datastore_type": datastore_type_from_scheme(p.scheme),
        "host": host,
        "port": port,
        "database": dbname,
        "user": user,
        "ssl_mode": ssl_mode,
    }

def stable_id(fields: Dict[str, Optional[str]]) -> str:
    norm = "|".join([
        (fields.get("datastore_type") or ""),
        (fields.get("host") or ""),
        (fields.get("port") or ""),
        (fields.get("database") or ""),
        (fields.get("user") or ""),
        (fields.get("url_redacted") or ""),
        (fields.get("instance_name") or ""),
    ]).lower()
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()[:16]

def is_probably_binary(data: bytes) -> bool:
    if b"\x00" in data:
        return True
    # crude: if many non-text bytes
    text_chars = sum(1 for b in data[:4096] if 9 <= b <= 13 or 32 <= b <= 126)
    sample = min(len(data), 4096)
    if sample == 0:
        return False
    return (text_chars / sample) < 0.60

@dataclass
class Finding:
    id: str
    datastore_type: str
    instance_name: Optional[str]
    host: Optional[str]
    port: Optional[str]
    database: Optional[str]
    user: Optional[str]
    ssl_mode: Optional[str]
    url_redacted: Optional[str]
    secrets_present: bool
    secret_fields: List[str]
    source: Dict[str, object]
    tags: List[str]


# ----------------------------
# Scanner
# ----------------------------

def scan_file(path: Path, max_bytes: int, verbose: bool) -> Tuple[List[Finding], List[str]]:
    findings: List[Finding] = []
    errors: List[str] = []

    try:
        data = path.read_bytes()
    except Exception as e:
        errors.append(f"read_error:{path}:{e}")
        return findings, errors

    if len(data) > max_bytes:
        return findings, errors

    if is_probably_binary(data):
        return findings, errors

    try:
        text = data.decode("utf-8", errors="replace")
    except Exception as e:
        errors.append(f"decode_error:{path}:{e}")
        return findings, errors

    detector = detector_for_path(str(path))
    tags = tags_for_path(str(path))

    # Track env-style assignments to aggregate within file
    env_map: Dict[str, Tuple[str, int]] = {}  # key -> (value, line)
    lines = text.splitlines()

    # 1) URL scheme matches
    for i, line in enumerate(lines, start=1):
        for m in URL_REGEX.finditer(line):
            raw = m.group(0)
            redacted_url, url_changed, url_secret_fields = _redact_url(raw)
            parsed = parse_db_url(raw)

            snippet, sn_changed, sn_fields = redact_text(line.strip())
            secret_fields = sorted(list(set(url_secret_fields + sn_fields)))
            secrets_present = bool(secret_fields)

            inst_name = None
            # best-effort: include env var mention in same line
            if "DATABASE_URL" in line.upper():
                inst_name = "DATABASE_URL"
            elif "SUPABASE" in line.upper():
                inst_name = "SUPABASE"
            elif "REDIS" in line.upper():
                inst_name = "REDIS"

            fdict = {
                "datastore_type": parsed["datastore_type"],
                "host": parsed["host"],
                "port": parsed["port"],
                "database": parsed["database"],
                "user": parsed["user"],
                "ssl_mode": parsed["ssl_mode"],
                "url_redacted": redacted_url,
                "instance_name": inst_name,
            }
            fid = stable_id(fdict)

            findings.append(Finding(
                id=fid,
                datastore_type=fdict["datastore_type"] or "unknown",
                instance_name=inst_name,
                host=fdict["host"],
                port=fdict["port"],
                database=fdict["database"],
                user=fdict["user"],
                ssl_mode=fdict["ssl_mode"],
                url_redacted=redacted_url,
                secrets_present=secrets_present or url_changed,
                secret_fields=secret_fields,
                source={
                    "file_path": str(path),
                    "line_start": i,
                    "line_end": i,
                    "snippet_redacted": (snippet[:240] + "…") if len(snippet) > 240 else snippet,
                    "detector": detector,
                },
                tags=tags,
            ))

        # 2) SQLite matches
        for m in SQLITE_REGEX.finditer(line):
            raw = m.group(0)
            snippet, _, sn_fields = redact_text(line.strip())

            db_path = raw
            dtype = "sqlite"
            url_redacted = None
            if raw.lower().startswith("sqlite:///"):
                url_redacted, _, _ = _redact_url(raw)
                db_path = urlparse(raw).path

            fdict = {
                "datastore_type": dtype,
                "host": None,
                "port": None,
                "database": db_path,
                "user": None,
                "ssl_mode": None,
                "url_redacted": url_redacted,
                "instance_name": None,
            }
            fid = stable_id(fdict)
            findings.append(Finding(
                id=fid,
                datastore_type=dtype,
                instance_name=None,
                host=None,
                port=None,
                database=db_path,
                user=None,
                ssl_mode=None,
                url_redacted=url_redacted,
                secrets_present=bool(sn_fields),
                secret_fields=sn_fields,
                source={
                    "file_path": str(path),
                    "line_start": i,
                    "line_end": i,
                    "snippet_redacted": (snippet[:240] + "…") if len(snippet) > 240 else snippet,
                    "detector": detector,
                },
                tags=tags,
            ))

        # 3) Supabase URL (project URL)
        if SUPABASE_URL_REGEX.search(line):
            raw = SUPABASE_URL_REGEX.search(line).group(0)
            snippet, _, sn_fields = redact_text(line.strip())

            fdict = {
                "datastore_type": "supabase",
                "host": raw.replace("https://", ""),
                "port": None,
                "database": None,
                "user": None,
                "ssl_mode": None,
                "url_redacted": raw,
                "instance_name": "SUPABASE_URL",
            }
            fid = stable_id(fdict)
            findings.append(Finding(
                id=fid,
                datastore_type="supabase",
                instance_name="SUPABASE_URL",
                host=fdict["host"],
                port=None,
                database=None,
                user=None,
                ssl_mode=None,
                url_redacted=raw,
                secrets_present=bool(sn_fields),
                secret_fields=sn_fields,
                source={
                    "file_path": str(path),
                    "line_start": i,
                    "line_end": i,
                    "snippet_redacted": (snippet[:240] + "…") if len(snippet) > 240 else snippet,
                    "detector": detector,
                },
                tags=tags,
            ))

        # 4) env assignments aggregation
        m = ENV_ASSIGN_REGEX.match(line)
        if m:
            key = m.group(2)
            if key in KNOWN_ENV_KEYS or key.upper().endswith("_DATABASE_URL"):
                val = strip_quotes(m.group(3))
                env_map[key] = (val, i)

    # Aggregate env_map into composed findings
    # Prefer URL if present
    if "DATABASE_URL" in env_map:
        val, ln = env_map["DATABASE_URL"]
        if val:
            redacted_url, _, fields = _redact_url(val)
            parsed = parse_db_url(val)
            snippet, _, sn_fields = redact_text(lines[ln-1].strip())
            secret_fields = sorted(list(set(fields + sn_fields)))
            fdict = {
                "datastore_type": parsed["datastore_type"],
                "host": parsed["host"],
                "port": parsed["port"],
                "database": parsed["database"],
                "user": parsed["user"],
                "ssl_mode": parsed["ssl_mode"],
                "url_redacted": redacted_url,
                "instance_name": "DATABASE_URL",
            }
            fid = stable_id(fdict)
            findings.append(Finding(
                id=fid,
                datastore_type=fdict["datastore_type"] or "unknown",
                instance_name="DATABASE_URL",
                host=fdict["host"],
                port=fdict["port"],
                database=fdict["database"],
                user=fdict["user"],
                ssl_mode=fdict["ssl_mode"],
                url_redacted=redacted_url,
                secrets_present=True if fields else bool(secret_fields),
                secret_fields=secret_fields,
                source={
                    "file_path": str(path),
                    "line_start": ln,
                    "line_end": ln,
                    "snippet_redacted": (snippet[:240] + "…") if len(snippet) > 240 else snippet,
                    "detector": detector,
                },
                tags=tags,
            ))

    # DB_HOST style
    keys = ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]
    if any(k in env_map for k in keys):
        host = env_map.get("DB_HOST", (None, 0))[0]
        port = env_map.get("DB_PORT", (None, 0))[0]
        db = env_map.get("DB_NAME", (None, 0))[0]
        user = env_map.get("DB_USER", (None, 0))[0]
        pw = env_map.get("DB_PASSWORD", (None, 0))[0]
        secret_fields = ["DB_PASSWORD"] if pw else []
        secrets_present = bool(pw)
        # choose earliest line number among keys present for source
        ln = min((env_map[k][1] for k in env_map if k in keys), default=1)
        snippet, _, sn_fields = redact_text(lines[ln-1].strip())
        secret_fields = sorted(list(set(secret_fields + sn_fields)))

        fdict = {
            "datastore_type": "unknown",
            "host": host,
            "port": port,
            "database": db,
            "user": user,
            "ssl_mode": None,
            "url_redacted": None,
            "instance_name": "DB_*",
        }
        fid = stable_id(fdict)
        findings.append(Finding(
            id=fid,
            datastore_type="unknown",
            instance_name="DB_*",
            host=host,
            port=port,
            database=db,
            user=user,
            ssl_mode=None,
            url_redacted=None,
            secrets_present=secrets_present or bool(sn_fields),
            secret_fields=secret_fields,
            source={
                "file_path": str(path),
                "line_start": ln,
                "line_end": ln,
                "snippet_redacted": (snippet[:240] + "…") if len(snippet) > 240 else snippet,
                "detector": detector,
            },
            tags=tags,
        ))

    # PG* style
    pg_keys = ["PGHOST", "PGPORT", "PGDATABASE", "PGUSER", "PGPASSWORD"]
    if any(k in env_map for k in pg_keys):
        host = env_map.get("PGHOST", (None, 0))[0]
        port = env_map.get("PGPORT", (None, 0))[0]
        db = env_map.get("PGDATABASE", (None, 0))[0]
        user = env_map.get("PGUSER", (None, 0))[0]
        pw = env_map.get("PGPASSWORD", (None, 0))[0]
        secret_fields = ["PGPASSWORD"] if pw else []
        secrets_present = bool(pw)
        ln = min((env_map[k][1] for k in env_map if k in pg_keys), default=1)
        snippet, _, sn_fields = redact_text(lines[ln-1].strip())
        secret_fields = sorted(list(set(secret_fields + sn_fields)))

        fdict = {
            "datastore_type": "postgres",
            "host": host,
            "port": port,
            "database": db,
            "user": user,
            "ssl_mode": None,
            "url_redacted": None,
            "instance_name": "PG*",
        }
        fid = stable_id(fdict)
        findings.append(Finding(
            id=fid,
            datastore_type="postgres",
            instance_name="PG*",
            host=host,
            port=port,
            database=db,
            user=user,
            ssl_mode=None,
            url_redacted=None,
            secrets_present=secrets_present or bool(sn_fields),
            secret_fields=secret_fields,
            source={
                "file_path": str(path),
                "line_start": ln,
                "line_end": ln,
                "snippet_redacted": (snippet[:240] + "…") if len(snippet) > 240 else snippet,
                "detector": detector,
            },
            tags=tags,
        ))

    return findings, errors


def walk_files(root: Path, exclude_dirs: List[str], max_file_mb: int) -> List[Path]:
    max_bytes = max_file_mb * 1024 * 1024
    out: List[Path] = []
    excl = set(exclude_dirs)

    for dirpath, dirnames, filenames in os.walk(root):
        # prune excluded dirs
        dirnames[:] = [d for d in dirnames if d not in excl]
        for fn in filenames:
            p = Path(dirpath) / fn
            try:
                if p.is_symlink():
                    continue
                if p.stat().st_size > max_bytes:
                    continue
            except Exception:
                continue
            out.append(p)
    return out


def dedupe_findings(findings: List[Finding]) -> List[Finding]:
    seen = {}
    for f in findings:
        if f.id not in seen:
            seen[f.id] = f
        else:
            # keep earliest source line/file (stable)
            prev = seen[f.id]
            a = (prev.source.get("file_path"), prev.source.get("line_start"))
            b = (f.source.get("file_path"), f.source.get("line_start"))
            if b < a:
                seen[f.id] = f
    # stable sort
    items = list(seen.values())
    items.sort(key=lambda x: (
        x.datastore_type or "",
        x.host or "",
        x.database or "",
        x.source.get("file_path") or "",
        int(x.source.get("line_start") or 0),
    ))
    return items


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_csv(path: Path, findings: List[Finding]) -> None:
    cols = [
        "id","datastore_type","instance_name","host","port","database","user","ssl_mode",
        "url_redacted","secrets_present","secret_fields","file_path","line_start","line_end","detector","tags"
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for x in findings:
            row = {
                "id": x.id,
                "datastore_type": x.datastore_type,
                "instance_name": x.instance_name,
                "host": x.host,
                "port": x.port,
                "database": x.database,
                "user": x.user,
                "ssl_mode": x.ssl_mode,
                "url_redacted": x.url_redacted,
                "secrets_present": x.secrets_present,
                "secret_fields": ",".join(x.secret_fields or []),
                "file_path": x.source.get("file_path"),
                "line_start": x.source.get("line_start"),
                "line_end": x.source.get("line_end"),
                "detector": x.source.get("detector"),
                "tags": ",".join(x.tags or []),
            }
            w.writerow(row)


def write_md(path: Path, findings: List[Finding], title: str) -> None:
    lines: List[str] = [f"# {title}", ""]
    if not findings:
        lines.append("*No findings.*")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return

    lines.append(f"Total findings: **{len(findings)}**")
    lines.append("")
    lines.append("| Type | Host | Port | Database | User | Instance | Source | Secrets |")
    lines.append("|---|---|---:|---|---|---|---|---|")
    for f in findings:
        src = f"{f.source.get('file_path')}:{f.source.get('line_start')}"
        secrets = "yes" if f.secrets_present else "no"
        lines.append(
            f"| {f.datastore_type or ''} | {f.host or ''} | {f.port or ''} | {f.database or ''} | {f.user or ''} | {f.instance_name or ''} | `{src}` | {secrets} |"
        )
    lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_summary_md(path: Path, findings: List[Finding]) -> None:
    from collections import Counter
    c = Counter([f.datastore_type for f in findings])
    lines = ["# Database Inventory Summary", ""]
    lines.append(f"Generated at: `{datetime.now(timezone.utc).isoformat()}`")
    lines.append("")
    if not findings:
        lines.append("*No findings.*")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return
    lines.append("## Counts by datastore type")
    lines.append("")
    lines.append("| Datastore | Count |")
    lines.append("|---|---:|")
    for k in sorted(c.keys()):
        lines.append(f"| {k} | {c[k]} |")
    lines.append("")
    # top secret-present
    s = [f for f in findings if f.secrets_present]
    lines.append(f"## Findings with secrets redacted: **{len(s)}**")
    lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Repo-wide datastore inventory (with redaction).")
    ap.add_argument("--root", default=".", help="Repo root to scan (default: .)")
    ap.add_argument("--out", default="tools/db-inventory/output", help="Output directory")
    ap.add_argument("--format", default="json,csv,md", help="Comma-separated: json,csv,md")
    ap.add_argument("--exclude-dirs", default=".git,node_modules,dist,build,.venv,__pycache__,.next",
                    help="Comma-separated directory names to skip")
    ap.add_argument("--max-file-mb", type=int, default=5, help="Skip files larger than this (MB)")
    ap.add_argument("--verbose", action="store_true", help="Verbose logging")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    outdir = Path(args.out).resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    exclude_dirs = [x.strip() for x in args.exclude_dirs.split(",") if x.strip()]
    max_bytes = args.max_file_mb * 1024 * 1024

    files = walk_files(root, exclude_dirs, args.max_file_mb)
    if args.verbose:
        print(f"[db-inventory] scanning {len(files)} files under {root}", file=sys.stderr)

    all_findings: List[Finding] = []
    errors: List[str] = []

    for p in files:
        fs, es = scan_file(p, max_bytes=max_bytes, verbose=args.verbose)
        all_findings.extend(fs)
        errors.extend(es)

    findings = dedupe_findings(all_findings)

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(root),
        "findings": [asdict(f) for f in findings],
        "errors": errors,
    }

    fmts = set([x.strip().lower() for x in args.format.split(",") if x.strip()])
    if "json" in fmts:
        write_json(outdir / "db_inventory.json", payload)
    if "csv" in fmts:
        write_csv(outdir / "db_inventory.csv", findings)
    if "md" in fmts:
        write_md(outdir / "db_inventory.md", findings, title="Database Inventory Report")
        write_summary_md(outdir / "db_inventory_summary.md", findings)

    if args.verbose:
        print(f"[db-inventory] findings={len(findings)} errors={len(errors)} out={outdir}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
