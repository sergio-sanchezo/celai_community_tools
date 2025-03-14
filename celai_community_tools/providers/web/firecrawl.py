from typing import Any, Dict, List, Optional

from cel.assistants.common import Param
from cel.assistants.function_context import FunctionContext
from cel.assistants.function_response import FunctionResponse
from celai_community_tools.providers.web.models import Formats
from celai_community_tools.tool import tool

# Import firecrawl library (you'll need to install this with pip)
try:
    from firecrawl import FirecrawlApp
except ImportError:
    # Create a fallback class for documentation/development without the actual dependency
    class FirecrawlApp:
        def __init__(self, api_key):
            self.api_key = api_key
        
        def scrape_url(self, url, params=None):
            return {"error": "Firecrawl not installed"}
            
        def async_crawl_url(self, url, params=None):
            return {"error": "Firecrawl not installed"}
            
        def crawl_url(self, url, params=None):
            return {"error": "Firecrawl not installed"}
            
        def check_crawl_status(self, crawl_id):
            return {"error": "Firecrawl not installed"}
            
        def cancel_crawl(self, crawl_id):
            return {"error": "Firecrawl not installed"}
            
        def map_url(self, url, params=None):
            return {"error": "Firecrawl not installed"}


@tool(
    name="ScrapeURL",
    desc="Scrape a URL using Firecrawl and return the data in specified formats",
    requires_secrets=["FIRECRAWL_API_KEY"],
    params=[
        Param(name="url", type="string", description="URL to scrape", required=True),
        Param(name="formats", type="string", description="Formats to retrieve as comma-separated string (markdown, html, rawHtml, links, screenshot, screenshot@fullPage). Defaults to 'markdown'.", required=False),
        Param(name="only_main_content", type="boolean", description="Only return the main content of the page excluding headers, navs, footers, etc.", required=False),
        Param(name="include_tags", type="string", description="List of tags to include in the output, comma-separated", required=False),
        Param(name="exclude_tags", type="string", description="List of tags to exclude from the output, comma-separated", required=False),
        Param(name="wait_for", type="integer", description="Specify a delay in milliseconds before fetching the content", required=False),
        Param(name="timeout", type="integer", description="Timeout in milliseconds for the request", required=False)
    ]
)
def scrape_url(params, ctx):
    """
    Scrape a URL using Firecrawl and return the data in specified formats.
    """
    # Extract parameters from the params dict
    url = params.get("url")
    formats = params.get("formats", "markdown")
    only_main_content = params.get("only_main_content", True)
    include_tags = params.get("include_tags")
    exclude_tags = params.get("exclude_tags")
    wait_for = params.get("wait_for", 10)
    timeout = params.get("timeout", 30000)
    
    # Use the FIRECRAWL_API_KEY from environment variables or .env file
    import os
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.environ.get("FIRECRAWL_API_KEY")
    
    if not api_key:
        return "Error: FIRECRAWL_API_KEY environment variable is required but not found."
    
    # Process format string into list of formats
    format_list = [fmt.strip() for fmt in formats.split(",")]
    valid_formats = []
    for fmt in format_list:
        try:
            valid_formats.append(Formats(fmt))
        except ValueError:
            continue
    
    if not valid_formats:
        valid_formats = [Formats.MARKDOWN]
        
    # Process include_tags and exclude_tags
    include_tags_list = None
    if include_tags:
        include_tags_list = [tag.strip() for tag in include_tags.split(",")]
        
    exclude_tags_list = None
    if exclude_tags:
        exclude_tags_list = [tag.strip() for tag in exclude_tags.split(",")]
    
    try:
        app = FirecrawlApp(api_key=api_key)
        scrape_params = {
            "formats": valid_formats,
            "onlyMainContent": only_main_content,
            "includeTags": include_tags_list or [],
            "excludeTags": exclude_tags_list or [],
            "waitFor": wait_for,
            "timeout": timeout,
        }

        print(f"Scraping URL: {url} with formats: {valid_formats}")
        response = app.scrape_url(url, params=scrape_params)
        
        # Format the result for better readability
        formatted_result = {
            "url": url,
            "formats": [f for f in valid_formats],
        }
        
        # Add specific format data
        for format_key in valid_formats:
            if format_key in response:
                if format_key == Formats.SCREENSHOT or format_key == Formats.SCREENSHOT_AT_FULL_PAGE:
                    formatted_result[format_key] = "[Base64 screenshot data available]"
                else:
                    # For text content, return a preview
                    content = response[format_key]
                    if isinstance(content, str) and len(content) > 500:
                        preview = content[:500] + "... [content truncated]"
                        formatted_result[format_key] = preview
                    else:
                        formatted_result[format_key] = content
        
        if len(formatted_result) <= 2:  # Only url and formats, no actual data
            return f"No content was retrieved from {url} in the specified formats."
            
        formatted_result["message"] = f"Successfully scraped content from {url}"

        print(f"Scrape result: {formatted_result}")
        return str(formatted_result)
        
    except Exception as e:
        return f"Error scraping URL {url}: {str(e)}"


