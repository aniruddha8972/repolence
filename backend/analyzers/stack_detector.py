"""
RepoLens — Stack Detector
Identifies programming language, framework, database, and tooling
from file extensions, package manifests, and source content.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class StackInfo:
    language:  str = "Unknown"
    framework: str = ""
    runtime:   str = ""
    database:  str = ""
    tools:     list[str] = field(default_factory=list)
    auth:      str = ""
    protocol:  str = "HTTP / REST"
    error_handling: str = "Not detected"

    @property
    def tag_list(self) -> list[str]:
        tags = []
        if self.language:   tags.append(self.language)
        if self.framework:  tags.append(self.framework)
        if self.runtime and self.runtime != self.language: tags.append(self.runtime)
        tags.extend(self.tools)
        return tags


def detect_stack(
    all_files:  list[str],
    pkg:        dict | None,
    all_src:    str,
) -> StackInfo:
    info = StackInfo()

    # ── Language from file extensions ────────────────────────────────────
    ext_count: dict[str, int] = {}
    for f in all_files:
        ext = f.rsplit(".", 1)[-1].lower() if "." in f else ""
        ext_count[ext] = ext_count.get(ext, 0) + 1

    if ext_count.get("ts", 0) > ext_count.get("js", 0):
        info.language = "TypeScript";  info.runtime = "Node.js"
    elif ext_count.get("js", 0):
        info.language = "JavaScript";  info.runtime = "Node.js"
    elif ext_count.get("py", 0):
        info.language = "Python";      info.runtime = "Python 3"
    elif ext_count.get("go", 0):
        info.language = "Go";          info.runtime = "Go runtime"
    elif ext_count.get("rs", 0):
        info.language = "Rust";        info.runtime = "Rust"
    elif ext_count.get("java", 0):
        info.language = "Java";        info.runtime = "JVM"
    elif ext_count.get("rb", 0):
        info.language = "Ruby";        info.runtime = "Ruby"
    elif ext_count.get("php", 0):
        info.language = "PHP";         info.runtime = "PHP"
    elif ext_count.get("swift", 0):
        info.language = "Swift";       info.runtime = "Swift"
    elif ext_count.get("cs", 0):
        info.language = "C#";          info.runtime = ".NET"
    elif ext_count.get("kt", 0) or ext_count.get("kts", 0):
        info.language = "Kotlin";      info.runtime = "JVM"

    # ── Python framework detection (from source) ─────────────────────────
    if info.language == "Python":
        if re.search(r"from\s+flask\b|import\s+flask\b", all_src, re.IGNORECASE):
            info.framework = "Flask"
        elif re.search(r"from\s+fastapi\b|import\s+fastapi\b|FastAPI\s*\(", all_src, re.IGNORECASE):
            info.framework = "FastAPI"
        elif re.search(r"DJANGO_SETTINGS|from\s+django\b|import\s+django\b", all_src, re.IGNORECASE):
            info.framework = "Django"
        elif re.search(r"from\s+tornado\b|tornado\.web", all_src, re.IGNORECASE):
            info.framework = "Tornado"
        elif re.search(r"from\s+sanic\b|Sanic\s*\(", all_src, re.IGNORECASE):
            info.framework = "Sanic"
        elif re.search(r"from\s+aiohttp\b|aiohttp\.web", all_src, re.IGNORECASE):
            info.framework = "aiohttp"

        # Python DB / ORM
        if re.search(r"sqlalchemy|declarative_base|Column\s*\(", all_src, re.IGNORECASE):
            info.database = "SQLAlchemy"
        elif re.search(r"MongoClient|pymongo", all_src, re.IGNORECASE):
            info.database = "MongoDB (pymongo)"
        elif re.search(r"psycopg2|asyncpg", all_src, re.IGNORECASE):
            info.database = "PostgreSQL"
        elif re.search(r"sqlite3|aiosqlite", all_src, re.IGNORECASE):
            info.database = "SQLite"
        elif re.search(r"aiomysql|MySQLdb|pymysql", all_src, re.IGNORECASE):
            info.database = "MySQL"
        elif re.search(r"\bredis\b|aioredis", all_src, re.IGNORECASE):
            info.database = "Redis"
        elif re.search(r"tortoise|Tortoise", all_src):
            info.database = "Tortoise ORM"

        # Python tools
        if re.search(r"pandas|numpy|matplotlib|sklearn|torch|tensorflow|keras", all_src, re.IGNORECASE):
            info.tools.append("Data Science / ML")
        if re.search(r"celery|Celery", all_src):
            info.tools.append("Celery")
        if re.search(r"pytest|unittest", all_src):
            info.tools.append("Testing")
        if re.search(r"pydantic|BaseModel", all_src):
            info.tools.append("Pydantic")
        if re.search(r"alembic", all_src, re.IGNORECASE):
            info.tools.append("Alembic")
        if re.search(r"pyjwt|from\s+jwt\b|import\s+jwt\b", all_src, re.IGNORECASE):
            info.tools.append("JWT")

    # ── Node.js stack from package.json ──────────────────────────────────
    if pkg:
        all_deps = {
            **pkg.get("dependencies", {}),
            **pkg.get("devDependencies", {}),
            **pkg.get("peerDependencies", {}),
        }

        # Framework
        if not info.framework:
            fw_map = [
                ("express",            "Express"),
                ("fastify",            "Fastify"),
                ("koa",                "Koa"),
                ("next",               "Next.js"),
                ("nuxt",               "Nuxt"),
                ("react",              "React"),
                ("vue",                "Vue"),
                ("@nestjs/core",       "NestJS"),
                ("@hapi/hapi",         "Hapi"),
                ("hapi",               "Hapi"),
                ("restify",            "Restify"),
                ("sails",              "Sails.js"),
            ]
            for pkg_name, fw_name in fw_map:
                if pkg_name in all_deps:
                    info.framework = fw_name
                    break

        # DB / ORM
        db_map = [
            ("prisma",             "Prisma"),
            ("@prisma/client",     "Prisma"),
            ("sequelize",          "Sequelize"),
            ("mongoose",           "MongoDB"),
            ("typeorm",            "TypeORM"),
            ("knex",               "Knex.js"),
            ("pg",                 "PostgreSQL"),
            ("mysql2",             "MySQL"),
            ("mongodb",            "MongoDB"),
            ("sqlite3",            "SQLite"),
            ("redis",              "Redis"),
            ("ioredis",            "Redis"),
        ]
        for pkg_name, db_name in db_map:
            if pkg_name in all_deps:
                if not info.database:
                    info.database = db_name
                if db_name not in info.tools:
                    info.tools.append(db_name)
                break

        # Tools
        tool_map = [
            ("typescript",            "TypeScript"),
            ("jest",                  "Jest"),
            ("vitest",                "Vitest"),
            ("mocha",                 "Mocha"),
            ("jasmine",               "Jasmine"),
            ("webpack",               "Webpack"),
            ("vite",                  "Vite"),
            ("rollup",                "Rollup"),
            ("esbuild",               "esbuild"),
            ("parcel",                "Parcel"),
            ("eslint",                "ESLint"),
            ("prettier",              "Prettier"),
            ("axios",                 "Axios"),
            ("node-fetch",            "node-fetch"),
            ("got",                   "got"),
            ("socket.io",             "Socket.IO"),
            ("ws",                    "WebSockets"),
            ("dotenv",                "dotenv"),
            ("graphql",               "GraphQL"),
            ("@apollo/server",        "Apollo"),
            ("kafkajs",               "Kafka"),
            ("amqplib",               "RabbitMQ"),
            ("passport",              "Passport.js"),
            ("jsonwebtoken",          "JWT"),
            ("@nestjs/swagger",       "Swagger"),
            ("swagger-ui-express",    "Swagger"),
            ("zod",                   "Zod"),
            ("joi",                   "Joi"),
            ("class-validator",       "class-validator"),
            ("bull",                  "Bull (Queue)"),
            ("bullmq",                "BullMQ"),
        ]
        for pkg_name, tool_name in tool_map:
            if pkg_name in all_deps and tool_name not in info.tools:
                info.tools.append(tool_name)

    if info.database and info.database not in info.tools:
        info.tools.insert(0, info.database)

    # ── Auth detection from source ───────────────────────────────────────
    if re.search(r"jsonwebtoken|jwt\.sign|jwt\.verify", all_src, re.IGNORECASE):
        info.auth = "JWT (jsonwebtoken)"
    elif re.search(r"pyjwt|from\s+jwt\b", all_src, re.IGNORECASE):
        info.auth = "JWT (PyJWT)"
    elif re.search(r"passport\.authenticate", all_src, re.IGNORECASE):
        info.auth = "Passport.js"
    elif re.search(r"express-session|cookie-session", all_src, re.IGNORECASE):
        info.auth = "Session / Cookie"
    elif re.search(r"oauth2?", all_src, re.IGNORECASE):
        info.auth = "OAuth 2.0"
    elif re.search(r"Bearer|bearer_token", all_src):
        info.auth = "Bearer Token"
    elif re.search(r"BasicAuth|basic_auth", all_src, re.IGNORECASE):
        info.auth = "Basic Auth"
    elif re.search(r"api[_-]?key", all_src, re.IGNORECASE):
        info.auth = "API Key"

    # ── Protocol ────────────────────────────────────────────────────────
    if re.search(r"graphql|apollo|gql`|from\s+graphene", all_src, re.IGNORECASE):
        info.protocol = "GraphQL"
    elif re.search(r"socket\.io|WebSocket|ws\.on", all_src, re.IGNORECASE):
        info.protocol = "WebSocket + HTTP"
    elif re.search(r"grpc|\.proto\b", all_src, re.IGNORECASE):
        info.protocol = "gRPC"
    elif re.search(r"kafka|rabbitmq|amqp|celery\.task", all_src, re.IGNORECASE):
        info.protocol = "Message Queue / Event"

    # ── Error handling ───────────────────────────────────────────────────
    if re.search(r"app\.use\([^)]*err|errorHandler|error_handler", all_src, re.IGNORECASE):
        info.error_handling = "Global error middleware"
    elif re.search(r"try\s*\{[\s\S]{0,600}catch", all_src):
        info.error_handling = "try / catch blocks"
    elif re.search(r"\.catch\s*\(", all_src):
        info.error_handling = "Promise .catch()"
    elif re.search(r"except\s+\w+", all_src):
        info.error_handling = "Python except blocks"

    return info
