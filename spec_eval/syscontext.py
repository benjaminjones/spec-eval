"""System context — what external systems does this code OBSERVABLY talk to? Deterministic pattern scan: NO
API key, NO model call, free + CI-fast. The spec analogue of an arc42 "context & scope" inventory, derived
from code evidence instead of hand-maintained prose.

An ENTRY is one observed external system: an infrastructure service reached through an SDK/driver import or a
connection-string scheme (PostgreSQL, S3, Kafka, ...), a URL literal (reported as a `referenced` mention —
capability, not confirmed traffic), an endpoint injected through an environment variable
(`PAYMENTS_API_URL`), or an inbound surface (a web framework
import — the code exposes an API; its callers are NOT observable from this repo). Every entry carries its
evidence sites (file:line + the matched source line), so a reader can verify each row the way they verify a
spec: against the code.

Scope by design: SYSTEMS and DIRECTION only — no installed-package lists, no endpoint schemas, no ownership
registers (fast-changing detail, already maintained elsewhere). Systems reachable only through config files (YAML, .env) or
partner-repo knowledge are invisible to this scan: the report says so instead of guessing.
"""
import os
import re
import hashlib
from . import coverage as coverage_mod

SCHEMA = 2            # fingerprint layout version — bump when the JSON shape changes; a differing schema
                      # (like a differing scanner digest) makes a diff a re-baseline, never code drift

EVIDENCE_CAP = 8      # evidence sites kept per entry PER DIRECTORY (so per-dir scoping can never lose a
                      # system whose evidence sits in a busy sibling dir); the total count is always reported
LINE_CAP = 160        # chars of a matched source line kept as evidence
FILE_CAP = 2_000_000  # bytes read per file — a code file past this is scanned on its head, not skipped

# --- detection tables (kind: infra | application | inbound-surface | configured) ---------------------------
# SDK / driver imports — module or package name -> the system the import talks to.
SDK_IMPORTS = {
    "psycopg2": ("PostgreSQL", "infra"), "psycopg": ("PostgreSQL", "infra"), "asyncpg": ("PostgreSQL", "infra"),
    "pg8000": ("PostgreSQL", "infra"), "pg": ("PostgreSQL", "infra"),
    "pymysql": ("MySQL", "infra"), "MySQLdb": ("MySQL", "infra"), "mysql": ("MySQL", "infra"),
    "mysql2": ("MySQL", "infra"), "mariadb": ("MariaDB", "infra"),
    "pymongo": ("MongoDB", "infra"), "motor": ("MongoDB", "infra"), "mongoose": ("MongoDB", "infra"),
    "mongodb": ("MongoDB", "infra"),
    "redis": ("Redis", "infra"), "aioredis": ("Redis", "infra"), "ioredis": ("Redis", "infra"),
    "kafka": ("Apache Kafka", "infra"), "confluent_kafka": ("Apache Kafka", "infra"),
    "aiokafka": ("Apache Kafka", "infra"), "kafkajs": ("Apache Kafka", "infra"),
    "pika": ("RabbitMQ (AMQP)", "infra"), "aio_pika": ("RabbitMQ (AMQP)", "infra"),
    "amqplib": ("RabbitMQ (AMQP)", "infra"), "amqp": ("RabbitMQ (AMQP)", "infra"),
    "celery": ("Celery broker", "infra"),
    "elasticsearch": ("Elasticsearch", "infra"), "opensearchpy": ("OpenSearch", "infra"),
    "cassandra": ("Cassandra", "infra"),
    "pymemcache": ("Memcached", "infra"), "memjs": ("Memcached", "infra"),
    "smtplib": ("SMTP (email)", "infra"), "nodemailer": ("SMTP (email)", "infra"),
    "ldap3": ("LDAP directory", "infra"),
    "cx_Oracle": ("Oracle", "infra"), "oracledb": ("Oracle", "infra"),
    "stripe": ("Stripe", "application"), "twilio": ("Twilio", "application"),
    "sendgrid": ("SendGrid", "application"), "slack_sdk": ("Slack", "application"),
    "@slack/web-api": ("Slack", "application"),
    "openai": ("OpenAI API", "application"), "anthropic": ("Anthropic API", "application"),
    "googleapiclient": ("Google APIs", "application"), "google.genai": ("Google Gemini API", "application"),
    "alpaca": ("Alpaca API", "application"), "ib_insync": ("Interactive Brokers API", "application"),
    "ccxt": ("Crypto exchange APIs (ccxt)", "application"), "yfinance": ("Yahoo Finance API", "application"),
    # abstraction layers — the driver import hides inside the library, so the seam is reported hedged
    # (same precedent as 'AWS (service not resolved)'); a co-located literal often resolves it further down
    "sqlalchemy": ("SQL database (engine not resolved)", "infra"),
    "django.db": ("SQL database (engine not resolved)", "infra"),
    "sequelize": ("SQL database (engine not resolved)", "infra"),
    "typeorm": ("SQL database (engine not resolved)", "infra"),
    "org.hibernate": ("SQL database (engine not resolved)", "infra"),
    "javax.persistence": ("SQL database (engine not resolved)", "infra"),
    "jakarta.persistence": ("SQL database (engine not resolved)", "infra"),
    "grpc": ("gRPC peer (target not resolved)", "application"),
    "@grpc/grpc-js": ("gRPC peer (target not resolved)", "application"),
    "google.golang.org/grpc": ("gRPC peer (target not resolved)", "application"),
    "graphql-request": ("GraphQL endpoint (not resolved)", "application"),
    "@apollo/client": ("GraphQL endpoint (not resolved)", "application"),
    "gql": ("GraphQL endpoint (not resolved)", "application"),
    # JVM dotted-package prefixes (matched the way org.springframework.web already is)
    "com.stripe": ("Stripe", "application"), "org.apache.kafka": ("Apache Kafka", "infra"),
    "com.mongodb": ("MongoDB", "infra"), "io.lettuce": ("Redis", "infra"), "jedis": ("Redis", "infra"),
    "com.azure": ("Azure (service not resolved)", "infra"),
    # .NET using-directives (case-sensitive on purpose)
    "StackExchange.Redis": ("Redis", "infra"), "Npgsql": ("PostgreSQL", "infra"),
    "MySql.Data": ("MySQL", "infra"), "MongoDB.Driver": ("MongoDB", "infra"),
    "Confluent.Kafka": ("Apache Kafka", "infra"), "RabbitMQ.Client": ("RabbitMQ (AMQP)", "infra"),
    "Azure.Storage.Blobs": ("Azure Blob Storage", "infra"),
    "Microsoft.EntityFrameworkCore": ("SQL database (engine not resolved)", "infra"),
    "Stripe": ("Stripe", "application"),                       # C# Stripe.net + Swift Stripe (capitalized)
    # more JVM dotted prefixes
    "com.twilio": ("Twilio", "application"), "com.rabbitmq": ("RabbitMQ (AMQP)", "infra"),
    "com.mysql": ("MySQL", "infra"), "org.jetbrains.exposed": ("SQL database (engine not resolved)", "infra"),
    # Go module paths (matched like the Go framework keys — the quote before the path satisfies the boundary)
    "github.com/lib/pq": ("PostgreSQL", "infra"), "github.com/jackc/pgx": ("PostgreSQL", "infra"),
    "github.com/redis/go-redis": ("Redis", "infra"), "github.com/go-redis/redis": ("Redis", "infra"),
    "github.com/segmentio/kafka-go": ("Apache Kafka", "infra"),
    "github.com/confluentinc/confluent-kafka-go": ("Apache Kafka", "infra"),
    "github.com/rabbitmq/amqp091-go": ("RabbitMQ (AMQP)", "infra"),
    "github.com/stripe/stripe-go": ("Stripe", "application"),
    "go.mongodb.org/mongo-driver": ("MongoDB", "infra"),
    "github.com/elastic/go-elasticsearch": ("Elasticsearch", "infra"),
    # Rust crates (underscore names; `use` lines are import-shaped)
    "sqlx": ("SQL database (engine not resolved)", "infra"), "diesel": ("SQL database (engine not resolved)", "infra"),
    "sea_orm": ("SQL database (engine not resolved)", "infra"), "tokio_postgres": ("PostgreSQL", "infra"),
    "rdkafka": ("Apache Kafka", "infra"), "lapin": ("RabbitMQ (AMQP)", "infra"),
    "tonic": ("gRPC peer (target not resolved)", "application"),
    # Swift packages (capitalized module names; the matcher is case-sensitive)
    "PostgresNIO": ("PostgreSQL", "infra"), "RediStack": ("Redis", "infra"),
    "MongoSwift": ("MongoDB", "infra"), "AWSS3": ("AWS S3", "infra"),
    "Kafka": ("Apache Kafka", "infra"), "GRPC": ("gRPC peer (target not resolved)", "application"),
}
# Web-framework imports — the code EXPOSES a surface; who calls it is not observable from this repo.
INBOUND_FRAMEWORKS = {
    "flask": "Flask", "fastapi": "FastAPI", "django": "Django", "tornado": "Tornado", "sanic": "Sanic",
    "bottle": "Bottle", "express": "Express", "fastify": "Fastify", "koa": "Koa", "@hapi/hapi": "hapi",
    "sinatra": "Sinatra", "github.com/gin-gonic/gin": "Gin", "github.com/labstack/echo": "Echo",
    "github.com/gofiber/fiber": "Fiber", "github.com/go-chi/chi": "chi", "org.springframework.web": "Spring",
    "actix_web": "Actix Web", "axum": "Axum", "rocket": "Rocket", "warp": "Warp",
    "Vapor": "Vapor", "Microsoft.AspNetCore": "ASP.NET Core", "io.ktor.server": "Ktor",
}
# Connection-string schemes -> system (matched anywhere, import or not).
SCHEME_SYSTEMS = {
    "postgresql": "PostgreSQL", "postgres": "PostgreSQL", "jdbc:postgresql": "PostgreSQL",
    "mysql": "MySQL", "jdbc:mysql": "MySQL", "jdbc:oracle": "Oracle", "jdbc:sqlserver": "SQL Server",
    "mongodb": "MongoDB", "mongodb+srv": "MongoDB", "redis": "Redis", "rediss": "Redis",
    "amqp": "RabbitMQ (AMQP)", "amqps": "RabbitMQ (AMQP)", "kafka": "Apache Kafka",
    "s3": "AWS S3", "gs": "Google Cloud Storage", "smtp": "SMTP (email)",
    "ftp": "FTP/SFTP server", "sftp": "FTP/SFTP server", "nats": "NATS", "mqtt": "MQTT broker",
}
# AWS service ids seen in `.client("...")` / `.resource("...")` -> display names (fallback: upper/title case).
AWS_SERVICES = {"s3": "S3", "sqs": "SQS", "sns": "SNS", "dynamodb": "DynamoDB", "kinesis": "Kinesis",
                "lambda": "Lambda", "ses": "SES", "secretsmanager": "Secrets Manager", "ssm": "SSM",
                "sts": "STS", "ec2": "EC2", "ecs": "ECS", "cloudwatch": "CloudWatch", "logs": "CloudWatch Logs",
                "firehose": "Firehose", "athena": "Athena", "glue": "Glue", "stepfunctions": "Step Functions",
                "events": "EventBridge", "cloudfront": "CloudFront", "route53": "Route 53"}
