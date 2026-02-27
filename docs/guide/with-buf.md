---
icon: lucide/package
---

# Using with buf

[buf](https://buf.build/) is the recommended way to use `protoc-gen-pydantic`. The
[quickstart](./quickstart) covers the basic setup. This page documents additional patterns
for buf users.

## Project layout

A typical project looks like:

```
myproject/
├── buf.yaml          # Buf module config
├── buf.gen.yaml      # Code generation config
├── proto/
│   └── api/v1/
│       └── user.proto
└── gen/
    └── api/v1/
        └── user_pydantic.py
```

## buf.yaml

```yaml
# buf.yaml
version: v2
modules:
  - path: proto
```

If you use `buf.validate`, add the BSR dependency:

```yaml
# buf.yaml
version: v2
modules:
  - path: proto
deps:
  - buf.build/bufbuild/protovalidate
```

Then run `buf dep update` to lock the dependency:

```sh
buf dep update
```

## buf.gen.yaml (with options)

Pass plugin options via the `opt` list:

```yaml
# buf.gen.yaml
version: v2
plugins:
  - local: go run github.com/cjermain/protoc-gen-pydantic@latest
    opt:
      - paths=source_relative
      - preserving_proto_field_name=false
      - auto_trim_enum_prefix=false
      - use_integers_for_enums=true
    out: gen
inputs:
  - directory: proto
```

See [Plugin Options](../options) for the full list.

## Watching for changes

buf does not have a built-in watch mode, but you can use a file watcher:

```sh
# With entr (brew install entr)
find proto -name '*.proto' | entr buf generate
```

## Multiple output directories

To generate for both default and non-default options in the same run:

```yaml
# buf.gen.yaml
version: v2
plugins:
  - local: go run github.com/cjermain/protoc-gen-pydantic@latest
    opt:
      - paths=source_relative
    out: gen
  - local: go run github.com/cjermain/protoc-gen-pydantic@latest
    opt:
      - paths=source_relative
      - use_integers_for_enums=true
    out: gen_integers
inputs:
  - directory: proto
```

## Verifying generated output

To check that generated files match what's committed to version control (useful in CI):

```sh
buf generate
git diff --exit-code gen/
```

Or use `buf generate --error-format json` for structured output.
