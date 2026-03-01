---
icon: lucide/folder-tree
---

# Nested Types

Proto3 allows messages and enums to be defined inside other messages. `protoc-gen-pydantic`
generates these as true Python **nested classes**, so they are accessible via dotted attribute
access — exactly as you would expect from idiomatic Python.

```python exec="on" session="nested-types"
import inspect
import os
import sys

sys.path.insert(0, os.path.join(os.environ["MKDOCS_CONFIG_DIR"], "test", "gen"))

from api.v1.nested_types_pydantic import Shipment
from api.v1.comments_pydantic import Outer
```

## Nested messages

=== ":lucide-file-code: nested_types.proto"

    ```proto
    message Shipment {
      message Item {
        string sku      = 1;
        int32  quantity = 2;
        double price    = 3;
      }

      string        order_id = 1;
      repeated Item items    = 2;
    }
    ```

=== ":simple-python: nested_types_pydantic.py"

    ```python exec="on" session="nested-types"
    print(f"```python\n{inspect.getsource(Shipment).rstrip()}\n```")
    ```

```python
# Usage
shipment = Shipment(
    order_id="shp-1",
    items=[
        Shipment.Item(sku="ABC", quantity=2, price=9.99),
        Shipment.Item(sku="XYZ", quantity=1, price=24.99),
    ],
)
print(shipment.items[0].sku)  # ABC
```

```python exec="on" session="nested-types"
shipment = Shipment(
    order_id="shp-1",
    items=[
        Shipment.Item(sku="ABC", quantity=2, price=9.99),
        Shipment.Item(sku="XYZ", quantity=1, price=24.99),
    ],
)
assert shipment.items[0].sku == "ABC"
assert shipment.items[1].price == 24.99
```

## Nested enums

Enums nested inside a message become nested classes of that message:

=== ":lucide-file-code: nested_types.proto"

    ```proto
    message Shipment {
      enum Status {
        STATUS_UNSPECIFIED = 0;
        STATUS_PENDING     = 1;
        STATUS_SHIPPED     = 2;
        STATUS_DELIVERED   = 3;
      }

      string status_note = 1;
      Status status      = 2;
    }
    ```

=== ":simple-python: nested_types_pydantic.py"

    ```python exec="on" session="nested-types"
    print(f"```python\n{inspect.getsource(Shipment).rstrip()}\n```")
    ```

```python
# Usage
shipment = Shipment(status=Shipment.Status.PENDING)
print(shipment.status)  # 'PENDING'
```

```python exec="on" session="nested-types"
shipment = Shipment(status=Shipment.Status.PENDING)
assert shipment.status == "PENDING"
assert Shipment().status is None
```

## Deeply nested types

Nesting can go arbitrarily deep:

=== ":lucide-file-code: comments.proto"

    ```proto
    message Outer {
      message Inner {
        message Deepest {
          string deepest_field = 1;
        }
      }
      Inner inner = 1;
    }
    ```

=== ":simple-python: comments_pydantic.py"

    ```python exec="on" session="nested-types"
    print(f"```python\n{inspect.getsource(Outer).rstrip()}\n```")
    ```

```python exec="on" session="nested-types"
# Outer.Inner.Deepest is accessible via dotted attribute access
deepest = Outer.Inner.Deepest(deepest_field="hello")
assert deepest.deepest_field == "hello"
```

## Cross-file references

When a message in one file references a nested type from another file, the import uses only the
**top-level class name**. The nested path is resolved via dotted attribute access at runtime:

```python
# gen/collections_pydantic.py
from .scalars_pydantic import Scalars


class Collections(_ProtoModel):
    nested_enum_repeated: "list[Scalars.NestedEnum]" = _Field(default_factory=list)
```

This means you only import `Scalars`, not `Scalars.NestedEnum` directly — Python resolves the
dotted access automatically.
