# Comments & Descriptions

Proto file comments are preserved in the generated Python output in two ways:

1. **Message / enum comments** → Python docstrings
2. **Field comments** → inline `# comment` + `Field(description=...)`

## Message docstrings

Leading comments on a message become its Python docstring:

::: code-group

```proto [comments.proto]
// A user account in the system.
// Represents a single registered user.
message User {
  string name = 1;
}
```

```python [comments_pydantic.py]
class User(_ProtoModel):
    """
    A user account in the system.
    Represents a single registered user.
    """

    name: "str" = _Field("")
```

:::

## Field descriptions

Field comments become both an inline Python comment and a `description=` argument on `_Field()`:

::: code-group

```proto [comments.proto]
message User {
  // The user's display name.
  string name = 1;

  // Age in full years.
  int32 age = 2;
}
```

```python [comments_pydantic.py]
class User(_ProtoModel):
    # The user's display name.
    name: "str" = _Field("", description="The user's display name.")

    # Age in full years.
    age: "int" = _Field(0, description="Age in full years.")
```

:::

The `description=` value is visible to downstream tools that consume Pydantic's JSON Schema,
such as FastAPI / Swagger UI.

## Disabling field descriptions

If you want to omit the `description=` argument (e.g. to keep generated files smaller),
use `disable_field_description=true`:

```yaml
# buf.gen.yaml
plugins:
  - local: protoc-gen-pydantic
    opt:
      - paths=source_relative
      - disable_field_description=true
    out: gen
```

With this option the inline comment is still emitted, but `Field()` has no `description=`:

```python
class User(_ProtoModel):
    # The user's display name.
    name: "str" = _Field("")
```

## Enum docstrings

Leading comments on enum types and values are preserved the same way:

::: code-group

```proto [comments.proto]
// The current lifecycle status of a task.
enum TaskStatus {
  // Not yet assigned a status.
  TASK_STATUS_UNSPECIFIED = 0;
  // Task is ready to be worked on.
  TASK_STATUS_OPEN = 1;
  // Task has been completed.
  TASK_STATUS_DONE = 2;
}
```

```python [comments_pydantic.py]
class TaskStatus(str, _Enum):
    """
    The current lifecycle status of a task.
    """

    # Not yet assigned a status.
    UNSPECIFIED = "UNSPECIFIED"

    # Task is ready to be worked on.
    OPEN = "OPEN"

    # Task has been completed.
    DONE = "DONE"
```

:::
