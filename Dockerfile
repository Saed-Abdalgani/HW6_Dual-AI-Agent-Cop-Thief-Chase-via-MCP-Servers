FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    CONFIG_PATH=config/config.cloud.yaml

COPY pyproject.toml uv.lock README.md ./
COPY config ./config
COPY src ./src

RUN uv sync --frozen --no-dev

CMD ["uv", "run", "cop-thief-mcp"]
