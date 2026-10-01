"""
Enterprise Brochure Generator - Dynamic Web Crawler & Link Discovery
Leverages Crawl4AI and Playwright to render JavaScript single-page apps (SPAs)
and extract DOM, discover internal links, and collect website content.
"""

import asyncio
import re
from typing import Dict, List, Set
from urllib.parse import urljoin, urlparse

from .config import (
    DEFAULT_MAX_CRAWL_PAGES,
    EXCLUDE_URL_PATTERNS,
    HEADLESS,
    PRIORITY_URL_KEYWORDS,
)
from .compressor import (
    calculate_token_compression_stats,
    clean_and_compress_markdown,
    strip_html_boilerplate,
)


def get_base_domain(url: str) -> str:
    """Extract netloc (domain) from a URL."""
    parsed = urlparse(url)
    return parsed.netloc.lower()


def is_valid_internal_link(target_url: str, base_domain: str) -> bool:
    """
    Validates if a URL is an internal page belonging to base_domain
    and does not match exclusion patterns (media, auth, blogs, etc.).
    """
    parsed = urlparse(target_url)
    target_domain = parsed.netloc.lower()

    # Must match domain or subdomain
    if target_domain and target_domain != base_domain and not target_domain.endswith("." + base_domain):
        return False

    # Filter out empty paths or purely hash fragments
    if not parsed.path or parsed.path == "/" and not parsed.query:
        return False

    # Check exclusion regexes
    path_and_query = parsed.path + ("?" + parsed.query if parsed.query else "")
    for pattern in EXCLUDE_URL_PATTERNS:
        if re.search(pattern, path_and_query, re.IGNORECASE):
            return False

    return True


def score_url_relevance(url: str) -> int:
    """
    Scores how relevant a URL is for an enterprise brochure based on keywords.
    Higher score means more critical enterprise info (e.g. pricing, about, services).
    """
    url_lower = url.lower()
    score = 0
    for keyword in PRIORITY_URL_KEYWORDS:
        if keyword in url_lower:
            score += 10
    # Prefer shorter clean paths
    score -= len(url.split("/"))
    return score


