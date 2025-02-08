FROM python:3.10-slim AS build

RUN mkdir /app

ENV VIRTUAL_ENV=/home/pf/.local \
	PATH="/home/pf/.local/bin:$PATH" \
	INSTALL_MODE=poetry

WORKDIR /app

RUN pip install uv
COPY pyproject.toml  poetry.lock* ./

RUN uv venv $VIRTUAL_ENV && \
	uv pip install setuptools && \
	uv tool install poetry --python-preference only-managed

RUN if [ "${INSTALL_MODE}" != "uv" ]; then \
	uv pip install -r pyproject.toml --no-cache; \
	else \
	uvx poetry install --without dev --no-update; \
	fi


FROM python:3.10-slim

COPY --from=build "/home/pf/.local" "/home/pf/.local/"
ENV PATH="${PATH}:/home/pf/.local/bin"

RUN groupadd --gid 1000 pf \
	&& useradd --uid 1000 --gid 1000 -m pf \
	&& apt-get update

RUN mkdir -p /app /home/pf/.local/share /home/pf/.local/lib
RUN chown -R pf:pf /app
RUN chown -R pf:pf /home/pf/.local/share/ 2>/dev/null
RUN chown -R pf:pf /home/pf/.local/lib/ 2>/dev/null

USER pf
WORKDIR /app
COPY . .
EXPOSE 8501

ENTRYPOINT ["streamlit", "run", "./src/0_🏠_Home.py", "--server.port=8501", "--server.address=0.0.0.0"]
