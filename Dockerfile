# ---- Stage 1: builder ----
# Installs dependencies into a virtualenv so the final image
# doesn't carry pip caches / build tools.
FROM python:3.11-slim AS builder

WORKDIR /build

RUN python -m venv /venv

ENV PATH="/venv/bin:$PATH"

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt


# stage2: runtime
FROM python:3.11-slim

WORKDIR  /code

# copy the pre-built virtualenv from the builder stage
COPY --from=builder /venv /venv
ENV PATH="/venv/bin:$PATH"

# copy only the app code (not tests, not .git, etc.)
COPY app ./app

# run as non-root user (good practice, small security win)
RUN useradd -m appuser
USER appuser

EXPOSE 8000

CMD [ "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000" ]