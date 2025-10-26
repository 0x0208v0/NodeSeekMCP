from __future__ import annotations

from datetime import datetime
from typing import Sequence
from typing import Tuple

import pendulum
from pendulum import DateTime
from pendulum.tz.timezone import Timezone

from nodeseekmcp.deepflood import TAG_ZH_MAP as DEEPFLOOD_TAG_MAP
from nodeseekmcp.models import RssPostSource
from nodeseekmcp.nodeseek import TAG_ZH_MAP as NODESEEK_TAG_MAP

DEFAULT_TIMEZONE = 'Asia/Shanghai'

TAG_DISPLAY_MAP = {
    RssPostSource.NODESEEK: NODESEEK_TAG_MAP,
    RssPostSource.DEEPFLOOD: DEEPFLOOD_TAG_MAP,
}


def _build_reverse_map() -> dict[RssPostSource, dict[str, str]]:
    reverse_maps: dict[RssPostSource, dict[str, str]] = {}
    for source, mapping in TAG_DISPLAY_MAP.items():
        reverse_map: dict[str, str] = {}
        for english, display in mapping.items():
            reverse_map[english.lower()] = english
            reverse_map[display.lower()] = english
        reverse_maps[source] = reverse_map
    return reverse_maps


TAG_REVERSE_MAP = _build_reverse_map()


def localize_tag(source_value: str, tag_value: str) -> str:
    if not tag_value:
        return tag_value
    try:
        source_enum = RssPostSource(source_value)
    except ValueError:
        return tag_value
    mapping = TAG_DISPLAY_MAP.get(source_enum, {})
    segments = [segment.strip() for segment in tag_value.split(',')]
    localized_segments: list[str] = []
    for segment in segments:
        if not segment:
            continue
        key = segment.lower()
        localized_segments.append(mapping.get(segment, mapping.get(key, segment)))
    if localized_segments:
        return ', '.join(localized_segments)
    return tag_value


def normalize_tag_filter(tag_value: str, source: RssPostSource | None = None) -> set[str]:
    if not tag_value:
        return set()
    normalized_value = tag_value.strip().lower()
    if not normalized_value:
        return set()
    sources = [source] if source else list(TAG_REVERSE_MAP.keys())
    matched_tags: set[str] = set()
    for src in sources:
        reverse_map = TAG_REVERSE_MAP.get(src, {})
        if normalized_value in reverse_map:
            matched_tags.add(reverse_map[normalized_value])
    if matched_tags:
        return matched_tags
    return {tag_value.strip()}


def normalize_tag_filters(
    tag_values: Sequence[str],
    source: RssPostSource | None = None,
) -> set[str]:
    normalized: set[str] = set()
    for value in tag_values:
        normalized.update(normalize_tag_filter(value, source))
    return normalized


def to_display_tag(tag_value: str, source: RssPostSource | None = None) -> str:
    if not tag_value:
        return tag_value
    normalized = tag_value.strip()
    if not normalized:
        return normalized
    sources = [source] if source else list(TAG_DISPLAY_MAP.keys())
    for src in sources:
        mapping = TAG_DISPLAY_MAP.get(src, {})
        for english, display in mapping.items():
            if normalized.lower() == english.lower():
                return display
    return normalized


def get_tag_options() -> list[Tuple[RssPostSource, str, str]]:
    options: list[Tuple[RssPostSource, str, str]] = []
    for source, mapping in TAG_DISPLAY_MAP.items():
        for english, display in mapping.items():
            options.append((source, english, display))
    options.sort(key=lambda item: (item[0].value, item[2]))
    return options


def to_timezone(dt: datetime, tz: Timezone | None = None) -> DateTime | None:
    if dt is None:
        return None
    timezone = tz or pendulum.timezone(DEFAULT_TIMEZONE)
    if dt.tzinfo is None:
        dt_instance = pendulum.instance(dt, tz='UTC')
    else:
        dt_instance = pendulum.instance(dt)
    return dt_instance.in_timezone(timezone)


def humanize_datetime(dt: DateTime, reference: DateTime | None = None) -> str:
    reference_dt = reference or pendulum.now(DEFAULT_TIMEZONE)
    if dt >= reference_dt:
        return '刚刚'
    delta = reference_dt - dt
    seconds = int(delta.total_seconds())
    if seconds < 60:
        return '刚刚'
    minutes = seconds // 60
    if minutes < 60:
        return f'{minutes}分钟前'
    hours = minutes // 60
    if hours < 24:
        return f'{hours}小时前'
    days = hours // 24
    return f'{days}天前'