@tool(
    name="CrawlWebsite",
    desc="Crawl a website using Firecrawl",
    requires_secrets=["FIRECRAWL_API_KEY"],
    params=[
        Param(name="url", type="string", description="URL to crawl", required=True),
        Param(name="exclude_paths", type="string", description="URL patterns to exclude from the crawl, comma-separated", required=False),
        Param(name="include_paths", type="string", description="URL patterns to include in the crawl, comma-separated", required=False),
        Param(name="max_depth", type="integer", description="Maximum depth to crawl relative to the entered URL", required=False),
        Param(name="ignore_sitemap", type="boolean", description="Ignore the website sitemap when crawling", required=False),
        Param(name="limit", type="integer", description="Limit the number of pages to crawl", required=False),
        Param(name="allow_backward_links", type="boolean", description="Enable navigation to previously linked pages", required=False),
        Param(name="allow_external_links", type="boolean", description="Allow following links to external websites", required=False),
        Param(name="webhook", type="string", description="The URL to send a POST request to when the crawl is completed", required=False),
        Param(name="async_crawl", type="boolean", description="Run the crawl asynchronously", required=False)
    ]
)
def crawl_website(params, ctx):
    """
    Crawl a website using Firecrawl. If the crawl is asynchronous, returns the crawl ID.
    If the crawl is synchronous, returns the crawl data.
    """
    # Extract parameters from the params dict
    url = params.get("url")
    exclude_paths = params.get("exclude_paths")
    include_paths = params.get("include_paths")
    max_depth = params.get("max_depth", 2)
    ignore_sitemap = params.get("ignore_sitemap", True)
    limit = params.get("limit", 10)
    allow_backward_links = params.get("allow_backward_links", False)
    allow_external_links = params.get("allow_external_links", False)
    webhook = params.get("webhook")
    async_crawl = params.get("async_crawl", True)
    
    # Use the FIRECRAWL_API_KEY from environment variables or .env file
    import os
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.environ.get("FIRECRAWL_API_KEY")
    
    if not api_key:
        return "Error: FIRECRAWL_API_KEY environment variable is required but not found."
    
    # Process exclude_paths and include_paths
    exclude_paths_list = None
    if exclude_paths:
        exclude_paths_list = [path.strip() for path in exclude_paths.split(",")]
        
    include_paths_list = None
    if include_paths:
        include_paths_list = [path.strip() for path in include_paths.split(",")]
    
    try:
        app = FirecrawlApp(api_key=api_key)
        crawl_params = {
            "limit": limit,
            "excludePaths": exclude_paths_list or [],
            "includePaths": include_paths_list or [],
            "maxDepth": max_depth,
            "ignoreSitemap": ignore_sitemap,
            "allowBackwardLinks": allow_backward_links,
            "allowExternalLinks": allow_external_links,
        }
        if webhook:
            crawl_params["webhook"] = webhook

        if async_crawl:
            response = app.async_crawl_url(url, params=crawl_params)
            # Remove URL as it's not clickable and only the ID is needed
            if "url" in response:
                del response["url"]
                
            result = {
                "message": f"Async crawl started for {url}",
                "crawl_id": response.get("crawl_id", "Unknown"),
                "status": response.get("status", "Unknown"),
            }
            return str(result)
        else:
            response = app.crawl_url(url, params=crawl_params)
            result = {
                "message": f"Completed crawl for {url}",
                "pages_crawled": len(response.get("data", [])),
                "status": response.get("status", "Unknown"),
            }
            return str(result)
    except Exception as e:
        return f"Error crawling website {url}: {str(e)}"


@tool(
    name="GetCrawlStatus",
    desc="Get the status of a Firecrawl crawl",
    requires_secrets=["FIRECRAWL_API_KEY"],
    params=[
        Param(name="crawl_id", type="string", description="The ID of the crawl job", required=True)
    ]
)
def get_crawl_status(params, ctx):
    """
    Get the status of a Firecrawl 'crawl' that is either in progress or recently completed.
    """
    # Extract parameters from the params dict
    crawl_id = params.get("crawl_id")
    
    # Use the FIRECRAWL_API_KEY from environment variables or .env file
    import os
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.environ.get("FIRECRAWL_API_KEY")
    
    if not api_key:
        return "Error: FIRECRAWL_API_KEY environment variable is required but not found."
    
    try:
        app = FirecrawlApp(api_key=api_key)
        crawl_status = app.check_crawl_status(crawl_id)
        
        # Remove data to avoid overloading the response
        if "data" in crawl_status:
            data_size = len(crawl_status["data"]) if isinstance(crawl_status["data"], list) else "present"
            del crawl_status["data"]
            crawl_status["data_message"] = f"Data is available. Use GetCrawlData to retrieve it. Size: {data_size}"
        
        result = {
            "message": f"Crawl status retrieved for ID: {crawl_id}",
            "crawl_id": crawl_id,
            **crawl_status
        }
        return str(result)
    except Exception as e:
        return f"Error getting crawl status for crawl ID {crawl_id}: {str(e)}"


