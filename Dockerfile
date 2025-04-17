# 1. Base Image
FROM python:3.13-alpine@sha256:18159b2be11db91f84b8f8f655cd860f805dbd9e49a583ddaac8ab39bf4fe1a7 AS builder

# 2. Working Directory
WORKDIR /app

# 3. Copy Files
# Copy project definition and license first for better caching
COPY pyproject.toml LICENSE ./
# Copy the source code
COPY pm ./pm

# 4. Install Dependencies
# Install the package and its dependencies
RUN pip install . --no-cache-dir

# 5. Entrypoint
ENTRYPOINT ["pm"]