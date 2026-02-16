# Build the protoc-gen-pydantic binary
build:
    go build -o protoc-gen-pydantic .

# Generate Python models from test protos
generate: build
    rm -rf test/gen test/gen_options test/gen_pb2
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

# Run all linters
lint: lint-go lint-python

# Auto-fix Python lint issues
fix-python:
    cd test && uv run ruff check --fix tests/
    cd test && uv run ruff format tests/

# Verify generated files match committed versions
check-generated: generate
    git diff --exit-code test/gen/ test/gen_options/ test/gen_pb2/

# Remove build artifacts and generated files
clean:
    rm -f protoc-gen-pydantic
    rm -rf test/gen test/gen_options test/gen_pb2
