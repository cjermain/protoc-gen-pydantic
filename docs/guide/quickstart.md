# Quickstart

This guide walks you through generating and using your first Pydantic model from a `.proto` file.
It uses `buf` for code generation — [install it here](https://buf.build/docs/installation) if you haven't already.

## 1. Install the plugin

```sh
go install github.com/cjermain/protoc-gen-pydantic@latest
```

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

## 3. Configure buf

Create `buf.yaml` at your project root:

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
  - local: protoc-gen-pydantic
    opt:
      - paths=source_relative
    out: gen
inputs:
  - directory: proto
```

## 4. Generate

```sh
buf generate
```

This creates `gen/user_pydantic.py`.

## 5. Use the generated model

```python
from gen.user_pydantic import User

# Construct
user = User(name="Alice", age=30, active=True, role=User.Role.ADMIN)
print(user.name)  # Alice
print(user.role)  # Role.ADMIN

# Validate on construction — wrong types raise ValidationError
try:
    User(name=123)  # name must be str
except Exception as e:
    print(e)

# Serialize to dict / JSON
d = user.model_dump()
j = user.model_dump_json()

# ProtoJSON-style (omits zero/default values, uses camelCase)
print(user.to_proto_json())
# {"name":"Alice","age":30,"active":true,"role":"ADMIN"}
```

## What's next?

- Add [buf.validate constraints](../buf-validate) to enforce field rules at the proto level
- Learn about [well-known type mappings](../features/well-known-types) (Timestamp, Duration, …)
- Configure [plugin options](../options) to adjust naming conventions
