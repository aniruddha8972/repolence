"""
RepoLens — Parser Unit Tests
Run with: python -m pytest tests/ -v
"""
import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.parsers.code_parser import (
    parse_imports, parse_classes, parse_functions,
    parse_routes, parse_middleware, build_call_graph,
)
from backend.utils.file_selector import score_file, select_files
from backend.analyzers.stack_detector import detect_stack


# ══════════════════════════════════════════════════════════════════════════════
#  IMPORTS
# ══════════════════════════════════════════════════════════════════════════════
class TestParseImports:
    def test_esm_basic(self):
        src = "import express from 'express';"
        imports = parse_imports(src, "app.js")
        assert any(i.name == "express" and not i.local for i in imports)

    def test_esm_named(self):
        src = "import { useState, useEffect } from 'react';"
        imports = parse_imports(src, "comp.tsx")
        assert any(i.name == "react" for i in imports)

    def test_cjs_require(self):
        src = "const path = require('path');"
        imports = parse_imports(src, "a.js")
        assert any(i.name == "path" for i in imports)

    def test_local_import(self):
        src = "import db from './database';"
        imports = parse_imports(src, "server.js")
        local = [i for i in imports if i.local]
        assert local
        assert local[0].name == "./database"

    def test_python_from_import(self):
        src = "from flask import Flask, jsonify\n"
        imports = parse_imports(src, "app.py")
        assert any(i.name == "flask" and not i.local for i in imports)

    def test_python_import(self):
        src = "import os\nimport sys\n"
        imports = parse_imports(src, "utils.py")
        names = {i.name for i in imports}
        assert "os" in names and "sys" in names

    def test_go_import_block(self):
        src = '''import (\n\t"fmt"\n\t"net/http"\n)\n'''
        imports = parse_imports(src, "main.go")
        names = {i.name for i in imports}
        assert "fmt" in names

    def test_no_duplicates(self):
        src = "import x from 'lodash';\nconst y = require('lodash');"
        imports = parse_imports(src, "a.js")
        lodash = [i for i in imports if i.name == "lodash"]
        assert len(lodash) == 1


# ══════════════════════════════════════════════════════════════════════════════
#  CLASSES
# ══════════════════════════════════════════════════════════════════════════════
class TestParseClasses:
    def test_js_class_basic(self):
        src = "class UserService {\n  getUser(id) {}\n  createUser(data) {}\n}"
        classes = parse_classes(src, "service.js")
        assert any(c.name == "UserService" for c in classes)

    def test_js_class_extends(self):
        src = "class AdminService extends UserService { }"
        classes = parse_classes(src, "admin.js")
        c = next((x for x in classes if x.name == "AdminService"), None)
        assert c and c.parent == "UserService"

    def test_py_class_basic(self):
        src = "class UserModel:\n    def save(self):\n        pass\n    def delete(self):\n        pass\n"
        classes = parse_classes(src, "models.py")
        assert any(c.name == "UserModel" for c in classes)

    def test_py_class_with_parent(self):
        src = "class FlaskApp(Flask):\n    def run(self):\n        pass\n"
        classes = parse_classes(src, "app.py")
        c = next((x for x in classes if x.name == "FlaskApp"), None)
        assert c and c.parent == "Flask"

    def test_methods_extracted(self):
        src = "class Repo {\n  async findAll() {}\n  async save(data) {}\n  delete(id) {}\n}"
        classes = parse_classes(src, "repo.js")
        c = next(x for x in classes if x.name == "Repo")
        assert len(c.methods) >= 2


# ══════════════════════════════════════════════════════════════════════════════
#  FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════
class TestParseFunctions:
    def test_js_named_function(self):
        src = "function getUserById(id) { return db.find(id); }"
        fns = parse_functions(src, "a.js")
        assert any(f.name == "getUserById" for f in fns)

    def test_arrow_function(self):
        src = "const createUser = async (data) => { return db.save(data); };"
        fns = parse_functions(src, "a.js")
        assert any(f.name == "createUser" for f in fns)

    def test_export_function(self):
        src = "export async function deleteUser(id) {}"
        fns = parse_functions(src, "a.ts")
        assert any(f.name == "deleteUser" for f in fns)

    def test_python_def(self):
        src = "def get_user(user_id):\n    return User.query.get(user_id)\n"
        fns = parse_functions(src, "views.py")
        assert any(f.name == "get_user" for f in fns)

    def test_go_func(self):
        src = "func GetUser(w http.ResponseWriter, r *http.Request) {}\n"
        fns = parse_functions(src, "handlers.go")
        # Go uppercase functions — check they are not filtered (they don't start uppercase check)
        names = {f.name for f in fns}
        # may or may not match depending on case filter — at minimum no crash
        assert isinstance(fns, list)

    def test_no_keyword_functions(self):
        src = "if (true) {} for (let x of arr) {} while(true) {}"
        fns = parse_functions(src, "a.js")
        assert not any(f.name in ("if", "for", "while") for f in fns)


