from __future__ import annotations

from contextlib import AsyncExitStack
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from nodeseekmcp import __version__
from nodeseekmcp.mcp_server import mcp
from nodeseekmcp.models import engine

templates = Jinja2Templates(directory=Path(__file__).parent / 'templates')

http_mcp_app = mcp.http_app(path='/mcp', transport='http', stateless_http=True)

streamable_http_mcp_app = mcp.http_app(path='/mcp', transport='streamable-http', stateless_http=True)

sse_mcp_app = mcp.http_app(path='/mcp', transport='sse', stateless_http=True)

mcp_http_apps = (
    http_mcp_app,
    streamable_http_mcp_app,
    sse_mcp_app,
)


@asynccontextmanager
async def combined_lifespan(_: FastAPI):
    """
    管理所有子应用的生命周期
    注意：FastAPI 挂载的子应用会自动调用其 lifespan，但为了确保资源正确初始化和清理，
    这里显式管理所有子应用的 lifespan context
    """
    async with AsyncExitStack() as stack:
        for mounted_app in mcp_http_apps:
            # 正确的方式：通过 router.lifespan_context 获取 lifespan
            if hasattr(mounted_app, 'router') and hasattr(mounted_app.router, 'lifespan_context'):
                ctx = mounted_app.router.lifespan_context(mounted_app)
                await stack.enter_async_context(ctx)
        yield
        # 清理数据库引擎连接池
        await engine.dispose()


app = FastAPI(
    title='server',
    version=__version__,
    lifespan=combined_lifespan,
)

# 修复路径冲突：每个应用挂载到不同的路径
# 这样三个传输协议都可以正常访问
app.mount('/http', http_mcp_app)

app.mount('/streamable-http', streamable_http_mcp_app)

app.mount('/sse', sse_mcp_app)


@app.get('/health_check')
async def health_check():
    return 'ok'


@app.get('/', response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request, 'index.html')


if __name__ == '__main__':
    uvicorn.run(
        'nodeseekmcp.app:app',
        host='0.0.0.0',
        port=8866,
        log_level='debug',
        workers=1,
        timeout_graceful_shutdown=0,
    )
