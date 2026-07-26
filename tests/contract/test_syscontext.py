"""Layer 1 — system context: the deterministic external-system scan behind the overview's System context
section and the free `context` command. Pins the ACs of spec_eval/syscontext.md: evidence-backed entries,
exclusion of test fixtures, dedup/merge, stable (diffable) ordering, and the empty-scan guarantee."""
import json
import os

import pytest

from spec_eval import cli, syscontext


@pytest.fixture
def ctx_repo(tmp_path):
    """A tiny integration-heavy repo: AWS + PostgreSQL + a partner API + env endpoints + an inbound surface,
    plus a test file whose fake evidence must NOT count."""
    (tmp_path / "store.py").write_text(
        "import boto3\n"
        "client = boto3.client(\"s3\")\n"
        "def save(bucket, key, data):\n"
        "    client.put_object(Bucket=bucket, Key=key, Body=data)\n")
    (tmp_path / "db.py").write_text(
        "import psycopg2\n"
        "DSN = 'postgres://db.internal:5432/orders'\n")
    (tmp_path / "billing.py").write_text(
        "import psycopg2\n"
        "import requests\n"
        "PARTNER = 'https://api.partner.com/v1/invoices'\n"
        "DOCS = 'https://example.com/how-to'\n")
    (tmp_path / "api.py").write_text(
        "import os\n"
        "from flask import Flask\n"
        "QUEUE = os.environ[\"ORDERS_QUEUE_URL\"]\n"
        "app = Flask(__name__)\n")
    (tmp_path / "test_store.py").write_text(
        "import boto3\n"
        "FAKE = 'https://api.fake-partner.com/v1'\n")
    return tmp_path


def _by_system(result):
    return {e["system"]: e for e in result["entries"]}


def test_scan_finds_the_observed_systems(ctx_repo):
    entries = _by_system(syscontext.scan(str(ctx_repo), {}))
    assert entries["AWS S3"]["kind"] == "infra" and entries["AWS S3"]["direction"] == "outbound"
    assert entries["AWS S3"]["via"] == ["sdk"]
    assert entries["PostgreSQL"]["evidence_total"] == 3                     # 2 imports + 1 scheme literal
    assert sorted(entries["PostgreSQL"]["via"]) == ["scheme", "sdk"]
    assert entries["HTTP endpoint api.partner.com"]["kind"] == "referenced"     # a mention, unconfirmed
    assert entries["Configured endpoint (ORDERS_QUEUE_URL)"]["kind"] == "configured"
    assert entries["HTTP surface exposed (Flask)"]["direction"] == "inbound"


def test_every_entry_carries_verifiable_evidence(ctx_repo):
    result = syscontext.scan(str(ctx_repo), {})
    for e in result["entries"]:
        assert e["evidence"], f"{e['system']} has no evidence site"
        for site in e["evidence"]:
            assert site["line"] >= 1 and site["match"]
            assert os.path.isfile(os.path.join(str(ctx_repo), site["file"]))


def test_doc_hosts_and_test_files_do_not_count(ctx_repo):
    systems = set(_by_system(syscontext.scan(str(ctx_repo), {})))
    assert "HTTP endpoint example.com" not in systems                        # doc-suffix host skipped
    assert "HTTP endpoint api.fake-partner.com" not in systems               # lives only in a test file
    assert not any("fake-partner" in s for s in systems)


def test_lookalike_tokens_are_not_imports(tmp_path):
    (tmp_path / "app.py").write_text("import redis_helper\nfrom . import my_pg_utils\n")
    assert syscontext.scan(str(tmp_path), {})["entries"] == []


def test_boto3_without_a_service_falls_back_to_one_generic_entry(tmp_path):
    (tmp_path / "aws.py").write_text("import boto3\n")
    (only,) = syscontext.scan(str(tmp_path), {})["entries"]
    assert only["system"] == "AWS (service not resolved)"


def test_scan_is_deterministic(ctx_repo):
    a = syscontext.scan(str(ctx_repo), {})
    b = syscontext.scan(str(ctx_repo), {})
    assert a == b
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def test_entries_are_stably_ordered_by_kind(ctx_repo):
    kinds = [e["kind"] for e in syscontext.scan(str(ctx_repo), {})["entries"]]
    order = [syscontext.KIND_ORDER[k] for k in kinds]
    assert order == sorted(order)                                            # infra → … → inbound-surface


