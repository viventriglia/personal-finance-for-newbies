FROM python:3.10-slim

WORKDIR /app

COPY . . 

RUN pip3 install poetry==v1.5.1

RUN poetry install --no-root

COPY creds/creds_sample.json /app/creds/creds.json

EXPOSE 8501

ENTRYPOINT ["poetry", "run", "streamlit", "run", "./src/0_🏠_Home.py", "--server.port=8501", "--server.address=0.0.0.0"]