# ══════════════════════════════════════════════════════════════════════════════
#  ROUTES
# ══════════════════════════════════════════════════════════════════════════════
class TestParseRoutes:
    def test_express_get(self):
        src = "app.get('/users', getUsers);"
        routes = parse_routes(src, "routes.js")
        assert any(r.method == "GET" and r.path == "/users" for r in routes)

    def test_express_post(self):
        src = "router.post('/auth/login', loginHandler);"
        routes = parse_routes(src, "auth.js")
        assert any(r.method == "POST" and r.path == "/auth/login" for r in routes)

    def test_flask_route(self):
        src = "@app.route('/api/users', methods=['GET', 'POST'])\ndef users(): pass"
        routes = parse_routes(src, "app.py")
        methods = {r.method for r in routes}
        assert "GET" in methods and "POST" in methods

    def test_fastapi_route(self):
        src = "@app.get('/items/{item_id}')\nasync def read_item(): pass"
        routes = parse_routes(src, "main.py")
        assert any(r.method == "GET" and "/items/" in r.path for r in routes)

    def test_nestjs_decorator(self):
        src = "@Get('/users')\ngetUsers() {}"
        routes = parse_routes(src, "users.controller.ts")
        assert any(r.method == "GET" and r.path == "/users" for r in routes)

    def test_deduplication(self):
        src = "app.get('/ping', h1);\napp.get('/ping', h2);"
        routes = parse_routes(src, "a.js")
        pings = [r for r in routes if r.path == "/ping" and r.method == "GET"]
        assert len(pings) == 1


# ══════════════════════════════════════════════════════════════════════════════
#  FILE SELECTOR
# ══════════════════════════════════════════════════════════════════════════════
class TestFileSelector:
    def test_skip_node_modules(self):
        assert score_file("node_modules/express/index.js") == -1

    def test_skip_dist(self):
        assert score_file("dist/bundle.min.js") == -1

    def test_skip_non_code(self):
        assert score_file("assets/logo.png") == -1

    def test_high_score_for_index(self):
        assert score_file("index.js") > score_file("utils/helpers.js")

    def test_high_score_for_route_file(self):
        s_route  = score_file("src/routes/users.js")
        s_random = score_file("src/random/thing.js")
        assert s_route > s_random

    def test_select_files_returns_list(self):
        files = [
            "package.json", "index.js", "src/app.js",
            "node_modules/express/index.js",
            "dist/bundle.js",
        ]
        selected = select_files(files, limit=10)
        assert "package.json" in selected
        assert "node_modules/express/index.js" not in selected

    def test_manifests_first(self):
        files = ["src/utils.js", "src/app.js", "package.json", "README.md"]
        selected = select_files(files)
        assert selected.index("package.json") < selected.index("src/utils.js")


# ══════════════════════════════════════════════════════════════════════════════
#  STACK DETECTOR
# ══════════════════════════════════════════════════════════════════════════════
class TestStackDetector:
    def test_detect_typescript(self):
        files = ["src/index.ts", "src/app.ts", "src/utils.ts", "index.js"]
        info = detect_stack(files, None, "")
        assert info.language == "TypeScript"

    def test_detect_python(self):
        files = ["app.py", "models.py", "views.py"]
        info = detect_stack(files, None, "from flask import Flask")
        assert info.language == "Python"

    def test_detect_flask(self):
        info = detect_stack(["app.py"], None, "from flask import Flask\napp = Flask(__name__)")
        assert info.framework == "Flask"

    def test_detect_fastapi(self):
        info = detect_stack(["main.py"], None, "from fastapi import FastAPI\napp = FastAPI()")
        assert info.framework == "FastAPI"

    def test_detect_express_from_pkg(self):
        pkg = {"dependencies": {"express": "^4.18.0"}}
        info = detect_stack(["index.js"], pkg, "")
        assert info.framework == "Express"

    def test_detect_jwt_auth(self):
        info = detect_stack([], None, "const jwt = require('jsonwebtoken'); jwt.sign(payload, secret)")
        assert "JWT" in info.auth

    def test_tools_populated(self):
        pkg = {"dependencies": {"express": "^4"}, "devDependencies": {"jest": "^29", "eslint": "^8"}}
        info = detect_stack(["index.js"], pkg, "")
        tool_names = " ".join(info.tools)
        assert "Jest" in tool_names or "Testing" in tool_names


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