def test_evidence_block_lists_only_observed_systems(ctx_repo):
    result = syscontext.scan(str(ctx_repo), {})
    block = syscontext.evidence_block(result)
    assert block.startswith("## OBSERVED SYSTEM EVIDENCE")
    assert "AWS S3" in block and "store.py:2" in block
    assert "never add to this list" in block


def test_evidence_block_scopes_to_a_directory(tmp_path):
    (tmp_path / "a").mkdir(), (tmp_path / "b").mkdir()
    (tmp_path / "a" / "s3.py").write_text("import boto3\nboto3.client('s3')\n")
    (tmp_path / "b" / "db.py").write_text("import psycopg2\n")
    result = syscontext.scan(str(tmp_path), {})
    assert "AWS S3" in syscontext.evidence_block(result, scope_dir="a")
    assert "PostgreSQL" not in syscontext.evidence_block(result, scope_dir="a")


def test_empty_scan_yields_no_block_and_an_honest_report(tmp_path):
    (tmp_path / "pure.py").write_text("def add(a, b):\n    return a + b\n")
    result = syscontext.scan(str(tmp_path), {})
    assert result["entries"] == []
    assert syscontext.evidence_block(result) == ""                           # INV-6: never an invented section
    report = syscontext.format_report(result, str(tmp_path))
    assert "0 external system(s) observed" in report
    assert "not observable from this repo" in report
    assert "capability in the code, not proof of runtime traffic" in report


def test_cli_context_writes_both_artifacts_without_a_key(ctx_repo, tmp_path, capsys, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    out = tmp_path / "reports"
    cli.main(["context", str(ctx_repo), "--out", str(out)])
    assert "external system(s) observed" in capsys.readouterr().out
    data = json.load(open(out / "system-context.json"))
    assert data["schema"] == syscontext.SCHEMA and data["entries"]
    assert data["scanner"]["version"] and data["scanner"]["tables_digest"]
    assert "# System context" in open(out / "system-context.md").read()
    assert any(json.loads(l)["command"] == "context" for l in open(out / "runs.jsonl"))


def test_cli_context_rejects_a_file_path(ctx_repo):
    with pytest.raises(SystemExit):
        cli.main(["context", str(ctx_repo / "store.py")])


# --- drift check: fingerprint diff by key set, 3 outcomes, provenance-first ---

def _scan(tmp_path, files):
    for name, body in files.items():
        p = tmp_path / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body)
    return syscontext.scan(str(tmp_path), {})


def test_identical_scan_is_clean(tmp_path):
    a = _scan(tmp_path, {"db.py": "import psycopg2\n"})
    d = syscontext.diff(a, a)
    assert d["outcome"] == "clean" and not d["added"] and not d["removed"]


def test_line_churn_is_not_drift(tmp_path):
    """The same system at a different line/second call site must NOT count as drift (key-set identity)."""
    base = _scan(tmp_path, {"db.py": "import psycopg2\n"})
    moved = _scan(tmp_path, {"db.py": "# a new top comment\n\nimport psycopg2\nquery = 1\n"})
    d = syscontext.diff(base, moved)
    assert d["outcome"] == "clean"                       # evidence line moved from 1 to 3; identity unchanged


def test_added_and_removed_systems_are_drift(tmp_path):
    base = _scan(tmp_path, {"db.py": "import psycopg2\n"})
    changed = _scan(tmp_path, {"db.py": "import redis\n"})       # dropped PostgreSQL, added Redis
    d = syscontext.diff(base, changed)
    assert d["outcome"] == "drift"
    assert [a["system"] for a in d["added"]] == ["Redis"]
    assert [r["system"] for r in d["removed"]] == ["PostgreSQL"]
    assert d["added"][0]["evidence"] and d["added"][0]["via"] == ["sdk"]