class EnterpriseWebCrawler:
    """
    Asynchronous web crawler with dynamic JavaScript rendering and link discovery.
    Uses Crawl4AI when available, with seamless Playwright async fallback.
    """

    def __init__(self, headless: bool = HEADLESS):
        self.headless = headless

    async def crawl_site(self, root_url: str, max_pages: int = DEFAULT_MAX_CRAWL_PAGES) -> Dict[str, any]:
        """
        Main crawling pipeline:
        1. Crawls root URL with full JS rendering.
        2. Discovers high-priority internal links (/about, /services, /pricing, etc.).
        3. Crawls discovered internal pages concurrently.
        4. Applies noise reduction and token compression to all pages.
        5. Returns structured crawled data with token metrics.
        """
        # Ensure scheme
        if not root_url.startswith("http://") and not root_url.startswith("https://"):
            root_url = "https://" + root_url

        base_domain = get_base_domain(root_url)

        # Step 1: Crawl Root Page
        root_result = await self._crawl_single_page(root_url)
        all_pages_data = {root_url: root_result}

        # Step 2: Internal Link Discovery
        discovered_links = self._extract_internal_links(
            html=root_result.get("raw_html", ""),
            base_url=root_url,
            base_domain=base_domain,
        )

        # Sort discovered links by enterprise relevance score
        sorted_links = sorted(discovered_links, key=score_url_relevance, reverse=True)
        links_to_crawl = sorted_links[: max_pages - 1]

        # Step 3: Concurrently Crawl Discovered Internal Pages
        if links_to_crawl:
            tasks = [self._crawl_single_page(link) for link in links_to_crawl]
            subpage_results = await asyncio.gather(*tasks, return_exceptions=True)

            for link, res in zip(links_to_crawl, subpage_results):
                if isinstance(res, dict) and res.get("content"):
                    all_pages_data[link] = res

        # Step 4: Aggregate and Compress Content
        combined_raw_text = ""
        combined_clean_markdown = ""

        for page_url, p_data in all_pages_data.items():
            header = f"\n\n--- SOURCE PAGE: {page_url} ---\n"
            combined_raw_text += header + p_data.get("raw_text", "")
            combined_clean_markdown += header + p_data.get("content", "")

        compression_stats = calculate_token_compression_stats(
            combined_raw_text, combined_clean_markdown
        )

        return {
            "root_url": root_url,
            "base_domain": base_domain,
            "crawled_pages_count": len(all_pages_data),
            "discovered_links": links_to_crawl,
            "combined_content": combined_clean_markdown,
            "compression_stats": compression_stats,
            "pages_detail": all_pages_data,
        }

    async def _crawl_single_page(self, url: str) -> Dict[str, str]:
        """
        Crawls a single URL using Playwright for full client-side dynamic JS execution.
        """
        try:
            # First attempt using Crawl4AI if installed and functional
            return await self._crawl_with_crawl4ai(url)
        except Exception:
            # Fallback to direct Playwright async engine
            return await self._crawl_with_playwright(url)

    async def _crawl_with_crawl4ai(self, url: str) -> Dict[str, str]:
        """Crawls via Crawl4AI AsyncWebCrawler."""
        from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

        browser_cfg = BrowserConfig(headless=self.headless, verbose=False)
        run_cfg = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            word_count_threshold=10,
            excluded_tags=["nav", "header", "footer", "form", "svg"],
            remove_overlay_elements=True,
        )

        async with AsyncWebCrawler(config=browser_cfg) as crawler:
            result = await crawler.arun(url=url, config=run_cfg)
            if not result.success:
                raise RuntimeError(f"Crawl4AI failed: {result.error_message}")

            raw_html = result.html or ""
            raw_markdown = result.markdown or ""
            clean_md = clean_and_compress_markdown(raw_markdown)

            return {
                "url": url,
                "raw_html": raw_html,
                "raw_text": raw_markdown,
                "content": clean_md,
            }

    async def _crawl_with_playwright(self, url: str) -> Dict[str, str]:
        """Direct Playwright async implementation capturing fully rendered DOM."""
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                )
            )
            page = await context.new_page()

            # Navigate and wait for DOM and network idle
            try:
                await page.goto(url, wait_until="networkidle", timeout=25000)
            except Exception:
                await page.goto(url, wait_until="domcontentloaded", timeout=25000)

            # Wait a short moment for client-side JS hydration / React / Vue rendering
            await page.wait_for_timeout(1500)

            # Capture complete rendered HTML
            raw_html = await page.content()
            
            # Extract main visible text
            body_text = await page.inner_text("body")

            await browser.close()

            # Clean and compress
            clean_html = strip_html_boilerplate(raw_html)
            clean_md = clean_and_compress_markdown(body_text)

            return {
                "url": url,
                "raw_html": raw_html,
                "raw_text": body_text,
                "content": clean_md,
            }

    def _extract_internal_links(self, html: str, base_url: str, base_domain: str) -> List[str]:
        """
        Parses all href attributes from the rendered HTML and selects unique,
        valid internal URLs.
        """
        found_links: Set[str] = set()
        # Find all href matches
        hrefs = re.findall(r'href=["\'](.*?)["\']', html, re.IGNORECASE)

        for href in hrefs:
            href = href.strip()
            if not href or href.startswith("#") or href.startswith("javascript:"):
                continue

            # Resolve relative URLs
            absolute_url = urljoin(base_url, href)
            # Remove hash anchor
            clean_url = absolute_url.split("#")[0].rstrip("/")

            if is_valid_internal_link(clean_url, base_domain):
                found_links.add(clean_url)

        return list(found_links)
