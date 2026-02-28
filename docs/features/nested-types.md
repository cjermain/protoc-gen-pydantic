---
icon: lucide/folder-tree
---

# Nested Types

Proto3 allows messages and enums to be defined inside other messages. `protoc-gen-pydantic`
generates these as true Python **nested classes**, so they are accessible via dotted attribute
access — exactly as you would expect from idiomatic Python.

## Nested messages

=== ":lucide-file-code: order.proto"

    ```proto
    message Order {
      message Item {
        string sku      = 1;
        int32  quantity = 2;
        double price    = 3;
      }

      string        order_id = 1;
      repeated Item items    = 2;
    }
    ```

=== ":simple-python: order_pydantic.py"

    ```python
    class Order(_ProtoModel):
        class Item(_ProtoModel):
            sku: "str" = _Field("")
            quantity: "int" = _Field(0)
            price: "float" = _Field(0.0)

        order_id: "str" = _Field("")
        items: "list[Order.Item]" = _Field(default_factory=list)
    ```

```python
# Usage
order = Order(
    order_id="ord-1",
    items=[
        Order.Item(sku="ABC", quantity=2, price=9.99),
        Order.Item(sku="XYZ", quantity=1, price=24.99),
    ],
)
print(order.items[0].sku)  # ABC
```

## Nested enums

Enums nested inside a message become nested classes of that message:

=== ":lucide-file-code: order.proto"

    ```proto
    message Order {
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

=== ":simple-python: order_pydantic.py"

    ```python
    class Order(_ProtoModel):
        class Status(str, _Enum):
            UNSPECIFIED = "UNSPECIFIED"
            PENDING = "PENDING"
            SHIPPED = "SHIPPED"
            DELIVERED = "DELIVERED"

        status_note: "str" = _Field("")
        status: "Order.Status | None" = _Field(None)
    ```

```python
# Usage
order = Order(status=Order.Status.PENDING)
print(order.status)  # 'PENDING'
```

## Deeply nested types

Nesting can go arbitrarily deep:

=== ":lucide-file-code: deep.proto"

    ```proto
    message Outer {
      message Inner {
        message Deepest {
          string value = 1;
        }
        Deepest data = 1;
      }
      Inner inner = 1;
    }
    ```

=== ":simple-python: deep_pydantic.py"

    ```python
    class Outer(_ProtoModel):
        class Inner(_ProtoModel):
            class Deepest(_ProtoModel):
                value: "str" = _Field("")

            data: "Outer.Inner.Deepest | None" = _Field(None)

        inner: "Outer.Inner | None" = _Field(None)
    ```

```python
obj = Outer(inner=Outer.Inner(data=Outer.Inner.Deepest(value="hello")))
print(obj.inner.data.value)  # hello
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
