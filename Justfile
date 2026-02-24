set shell := ["bash", "-euo", "pipefail", "-c"]

# Check required tools and install pre-commit hooks
init:
    #!/usr/bin/env bash
    set -euo pipefail
    missing=()
    for cmd in go buf protoc uv golangci-lint pre-commit; do
        if ! command -v "$cmd" &>/dev/null; then
            missing+=("$cmd")
        fi
    done
    if [ ${#missing[@]} -ne 0 ]; then
        echo "Missing required tools: ${missing[*]}"
        exit 1
    fi
    echo "go:             $(go version | awk '{print $3}')"
    echo "buf:            $(buf --version)"
    echo "protoc:         $(protoc --version | awk '{print $2}')"
    echo "uv:             $(uv --version | awk '{print $2}')"
    echo "golangci-lint:  $(golangci-lint --version | awk '{print $4}')"
    echo "pre-commit:     $(pre-commit --version | awk '{print $2}')"
    cd test && uv sync
    pre-commit install
    echo "Ready to go."

# Build the protoc-gen-pydantic binary
build:
    go build -o protoc-gen-pydantic .

# Generate Python models from test protos
generate: build
    rm -rf test/gen test/gen_options
    buf generate

# Run Python tests
test:
    cd test && uv run pytest -v

# Full rebuild + generate + test cycle
dev: generate test

# Run Go linter
lint-go:
    golangci-lint run

# Run Python linters on test suite
lint-python:
    cd test && uv run ruff check tests/
    cd test && uv run ruff format --check tests/

# Run type checker on test suite code
lint-types:
    cd test && uv run ty check tests/

# Run all linters
lint: lint-go lint-python lint-types

# Auto-fix Python lint issues
fix-python:
    cd test && uv run ruff check --fix tests/
    cd test && uv run ruff format tests/

# Verify generated files match committed versions
check-generated: generate
    git diff --exit-code test/gen/ test/gen_options/

# Build a coverage-instrumented binary
build-cover:
    go build -cover -o protoc-gen-pydantic-cov .

# Generate Python models using the coverage-instrumented binary
generate-cover: build-cover
    rm -rf test/gen test/gen_options
    mkdir -p covdata
    rm -f covdata/*
    GOCOVERDIR="$(pwd)/covdata" buf generate --template buf.gen-cov.yaml

# Collect Go coverage: generate with instrumented binary and emit coverage.out
coverage: generate-cover
    go tool covdata textfmt -i=covdata -o coverage.out
    go tool cover -func coverage.out

# Remove build artifacts and generated files
clean:
    rm -f protoc-gen-pydantic protoc-gen-pydantic-cov coverage.out
    rm -rf test/gen test/gen_options covdata