def test_scanner_change_is_rebaseline_not_drift(tmp_path):
    """A differing tables digest (the scanner learned to see more) must read as re-baseline, never drift —
    even when the entry sets genuinely differ."""
    base = _scan(tmp_path, {"db.py": "import psycopg2\nimport redis\n"})
    base_stale = {**base, "scanner": {**base["scanner"], "tables_digest": "0000olddigest00"}}
    current = _scan(tmp_path, {"db.py": "import psycopg2\n"})     # Redis gone — would be drift under same scanner
    d = syscontext.diff(base_stale, current)
    assert d["outcome"] == "rebaseline" and d["scanner_changed"] is True


def test_schema_change_is_rebaseline(tmp_path):
    base = _scan(tmp_path, {"db.py": "import psycopg2\n"})
    old = {**base, "schema": 1}
    d = syscontext.diff(old, syscontext.scan(str(tmp_path), {}))
    assert d["outcome"] == "rebaseline"


def test_receipt_is_named_deltas_with_evidence(tmp_path):
    base = _scan(tmp_path, {"db.py": "import psycopg2\n"})
    changed = _scan(tmp_path, {"db.py": "import redis\n"})
    r = syscontext.diff_receipt(syscontext.diff(base, changed), sha="abc1234")
    assert "System-context drift @ abc1234" in r
    assert "+ Redis (outbound, via sdk)" in r and "db.py:" in r
    assert "- PostgreSQL (outbound)" in r
    assert syscontext.diff_receipt(syscontext.diff(base, base)) == "0 system-context changes"


def test_cli_check_gates_on_drift(tmp_path, capsys):
    (tmp_path / "db.py").write_text("import psycopg2\n")
    out = tmp_path / "reports"
    cli.main(["context", str(tmp_path), "--out", str(out)])       # store the baseline
    (tmp_path / "db.py").write_text("import redis\n")             # code drifts
    with pytest.raises(SystemExit) as ex:
        cli.main(["context", str(tmp_path), "--check", "--out", str(out)])
    assert ex.value.code == 1
    assert "drift" in capsys.readouterr().out.lower()
    assert json.load(open(out / "system-context.json"))["entries"][0]["system"] == "PostgreSQL"  # not overwritten


def test_cli_check_clean_passes(tmp_path, capsys):
    (tmp_path / "db.py").write_text("import psycopg2\n")
    out = tmp_path / "reports"
    cli.main(["context", str(tmp_path), "--out", str(out)])
    with pytest.raises(SystemExit) as ex:
        cli.main(["context", str(tmp_path), "--check", "--out", str(out)])
    assert ex.value.code == 0
    assert "0 system-context changes" in capsys.readouterr().out


def test_cli_check_without_baseline_is_a_no_op(tmp_path, capsys):
    (tmp_path / "db.py").write_text("import psycopg2\n")
    with pytest.raises(SystemExit) as ex:
        cli.main(["context", str(tmp_path), "--check", "--out", str(tmp_path / "empty")])
    assert ex.value.code == 0
    assert "no baseline" in capsys.readouterr().out


# --- regressions pinned by the adversarial review ---

def test_getenv_idiom_counts_as_an_env_endpoint(tmp_path):
    """AC-9: os.getenv / os.Getenv / System.getenv — no 'environ' on the line."""
    (tmp_path / "cfg.py").write_text("import os\nDB = os.getenv(\"DATABASE_URL\")\n")
    (tmp_path / "pay.go").write_text("package main\nvar url = os.Getenv(\"PAYMENTS_API_URL\")\n")
    systems = _by_system(syscontext.scan(str(tmp_path), {}))
    assert "Configured endpoint (DATABASE_URL)" in systems
    assert "Configured endpoint (PAYMENTS_API_URL)" in systems


def test_go_frameworks_match_in_both_import_forms(tmp_path):
    """AC-10: the single-line form and the multi-line import ( … ) block."""
    (tmp_path / "single.go").write_text('package main\nimport "github.com/gin-gonic/gin"\n')
    (tmp_path / "block.go").write_text(
        'package main\nimport (\n\t"fmt"\n\t"github.com/labstack/echo/v4"\n)\n')
    systems = _by_system(syscontext.scan(str(tmp_path), {}))
    assert "HTTP surface exposed (Gin)" in systems
    assert "HTTP surface exposed (Echo)" in systems