# Literal-URL hosts that are documentation, not integration (suffix match).
SKIP_HOST_SUFFIXES = ("example.com", "example.org", "example.net", "w3.org", "schema.org", "json-schema.org",
                      "github.com", "wikipedia.org", "pypi.org", "npmjs.com", "opensource.org",
                      "creativecommons.org", "shields.io", "readthedocs.io", "stackoverflow.com")
# api.github.com IS an integration; bare github.com above is a doc link.
KEEP_HOSTS = {"api.github.com"}

KIND_ORDER = {"infra": 0, "application": 1, "configured": 2, "referenced": 3, "inbound-surface": 4}

# directories whose code demonstrates integrations rather than having them — never scanned
ILLUSTRATIVE_DIRS = {"examples", "example", "samples", "sample", "demo", "demos"}

# recognized source extensions OUTSIDE the scan's support — counted and reported so a language gap is
# stated, never silent (a repo full of these must not read as "talks to nothing")
OTHER_SOURCE_EXT = (".c", ".cpp", ".cc", ".cxx", ".h", ".hpp", ".hh", ".m", ".mm", ".scala", ".sc",
                    ".groovy", ".clj", ".cljs", ".cljc", ".ex", ".exs", ".erl", ".hs", ".ml", ".fs",
                    ".vb", ".pl", ".r", ".jl", ".dart", ".lua", ".zig", ".nim")

_IMPORTISH = re.compile(r"^\s*(?:import\b|from\b|use\b|pub\s+use\b|extern\s+crate\b|export\b.*\bfrom\b"
                        r"|\}\s*,?\s*from\b)|\brequire\(|\brequire\s+['\"]|\bimport\(")
