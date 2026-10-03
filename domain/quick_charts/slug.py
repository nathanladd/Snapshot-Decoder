"""
Shared chart-title slugify rules.

My Charts title-uniqueness validation compares slugs rather than raw titles,
so "EGR Flow" and "egr-flow!" count as the same name and a user chart can't
shadow a built-in Quick Chart. The rules match Snapshot Decoder Web's
slug.ts, which still uses them to find a chart's hosted Quick IQ page.
"""

import re


def slugify_chart_title(title: str) -> str:
    """Return the slug for a chart title."""
    slug = title.strip()
    slug = slug.replace("&", " and ")
    slug = slug.replace("/", "-")
    slug = re.sub(r"\s+", "-", slug)
    slug = re.sub(r"[^A-Za-z0-9\-]", "", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug
