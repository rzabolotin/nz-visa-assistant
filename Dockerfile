FROM python:3.9

WORKDIR /app

# Install pipenv
RUN pip install --no-cache-dir pipenv

# Copy Pipfile and Pipfile.lock
COPY Pipfile Pipfile.lock ./

# Install dependencies using pipenv (excluding dev dependencies)
RUN pipenv install --deploy --ignore-pipfile

# Set the SENTENCE_TRANSFORMERS_MODEL as an argument
ARG SENTENCE_TRANSFORMERS_MODEL

# Download the SentenceTransformer model
RUN pipenv run python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('${SENTENCE_TRANSFORMERS_MODEL}')"

# Copy the indexer script
COPY scripts/indexer.py .

# Set the entrypoint to use pipenv
ENTRYPOINT ["pipenv", "run", "python", "indexer.py"]
