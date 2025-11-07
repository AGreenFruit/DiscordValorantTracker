"""HTTP utility functions for making concurrent requests"""
import asyncio
import aiohttp
from typing import List, Tuple, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


async def request_many(
    requests: List[Tuple[str, str, Optional[Dict[str, Any]], Optional[Dict[str, str]]]],
    timeout: int = 30
) -> List[Dict[str, Any]]:
    """
    Make multiple HTTP requests concurrently.
    """
    async with aiohttp.ClientSession() as session:
        tasks = []
        for request_tuple in requests:
            method = request_tuple[0]
            url = request_tuple[1]
            json_body = request_tuple[2] if len(request_tuple) > 2 else None
            headers = request_tuple[3] if len(request_tuple) > 3 else None

            tasks.append(_make_request(session, method, url, json_body, headers, timeout))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results


async def _make_request(
    session: aiohttp.ClientSession,
    method: str,
    url: str,
    json_body: Optional[Dict[str, Any]],
    headers: Optional[Dict[str, str]],
    timeout: int
) -> Dict[str, Any]:
    """Make a single HTTP request"""
    try:
        async with session.request(
            method=method,
            url=url,
            json=json_body,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=timeout)
        ) as response:
            try:
                data = await response.json()
            except Exception:
                data = await response.text()

            return {
                "status": response.status,
                "data": data,
                "url": url,
                "error": None
            }
    except Exception as e:
        logger.error(f"Request failed for {url}: {e}")
        return {
            "status": None,
            "data": None,
            "url": url,
            "error": str(e)
        }
