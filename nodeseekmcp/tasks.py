# https://github.com/agronholm/apscheduler/blob/3.x/examples/schedulers/asyncio_.py


from __future__ import annotations

import asyncio
import os

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from nodeseekmcp.deepflood import DeepFloodClient
from nodeseekmcp.models import RssPostHistory
from nodeseekmcp.models import RssPostSource
from nodeseekmcp.models import create_session
from nodeseekmcp.models import create_tables
from nodeseekmcp.models import upsert
from nodeseekmcp.nodeseek import NodeSeekClient


async def sync_nodeseek_rss_post_history():
    print('sync_nodeseek_rss_post_history start...', flush=True)

    client = NodeSeekClient()
    rss_posts = client.get_rss_posts()
    print(f'{len(rss_posts)=}', flush=True)

    post_data_list = []
    for rss_post in rss_posts:
        post_data = dict(
            source=RssPostSource.NODESEEK,
            post_id=rss_post.post_id,
            url=rss_post.url,
            author=rss_post.author,
            title=rss_post.title,
            tag=rss_post.tag,
            summary=rss_post.summary,
            published_at=rss_post.published_at,
        )
        post_data_list.append(post_data)

    await create_tables()

    async with create_session() as session:
        await session.execute(upsert(RssPostHistory), post_data_list)
        print('sync_nodeseek_rss_post_history done', flush=True)


async def sync_deepflood_rss_post_history():
    print('sync_deepflood_rss_post_history start...', flush=True)

    client = DeepFloodClient()
    rss_posts = client.get_rss_posts()
    print(f'{len(rss_posts)=}', flush=True)

    post_data_list = []
    for rss_post in rss_posts:
        post_data = dict(
            source=RssPostSource.DEEPFLOOD,
            post_id=rss_post.post_id,
            url=rss_post.url,
            author=rss_post.author,
            title=rss_post.title,
            tag=rss_post.tag,
            summary=rss_post.summary,
            published_at=rss_post.published_at,
        )
        post_data_list.append(post_data)

    await create_tables()

    async with create_session() as session:
        await session.execute(upsert(RssPostHistory), post_data_list)
        print('sync_deepflood_rss_post_history done', flush=True)


async def main():
    scheduler = AsyncIOScheduler()

    # NodeSeek RSS 抓取任务，每10秒执行一次
    scheduler.add_job(sync_nodeseek_rss_post_history, 'interval', seconds=10, kwargs={})

    # DeepFlood RSS 抓取任务，每10秒执行一次
    scheduler.add_job(sync_deepflood_rss_post_history, 'interval', seconds=10, kwargs={})

    scheduler.start()

    print('Press Ctrl+{} to exit'.format('Break' if os.name == 'nt' else 'C'), flush=True)
    while True:
        await asyncio.sleep(9.876543210)


if __name__ == '__main__':
    asyncio.run(main())
