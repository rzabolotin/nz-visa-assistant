FROM python:3.12

WORKDIR /app

RUN pip install --no-cache-dir pipenv

COPY ../Pipfile Pipfile.lock ./

RUN pipenv install --deploy --ignore-pipfile

ARG SENTENCE_TRANSFORMERS_MODEL

RUN pipenv run python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('${SENTENCE_TRANSFORMERS_MODEL}')"

COPY indexer.py .

COPY ../scripts/runner.sh /usr/local/bin/runner

RUN chmod +x /usr/local/bin/runner

ENTRYPOINT ["tail", "-f", "/dev/null"]
