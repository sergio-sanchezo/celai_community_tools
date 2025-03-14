from enum import Enum


# Models and enums for firecrawl web tools
class Formats(str, Enum):
    """
    Output formats for web scraping.
    """
    MARKDOWN = "markdown"
    HTML = "html"
    RAW_HTML = "rawHtml"
    LINKS = "links"
    SCREENSHOT = "screenshot"
    SCREENSHOT_AT_FULL_PAGE = "screenshot@fullPage"