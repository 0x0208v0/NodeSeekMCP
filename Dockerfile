#FROM python:3.13-slim-bookworm AS builder
FROM python:3.13-alpine AS builder

WORKDIR /opt
COPY ./nodeseekmcp /opt/nodeseekmcp
COPY ./pyproject.toml /opt
RUN  python -m pip install --upgrade build  && python -m build


FROM python:3.13-alpine

WORKDIR /opt/nodeseekmcp
COPY --from=builder /opt/dist /opt/nodeseekmcp/dist
RUN python -m pip install --no-cache-dir /opt/nodeseekmcp/dist/*.whl && rm -rf /opt/nodeseekmcp/dist

COPY ./supervisor.conf /opt/nodeseekmcp
COPY ./gunicorn.conf.py /opt/nodeseekmcp

EXPOSE 8866

CMD ["supervisord", "-c", "supervisor.conf", "-n"]


# docker build -f Dockerfile -t nodeseekmcp .

# 本机运行
# docker run --name nodeseekmcp --rm -p 8086:8866 -it nodeseekmcp sh

# IPv4
# docker run --name nodeseekmcp --rm -p 0.0.0.0:80:8866 -it nodeseekmcp

# IPv6
# docker run --name nodeseekmcp --rm -p :::80:8866 -it nodeseekmcp
