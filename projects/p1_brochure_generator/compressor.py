"""
Enterprise Brochure Generator - Noise Reduction & Token Compression
Strips HTML boilerplate, navigation, footers, cookie banners, and redundant whitespace
to drastically reduce LLM context token consumption.
"""

import re
from typing import Dict, Tuple


def strip_html_boilerplate(html_content: str) -> str:
    """
    Remove boilerplate HTML elements like head, nav, footer, scripts, styles,
    and common cookie consent pop-ups.
    """
    if not html_content:
        return ""

    # Remove script and style tags
    clean = re.sub(r"<(script|style|noscript)[^>]*>.*?</\1>", " ", html_content, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove header, footer, nav, aside tags
    clean = re.sub(r"<(nav|header|footer|aside)[^>]*>.*?</\1>", " ", clean, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove SVG tags and comments
    clean = re.sub(r"<svg[^>]*>.*?</svg>", " ", clean, flags=re.DOTALL | re.IGNORECASE)
    clean = re.sub(r"<!--.*?-->", " ", clean, flags=re.DOTALL)
    
    # Remove elements matching common cookie / banner class names
    clean = re.sub(
        r'<[^>]*(?:id|class)=["\'][^"\']*(?:cookie|consent|banner|gdpr|modal|popup)[^"\']*["\'][^>]*>.*?</[^>]+>',
        " ",
        clean,
        flags=re.DOTALL | re.IGNORECASE,
    )
    
    return clean


def clean_and_compress_markdown(text: str) -> str:
    """
    Takes raw extracted markdown or text and applies aggressive token compression:
    1. Removes empty markdown links: [text]() or [](url)
    2. Strips image tags: ![alt](url) -> saves hundreds of tokens
    3. Condenses excessive whitespace and repeated newlines
    4. Strips repeated navigation bullet points and legal disclaimers
    """
    if not text:
        return ""

    # Remove markdown images (useless for text-based brochure generation)
    text = re.sub(r"!\[.*?\]\(.*?\)", "", text)

    # Remove empty markdown links
    text = re.sub(r"\[\s*\]\(.*?\)", "", text)

    # Simplify links to just their label: [Click Here](http...) -> Click Here
    # (keeps context intact while reducing token overhead of long URLs)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)

    # Remove HTML remnants
    text = re.sub(r"<[^>]+>", " ", text)

    # Remove repetitive social share/media lines
    social_pattern = r"(?i)(share on facebook|follow us on|tweet|linkedin|instagram|cookie policy|all rights reserved)"
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        # Skip lines that are purely repetitive social icons/disclaimers
        if re.search(social_pattern, stripped) and len(stripped) < 80:
            continue
        lines.append(stripped)

    # Rejoin lines
    compressed = "\n".join(lines)

    # Condense 3+ newlines to 2
    compressed = re.sub(r"\n{3,}", "\n\n", compressed)

    # Condense multiple spaces to a single space
    compressed = re.sub(r"[ \t]{2,}", " ", compressed)

    return compressed.strip()


def calculate_token_compression_stats(original_text: str, compressed_text: str) -> Dict[str, float]:
    """
    Calculates estimated token counts (approx 4 chars per token) and savings percentage.
    """
    orig_chars = len(original_text)
    comp_chars = len(compressed_text)

    orig_tokens = round(orig_chars / 4)
    comp_tokens = round(comp_chars / 4)

    savings_pct = 0.0
    if orig_tokens > 0:
        savings_pct = round(((orig_tokens - comp_tokens) / orig_tokens) * 100, 2)

    return {
        "original_tokens_est": orig_tokens,
        "compressed_tokens_est": comp_tokens,
        "tokens_saved": orig_tokens - comp_tokens,
        "compression_percentage": savings_pct,
    }
