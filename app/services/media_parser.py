from __future__ import annotations

from urllib.parse import urlparse

import httpx

from app.models.comment import CommentResource


class MediaParser:
    async def resolve_link(self, url: str) -> str:
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=10) as client:
                response = await client.head(url)
                if response.status_code >= 400:
                    response = await client.get(url)
                return str(response.url)
        except Exception:
            return url

    async def normalize_resources(self, resources: list[CommentResource]) -> list[CommentResource]:
        normalized: list[CommentResource] = []
        seen: set[tuple[str, str]] = set()
        for resource in resources:
            url = resource.url
            if resource.type == "link" and urlparse(url).netloc.endswith("t.co"):
                url = await self.resolve_link(url)
            key = (resource.type, url)
            if key in seen:
                continue
            seen.add(key)
            normalized.append(resource.model_copy(update={"url": url}))
        return normalized