_USING = re.compile(r"^\s*(?:global\s+)?using\s+(?:\w+\s*=\s*)?[A-Za-z_][\w.]*\s*;")   # C# namespace import
                                                     # (strict: excludes TS 5.2 `using x = await …` declarations)
_IMPORT_TYPE = re.compile(r"^\s*import\s+type\b")    # TS type-only import — erased at runtime, not a dependency
_COMMENT = re.compile(r"^\s*(?:#|//|/\*|\*|--|<!--|;;)")   # comment lines carry prose, not integrations
_GO_IMPORT_OPEN = re.compile(r"^\s*import\s*\(")     # Go's multi-line import block: quoted paths, no keyword
_GO_IMPORT_CLOSE = re.compile(r"^\s*\)")
_URL = re.compile(r"https?://([A-Za-z0-9][A-Za-z0-9.-]*\.[A-Za-z]{2,})(?::\d+)?")
# schemes: `postgres://`, SQLAlchemy dialects (`postgresql+asyncpg://`), `jdbc:x://`, and Oracle's
# subprotocol form `jdbc:oracle:thin:@//host/svc` (which never uses `://`).
_SCHEME = re.compile(r"\b(jdbc:[a-z]+)(?::[a-z0-9]+)+:@|\b(jdbc:[a-z]+|[a-z][a-z0-9+]{1,31})://")
_AWS_CLIENT = re.compile(r"\.\s*(?:client|resource)\(\s*['\"]([a-z0-9-]+)['\"]")
_ENV_SUFFIX = r"(?:URL|URI|HOST|HOSTNAME|ENDPOINT|DSN|BUCKET|QUEUE|TOPIC|BROKER|ADDR|SERVER)S?"
_ENV_QUOTED = re.compile(r"['\"]([A-Z][A-Z0-9]*(?:_[A-Z0-9]+)*_" + _ENV_SUFFIX + r")['\"]")
_ENV_BARE = re.compile(r"process\.env\.([A-Z0-9_]*_" + _ENV_SUFFIX + r")\b")
_ENV_DESTRUCTURE = re.compile(r"\{([^{}]*)\}\s*=\s*process\.env")   # const { PAYMENTS_API_URL } = process.env
_ENV_NAME = re.compile(r"\b([A-Z][A-Z0-9]*(?:_[A-Z0-9]+)*_" + _ENV_SUFFIX + r")\b")
_HAS_ENV = re.compile(r"(?i)env|\bvar\s*\(")   # cheap gate only — environ/getenv/process.env/ENV[…]/Rust var();
                                               # the strict _ENV_* regexes above decide what actually counts


# One AWS service resolver per SDK ecosystem — each maps its service id through AWS_SERVICES.
_AWS_ECOSYSTEMS = (
    re.compile(r"@aws-sdk/client-([a-z0-9-]+)"),                      # JS/TS v3
    re.compile(r"github\.com/aws/aws-sdk-go(?:-v2)?/service/([a-z0-9]+)"),   # Go
    re.compile(r"\baws_sdk_([a-z0-9_]+)\b"),                          # Rust
    re.compile(r"com\.amazonaws\.services\.([a-z0-9]+)"),             # Java v1
    re.compile(r"software\.amazon\.awssdk\.services\.([a-z0-9]+)"),   # Java v2
    re.compile(r"^\s*(?:global\s+)?using\s+Amazon\.([A-Za-z0-9]+)"),  # .NET (AWSSDK.*)
)
_AWS_PLUMBING = ("runtime", "extensions", "util", "core", "config", "auth")   # SDK namespaces, not services
_AWS_JAVA_MARKERS = ("software.amazon.awssdk", "com.amazonaws")               # SDK present but no service named
# Detectors that live off the module-level tables — hoisted so they are named, compiled once, and hashable by
# `_tables_digest` (any change to detection knowledge MUST move the digest — that is what keeps a scanner
# upgrade a re-baseline instead of false drift).
_GOOGLE_CLOUD_RE = re.compile(r"google\.cloud[\./]([a-z_]+)|from\s+google\.cloud\s+import\s+([a-z_]+)"
                              r"|@google-cloud/([a-z-]+)")
_GOOGLE_GENAI_RE = re.compile(r"from\s+google\s+import\s+genai\b")
_DJANGO_BACKENDS_RE = re.compile(r"django\.db\.backends\.(postgresql(?:_psycopg2)?|mysql|oracle)")
_DJANGO_ENGINE_MAP = {"mysql": "MySQL", "oracle": "Oracle"}                    # else PostgreSQL
_AZURE_SDK = {"azure.storage.blob": "Azure Blob Storage", "@azure/storage-blob": "Azure Blob Storage",
              "azure.servicebus": "Azure Service Bus", "@azure/service-bus": "Azure Service Bus",
              "azure.cosmos": "Azure Cosmos DB", "@azure/cosmos": "Azure Cosmos DB"}

# --- entry-point detection (how the repo is INVOKED) — a SEPARATE scanner with its OWN provenance, never
# folded into `_tables_digest`, so an entry-point-detection change never re-baselines the system-context
# fingerprint. Python + packaging-manifest focused; other languages are a stated gap, never a fabricated node.
EP_SCHEMA = 1                 # entry-point result layout version (separate artifact from the `scan()` result)
EP_KIND_ORDER = {"script": 0, "package-main": 1, "web-app": 2, "cli-main": 3, "module-main": 4}
EP_MODULE_MAIN_CAP = 6        # bare `if __name__ == '__main__'` guards kept in the cluster — capped so a repo
                              # full of demo/self-test guards can't drown the declared roots
_MAIN_GUARD = re.compile(r"""^\s*if\s+__name__\s*==\s*["']__main__["']""")   # anchored: a guard is a statement,
                                                                             # never a substring of a string literal
_ARGPARSE = re.compile(r"\bArgumentParser\s*\(|\badd_subparsers\s*\(")
_CLICK = re.compile(r"@click\.(?:group|command)\b")
# Framework app-object construction — an OBSERVED CAPABILITY ("constructs a Flask app"), NOT a confirmed served
# entry point: which server is actually invoked is deploy-time WSGI/ASGI/gunicorn config, invisible to a scan.
FRAMEWORK_APP_FACTORIES = ("Flask", "FastAPI", "Sanic", "Quart", "Bottle", "Tornado")
_APP_FACTORY = re.compile(r"\b([A-Za-z_]\w*)\s*=\s*(" + "|".join(FRAMEWORK_APP_FACTORIES) + r")\s*\(")
# Packaging-manifest script groups — `[project.scripts]` & friends DECLARE a console entry point by name.
# setup.py is NOT parsed (it is executable — entry_points can be built conditionally, so a static read would
# fabricate or miss rows); pyproject.toml / setup.cfg are static and safe.
_MANIFEST_SCRIPT_SECTIONS = ("[project.scripts]", "[project.gui-scripts]", "[tool.poetry.scripts]")
_TOML_HEADER = re.compile(r"^\s*(\[\[?[^\]\[]+\]\]?)")   # a TOML table header, tolerating a trailing comment
_MANIFEST_SCRIPT_ROW = re.compile(r"""^\s*["']?([\w.-]+)["']?\s*=\s*["']([^"']+)["']""")
_SETUPCFG_SCRIPT_GROUP = re.compile(r"^\s*(?:console_scripts|gui_scripts)\s*=")
_SETUPCFG_SCRIPT_ROW = re.compile(r"^\s*([\w.-]+)\s*=\s*([\w.:]+)")


