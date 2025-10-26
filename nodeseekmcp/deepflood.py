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

DEFAULT_RSS_URL = 'https://feed.deepflood.com/topic.rss.xml'

DEFAULT_BASE_URL = 'https://www.deepflood.com'

DEFAULT_USER_AGENT = 'Mozilla/5.0 (X11; Linux i686; rv:95.0) Gecko/20100101 Firefox/95.0'

DEFAULT_TIMEOUT = 10.24

TAG_ZH_MAP = {
    'ai': '人工智能',
    'daily': '摸鱼闲聊',
    'emotion': '情感八卦',
    'stream': '影音图文',
    'sports': '运动赛事',
    'game': '游戏同好',
    'coupon': '羊毛福利',
    'promotion': '服务推广',
    'financial': '投资理财',
    'device': '电子设备',
    'feedback': '运营反馈',
    'inside': '内部版块',
    'sandbox': '沙盒测试',
}


class RssPost(BaseModel):
    post_id: str = Field(description='帖子ID', examples=['31742'])
    url: str = Field(description='帖子URL', examples=['https://www.deepflood.com/post-31742-1'])
    author: str = Field(description='帖子作者', examples=['AaronNS'])
    title: str = Field(
        description='帖子标题',
        examples=['Windows 10 停止支持推动全球换机潮 Mac 销量同比增长近15%'],
    )
    tag: str = Field(description='帖子标签', examples=['电子设备'])
    summary: str = Field(
        description='帖子摘要',
        examples=['MacRumors援引CounterpointResearch报告称，因微软即将终止Windows10支持...'],
    )
    published_at: datetime = Field(description='帖子发布时间', examples=['2025-10-26T14:23:33+00:00'])


class DeepFloodClient:
    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        rss_url: str = DEFAULT_RSS_URL,
        user_agent: str = DEFAULT_USER_AGENT,
        timeout: float = DEFAULT_TIMEOUT,
        logger: logging.Logger | None = None,
    ):
        self.base_url = base_url.rstrip('/')
        self.rss_url = rss_url.rstrip('/')

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
                summary=entry.get('summary', ''),
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
    client = DeepFloodClient()
    rss_posts = client.get_rss_posts()
    print(rss_posts)
