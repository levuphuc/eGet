from fastapi import APIRouter, Depends, HTTPException, Request, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from models.request import ScrapeRequest
from models.response import ScrapeResponse
from services.scraper.scraper import WebScraper
from services.scraper.cloudflare_bypass import CloudflareBypassService
from services.scraper.enhanced_config import should_use_undetected_for_url, get_enhanced_scraping_options
from services.cache.cache_service import CacheService
from core.config import settings
import jwt
from loguru import logger

router = APIRouter(tags=["scraper"])
security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> bool:
    try:
        jwt.decode(credentials.credentials, settings.SECRET_KEY, algorithms=["HS256"])
        return True
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.post("/scrape", response_model=ScrapeResponse)
async def scrape_url(request: ScrapeRequest, req: Request):
    try:
        logger.info(f"🚀 Processing intelligent scrape request for URL: {request.url}")
        
        # Check if scraper exists in app state
        if not hasattr(req.app.state, "scraper"):
            logger.error("Scraper not initialized in app state")
            raise HTTPException(
                status_code=500,
                detail="Scraper service not initialized"
            )

        # Build base options from request
        base_options = {
            "only_main": request.onlyMainContent,
            "timeout": request.timeout or settings.TIMEOUT,
            "user_agent": settings.DEFAULT_USER_AGENT,
            "headers": request.headers,
            "include_screenshot": request.includeScreenshot,
            "include_raw_html": request.includeRawHtml,
            "screenshot_quality": settings.SCREENSHOT_QUALITY,
            "wait_for_selector": request.waitFor,
            "stealth": request.stealth if hasattr(request, 'stealth') else False
        }
        
        if request.actions:
            base_options["actions"] = request.actions

        # Check if URL needs Cloudflare bypass
        url_str = str(request.url)
        needs_bypass = should_use_undetected_for_url(url_str, base_options)
        
        if needs_bypass:
            logger.info(f"🛡️ Cloudflare bypass detected for: {url_str}")
            
            # Get cache service from app state
            cache_service = None
            if hasattr(req.app.state, 'scraper') and hasattr(req.app.state.scraper, 'cache_service'):
                cache_service = req.app.state.scraper.cache_service
            
            # Use specialized Cloudflare bypass service
            bypass_service = CloudflareBypassService(cache_service=cache_service)
            
            # Get enhanced options for bypass
            enhanced_options = get_enhanced_scraping_options(url_str, base_options)
            
            logger.info(f"🔧 Using enhanced bypass options: timeout={enhanced_options.get('timeout')}s, stealth={enhanced_options.get('stealth')}")
            
            result = await bypass_service.bypass_and_scrape(url_str, enhanced_options)
            
            # Add bypass metadata
            if result.get('success') and result.get('data', {}).get('metadata'):
                result['data']['metadata']['bypass_used'] = True
                result['data']['metadata']['bypass_method'] = 'cloudflare_bypass_service'
            
        else:
            logger.info(f"📄 Using standard scraper for: {url_str}")
            
            # Use standard scraper for non-Cloudflare URLs
            result = await req.app.state.scraper.scrape(url_str, base_options)
            
            # Add standard scraper metadata
            if result.get('success') and result.get('data', {}).get('metadata'):
                result['data']['metadata']['bypass_used'] = False
                result['data']['metadata']['bypass_method'] = 'standard_scraper'

        logger.debug(f"Scraping completed with method: {'bypass' if needs_bypass else 'standard'}")
        
        if not result:
            raise HTTPException(
                status_code=500,
                detail="Scraping failed - no result returned"
            )
            
        return result
        
    except Exception as e:
        logger.exception(f"Scraping error: {str(e)}")  # This will log the full traceback
        raise HTTPException(
            status_code=500,
            detail=f"Scraping failed: {str(e)}"
        )