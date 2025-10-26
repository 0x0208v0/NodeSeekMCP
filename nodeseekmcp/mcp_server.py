from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Annotated

import pendulum
from fastmcp import FastMCP
from pydantic import BaseModel
from pydantic import Field

from nodeseekmcp.models import RssPostHistory
from nodeseekmcp.models import RssPostSource

mcp = FastMCP('NodeSeek MCP Server')

DEFAULT_TIMEZONE = 'Asia/Shanghai'


class BaseResponse(BaseModel):
    success: bool = Field(default=True, description='是否调用成功，成功为True，失败为False')
    error: str = Field(default='', description='错误信息，调用成功时为空')


class RssPostItem(BaseModel):
    source: RssPostSource = Field(description='帖子来源，nodeseek 或 deepflood')
    post_id: str = Field(description='帖子ID', examples=['419416'])
    url: str = Field(description='帖子URL', examples=['https://www.nodeseek.com/post-419416-1'])
    author: str = Field(description='帖子作者', examples=['0x0208v0'])
    title: str = Field(
        description='帖子标题',
        examples=['基于论坛nodeimage图床API，开源个Python版客户端，支持批量转存和备份，老人小孩很爱吃～'],
    )
    tag: str = Field(description='帖子标签', examples=['技术'])
    summary: str = Field(
        description='帖子摘要',
        examples=['如题，楼主作为灌水区UP主（不是， 基于论坛 nodeimage 图床 API，写了个 Python 版命令行工具...'],
    )
    published_at: datetime = Field(description='帖子发布时间', examples=['2025-08-10T16:49:46+00:00'])


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
    rss_posts: list[RssPostItem] = Field(default_factory=list, description='RSS帖子列表')
    total_count: int = Field(default=0, description='帖子总数')
    start_time: str = Field(
        default='',
        description=f'本次查询使用的开始时间，ISO 8601 格式，时区为 {DEFAULT_TIMEZONE}',
    )
    end_time: str = Field(
        default='',
        description=f'本次查询使用的结束时间，ISO 8601 格式，时区为 {DEFAULT_TIMEZONE}',
    )


@mcp.tool(
    name='get_forum_rss_posts',
    description=(
        f'查询论坛 RSS 帖子，可按来源（nodeseek 或 deepflood）、时间区间和分页过滤；'
        f'若未指定时间区间，则默认返回最近1小时内的帖子；时间均以 {DEFAULT_TIMEZONE} 时区计算'
    ),
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
            description=(
                '开始时间，格式为YYYY-MM-DD HH:mm:ss，需与 end_time 同时提供；'
                f'时间基于 {DEFAULT_TIMEZONE} 时区；留空时默认取最近1小时'
            ),
        ),
    ],
    end_time: Annotated[
        str,
        Field(
            default='',
            alias='end_time',
            description=(
                '结束时间，格式为YYYY-MM-DD HH:mm:ss，需与 start_time 同时提供；'
                f'时间基于 {DEFAULT_TIMEZONE} 时区；留空时默认取最近1小时'
            ),
        ),
    ],
    page: Annotated[int, Field(default=1, alias='page', description='第几页，默认为1，最小1')],
    page_size: Annotated[
        int,
        Field(
            default=50,
            alias='page_size',
            description='每页帖子数量，默认为50，最小1，最大200',
        ),
    ],
) -> GetRssPostHistoryResponse:
    timezone = pendulum.timezone(DEFAULT_TIMEZONE)
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
        start_time_str = start_time.strip()
        end_time_str = end_time.strip()
        if bool(start_time_str) ^ bool(end_time_str):
            return GetRssPostHistoryResponse(
                success=False,
                error='start_time 与 end_time 需要同时传递或同时留空',
            )
        if start_time_str and end_time_str:
            start_time_dt = pendulum.parse(start_time_str, tz=timezone)
            end_time_dt = pendulum.parse(end_time_str, tz=timezone)
        else:
            end_time_dt = pendulum.now(timezone)
            start_time_dt = end_time_dt - pendulum.duration(hours=1)
        if start_time_dt >= end_time_dt:
            return GetRssPostHistoryResponse(
                success=False,
                error='start_time 需要早于 end_time',
            )
        rss_posts, total_count = await RssPostHistory.get_list_by_page(
            source=source_enum,
            start_time=start_time_dt,
            end_time=end_time_dt,
            page=max(1, page),
            page_size=min(200, max(1, page_size)),
        )
        return GetRssPostHistoryResponse(
            rss_posts=[
                RssPostItem(
                    source=post.source,
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
            start_time=start_time_dt.to_iso8601_string(),
            end_time=end_time_dt.to_iso8601_string(),
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