@tool(
    name="GetCrawlData",
    desc="Get the data of a Firecrawl crawl",
    requires_secrets=["FIRECRAWL_API_KEY"],
    params=[
        Param(name="crawl_id", type="string", description="The ID of the crawl job", required=True)
    ]
)
def get_crawl_data(params, ctx):
    """
    Get the data of a Firecrawl 'crawl' that is either in progress or recently completed.
    """
    # Extract parameters from the params dict
    crawl_id = params.get("crawl_id")
    
    # Use the FIRECRAWL_API_KEY from environment variables or .env file
    import os
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.environ.get("FIRECRAWL_API_KEY")
    
    if not api_key:
        return "Error: FIRECRAWL_API_KEY environment variable is required but not found."
    
    try:
        app = FirecrawlApp(api_key=api_key)
        crawl_data = app.check_crawl_status(crawl_id)
        
        if "next_url" in crawl_data:
            result = {
                "message": f"Crawl data is too large for direct retrieval. Use the next_url to paginate.",
                "crawl_id": crawl_id,
                "next_url": crawl_data["next_url"],
                "data_preview": "Data exceeds 10MB limit"
            }
            return str(result)
        
        # Summarize data rather than returning it all
        if "data" in crawl_data and isinstance(crawl_data["data"], list):
            data_count = len(crawl_data["data"])
            data_sample = crawl_data["data"][:3] if data_count > 0 else []
            
            result = {
                "message": f"Retrieved {data_count} pages of crawl data for ID: {crawl_id}",
                "crawl_id": crawl_id,
                "total_pages": data_count,
                "sample_pages": data_sample
            }
            return str(result)
        
        result = {
            "message": f"Retrieved crawl data for ID: {crawl_id}",
            "crawl_id": crawl_id,
            **crawl_data
        }
        return str(result)
    except Exception as e:
        return f"Error getting crawl data for crawl ID {crawl_id}: {str(e)}"


@tool(
    name="CancelCrawl",
    desc="Cancel an asynchronous crawl job",
    requires_secrets=["FIRECRAWL_API_KEY"],
    params=[
        Param(name="crawl_id", type="string", description="The ID of the asynchronous crawl job to cancel", required=True)
    ]
)
def cancel_crawl(params, ctx):
    """
    Cancel an asynchronous crawl job that is in progress using the Firecrawl API.
    """
    # Extract parameters from the params dict
    crawl_id = params.get("crawl_id")
    
    # Use the FIRECRAWL_API_KEY from environment variables or .env file
    import os
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.environ.get("FIRECRAWL_API_KEY")
    
    if not api_key:
        return "Error: FIRECRAWL_API_KEY environment variable is required but not found."
    
    try:
        app = FirecrawlApp(api_key=api_key)
        cancellation_status = app.cancel_crawl(crawl_id)
        
        result = {
            "message": f"Crawl with ID {crawl_id} has been cancelled",
            "crawl_id": crawl_id,
            **cancellation_status
        }
        return str(result)
    except Exception as e:
        return f"Error cancelling crawl with ID {crawl_id}: {str(e)}"


@tool(
    name="MapWebsite",
    desc="Map a website to discover its structure",
    requires_secrets=["FIRECRAWL_API_KEY"],
    params=[
        Param(name="url", type="string", description="The base URL to start crawling from", required=True),
        Param(name="search", type="string", description="Search query to use for mapping", required=False),
        Param(name="ignore_sitemap", type="boolean", description="Ignore the website sitemap when crawling", required=False),
        Param(name="include_subdomains", type="boolean", description="Include subdomains of the website", required=False),
        Param(name="limit", type="integer", description="Maximum number of links to return", required=False)
    ]
)
def map_website(params, ctx):
    """
    Map a website from a single URL to a map of the entire website.
    """
    # Extract parameters from the params dict
    url = params.get("url")
    search = params.get("search")
    ignore_sitemap = params.get("ignore_sitemap", True)
    include_subdomains = params.get("include_subdomains", False)
    limit = params.get("limit", 5000)
    
    # Use the FIRECRAWL_API_KEY from environment variables or .env file
    import os
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.environ.get("FIRECRAWL_API_KEY")
    
    if not api_key:
        return "Error: FIRECRAWL_API_KEY environment variable is required but not found."
    
    try:
        app = FirecrawlApp(api_key=api_key)
        map_params = {
            "ignoreSitemap": ignore_sitemap,
            "includeSubdomains": include_subdomains,
            "limit": limit,
        }
        if search:
            map_params["search"] = search

        map_result = app.map_url(url, params=map_params)
        
        # Format a more readable response with summary
        if "links" in map_result and isinstance(map_result["links"], list):
            link_count = len(map_result["links"])
            sample_links = map_result["links"][:5] if link_count > 0 else []
            
            result = {
                "message": f"Successfully mapped {link_count} links from {url}",
                "url": url,
                "total_links": link_count,
                "sample_links": sample_links
            }
            return str(result)
        
        result = {
            "message": f"Website mapping completed for {url}",
            **map_result
        }
        return str(result)
    except Exception as e:
        return f"Error mapping website {url}: {str(e)}"