def _token_hit(line, key):
    """Does `key` occur in `line` as a module token (not inside a longer name or a relative path)?"""
    return re.search(r"(?<![\w@/.-])" + re.escape(key) + r"(?![\w-])", line) is not None


C_FAMILY = (".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".go", ".rs", ".java", ".kt", ".kts",
            ".swift", ".cs", ".php", ".c", ".cpp", ".cc", ".h", ".hpp")
HASH_FAMILY = (".py", ".rb")


def _visible_code(line, in_block, style):
    """Return (visible_text, new_in_block): the line with comment spans removed. `style` 'c' strips
    /* … */ blocks (state carried across lines) and trailing //; 'hash' strips a trailing unquoted #.
    A naive quote tracker ('\", ', `, backslash escapes) keeps markers inside string literals — glob
    patterns like \"src/*\" — from toggling block state or truncating the line."""
    out = []
    quote = None
    i, n = 0, len(line)
    while i < n:
        c = line[i]
        if in_block:
            if c == "*" and i + 1 < n and line[i + 1] == "/":
                in_block = False
                i += 2
                continue
            i += 1
            continue
        if quote:
            out.append(c)
            if c == "\\" and i + 1 < n:
                out.append(line[i + 1])
                i += 2
                continue
            if c == quote:
                quote = None
            i += 1
            continue
        if c in ("\"", "'", "`"):
            quote = c
            out.append(c)
            i += 1
            continue
        if style == "c" and c == "/" and i + 1 < n:
            if line[i + 1] == "*":
                in_block = True
                i += 2
                continue
            if line[i + 1] == "/":
                break                                        # trailing // comment
        if style == "hash" and c == "#":
            break                                            # trailing # comment
        out.append(c)
        i += 1
    return "".join(out), in_block


def _visible_lines(rel, text):
    """Yield (lineno, raw_line, visible) for each line that carries visible, non-comment code — Python
    triple-quoted blocks and C-family / trailing-# comments stripped exactly as the scanner sees them, so a
    match can never fire on prose. Shared by the system-context scan and the entry-point scan; go-block/boto3
    tracking and all detection stay in the callers."""
    in_doc = False                 # inside a Python multi-line triple-quoted block — prose, like comments
    c_block = False                # inside a /* ... */ block comment (C-family files)
    for lineno, line in enumerate(text.splitlines(), 1):
        if rel.endswith(".py"):
            q = line.count('"""') + line.count("'''")
            if in_doc:
                if q % 2 == 1:
                    in_doc = False
                continue                                     # the line sits in (or closes) the block
            if q % 2 == 1:
                in_doc = True
                continue                                     # the opener line starts prose
        if rel.endswith(C_FAMILY):
            vis, c_block = _visible_code(line, c_block, "c")
        elif rel.endswith(HASH_FAMILY):
            vis, _ = _visible_code(line, False, "hash")
        else:
            vis = line
        if not vis.strip() or _COMMENT.match(vis):
            continue
        yield lineno, line, vis


def _scan_file(repo, rel, add):
    try:
        raw = open(os.path.join(repo, rel), "rb").read(FILE_CAP)
    except OSError:
        return
    text = raw.decode("utf-8", errors="ignore")     # fixed encoding: the scan must not vary with the locale
    boto3_import = None            # (lineno, line) of `import boto3` — reported only if no client id resolves
    boto3_resolved = False
    go_block = False               # inside Go's `import ( ... )` block — those lines carry no keyword
    for lineno, line, vis in _visible_lines(rel, text):
        if rel.endswith(".go"):
            if _GO_IMPORT_OPEN.match(vis):
                go_block = True
            elif go_block and _GO_IMPORT_CLOSE.match(vis):
                go_block = False
        if (_IMPORTISH.search(vis) and not _IMPORT_TYPE.match(vis)) or _USING.match(vis) or go_block:
            if _token_hit(vis, "boto3"):
                boto3_import = boto3_import or (lineno, line)
            for key, (system, kind) in SDK_IMPORTS.items():
                if _token_hit(vis, key):
                    add(system, kind, "outbound", "sdk", rel, lineno, line)
            for key, fw in INBOUND_FRAMEWORKS.items():
                if _token_hit(vis, key):
                    add(f"HTTP surface exposed ({fw})", "inbound-surface", "inbound", "framework",
                        rel, lineno, line)
            m = _GOOGLE_CLOUD_RE.search(vis)
            if m:
                svc = (m.group(1) or m.group(2) or m.group(3)).replace("_", " ").replace("-", " ").title()
                add(f"Google Cloud {svc}", "infra", "outbound", "sdk", rel, lineno, line)
            if _GOOGLE_GENAI_RE.search(vis):
                add("Google Gemini API", "application", "outbound", "sdk", rel, lineno, line)
            aws_hit = False
            for rx in _AWS_ECOSYSTEMS:
                m = rx.search(vis)
                if m:
                    sid = m.group(1).replace("_", "-").lower()
                    if sid in _AWS_PLUMBING:
                        continue                     # SDK plumbing namespaces, not services
                    name = AWS_SERVICES.get(sid) or (sid.upper() if len(sid) <= 4
                                                     else sid.replace("-", " ").title())
                    add(f"AWS {name}", "infra", "outbound", "sdk", rel, lineno, line)
                    aws_hit = True
            if not aws_hit and any(marker in vis for marker in _AWS_JAVA_MARKERS):
                add("AWS (service not resolved)", "infra", "outbound", "sdk", rel, lineno, line)
            for key, system in _AZURE_SDK.items():
                if key in vis:
                    add(system, "infra", "outbound", "sdk", rel, lineno, line)
        m = _AWS_CLIENT.search(vis)
        if m:
            sid = m.group(1)
            if sid in AWS_SERVICES:
                boto3_resolved = True
                add(f"AWS {AWS_SERVICES[sid]}", "infra", "outbound", "sdk", rel, lineno, line)
            elif boto3_import:      # unknown id, but the file demonstrably uses boto3: title-case fallback
                boto3_resolved = True
                name = sid.upper() if len(sid) <= 4 else sid.replace("-", " ").title()
                add(f"AWS {name}", "infra", "outbound", "sdk", rel, lineno, line)
        m = _DJANGO_BACKENDS_RE.search(vis)
        if m:                           # the engine literal resolves what the django.db import hedges
            add(_DJANGO_ENGINE_MAP.get(m.group(1), "PostgreSQL"),
                "infra", "outbound", "sdk", rel, lineno, line)
        for m in _URL.finditer(vis):
            host = m.group(1).lower()
            skip = any(host == s or host.endswith("." + s) for s in SKIP_HOST_SUFFIXES)
            if host in KEEP_HOSTS or not skip:
                add(f"HTTP endpoint {host}", "referenced", "outbound", "url", rel, lineno, line)
        for m in _SCHEME.finditer(vis):
            scheme = m.group(1) or m.group(2)
            system = SCHEME_SYSTEMS.get(scheme) or SCHEME_SYSTEMS.get(scheme.split("+", 1)[0])
            if system:
                add(system, "infra", "outbound", "scheme", rel, lineno, line)
        if _HAS_ENV.search(vis):
            for m in list(_ENV_QUOTED.finditer(vis)) + list(_ENV_BARE.finditer(vis)):
                add(f"Configured endpoint ({m.group(1)})", "configured", "outbound", "env", rel, lineno, line)
            dm = _ENV_DESTRUCTURE.search(vis)
            if dm:
                for name in _ENV_NAME.findall(dm.group(1)):
                    add(f"Configured endpoint ({name})", "configured", "outbound", "env", rel, lineno, line)
    if boto3_import and not boto3_resolved:
        lineno, line = boto3_import
        add("AWS (service not resolved)", "infra", "outbound", "sdk", rel, lineno, line)


