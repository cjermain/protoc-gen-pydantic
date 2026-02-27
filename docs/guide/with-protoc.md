---
icon: lucide/terminal
---

# Using with protoc

If you prefer to drive code generation directly with `protoc` rather than `buf`, this page covers the details.

## Basic usage

```sh
protoc --pydantic_out=./gen \
       --proto_path=./proto \
       ./proto/user.proto
```

This writes `gen/user_pydantic.py`.

## Specifying the binary explicitly

If `protoc-gen-pydantic` is not on your `PATH`, point `protoc` to it directly:

```sh
protoc --pydantic_out=./gen \
       --plugin=protoc-gen-pydantic=./protoc-gen-pydantic \
       --proto_path=./proto \
       ./proto/user.proto
```

## Plugin options

Options are passed with `--pydantic_opt=`:

```sh
protoc --pydantic_out=./gen \
       --pydantic_opt=preserving_proto_field_name=false \
       --pydantic_opt=auto_trim_enum_prefix=false \
       --proto_path=./proto \
       ./proto/user.proto
```

Multiple options can be combined in a single `--pydantic_opt`:

```sh
protoc --pydantic_out=./gen \
       --pydantic_opt=preserving_proto_field_name=false,use_integers_for_enums=true \
       --proto_path=./proto \
       ./proto/user.proto
```

See [Plugin Options](../options) for the full list.

## Generating multiple files

Pass all proto files on the command line:

```sh
protoc --pydantic_out=./gen \
       --proto_path=./proto \
       ./proto/user.proto \
       ./proto/order.proto \
       ./proto/product.proto
```

## Cross-package imports

When a message in one package references a message from another, both `--proto_path` entries
must be visible to `protoc`. The plugin resolves cross-package imports and emits the correct
relative Python imports automatically.

```sh
protoc --pydantic_out=./gen \
       --proto_path=./proto \
       --proto_path=./vendor/proto \
       ./proto/api/v1/order.proto
```

## Well-known types

For well-known types (`Timestamp`, `Duration`, `Struct`, etc.) you do not need to generate
their Python equivalents — the plugin maps them directly to native Python types. Make sure
`protoc` can find the WKT `.proto` files though:

```sh
# With protoc installed via apt / brew, WKTs are typically at:
INCLUDE=$(dirname $(which protoc))/../include

protoc --pydantic_out=./gen \
       --proto_path=./proto \
       --proto_path=$INCLUDE \
       ./proto/user.proto
```

## buf.validate with protoc

buf.validate requires the `validate.proto` file. You can vendor it or download it:

```sh
# Download validate.proto from GitHub
mkdir -p proto/buf/validate
curl -sSL https://raw.githubusercontent.com/bufbuild/protovalidate/main/proto/protovalidate/buf/validate/validate.proto \
     -o proto/buf/validate/validate.proto
```

Then include it in your `--proto_path`:

```sh
protoc --pydantic_out=./gen \
       --proto_path=./proto \
       ./proto/user.proto
```

> **Tip:** `buf` handles dependency management automatically. Consider [using buf](./with-buf)
> if you use buf.validate or need to import external packages.
