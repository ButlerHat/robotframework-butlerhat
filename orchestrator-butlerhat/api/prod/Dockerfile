FROM mcr.microsoft.com/devcontainers/miniconda:0-3 AS base

# Context must be in api/ folder
COPY conda.yaml ./conda.yaml
RUN umask 0002 && conda env create -n fastapi -f ./conda.yaml
RUN conda init bash

# Copy files
WORKDIR /workspaces/api
COPY data_types/ ./data_types/
COPY app.py ./app.py

RUN chown -R vscode:vscode /workspaces/api

# Set environment variables
ENV PATH /opt/conda/envs/fastapi/bin:$PATH
ENV PYTHONPATH /workspaces/api

# Entrypoint
EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]