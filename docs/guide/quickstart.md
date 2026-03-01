---
icon: lucide/zap
---

# Quickstart

This guide walks you through generating and using your first Pydantic model from a `.proto` file.
It uses `buf` for code generation — [install it here](https://buf.build/docs/installation) if you haven't already.

## 1. Set up the project

Your project will have this layout:

```
myproject/
├── pyproject.toml
├── buf.yaml
├── buf.gen.yaml
├── proto/
│   └── user.proto
└── gen/
    └── user_pydantic.py    ← generated
```

Create `pyproject.toml`:

```toml
[project]
name = "myproject"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
    "pydantic>=2.9",
]

[build-system]
requires = ["uv_build"]
build-backend = "uv_build"

[tool.uv.build-backend]
module-root = "gen"
namespace = true
```

`module-root = "gen"` tells uv that generated files live in `gen/`, and `namespace = true` makes
them importable as a [namespace package](https://peps.python.org/pep-0420/) — no `__init__.py`
required.

Create `buf.yaml`:

```yaml
# buf.yaml
version: v2
modules:
  - path: proto
```

Create `buf.gen.yaml`:

```yaml
# buf.gen.yaml
version: v2
plugins:
  - local: go run github.com/cjermain/protoc-gen-pydantic@latest
    opt:
      - paths=source_relative
    out: gen
inputs:
  - directory: proto
```

This runs the plugin via `go run` — no separate install step needed. You need Go 1.21+ on your `PATH`.

## 2. Write a proto file

Create `proto/user.proto`:

```proto
syntax = "proto3";

package example;

option go_package = "example/api";

// A user account.
message User {
  string name = 1;
  int32  age  = 2;
  bool   active = 3;

  enum Role {
    ROLE_UNSPECIFIED = 0;
    ROLE_VIEWER      = 1;
    ROLE_ADMIN       = 2;
  }

  Role role = 4;
}
```

## 3. Generate

Install dependencies and generate the Pydantic model:

```sh
uv sync
buf generate
```

This creates `gen/user_pydantic.py`.

## 4. Use the generated model

```sh
uv run python
```

Because `pyproject.toml` sets `module-root = "gen"`, uv treats `gen/` as the package root —
so `user_pydantic` is importable directly without a `gen.` prefix.

```python
>>> from user_pydantic import User
>>> user = User(name="Alice", age=30, active=True, role=User.Role.ADMIN)
>>> user.name
'Alice'
>>> user.role
'ADMIN'
>>> user.to_proto_json()
'{"name":"Alice","age":30,"active":true,"role":"ADMIN"}'
>>> User(name=123)  # wrong type raises immediately
ValidationError: 1 validation error for User
name
  Input should be a valid string [type=string_type, ...]
```

`to_proto_json()` follows ProtoJSON conventions: it omits fields at their default (zero) values
and uses the original proto field names. See [Generated Model API](../features/generated-model-api.md)
for the full serialization interface.

## What's next?

- Explore [advanced buf patterns](./with-buf.md) — multiple outputs, watching for changes, CI verification
- Add [buf.validate constraints](../buf-validate.md) to enforce field rules at the proto level
- Learn about [well-known type mappings](../features/well-known-types.md) (Timestamp, Duration, …)
- Configure [plugin options](../options.md) to adjust naming conventions
