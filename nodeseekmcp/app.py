from __future__ import annotations

from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from nodeseekmcp import __version__
from nodeseekmcp.mcp_server import mcp

mcp_app = mcp.http_app(path='/nodeseek', transport='streamable-http', stateless_http=True)

app = FastAPI(
    title='server',
    version=__version__,
    lifespan=mcp_app.lifespan,
)

templates = Jinja2Templates(directory=Path(__file__).parent / 'templates')

app.mount('/mcp', mcp_app)


@app.get('/health_check')
async def health_check():
    return 'ok'


@app.get('/', response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request, 'index.html')


if __name__ == '__main__':
    uvicorn.run("nodeseekmcp.app:app", host='0.0.0.0', port=8866, log_level='debug', workers=2)
