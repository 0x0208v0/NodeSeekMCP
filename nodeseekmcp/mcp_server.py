from __future__ import annotations

import asyncio
from typing import Annotated

import pendulum
from fastmcp import FastMCP
from pydantic import BaseModel
from pydantic import Field

from nodeseekmcp.models import RssPostHistory
from nodeseekmcp.models import RssPostSource
from nodeseekmcp.nodeseek import RssPost

mcp = FastMCP('NodeSeek MCP Server')


class BaseResponse(BaseModel):
    success: bool = Field(default=True, description='是否调用成功，成功为True，失败为False')
    error: str = Field(default='', description='错误信息，调用成功时为空')


class GetCurrentTimeResponse(BaseResponse):
    timezone: str = Field(default='UTC', description='使用的时区名称')
    current_time: str = Field(default='', description='当前时间，ISO 8601 格式')


@mcp.tool(
    name='get_current_time',
    description='获取当前时间，默认为Asia/Shanghai，可指定时区',
)
async def get_current_time(
    timezone: Annotated[
        str,
        Field(
            default='Asia/Shanghai',
            alias='timezone',
            description='时区名称，例如Asia/Shanghai，默认为Asia/Shanghai',
        ),
    ],
) -> GetCurrentTimeResponse:
    try:
        tz = pendulum.timezone(timezone)
    except Exception:
        return GetCurrentTimeResponse(
            success=False,
            error=f'Invalid timezone: {timezone}',
        )
    now = pendulum.now(tz).to_iso8601_string()
    return GetCurrentTimeResponse(
        timezone=tz.name,
        current_time=now,
    )


class GetRssPostHistoryResponse(BaseResponse):
    rss_posts: list[RssPost] = Field(default_factory=list, description='RSS帖子列表')
    total_count: int = Field(default=0, description='帖子总数')


@mcp.tool(
    name='get_forum_rss_posts',
    description='查询论坛 RSS 帖子，可按来源（nodeseek 或 deepflood）、时间区间和分页过滤',
)
async def get_rss_posts(
    source: Annotated[
        str,
        Field(
            default='',
            alias='source',
            description='数据来源，支持 nodeseek（NodeSeek）或 deepflood（DeepFlood），为空表示不限制',
        ),
    ],
    start_time: Annotated[
        str,
        Field(
            default='',
            alias='start_time',
            description='开始时间，格式为YYYY-MM-DD HH:mm:ss，为空则表示不限制开始时间',
        ),
    ],
    end_time: Annotated[
        str,
        Field(
            default='',
            alias='end_time',
            description='结束时间，格式为YYYY-MM-DD HH:mm:ss，为空则表示不限制结束时间',
        ),
    ],
    page: Annotated[int, Field(default=1, alias='page', description='第几页，默认为1，最小1')],
    page_size: Annotated[
        int,
        Field(
            default=20,
            alias='page_size',
            description='每页帖子数量，默认为20，最小1，最大100',
        ),
    ],
) -> GetRssPostHistoryResponse:
    timezone = 'Asia/Shanghai'
    try:
        normalized_source = source.strip().lower()
        if normalized_source:
            try:
                source_enum = RssPostSource(normalized_source)
            except ValueError:
                return GetRssPostHistoryResponse(
                    success=False,
                    error=f'Invalid source: {source}',
                )
        else:
            source_enum = None
        start_time = pendulum.parse(start_time, tz=timezone) if start_time else None
        end_time = pendulum.parse(end_time, tz=timezone) if end_time else None
        rss_posts, total_count = await RssPostHistory.get_list_by_page(
            source=source_enum,
            start_time=start_time,
            end_time=end_time,
            page=max(1, page),
            page_size=min(100, max(1, page_size)),
        )
        return GetRssPostHistoryResponse(
            rss_posts=[
                RssPost(
                    post_id=post.post_id,
                    url=post.url,
                    author=post.author,
                    title=post.title,
                    tag=post.tag,
                    summary=post.summary,
                    published_at=post.published_at,
                )
                for post in rss_posts
            ],
            total_count=total_count,
        )
    except Exception as e:
        return GetRssPostHistoryResponse(error=str(e), success=False)


if __name__ == '__main__':
    asyncio.run(
        mcp.run_http_async(
            transport='streamable-http',
            host='0.0.0.0',
            port=8866,
            stateless_http=True,
            log_level='debug',
        )
    )