def test_unknown_boto3_service_gets_a_titled_entry_not_silence(tmp_path):
    (tmp_path / "ml.py").write_text(
        "import boto3\nboto3.client(\"s3\")\nboto3.client(\"bedrock-runtime\")\n")
    systems = _by_system(syscontext.scan(str(tmp_path), {}))
    assert "AWS S3" in systems
    assert "AWS Bedrock Runtime" in systems                    # not swallowed by the known-id hit
    assert "AWS (service not resolved)" not in systems


def test_sqlalchemy_dialect_dsn_maps_to_its_base_system(tmp_path):
    (tmp_path / "db.py").write_text(
        "from sqlalchemy import create_engine\n"
        "e = create_engine('postgresql+asyncpg://svc@db.internal:5432/orders')\n")
    assert "PostgreSQL" in _by_system(syscontext.scan(str(tmp_path), {}))


def test_google_from_imports_are_detected(tmp_path):
    (tmp_path / "gcs.py").write_text("from google.cloud import storage\n")
    (tmp_path / "llm.py").write_text("from google import genai\n")
    systems = _by_system(syscontext.scan(str(tmp_path), {}))
    assert "Google Cloud Storage" in systems
    assert "Google Gemini API" in systems


def test_oracle_jdbc_thin_url_is_detected(tmp_path):
    (tmp_path / "Dao.java").write_text(
        'String url = "jdbc:oracle:thin:@//db.internal:1521/orders";\n')
    assert "Oracle" in _by_system(syscontext.scan(str(tmp_path), {}))


def test_doc_host_skip_respects_domain_boundaries(tmp_path):
    (tmp_path / "hooks.py").write_text("URL = 'https://hooks.mygithub.com/api/notify'\n")
    assert "HTTP endpoint hooks.mygithub.com" in _by_system(syscontext.scan(str(tmp_path), {}))


def test_orm_and_rpc_abstraction_layers_yield_hedged_entries(tmp_path):
    """AC-11: the driver hides inside the library — report the seam, honestly hedged."""
    (tmp_path / "models.py").write_text("import sqlalchemy\n")
    (tmp_path / "rpc.py").write_text("import grpc\n")
    systems = _by_system(syscontext.scan(str(tmp_path), {}))
    assert "SQL database (engine not resolved)" in systems
    assert "gRPC peer (target not resolved)" in systems


def test_django_engine_literal_resolves_the_database(tmp_path):
    (tmp_path / "settings.py").write_text(
        "DATABASES = {'default': {'ENGINE': 'django.db.backends.postgresql'}}\n")
    assert "PostgreSQL" in _by_system(syscontext.scan(str(tmp_path), {}))


def test_jvm_dotnet_ruby_import_idioms(tmp_path):
    """AC-12: Java dotted packages, C# using-directives, Ruby parenless require."""
    (tmp_path / "Producer.java").write_text(
        "import org.apache.kafka.clients.producer.KafkaProducer;\n"
        "import com.stripe.Stripe;\n"
        "import software.amazon.awssdk.services.s3.S3Client;\n")
    (tmp_path / "Cache.cs").write_text("using StackExchange.Redis;\nusing Npgsql;\n")
    (tmp_path / "app.rb").write_text("require \"redis\"\nrequire \"sinatra\"\n")
    systems = _by_system(syscontext.scan(str(tmp_path), {}))
    assert "Apache Kafka" in systems and "Stripe" in systems
    assert "AWS S3" in systems                                    # Java v2 SDK service resolution
    assert "Redis" in systems and "PostgreSQL" in systems
    assert "HTTP surface exposed (Sinatra)" in systems            # un-deadened by parenless require


def test_lazy_function_body_imports_count(tmp_path):
    """A vendor SDK imported lazily inside a function is still observed evidence."""
    (tmp_path / "broker.py").write_text(
        "def client():\n"
        "    from alpaca.trading.client import TradingClient\n"
        "    return TradingClient()\n")
    assert "Alpaca API" in _by_system(syscontext.scan(str(tmp_path), {}))