def scan(repo, config):
    """Scan the repo's code files for external-system evidence. Deterministic: same tree -> same result.
    Walks the same code universe as coverage (code_ext, PRUNE_DIRS) but keeps glue/tooling files (real
    integrations often live in entrypoints and scripts) and skips tests/generated/user-excluded files
    (mock endpoints and fixture URLs are noise, not context)."""
    repo = os.path.abspath(repo)
    exts = tuple(config.get("code_ext") or coverage_mod.DEFAULT_CODE_EXT)
    user_excludes = config.get("exclude", [])
    entries = {}
    files_scanned = 0
    unscanned = {}                 # ext -> count of recognized-but-unsupported source files (not walked)

    def add(system, kind, direction, via, rel, lineno, line):
        rec = entries.setdefault((system, direction),
                                 {"system": system, "kind": kind, "direction": direction,
                                  "via": set(), "evidence": [], "evidence_total": 0})
        rec["via"].add(via)
        rec["evidence_total"] += 1
        d = os.path.dirname(rel)                   # cap per DIRECTORY: per-dir scoping must always find the
        if sum(1 for e in rec["evidence"]          # sites of a dir that observed the system (INV-6)
               if os.path.dirname(e["file"]) == d) < EVIDENCE_CAP:
            rec["evidence"].append({"file": rel, "line": lineno, "match": line.strip()[:LINE_CAP]})

    for root, dirs, files in os.walk(repo):
        dirs[:] = sorted(d for d in dirs if d not in coverage_mod.PRUNE_DIRS)   # sorted: INV-1 determinism
                                                                                # across filesystems
        for fn in sorted(files):
            if not fn.endswith(exts):
                if fn.endswith(OTHER_SOURCE_EXT):
                    ext = "." + fn.rsplit(".", 1)[1]
                    unscanned[ext] = unscanned.get(ext, 0) + 1
                continue
            rel = os.path.relpath(os.path.join(root, fn), repo)
            if coverage_mod.classify_exclude(rel, user_excludes) in ("test", "generated", "user"):
                continue
            if set(rel.split(os.sep)) & ILLUSTRATIVE_DIRS:
                continue                       # example code demonstrates integrations, it doesn't have them
            files_scanned += 1
            _scan_file(repo, rel, add)

    out = []
    for rec in entries.values():
        rec["via"] = sorted(rec["via"])
        rec["evidence"].sort(key=lambda e: (e["file"], e["line"]))
        out.append(rec)
    out.sort(key=lambda r: (KIND_ORDER.get(r["kind"], 9), r["system"], r["direction"]))
    return {"schema": SCHEMA, "scanner": scanner_provenance(),
            "repo": os.path.basename(repo), "files_scanned": files_scanned,
            "unscanned": dict(sorted(unscanned.items())), "entries": out}


def _tables_digest():
    """A stable 16-char hash of the detection TABLES and detection REGEXES — the knowledge that shapes the
    observed `(system, direction)` key set. A change to any of them (a new SDK key, a new scheme, a widened
    matcher, a changed gate) moves the digest, so a fingerprint diff across differing digests is a re-baseline
    ('the scanner learned to see more'), never code drift. It is not a proof over every character of
    `_scan_file` — the scanner `version` in the provenance compare is the catch-all for any detection change
    the digest doesn't reach. `sorted()` on every set/dict makes the hash order-independent, hence
    deterministic across Python runs."""
    payload = repr([
        sorted(SDK_IMPORTS.items()), sorted(INBOUND_FRAMEWORKS.items()), sorted(SCHEME_SYSTEMS.items()),
        sorted(AWS_SERVICES.items()), sorted(SKIP_HOST_SUFFIXES), sorted(KEEP_HOSTS),
        sorted(ILLUSTRATIVE_DIRS), sorted(OTHER_SOURCE_EXT), _ENV_SUFFIX,
        [r.pattern for r in _AWS_ECOSYSTEMS], sorted(_AWS_PLUMBING), sorted(_AWS_JAVA_MARKERS),
        sorted(_AZURE_SDK.items()), sorted(_DJANGO_ENGINE_MAP.items()),
        _GOOGLE_CLOUD_RE.pattern, _GOOGLE_GENAI_RE.pattern, _DJANGO_BACKENDS_RE.pattern,
        # the matching regexes shape the key set — widen one and new systems match
        _URL.pattern, _SCHEME.pattern, _AWS_CLIENT.pattern,
        _ENV_QUOTED.pattern, _ENV_BARE.pattern, _ENV_DESTRUCTURE.pattern, _ENV_NAME.pattern,
        # and the gates that decide which lines are even inspected
        _IMPORTISH.pattern, _USING.pattern, _IMPORT_TYPE.pattern, _HAS_ENV.pattern, _COMMENT.pattern,
        _GO_IMPORT_OPEN.pattern, _GO_IMPORT_CLOSE.pattern, sorted(C_FAMILY), sorted(HASH_FAMILY),
    ])
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def scanner_provenance():
    """Identity of the scanner that produced a fingerprint: package version + detection-table digest.
    The drift check compares this FIRST — a differing provenance means the two fingerprints are not
    comparable as code drift."""
    from spec_eval import __version__
    return {"version": __version__, "tables_digest": _tables_digest()}


