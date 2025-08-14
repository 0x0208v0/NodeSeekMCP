from __future__ import annotations

import logging
from datetime import datetime
from typing import Self

import arrow
import feedparser
import httpx
import pendulum
from pydantic import BaseModel
from pydantic import Field

DEFAULT_RSS_URL = 'https://rss.nodeseek.com'

DEFAULT_BASE_URL = 'https://www.nodeseek.com'

DEFAULT_BASE_API_URL = 'https://api.nodeseek.com'

DEFAULT_USER_AGENT = 'Mozilla/5.0 (X11; Linux i686; rv:95.0) Gecko/20100101 Firefox/95.0'

DEFAULT_TIMEOUT = 10.24

TAG_ZH_MAP = {
    'daily': '日常',
    'tech': '技术',
    'info': '情报',
    'review': '测评',
    'trade': '交易',
    'carpool': '拼车',
    'promotion': '推广',
    'dev': 'Dev',
    'photo-share': '贴图',
    'life': '生活',
    'expose': '曝光',
    'inside': '内版',
    'sandbox': '沙盒',
    'meaningless': '无意义',
}


class RssPost(BaseModel):
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


class NodeSeekClient:
    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        rss_url: str = DEFAULT_RSS_URL,
        base_api_url: str = DEFAULT_BASE_API_URL,
        user_agent: str = DEFAULT_USER_AGENT,
        timeout: float = DEFAULT_TIMEOUT,
        logger: logging.Logger | None = None,
    ):
        self.base_url = base_url.rstrip('/')
        self.rss_url = rss_url.rstrip('/')
        self.base_api_url = base_api_url.rstrip('/')

        self.user_agent = user_agent
        self.timeout = timeout
        self.logger = logger or logging.getLogger(__name__)

    @classmethod
    def from_env(cls, logger: logging.Logger | None = None) -> Self:
        return cls(logger=logger)

    def _get_headers(self) -> dict:
        return {
            'User-Agent': self.user_agent,
        }

    def _request(self, method: str, url: str, **kwargs) -> str:
        response = httpx.request(
            method=method,
            url=url,
            headers=self._get_headers(),
            timeout=self.timeout,
            **kwargs,
        )
        if response.status_code != 200:
            raise ValueError(f'Request failed status_code={response.status_code}, body={response.text}')
        return response.text

    def get_rss_posts(self) -> list[RssPost]:
        content = self._request('GET', self.rss_url)
        result = feedparser.parse(content)
        rss_posts = []
        for entry in result['entries']:
            rss_post = RssPost(
                post_id=entry['id'],
                url=entry['link'],
                author=entry['author'],
                title=entry['title'],
                tag=', '.join([tag['term'] for tag in entry['tags']]),
                summary=entry.get('summary', ''),  # 有权限的帖子可能没有summary
                published_at=(
                    arrow.get(
                        pendulum.parse(entry['published'], strict=False).strftime('%Y-%m-%d %H:%M:%S'),
                        tzinfo='GMT',
                    ).datetime
                ),
            )
            rss_posts.append(rss_post)
        return rss_posts

    def get_post_detail(self, post_id: str, page: int = 1) -> str:
        url = f'{self.base_url}/post-{post_id}-{page}'
        return self._request('GET', url)


if __name__ == '__main__':
    client = NodeSeekClient()
    rss_posts = client.get_rss_posts()
    print(rss_posts)
