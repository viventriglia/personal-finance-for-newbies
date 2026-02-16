FROM python:3.10-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml ./

RUN touch README.md

RUN uv pip install --system --no-cache -r pyproject.toml

COPY . .

EXPOSE 8501

ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["streamlit", "run", "src/0_🏠_Home.py", "--server.port=8501", "--server.address=0.0.0.0"]
