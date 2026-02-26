# Using with buf

[buf](https://buf.build/) is the recommended way to use `protoc-gen-pydantic`. It handles
dependency management, linting, and code generation configuration in a declarative way.

## Installation

```sh
# macOS / Linux
brew install bufbuild/buf/buf

# or download directly
curl -sSL https://github.com/bufbuild/buf/releases/latest/download/buf-Linux-x86_64 -o buf
chmod +x buf && mv buf /usr/local/bin/
```

See the [buf installation docs](https://buf.build/docs/installation) for all platforms.

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

## buf.gen.yaml (minimal)

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

`paths=source_relative` ensures output mirrors your proto directory structure.

## buf.gen.yaml (with options)

```yaml
# buf.gen.yaml
version: v2
plugins:
  - local: protoc-gen-pydantic
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

## Generating

```sh
buf generate
```

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
  - local: protoc-gen-pydantic
    opt:
      - paths=source_relative
    out: gen
  - local: protoc-gen-pydantic
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
