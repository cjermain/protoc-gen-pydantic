---
layout: home

hero:
  name: protoc-gen-pydantic
  text: Protobuf → Pydantic
  tagline: A protoc plugin that generates type-safe Pydantic v2 models from .proto files — with full proto3 support, nested classes, well-known types, and buf.validate integration.
  image:
    src: /protoc-gen-pydantic.png
    alt: protoc-gen-pydantic
  actions:
    - theme: brand
      text: Get Started
      link: /guide/installation
    - theme: alt
      text: View on GitHub
      link: https://github.com/cjermain/protoc-gen-pydantic

features:
  - icon: 🔷
    title: Full proto3 Support
    details: Scalars, optional, repeated, map, oneof — all proto3 field types generate correct Pydantic annotations with proper defaults.
  - icon: 🪆
    title: True Nested Classes
    details: Nested messages and enums become real Python nested classes (e.g. Order.Item, Order.Status) — no name mangling, no flat namespace.
  - icon: 🕐
    title: Well-Known Types
    details: Timestamp → datetime, Duration → timedelta, Struct → dict[str, Any], wrapper types → native Python — WKTs map to the most useful Python equivalents.
  - icon: ✅
    title: buf.validate Integration
    details: Field constraints from buf.validate translate automatically to Pydantic Field() kwargs — bounds, lengths, patterns, Literal[], AfterValidator, and more.
  - icon: 💬
    title: Comment Preservation
    details: Proto comments become Python docstrings and Field(description=...) values, keeping documentation close to the data.
  - icon: 🔗
    title: Cross-Package References
    details: Messages from other .proto packages are imported correctly. Only the top-level class is imported; nested types are resolved via dotted attribute access.
---

## Quick look

::: code-group

```proto [user.proto]
syntax = "proto3";

package example;

import "buf/validate/validate.proto";

// A user account.
message User {
  // Display name (1–50 characters).
  string name = 1 [
    (buf.validate.field).string.min_len = 1,
    (buf.validate.field).string.max_len = 50
  ];

  // Age in years.
  int32 age = 2 [(buf.validate.field).int32.gte = 0];

  // Contact email address.
  string email = 3 [(buf.validate.field).string.email = true];

  enum Role {
    ROLE_UNSPECIFIED = 0;
    ROLE_VIEWER = 1;
    ROLE_EDITOR = 2;
    ROLE_ADMIN = 3;
  }

  Role role = 4;
}
```

```python [user_pydantic.py (generated)]
from enum import Enum as _Enum
from typing import Annotated as _Annotated

from pydantic import (
    AfterValidator as _AfterValidator,
    BaseModel as _BaseModel,
    Field as _Field,
)

from ._proto_types import _validate_email


class User(_BaseModel):
    """A user account."""

    class Role(str, _Enum):
        UNSPECIFIED = "UNSPECIFIED"
        VIEWER = "VIEWER"
        EDITOR = "EDITOR"
        ADMIN = "ADMIN"

    # Display name (1–50 characters).
    name: "str" = _Field(
        "",
        min_length=1,
        max_length=50,
        description="Display name (1–50 characters).",
    )

    # Age in years.
    age: "int" = _Field(0, ge=0, description="Age in years.")

    # Contact email address.
    email: "_Annotated[str, _AfterValidator(_validate_email)]" = _Field(
        "",
        description="Contact email address.",
    )

    role: "User.Role | None" = _Field(None)
```

```python [usage.py]
from gen.user_pydantic import User

# Construct and validate
user = User(name="Alice", age=30, email="alice@example.com", role=User.Role.EDITOR)

# Serialize (ProtoJSON — omits zero values, uses camelCase aliases)
print(user.to_proto_json())
# {"name": "Alice", "age": 30, "email": "alice@example.com", "role": "EDITOR"}

# Validation errors are raised immediately
User(name="", age=-1)  # ValidationError: name too short, age below 0
```

:::
