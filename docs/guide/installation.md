# Installation

`protoc-gen-pydantic` is a single statically-linked binary with no runtime dependencies.
Choose the method that fits your workflow.

## Pre-built binaries

Download the latest release for your platform from
[GitHub Releases](https://github.com/cjermain/protoc-gen-pydantic/releases/latest).

Binaries are available for Linux, macOS, and Windows (amd64 and arm64).

After downloading, make the binary executable and place it somewhere on your `PATH`:

```sh
chmod +x protoc-gen-pydantic
mv protoc-gen-pydantic /usr/local/bin/
```

## Install with Go

If you have Go 1.21+ installed:

```sh
go install github.com/cjermain/protoc-gen-pydantic@latest
```

This places the binary in `$(go env GOPATH)/bin`. Make sure that directory is on your `PATH`.

## Build from source

```sh
git clone https://github.com/cjermain/protoc-gen-pydantic
cd protoc-gen-pydantic
go build -o protoc-gen-pydantic .
```

## Verify installation

```sh
protoc-gen-pydantic --version
```

## Prerequisites

To use the plugin you also need one of:

- **[protoc](https://github.com/protocolbuffers/protobuf/releases)** — the Protocol Buffers compiler
- **[buf](https://buf.build/docs/installation)** — recommended; handles dependency management and code generation configuration automatically

For most projects, `buf` is the simpler choice. See [Using with buf](./with-buf) for details.