def test_python_docstrings_are_prose_not_integrations(tmp_path):
    """AC-13: a connection-string example in a docstring must not become evidence."""
    (tmp_path / "cache.py").write_text(
        'def connect():\n'
        '    """Connect to the cache.\n'
        '\n'
        '    Example: cache = Cache("redis://localhost:6379/0")\n'
        '    See https://docs.internal-vendor.io/cache\n'
        '    """\n'
        '    pass\n')
    assert syscontext.scan(str(tmp_path), {})["entries"] == []


def test_illustrative_directories_are_never_scanned(tmp_path):
    """AC-14: example code demonstrates integrations, it doesn't have them."""
    (tmp_path / "examples").mkdir()
    (tmp_path / "examples" / "demo.py").write_text("import stripe\n")
    assert syscontext.scan(str(tmp_path), {})["entries"] == []


def test_comment_lines_are_prose_not_integrations(tmp_path):
    """The scanner must not detect its own kind of pattern documentation — schemes/URLs in comments."""
    (tmp_path / "notes.py").write_text(
        "# reach the db at postgres://db.internal:5432/orders\n"
        "// see https://api.partner.com/v1\n")
    assert syscontext.scan(str(tmp_path), {})["entries"] == []


def test_block_comments_and_trailing_comments_are_prose(tmp_path):
    """/* … */ interiors and trailing // comments never produce rows; block markers inside string
    literals (globs) must not swallow the rest of the file."""
    (tmp_path / "svc.ts").write_text(
        "/*\n"
        " legacy: import Stripe from \"stripe\";\n"
        " nats://bus.internal:4222\n"
        "*/\n"
        "const retries = 3; // mirror: https://fx-mirror.internal.dev\n"
        "const g = glob(\"src/*\");\n"
        "import Redis from \"ioredis\";\n")
    systems = _by_system(syscontext.scan(str(tmp_path), {}))
    assert "Redis" in systems                                 # the glob string didn't open block state
    assert not any("Stripe" in s or "NATS" in s or "fx-mirror" in s for s in systems)


def test_aws_sdks_resolve_across_ecosystems(tmp_path):
    (tmp_path / "a.js").write_text("const { S3Client } = require('@aws-sdk/client-s3');\n")
    (tmp_path / "b.go").write_text('package b\nimport "github.com/aws/aws-sdk-go-v2/service/sqs"\n')
    (tmp_path / "c.rs").write_text("use aws_sdk_dynamodb::Client;\n")
    (tmp_path / "D.java").write_text("import com.amazonaws.services.sns.AmazonSNS;\n")
    (tmp_path / "E.cs").write_text("using Amazon.S3;\n")
    systems = _by_system(syscontext.scan(str(tmp_path), {}))
    for s in ("AWS S3", "AWS SQS", "AWS DynamoDB", "AWS SNS"):
        assert s in systems, s
    assert systems["AWS S3"]["evidence_total"] == 2           # JS v3 + .NET merge into one entry


def test_modern_js_import_shapes(tmp_path):
    (tmp_path / "a.ts").write_text('import {\n  Kafka,\n  logLevel,\n} from "kafkajs";\n')
    (tmp_path / "b.ts").write_text('export { Kafka } from "kafkajs";\n')
    (tmp_path / "c.ts").write_text('const amqp = await import("amqplib");\n')
    (tmp_path / "d.ts").write_text('import type { RedisOptions } from "ioredis";\n')
    (tmp_path / "e.mjs").write_text("import { MongoClient } from 'mongodb'\n")
    systems = _by_system(syscontext.scan(str(tmp_path), {}))
    assert "Apache Kafka" in systems                          # multi-line closing + export…from
    assert "RabbitMQ (AMQP)" in systems                       # dynamic import()
    assert "MongoDB" in systems                               # .mjs is walked
    assert "Redis" not in systems                             # import type is erased at runtime


