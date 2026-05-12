ARG FRONTEND_IMAGE=node:20-alpine
ARG RUNTIME_IMAGE=python:3.11-slim

FROM ${FRONTEND_IMAGE} AS frontend
WORKDIR /src
COPY frontend ./frontend
WORKDIR /src/frontend
RUN npm install --no-audit --no-fund
RUN npm run build

FROM ${RUNTIME_IMAGE}
WORKDIR /opt/spec-dep

RUN apt-get update && apt-get install -y --no-install-recommends antiword && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /opt/spec-dep/backend/requirements.txt
RUN pip install --no-cache-dir -r /opt/spec-dep/backend/requirements.txt

COPY backend/app /opt/spec-dep/backend/app
COPY executable /opt/spec-dep/executable
COPY work /opt/spec-dep/work
COPY --from=frontend /src/frontend/dist /opt/spec-dep/frontend/dist

RUN mkdir -p /opt/spec-dep/work/input/req \
  && mkdir -p /opt/spec-dep/work/input/dependencies \
  && mkdir -p /opt/spec-dep/work/output \
  && mkdir -p /opt/spec-dep/work/logs \
  && mkdir -p /opt/spec-dep/work/uploads

ENV PYTHONPATH=/opt/spec-dep/backend
ENV SPEC_DEP_CONFIG=/opt/spec-dep/executable/config.yaml
ENV SPEC_DEP_HOST=0.0.0.0
ENV SPEC_DEP_PORT=8766
ENV SPEC_DEP_WORK_DIR=/opt/spec-dep/work

EXPOSE 8766

ENTRYPOINT ["python", "-m", "app.cli.main"]
CMD ["web", "--host", "0.0.0.0", "--port", "8766"]
