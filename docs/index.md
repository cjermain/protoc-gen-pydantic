---
hide:
  - navigation
  - toc
---

<div align="center" markdown>

![protoc-gen-pydantic](assets/protoc-gen-pydantic.png){ width="280" }

# protoc-gen-pydantic

**Protobuf → Pydantic** · A protoc plugin that generates type-safe Pydantic v2
models from `.proto` files — with full proto3 support, nested classes,
well-known types, and buf.validate integration.

[Get Started](guide/installation.md){ .md-button .md-button--primary }
[View on GitHub](https://github.com/cjermain/protoc-gen-pydantic){ .md-button }

</div>

---

<div class="grid cards" markdown>

- 🔷 **Full proto3 Support**

    Scalars, optional, repeated, map, oneof — all field types generate correct
    Pydantic annotations with proper defaults.

- 🪆 **True Nested Classes**

    Nested messages and enums become real Python nested classes
    (e.g. `Order.Item`, `Order.Status`) — no name mangling, no flat namespace.

- 🕐 **Well-Known Types**

    `Timestamp` → `datetime`, `Duration` → `timedelta`, `Struct` → `dict[str, Any]`,
    wrapper types → native Python equivalents.

- ✅ **buf.validate Integration**

    Field constraints translate automatically to Pydantic `Field()` kwargs —
    bounds, lengths, patterns, `Literal[]`, `AfterValidator`, and more.

- 💬 **Comment Preservation**

    Proto comments become Python docstrings and `Field(description=...)` values,
    keeping documentation close to the data.

- 🔗 **Cross-Package References**

    Messages from other `.proto` packages are imported correctly. Nested types
    are resolved via dotted attribute access.

</div>

## Quick look

=== "user.proto"

    ```proto
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

=== "user_pydantic.py (generated)"

    ```python
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

=== "usage.py"

    ```python
    from gen.user_pydantic import User

    # Construct and validate
    user = User(name="Alice", age=30, email="alice@example.com", role=User.Role.EDITOR)

    # Serialize (ProtoJSON — omits zero values, uses camelCase aliases)
    print(user.to_proto_json())
    # {"name": "Alice", "age": 30, "email": "alice@example.com", "role": "EDITOR"}

    # Validation errors are raised immediately
    User(name="", age=-1)  # ValidationError: name too short, age below 0
    ```
