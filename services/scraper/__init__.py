from .scraper import WebScraper as OriginalWebScraper, BrowserContext, ContentExtractor
from .enhanced_scraper import EnhancedWebScraper, EnhancedBrowserContext, EnhancedBrowserPool
from .cloudflare_bypass import CloudflareBypassService
from .enhanced_config import get_enhanced_scraping_options, should_use_undetected_for_url

# For backward compatibility, WebScraper now points to the enhanced version
WebScraper = EnhancedWebScraper

__all__ = [
    'WebScraper',                      # Enhanced version (default)
    'EnhancedWebScraper',              # Explicit enhanced version
    'OriginalWebScraper',              # Original version (if needed)
    'BrowserContext',                  # Original browser context
    'EnhancedBrowserContext',          # Enhanced browser context
    'EnhancedBrowserPool',             # Enhanced browser pool
    'ContentExtractor',                # Content extractor
    'CloudflareBypassService',         # Cloudflare bypass service
    'get_enhanced_scraping_options',   # Enhanced config utility
    'should_use_undetected_for_url'    # URL analysis utility
]