def test_rust_swift_csharp_kotlin_ecosystems(tmp_path):
    (tmp_path / "m.rs").write_text(
        "use sqlx::PgPool;\nuse axum::Router;\npub use twilio::Client;\nextern crate elasticsearch;\n")
    (tmp_path / "S.swift").write_text("import Vapor\nimport PostgresNIO\n")
    (tmp_path / "P.cs").write_text(
        "global using RabbitMQ.Client;\nusing Microsoft.AspNetCore.Mvc;\nusing Microsoft.EntityFrameworkCore;\n")
    (tmp_path / "K.kt").write_text(
        "import io.ktor.server.application.Application\nimport org.jetbrains.exposed.sql.Database\n")
    systems = _by_system(syscontext.scan(str(tmp_path), {}))
    for s in ("SQL database (engine not resolved)", "Twilio", "Elasticsearch", "PostgreSQL",
              "RabbitMQ (AMQP)"):
        assert s in systems, s
    for fw in ("Axum", "Vapor", "ASP.NET Core", "Ktor"):
        assert f"HTTP surface exposed ({fw})" in systems, fw


def test_ts_using_declaration_is_not_an_import(tmp_path):
    (tmp_path / "u.ts").write_text("using amqp = await channelPool.acquire();\n")
    assert syscontext.scan(str(tmp_path), {})["entries"] == []


def test_env_idioms_plural_and_destructured(tmp_path):
    (tmp_path / "e.js").write_text(
        "const brokers = process.env.KAFKA_BROKERS;\n"
        "const { PAYMENTS_API_URL } = process.env;\n")
    systems = _by_system(syscontext.scan(str(tmp_path), {}))
    assert "Configured endpoint (KAFKA_BROKERS)" in systems
    assert "Configured endpoint (PAYMENTS_API_URL)" in systems


def test_build_output_dirs_are_pruned(tmp_path):
    (tmp_path / "target").mkdir()
    (tmp_path / "target" / "gen.rs").write_text("use redis::Client;\n")
    assert syscontext.scan(str(tmp_path), {})["entries"] == []


def test_unsupported_languages_are_reported_never_silent(tmp_path):
    """AC-19 / INV-7: a repo the scanner can't fully read must say so on every surface."""
    (tmp_path / "svc.py").write_text("import psycopg2\n")
    (tmp_path / "main.cpp").write_text('#include <hiredis/hiredis.h>\n')
    (tmp_path / "core.clj").write_text('(ns core (:require [next.jdbc]))\n')
    result = syscontext.scan(str(tmp_path), {})
    assert result["unscanned"] == {".clj": 1, ".cpp": 1}
    note = syscontext.unscanned_note(result)
    assert note.startswith("Not scanned:") and ".cpp" in note and ".clj" in note
    assert note in syscontext.evidence_block(result)                  # repo-level block carries it
    assert note in syscontext.format_report(result, str(tmp_path))
    (tmp_path / "pure").mkdir()
    (tmp_path / "pure" / "ok.py").write_text("import psycopg2\n")
    assert syscontext.scan(str(tmp_path / "pure"), {})["unscanned"] == {}
    assert syscontext.unscanned_note(syscontext.scan(str(tmp_path / "pure"), {})) == ""


def test_cli_context_warns_on_unscanned_languages(tmp_path, capsys):
    (tmp_path / "svc.py").write_text("import psycopg2\n")
    (tmp_path / "main.cpp").write_text("int main() {}\n")
    cli.main(["context", str(tmp_path), "--out", str(tmp_path / "out")])
    assert "⚠ Not scanned:" in capsys.readouterr().out


def test_evidence_cap_is_per_directory_so_scoping_never_loses_a_dir(tmp_path):
    """A busy sibling dir must not evict another dir's only evidence site (INV-6 via the per-dir cap)."""
    (tmp_path / "aa").mkdir(), (tmp_path / "zz").mkdir()
    for i in range(syscontext.EVIDENCE_CAP + 2):
        (tmp_path / "aa" / f"m{i}.py").write_text("import psycopg2\n")
    (tmp_path / "zz" / "db.py").write_text("import psycopg2\n")
    result = syscontext.scan(str(tmp_path), {})
    assert "PostgreSQL" in syscontext.evidence_block(result, scope_dir="zz")
    (entry,) = result["entries"]
    assert entry["evidence_total"] == syscontext.EVIDENCE_CAP + 3     # every site still counted
