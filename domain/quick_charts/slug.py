"""
Shared chart-title slugify rules.

Quick IQ resolves a chart's hosted help page by slugifying its *title*
(https://decoder.rudi-hq.com/quick-iq/{slug}.html), not by action_id. My
Charts title-uniqueness validation must slugify with the exact same rules so
a user title can never collide with a built-in chart's Quick IQ page.
"""

import re


def slugify_chart_title(title: str) -> str:
    """Return the Quick IQ slug for a chart title."""
    slug = title.strip()
    slug = slug.replace("&", " and ")
    slug = slug.replace("/", "-")
    slug = re.sub(r"\s+", "-", slug)
    slug = re.sub(r"[^A-Za-z0-9\-]", "", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug
