from __future__ import annotations

import asyncio
import os
import sys

import click
import uvicorn

from nodeseekmcp import tasks
from nodeseekmcp.app import app
from nodeseekmcp.mcp_server import mcp


@click.group()
@click.pass_context
def cli(ctx):
    ctx.ensure_object(dict)

    click.echo(f'Current working directory: {os.getcwd()}')
    click.echo(f'Python executable: {sys.executable}')


@cli.command()
@click.option('--host', default='::', help='Host to bind to (default :: for IPv6, 0.0.0.0 for IPv4)')
@click.option('--port', default=80, type=int, help='Port to bind to (default: 80)')
@click.pass_context
def run_mcp(ctx, host, port):
    asyncio.run(mcp.run_http_async(
        transport='streamable-http', host=host, port=port, stateless_http=True,
    ))


@cli.command()
@click.option('--host', default='::', help='Host to bind to (default: :: for IPv6, 0.0.0.0 for IPv4)')
@click.option('--port', default=80, type=int, help='Port to bind to (default: 80)')
@click.pass_context
def run_app(ctx, host, port):
    uvicorn.run(app, host=host, port=port)


@cli.command()
@click.pass_context
def run_tasks(ctx):
    asyncio.run(tasks.main())


if __name__ == '__main__':
    # cli(['run-mcp'])

    # cli(['run-app'])

    cli(['run-tasks'])
