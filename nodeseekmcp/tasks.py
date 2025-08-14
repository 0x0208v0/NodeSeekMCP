# https://github.com/agronholm/apscheduler/blob/3.x/examples/schedulers/asyncio_.py


from __future__ import annotations

import asyncio
import os

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from nodeseekmcp.models import RssPostHistory
from nodeseekmcp.models import create_session
from nodeseekmcp.models import create_tables
from nodeseekmcp.models import upsert
from nodeseekmcp.nodeseek import NodeSeekClient


async def sync_rss_post_history():
    print('sync_rss_post_history start...', flush=True)

    client = NodeSeekClient()
    rss_posts = client.get_rss_posts()
    print(f'{len(rss_posts)=}', flush=True)

    post_data_list = []
    for rss_post in rss_posts:
        post_data = dict(
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
        await session.commit()
        print('sync_rss_post_history done', flush=True)


async def main():
    scheduler = AsyncIOScheduler()

    scheduler.add_job(sync_rss_post_history, 'interval', seconds=10, kwargs={})

    scheduler.start()

    print('Press Ctrl+{} to exit'.format('Break' if os.name == 'nt' else 'C'), flush=True)
    while True:
        await asyncio.sleep(9.876543210)


if __name__ == '__main__':
    asyncio.run(main())
