---
icon: lucide/message-square-text
---

# Comments & Descriptions

Proto file comments are preserved in the generated Python output in two ways:

1. **Message / enum comments** → Python docstrings
2. **Field comments** → inline `# comment` + `Field(description=...)`

```python exec="on" session="comments"
import inspect
import os
import sys

sys.path.insert(0, os.path.join(os.environ["MKDOCS_CONFIG_DIR"], "test", "gen"))

from api.v1.doc_comments_pydantic import TaskStatus, User
```

## Message docstrings

Leading comments on a message become its Python docstring:

=== ":lucide-file-code: doc_comments.proto"

    ```proto
    // A user account in the system.
    // Represents a single registered user.
    message User {
      // The user's display name.
      string name = 1;

      // Age in full years.
      int32 age = 2;
    }
    ```

=== ":simple-python: doc_comments_pydantic.py"

    ```python exec="on" session="comments"
    print(f"```python\n{inspect.getsource(User).rstrip()}\n```")
    ```

```python exec="on" session="comments"
user = User(name="Alice", age=30)
assert user.name == "Alice"
assert User.__doc__ is not None
assert "A user account in the system." in User.__doc__
```

## Field descriptions

Field comments become both an inline Python comment and a `description=` argument on `_Field()`:

=== ":lucide-file-code: doc_comments.proto"

    ```proto
    message User {
      // The user's display name.
      string name = 1;

      // Age in full years.
      int32 age = 2;
    }
    ```

=== ":simple-python: doc_comments_pydantic.py"

    ```python exec="on" session="comments"
    print(f"```python\n{inspect.getsource(User).rstrip()}\n```")
    ```

```python exec="on" session="comments"
import json as _json

schema = User.model_json_schema()
assert schema["properties"]["name"]["description"] == "The user's display name."
assert schema["properties"]["age"]["description"] == "Age in full years."
```

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
    name: "str" = _Field(default="")
```

## Enum docstrings

Leading comments on enum types and values are preserved the same way:

=== ":lucide-file-code: doc_comments.proto"

    ```proto
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

=== ":simple-python: doc_comments_pydantic.py"

    ```python exec="on" session="comments"
    print(f"```python\n{inspect.getsource(TaskStatus).rstrip()}\n```")
    ```

```python exec="on" session="comments"
assert "The current lifecycle status of a task." in TaskStatus.__doc__
assert TaskStatus.OPEN == "OPEN"
```