# --- entry-point scan: how is this codebase INVOKED? A deterministic sibling of `scan()` with its OWN
# provenance, feeding the repo overview's Architecture (data flow) invocation diagram. ------------------------

def _module_dotted(rel):
    """`spec_eval/cli.py` -> `spec_eval.cli` — the dotted module name for an entry-point label."""
    return os.path.splitext(rel)[0].replace(os.sep, ".")


def _scan_entrypoints_file(repo, rel, found, module_mains):
    """Collect entry-point evidence from one file's VISIBLE lines (prose can never be a root). `__main__.py`
    is a declared package entry (`python -m pkg`); a `__main__` guard with argparse/click is a cli-main; a
    bare guard is a (capped) module-main; a framework app object is an observed web-app capability."""
    try:
        text = open(os.path.join(repo, rel), "rb").read(FILE_CAP).decode("utf-8", errors="ignore")
    except OSError:
        return
    guard = None                   # (lineno, matched line) of the __main__ guard
    has_cli = False                # argparse / click seen in this file
    for lineno, line, vis in _visible_lines(rel, text):
        if guard is None and _MAIN_GUARD.match(vis):
            guard = (lineno, line.strip()[:LINE_CAP])
        if _ARGPARSE.search(vis) or _CLICK.search(vis):
            has_cli = True
        m = _APP_FACTORY.search(vis)
        if m:
            found.append(("web-app", m.group(1), f"{m.group(2)} app object (constructed)",
                          rel, lineno, line.strip()[:LINE_CAP]))
    if os.path.basename(rel) == "__main__.py":
        pkg = os.path.dirname(rel).replace(os.sep, ".") or os.path.basename(repo)
        found.append(("package-main", pkg, f"python -m {pkg}", rel, 1, "__main__.py"))
    elif guard is not None:
        ln, ltext = guard
        if has_cli:
            found.append(("cli-main", _module_dotted(rel), "command-line interface", rel, ln, ltext))
        else:
            module_mains.append(("module-main", _module_dotted(rel), "run as a script", rel, ln, ltext))


def _read_text(path):
    """Read a file as UTF-8, locale-independent — matches the code scanners (`_scan_file`), so the manifest
    parse is byte-deterministic across hosts (a locale-default decode would vary the entry-point targets)."""
    return open(path, "rb").read().decode("utf-8", errors="ignore")


def _parse_manifest_scripts(repo):
    """DECLARED console entry points from packaging manifests, read statically (UTF-8, no tomllib, never
    importing setup.py). Returns [(name, target, file, lineno, line)] sorted by name. Scoped to console/gui
    script groups only — plugin entry-point groups (pytest11, ...) are not entry points."""
    out = []
    pp = os.path.join(repo, "pyproject.toml")
    if os.path.exists(pp):
        section = None
        for lineno, line in enumerate(_read_text(pp).splitlines(), 1):
            h = _TOML_HEADER.match(line)
            if h:                                    # ANY table header resets section (no state leak past a
                section = h.group(1) if h.group(1) in _MANIFEST_SCRIPT_SECTIONS else None  # non-script table)
                continue                             # and matches even with a trailing inline comment
            if section:
                m = _MANIFEST_SCRIPT_ROW.match(line)
                if m:
                    out.append((m.group(1), m.group(2), "pyproject.toml", lineno, line.strip()[:LINE_CAP]))
    sc = os.path.join(repo, "setup.cfg")
    if os.path.exists(sc):
        in_group = False
        for lineno, line in enumerate(_read_text(sc).splitlines(), 1):
            if line.strip().startswith("["):                       # a new [section] ends the console_scripts block
                in_group = False
                continue
            if _SETUPCFG_SCRIPT_GROUP.match(line):
                in_group = True
                continue
            if in_group:
                if line.strip() and not line[:1].isspace():        # dedented non-blank -> the block ended
                    in_group = False
                    continue
                m = _SETUPCFG_SCRIPT_ROW.match(line)
                if m:
                    out.append((m.group(1), m.group(2), "setup.cfg", lineno, line.strip()[:LINE_CAP]))
    return sorted(out, key=lambda r: (r[0], r[1], r[2], r[3]))


def scan_entrypoints(repo, config):
    """Scan how the repo is INVOKED. Deterministic: same tree -> same result. Two passes over the SAME code
    universe/exclusions as `scan()` (a code walk on visible lines for guards / app objects / CLI mains) plus a
    static manifest read for declared console scripts. Returns
    `{schema, scanner, repo, files_scanned, entrypoints:[{kind, name, target, evidence:{file,line,match}}]}`."""
    repo = os.path.abspath(repo)
    exts = tuple(config.get("code_ext") or coverage_mod.DEFAULT_CODE_EXT)
    user_excludes = config.get("exclude", [])
    found = []
    module_mains = []
    files_scanned = 0
    for root, dirs, files in os.walk(repo):
        dirs[:] = sorted(d for d in dirs if d not in coverage_mod.PRUNE_DIRS)   # sorted: INV-1 determinism
        for fn in sorted(files):
            if not fn.endswith(exts):
                continue
            rel = os.path.relpath(os.path.join(root, fn), repo)
            if coverage_mod.classify_exclude(rel, user_excludes) in ("test", "generated", "user"):
                continue
            if set(rel.split(os.sep)) & ILLUSTRATIVE_DIRS:
                continue                       # example code demonstrates entry points, it doesn't have them
            files_scanned += 1
            _scan_entrypoints_file(repo, rel, found, module_mains)
    module_mains.sort(key=lambda r: (r[3], r[4]))     # (file, line): deterministic, and cap the weakest tier
    found.extend(module_mains[:EP_MODULE_MAIN_CAP])
    for name, target, mfile, lineno, line in _parse_manifest_scripts(repo):
        found.append(("script", name, target, mfile, lineno, line))
    entrypoints = [{"kind": k, "name": n, "target": t,
                    "evidence": {"file": f, "line": ln, "match": m}} for (k, n, t, f, ln, m) in found]
    entrypoints.sort(key=lambda e: (EP_KIND_ORDER.get(e["kind"], 9), e["name"], e["target"] or "",
                                    e["evidence"]["file"], e["evidence"]["line"]))
    return {"schema": EP_SCHEMA, "scanner": ep_scanner_provenance(),
            "repo": os.path.basename(repo), "files_scanned": files_scanned, "entrypoints": entrypoints}


