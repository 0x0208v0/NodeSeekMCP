from __future__ import annotations

import datetime


def time_ago(dt: datetime.datetime) -> str:
    now = datetime.datetime.now(datetime.UTC)
    time_difference = now - dt

    days = time_difference.days
    seconds = time_difference.seconds
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60

    if days > 0:
        return f'{days} day{"s" if days > 1 else ""} ago'
    elif hours > 0:
        return f'{hours}h {minutes}min ago' if minutes > 0 else f'{hours}h ago'
    elif minutes > 0:
        return f'{minutes}min ago'
    else:
        return f'{seconds}s ago'
