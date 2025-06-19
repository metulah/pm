# 1. Base Image
FROM python:3.13-alpine@sha256:9b4929a72599b6c6389ece4ecbf415fd1355129f22bb92bb137eea098f05e975 AS builder

# 2. Working Directory
WORKDIR /app

# 3. Copy Files
# Copy project definition and license first for better caching
COPY pyproject.toml LICENSE README.md ./

# Copy the source code
COPY src ./pm

# 4. Install Dependencies
# Install the package and its dependencies
RUN pip install . --no-cache-dir

# 5. Entrypoint
ENTRYPOINT ["pm"]