def _ep_tables_digest():
    """16-char hash of the ENTRY-POINT detection knowledge — SEPARATE from `_tables_digest` so an entry-point
    detection change never re-baselines the system-context fingerprint (the two scanners keep distinct
    provenance)."""
    payload = repr([
        sorted(EP_KIND_ORDER.items()), sorted(FRAMEWORK_APP_FACTORIES), EP_MODULE_MAIN_CAP,
        _MAIN_GUARD.pattern, _ARGPARSE.pattern, _CLICK.pattern, _APP_FACTORY.pattern,
        sorted(_MANIFEST_SCRIPT_SECTIONS), _TOML_HEADER.pattern, _MANIFEST_SCRIPT_ROW.pattern,
        _SETUPCFG_SCRIPT_GROUP.pattern, _SETUPCFG_SCRIPT_ROW.pattern,
    ])
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def ep_scanner_provenance():
    """Identity of the entry-point scanner: package version + its own detection-table digest, kept apart from
    the system-context scanner's provenance."""
    from spec_eval import __version__
    return {"version": __version__, "ep_tables_digest": _ep_tables_digest()}


def _scoped(result, scope_dir):
    """Entries re-filtered to evidence sitting DIRECTLY in `scope_dir` (the per-dir overview's file set)."""
    if scope_dir is None:
        return result["entries"]
    scoped = []
    for rec in result["entries"]:
        ev = [e for e in rec["evidence"] if os.path.dirname(e["file"]) == scope_dir]
        if ev:
            scoped.append({**rec, "evidence": ev, "evidence_total": len(ev)})   # kept in-scope sites
    return scoped


def unscanned_note(result):
    """The fixed language-gap line, or '' — a repo with unsupported source files must never read as
    'talks to nothing'; the gap is stated wherever the inventory is shown."""
    u = result.get("unscanned") or {}
    if not u:
        return ""
    parts = ", ".join(f"{n} {ext}" for ext, n in u.items())
    return (f"Not scanned: {parts} source file(s) — language(s) outside the scan's support; their "
            f"integrations are not represented. Add the extension(s) to `code_ext` to include them "
            f"with the generic matchers.")


def evidence_block(result, scope_dir=None):
    """The OBSERVED SYSTEM EVIDENCE block handed to the overview synthesis call — one line per observed
    system, each with a verifiable evidence site. Empty string when nothing was observed (the overview then
    carries no System context section at all — never an invented one)."""
    entries = _scoped(result, scope_dir)
    if not entries:
        return ""
    lines = ["## OBSERVED SYSTEM EVIDENCE (system context)",
             "Deterministic code scan — every system below was observed in this repository's code. Anything "
             "not listed was NOT observed; never add to this list."]
    for rec in entries:
        e = rec["evidence"][0]
        more = f" (+{rec['evidence_total'] - 1} more site(s))" if rec["evidence_total"] > 1 else ""
        lines.append(f"- {rec['system']} | kind: {rec['kind']} | direction: {rec['direction']} | "
                     f"via: {', '.join(rec['via'])} | evidence: `{e['file']}:{e['line']}` — "
                     f"`{e['match']}`{more}")
    note = unscanned_note(result)
    if note and scope_dir is None:                 # repo-level block carries the language-gap line
        lines.append(note)
    return "\n".join(lines)


def entrypoints_block(ep_result, scope_dir=None):
    """The OBSERVED ENTRY POINTS block handed to the repo overview synthesis call — one line per detected
    entry point with a verifiable evidence site, for the Architecture section's invocation diagram. Empty
    string when none detected (the diagram then shows no entry cluster — never an invented one)."""
    entries = ep_result.get("entrypoints", [])
    if scope_dir is not None:
        entries = [e for e in entries if os.path.dirname(e["evidence"]["file"]) == scope_dir]
    if not entries:
        return ""
    lines = ["## OBSERVED ENTRY POINTS (architecture)",
             "Deterministic code + manifest scan — every entry point below was observed. NEVER add one not "
             "listed. Each of these MUST appear in the invocation diagram as a scanner-verified entry point, "
             "noted with its file:line."]
    for e in entries:
        tgt = f" -> {e['target']}" if e.get("target") else ""
        ev = e["evidence"]
        lines.append(f"- {e['name']}{tgt} | kind: {e['kind']} | evidence: `{ev['file']}:{ev['line']}` — "
                     f"`{ev['match']}`")
    return "\n".join(lines)


def format_report(result, repo):
    name = os.path.basename(os.path.abspath(repo))
    lines = [f"# System context — `{name}`"]
    n = len(result["entries"])
    lines.append(f"**{n} external system(s) observed** across {result['files_scanned']} scanned code file(s). "
                 f"Deterministic scan — no AI, no key.")
    lines.append("")
    if result["entries"]:
        lines.append("| External system | Kind | Direction | Via | Evidence |")
        lines.append("|---|---|---|---|---|")
        for rec in result["entries"]:
            e = rec["evidence"][0]
            more = f" +{rec['evidence_total'] - 1} more" if rec["evidence_total"] > 1 else ""
            lines.append(f"| {rec['system']} | {rec['kind']} | {rec['direction']} | "
                         f"{', '.join(rec['via'])} | `{e['file']}:{e['line']}`{more} |")
        lines.append("")
    lines.append("> Derived from this repository's code — rows are evidence of capability in the code, not "
                 "proof of runtime traffic, and a `referenced` row is a URL mention only (integration "
                 "unconfirmed). Inbound callers and partner-system behavior are not observable from this repo "
                 "— confirm asserted context with the owning teams. Systems reached only through config files "
                 "are not scanned. Installed packages and endpoint schemas are out of scope by design.")
    note = unscanned_note(result)
    if note:
        lines.append("")
        lines.append(f"> ⚠ {note}")
    return "\n".join(lines)


# --- drift check: compare a fresh scan against a stored fingerprint -----------------------------------------

def _delta_entry(e):
    """The change-relevant slice of an entry for a receipt: identity + how + one verifiable evidence site."""
    site = (e.get("evidence") or [{}])[0]
    ref = f"{site.get('file')}:{site.get('line')}" if site.get("file") else None
    return {"system": e["system"], "direction": e["direction"], "kind": e.get("kind"),
            "via": e.get("via", []), "evidence": ref}


