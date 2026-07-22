---
icon: lucide/table
---

# Field Types

`protoc-gen-pydantic` supports all standard proto3 field types and generates correct Pydantic
annotations with appropriate defaults.

```python exec="on" session="field-types"
import inspect
import os
import sys

sys.path.insert(0, os.path.join(os.environ["MKDOCS_CONFIG_DIR"], "test", "gen"))

from api.v1.field_types_pydantic import (
    Address,
    Config,
    Order,
    Payment,
    Person,
    SearchRequest,
    TaggedItem,
    Task,
)
```

## Scalar fields

All proto3 scalar types map to native Python types:

| Proto type | Python type | Default |
|---|---|---|
| `string` | `str` | `""` |
| `bool` | `bool` | `False` |
| `int32`, `sint32`, `sfixed32` | `int` | `0` |
| `uint32`, `fixed32` | `int` | `0` |
| `int64`, `sint64`, `sfixed64` | `ProtoInt64` | `0` |
| `uint64`, `fixed64` | `ProtoUInt64` | `0` |
| `float` | `float` | `0.0` |
| `double` | `float` | `0.0` |
| `bytes` | `bytes` | `b""` |

`ProtoInt64` and `ProtoUInt64` are type aliases for `int` that carry JSON serialization semantics
(proto3 encodes 64-bit integers as strings in JSON).

=== ":lucide-file-code: field_types.proto"

    ```proto
    message Person {
      string name   = 1;
      int32  age    = 2;
      bool   active = 3;
      double score  = 4;
      bytes  avatar = 5;
    }
    ```

=== ":simple-python: field_types_pydantic.py"

    ```python exec="on" session="field-types"
    print(f"```python\n{inspect.getsource(Person).rstrip()}\n```")
    ```

```python exec="on" session="field-types"
person = Person(name="Alice", age=30)
assert person.name == "Alice"
assert person.age == 30
assert person.active is False
assert person.score == 0.0
assert person.avatar == b""
assert person.model_dump_json() == '{"name":"Alice","age":30}'
```

## Optional fields

`optional` fields use `T | None` with a default of `None`, distinguishing "field not set"
from the zero value:

=== ":lucide-file-code: field_types.proto"

    ```proto
    message SearchRequest {
      optional string query           = 1;
      optional int32  page_size       = 2;
      optional bool   include_deleted = 3;
    }
    ```

=== ":simple-python: field_types_pydantic.py"

    ```python exec="on" session="field-types"
    print(f"```python\n{inspect.getsource(SearchRequest).rstrip()}\n```")
    ```

```python exec="on" session="field-types"
req = SearchRequest()
assert req.query is None
assert req.page_size is None
assert req.include_deleted is None
assert req.model_dump_json() == "{}"
req2 = SearchRequest(query="hello", page_size=10)
assert req2.model_dump_json() == '{"query":"hello","pageSize":10}'
```

## Repeated fields

`repeated` fields generate `list[T]` with `default_factory=list`:

=== ":lucide-file-code: field_types.proto"

    ```proto
    message TaggedItem {
      string          name   = 1;
      repeated string tags   = 2;
      repeated int32  scores = 3;
    }
    ```

=== ":simple-python: field_types_pydantic.py"

    ```python exec="on" session="field-types"
    print(f"```python\n{inspect.getsource(TaggedItem).rstrip()}\n```")
    ```

```python exec="on" session="field-types"
item = TaggedItem(name="widget", tags=["a", "b"], scores=[1, 2, 3])
assert item.tags == ["a", "b"]
assert item.scores == [1, 2, 3]
assert TaggedItem().tags == []
assert item.model_dump_json() == '{"name":"widget","tags":["a","b"],"scores":[1,2,3]}'
```

## Map fields

`map<K, V>` fields generate `dict[K, V]` with `default_factory=dict`:

=== ":lucide-file-code: field_types.proto"

    ```proto
    message Config {
      map<string, string> labels   = 1;
      map<string, int32>  counters = 2;
    }
    ```

=== ":simple-python: field_types_pydantic.py"

    ```python exec="on" session="field-types"
    print(f"```python\n{inspect.getsource(Config).rstrip()}\n```")
    ```

```python exec="on" session="field-types"
cfg = Config(labels={"env": "prod"}, counters={"hits": 42})
assert cfg.labels == {"env": "prod"}
assert cfg.counters == {"hits": 42}
assert Config().labels == {}
assert cfg.model_dump_json() == '{"labels":{"env":"prod"},"counters":{"hits":42}}'
```

## Oneof fields

`oneof` groups generate one field per variant, all typed as `T | None = None`.
A `@model_validator` is generated for each group and raises `ValidationError`
if more than one field is set, enforcing proto3's at-most-one semantics at
runtime.

=== ":lucide-file-code: field_types.proto"

    ```proto
    message Payment {
      oneof method {
        string credit_card = 1;
        string paypal      = 2;
        string bank_iban   = 3;
      }
    }
    ```

=== ":simple-python: field_types_pydantic.py"

    ```python exec="on" session="field-types"
    print(f"```python\n{inspect.getsource(Payment).rstrip()}\n```")
    ```

```python exec="on" session="field-types"
from pydantic import ValidationError

pay = Payment(credit_card="4242424242424242")
assert pay.credit_card == "4242424242424242"
assert pay.paypal is None
assert pay.bank_iban is None
assert pay.model_dump_json() == '{"creditCard":"4242424242424242"}'
try:
    Payment(credit_card="4242424242424242", paypal="me@paypal.com")  # raises
except ValidationError:
    pass
```

## Message fields

Message-typed fields default to `None` (not an empty sub-message):

=== ":lucide-file-code: field_types.proto"

    ```proto
    message Address {
      string street = 1;
      string city   = 2;
    }

    message Order {
      string  order_id = 1;
      Address address  = 2;
    }
    ```

=== ":simple-python: field_types_pydantic.py"

    ```python exec="on" session="field-types"
    addr_src = inspect.getsource(Address).rstrip()
    order_src = inspect.getsource(Order).rstrip()
    print(f"```python\n{addr_src}\n\n\n{order_src}\n```")
    ```

```python exec="on" session="field-types"
order = Order(order_id="ord-1", address=Address(street="Main St", city="Springfield"))
assert order.address.city == "Springfield"
assert Order().address is None
assert (
    order.model_dump_json()
    == '{"orderId":"ord-1","address":{"street":"Main St","city":"Springfield"}}'
)
```

## Enum fields

Enum-typed fields also default to `None`. See the [Enums page](./enums.md) for full details.

=== ":lucide-file-code: field_types.proto"

    ```proto
    message Task {
      string status_label = 1;
      Status status       = 2;

      enum Status {
        STATUS_UNSPECIFIED = 0;
        STATUS_OPEN        = 1;
        STATUS_DONE        = 2;
      }
    }
    ```

=== ":simple-python: field_types_pydantic.py"

    ```python exec="on" session="field-types"
    print(f"```python\n{inspect.getsource(Task).rstrip()}\n```")
    ```

```python exec="on" session="field-types"
task = Task(status=Task.Status.OPEN)
assert task.status == "OPEN"
assert Task().status is None
assert task.model_dump_json() == '{"status":"OPEN"}'
```