def diff(baseline, current):
    """Compare two scan results by their (system, direction) KEY SET — the identity that matters — never by
    JSON bytes (evidence line-churn, a second call site, or a file rename are not drift). Returns
    `{outcome, scanner_changed, added[], removed[]}`:
      - 'clean'      — the same systems; only verification payload moved.
      - 'drift'      — a system was added or removed (the only outcome a gate fails on).
      - 'rebaseline' — the scanner (version / tables digest) or schema differs, so the two fingerprints are
                       NOT comparable as code drift; re-store the baseline. Never counts as drift."""
    def prov(r):
        s = r.get("scanner") or {}
        return (r.get("schema"), s.get("version"), s.get("tables_digest"))   # version is the catch-all: ANY
    scanner_changed = prov(baseline) != prov(current)                        # released scanner change -> rebaseline

    bi = {(e["system"], e["direction"]): e for e in baseline.get("entries", [])}
    ci = {(e["system"], e["direction"]): e for e in current.get("entries", [])}
    added = [_delta_entry(ci[k]) for k in sorted(set(ci) - set(bi))]
    removed = [_delta_entry(bi[k]) for k in sorted(set(bi) - set(ci))]

    outcome = "rebaseline" if scanner_changed else ("drift" if (added or removed) else "clean")
    return {"outcome": outcome, "scanner_changed": scanner_changed, "added": added, "removed": removed}


def _delta_lines(d):
    lines = []
    for e in d["added"]:
        ev = f" — {e['evidence']}" if e["evidence"] else ""
        lines.append(f"  + {e['system']} ({e['direction']}, via {', '.join(e['via'])}){ev}")
    for e in d["removed"]:
        lines.append(f"  - {e['system']} ({e['direction']})")
    return "\n".join(lines)


def diff_receipt(d, sha=None):
    """A named-delta receipt in SPEC-HEALTH's click-to-verify style — one line per changed system, each with
    an evidence site — never a full-table reprint or an evidence-churn row."""
    at = f" @ {sha}" if sha else ""
    if d["outcome"] == "clean":
        return f"0 system-context changes{at}"
    if d["outcome"] == "rebaseline":
        head = (f"scanner changed — re-baseline{at}: the stored fingerprint came from a different scanner "
                f"version/tables, so its diff is scanner coverage, not code drift. Re-run `spec-eval "
                f"context` to re-store.")
        body = _delta_lines(d)
        return head + ("\n" + body if body else "")
    return f"System-context drift{at}:\n" + _delta_lines(d)


# --- overview freshness stamp: does a generated overview still match the scan it was rendered from? ---------

STAMP_RE = re.compile(r"<!--\s*system-context-fingerprint:\s*([0-9a-f]+)\s*-->")


def fingerprint_digest(result):
    """A 12-char hash of the observed `(system, direction)` key set — the same identity `diff` uses. Two
    scans with the same systems share a digest even if evidence sites moved."""
    keys = sorted((e["system"], e["direction"]) for e in result.get("entries", []))
    return hashlib.sha256(repr(keys).encode()).hexdigest()[:12]


def stamp_comment(result):
    """The HTML-comment receipt appended to a generated overview: the fingerprint the System context section
    was rendered from. Invisible in rendered markdown; read back by `overview_stale`."""
    return f"<!-- system-context-fingerprint: {fingerprint_digest(result)} -->"


def read_stamp(markdown):
    m = STAMP_RE.search(markdown)
    return m.group(1) if m else None


def overview_stale(markdown, current):
    """True when the overview carries a stamp whose digest no longer matches the current scan — the code's
    external systems changed but the overview was not regenerated. Absent stamp -> not stale (nothing to
    verify)."""
    stamp = read_stamp(markdown)
    return stamp is not None and stamp != fingerprint_digest(current)


# --- architecture diagram freshness stamp (edge 3: fingerprint -> diagram) ----------------------------------
# A PARALLEL, distinct stamp so a stale diagram can be flagged without touching the system-context stamp above.
# Its digest composes BOTH scanner-derived layers (external systems + entry points) AND the module set the
# diagram was drawn over, so a new system, a new entry point, or an added/renamed module all trip `--check`.
# Like `fingerprint_digest`, it excludes the detection tables — a scanner upgrade is a benign re-baseline.

ARCH_STAMP_RE = re.compile(r"<!--\s*architecture-fingerprint:\s*([0-9a-f]+)\s*-->")


def architecture_digest(ctx_result, ep_result, modules):
    """A 12-char hash binding the diagram to what it depicts: the observed `(system, direction)` key set, the
    `(kind, name, target)` entry-point key set, and the sorted module identifiers."""
    sys_keys = sorted((e["system"], e["direction"]) for e in ctx_result.get("entries", []))
    ep_keys = sorted((e["kind"], e["name"], e.get("target") or "") for e in ep_result.get("entrypoints", []))
    payload = repr([sys_keys, ep_keys, sorted(modules)])
    return hashlib.sha256(payload.encode()).hexdigest()[:12]


def architecture_stamp_comment(ctx_result, ep_result, modules):
    """The HTML-comment receipt appended to a generated overview alongside (and distinct from) the
    system-context stamp: the architecture fingerprint the diagram was rendered from."""
    return f"<!-- architecture-fingerprint: {architecture_digest(ctx_result, ep_result, modules)} -->"


def read_arch_stamp(markdown):
    m = ARCH_STAMP_RE.search(markdown)
    return m.group(1) if m else None


def diagram_stale(markdown, ctx_result, ep_result, modules):
    """True when the overview carries an architecture stamp whose digest no longer matches a fresh scan — the
    systems, entry points, or module set changed but the diagram was not regenerated. Absent stamp -> not
    stale. Diagram staleness WARNS; it never gates."""
    stamp = read_arch_stamp(markdown)
    return stamp is not None and stamp != architecture_digest(ctx_result, ep_result, modules)


def restamp_architecture(markdown, ctx_result, ep_result, modules):
    """Refresh (replace-or-append) ONLY the architecture-fingerprint stamp — used by `diagram --write`, which
    regenerates the diagram alone. Any existing system-context stamp is left BYTE-IDENTICAL: a diagram update
    must never re-bless a stale System context table, and it never adds a system-context stamp of its own."""
    stamp = architecture_stamp_comment(ctx_result, ep_result, modules)
    if ARCH_STAMP_RE.search(markdown):
        return ARCH_STAMP_RE.sub(lambda _m: stamp, markdown, count=1)
    return markdown.rstrip() + "\n\n" + stamp + "\n"
