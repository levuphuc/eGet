# -*- coding: utf-8 -*-
"""
Optimized Cloudflare Bypass Service
Specialized service for bypassing Cloudflare protection with high success rate
"""

import asyncio
import time
import random
import json
import base64
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from bs4 import BeautifulSoup
import html2text
from loguru import logger

from core.config import get_settings
from services.cache.cache_service import CacheService

settings = get_settings()

class CloudflareBypassService:
    """Optimized service specifically for Cloudflare bypass"""
    
    # Domain-specific configurations
    DOMAIN_CONFIGS = {
        'tuesy.net': {
            'wait_time': 35,
            'scroll_amount': 500,
            'scroll_wait': 2,
            'final_wait': 5,
            'chrome_version': 139,
            'retry_attempts': 3,
            'cloudflare_indicators': ['cloudflare', 'checking your browser', 'please wait']
        },
        'default': {
            'wait_time': 20,
            'scroll_amount': 300,
            'scroll_wait': 1,
            'final_wait': 3,
            'chrome_version': None,
            'retry_attempts': 2,
            'cloudflare_indicators': ['cloudflare', 'checking your browser']
        }
    }
    
    def __init__(self, cache_service: Optional[CacheService] = None):
        self.cache_service = cache_service
        self.active_drivers = {}
        self.success_count = 0
        self.failure_count = 0
        
    async def bypass_and_scrape(self, url: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Main method to bypass Cloudflare and scrape content"""
        logger.info(f"🚀 Starting optimized Cloudflare bypass for: {url}")
        
        start_time = time.time()
        domain = urlparse(url).netloc
        config = self.DOMAIN_CONFIGS.get(domain, self.DOMAIN_CONFIGS['default'])
        
        # Check cache first
        if self.cache_service:
            cached = await self._check_cache(url)
            if cached:
                logger.info(f"✅ Retrieved from cache: {url}")
                return cached
        
        driver = None
        try:
            # Create optimized undetected Chrome driver
            driver = await self._create_optimized_driver(config)
            
            # Perform bypass with retries
            content = await self._perform_bypass_with_retries(driver, url, config, options)
            
            if content:
                result = await self._process_content(content, url, driver)
                
                # Cache successful result
                if self.cache_service and result.get('success'):
                    await self._cache_result(url, result)
                
                self.success_count += 1
                duration = time.time() - start_time
                logger.info(f"🎉 Cloudflare bypass successful in {duration:.2f}s")
                
                return result
            else:
                raise Exception("Failed to bypass Cloudflare after all attempts")
                
        except Exception as e:
            self.failure_count += 1
            logger.error(f"❌ Cloudflare bypass failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'data': {
                    'metadata': {
                        'url': url,
                        'error': str(e),
                        'bypass_method': 'undetected_chrome'
                    }
                }
            }
        finally:
            if driver:
                await self._cleanup_driver(driver)
    
    async def _create_optimized_driver(self, config: Dict[str, Any]) -> uc.Chrome:
        """Create optimized undetected Chrome driver"""
        logger.info("🔧 Creating optimized undetected Chrome driver")
        
        # Optimized Chrome options for Vietnamese sites
        options = uc.ChromeOptions()
        
        # Essential options only (avoid compatibility issues)
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-extensions')
        options.add_argument('--no-first-run')
        options.add_argument('--disable-default-apps')
        options.add_argument('--disable-infobars')
        options.add_argument('--window-size=1920,1080')
        
        # Vietnamese locale support
        options.add_argument('--lang=vi-VN')
        options.add_experimental_option('prefs', {
            'intl.accept_languages': 'vi-VN,vi,en-US,en',
            'profile.default_content_setting_values.notifications': 2
        })
        
        # User agent for Vietnamese context
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"
        options.add_argument(f'--user-agent={user_agent}')
        
        try:
            # Create driver with specific Chrome version if configured
            if config.get('chrome_version'):
                driver = uc.Chrome(options=options, version_main=config['chrome_version'])
            else:
                driver = uc.Chrome(options=options)
            
            logger.info("✅ Undetected Chrome driver created successfully")
            return driver
            
        except Exception as e:
            logger.error(f"❌ Failed to create driver: {e}")
            raise
    
    async def _perform_bypass_with_retries(self, driver: uc.Chrome, url: str, config: Dict[str, Any], options: Dict[str, Any] = None) -> Optional[str]:
        """Perform Cloudflare bypass with intelligent retries"""
        
        max_attempts = config.get('retry_attempts', 2)
        
        for attempt in range(1, max_attempts + 1):
            logger.info(f"🔄 Bypass attempt {attempt}/{max_attempts}")
            
            try:
                # Navigate to URL
                logger.info(f"📍 Navigating to: {url}")
                driver.get(url)
                
                # Initial wait for page load
                time.sleep(5)
                
                # Check for Cloudflare challenge
                page_source = driver.page_source.lower()
                cloudflare_detected = any(indicator in page_source for indicator in config['cloudflare_indicators'])
                
                if cloudflare_detected:
                    logger.info("🛡️ Cloudflare challenge detected, waiting for bypass...")
                    
                    # Extended wait for Cloudflare bypass
                    total_wait = config['wait_time']
                    wait_interval = 5
                    
                    for i in range(0, total_wait, wait_interval):
                        time.sleep(wait_interval)
                        
                        # Check if bypass is complete
                        current_source = driver.page_source.lower()
                        if not any(indicator in current_source for indicator in config['cloudflare_indicators']):
                            logger.info(f"✅ Cloudflare bypass completed after {i + wait_interval}s")
                            break
                        
                        logger.info(f"⏳ Still waiting for bypass... ({i + wait_interval}s/{total_wait}s)")
                    
                    # Additional wait after bypass
                    time.sleep(config['final_wait'])
                
                # Simulate human behavior
                await self._simulate_human_behavior(driver, config)
                
                # Get final content
                final_content = driver.page_source
                
                # Verify content quality
                if self._verify_content_quality(final_content, url):
                    logger.info(f"✅ Quality content retrieved on attempt {attempt}")
                    return final_content
                else:
                    logger.warning(f"⚠️ Poor content quality on attempt {attempt}")
                    if attempt < max_attempts:
                        time.sleep(random.uniform(3, 7))  # Random delay before retry
                        continue
                
            except Exception as e:
                logger.error(f"❌ Attempt {attempt} failed: {str(e)}")
                if attempt < max_attempts:
                    time.sleep(random.uniform(5, 10))  # Longer delay on error
                    continue
                
        return None
    
    async def _simulate_human_behavior(self, driver: uc.Chrome, config: Dict[str, Any]):
        """Simulate realistic human browsing behavior"""
        try:
            # Scroll down slowly
            scroll_amount = config.get('scroll_amount', 500)
            scroll_wait = config.get('scroll_wait', 2)
            
            driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
            time.sleep(scroll_wait)
            
            # Random small scroll
            random_scroll = random.randint(100, 300)
            driver.execute_script(f"window.scrollBy(0, {random_scroll});")
            time.sleep(1)
            
            # Scroll back up slightly
            driver.execute_script(f"window.scrollBy(0, -{random_scroll // 2});")
            time.sleep(1)
            
        except Exception as e:
            logger.warning(f"⚠️ Human behavior simulation warning: {e}")
    
    def _verify_content_quality(self, content: str, url: str) -> bool:
        """Verify that the retrieved content is of good quality"""
        if not content or len(content) < 1000:
            return False
        
        # Check for Cloudflare indicators
        content_lower = content.lower()
        cloudflare_indicators = ['cloudflare', 'checking your browser', 'please wait']
        if any(indicator in content_lower for indicator in cloudflare_indicators):
            return False
        
        # Check for actual content indicators
        quality_indicators = ['<title>', '<body>', '<main>', '<article>', '<div']
        if not any(indicator in content_lower for indicator in quality_indicators):
            return False
        
        # Domain-specific quality checks
        if 'tuesy.net' in url:
            vietnamese_indicators = ['tuệ sỹ', 'bát quan', 'trai giới']
            if not any(indicator in content_lower for indicator in vietnamese_indicators):
                return False
        
        return True
    
    async def _process_content(self, content: str, url: str, driver: uc.Chrome) -> Dict[str, Any]:
        """Process and extract content from HTML"""
        logger.info("🔄 Processing extracted content")
        
        try:
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract metadata
            title = soup.find('title')
            title_text = title.get_text().strip() if title else ""
            
            description_meta = soup.find('meta', attrs={'name': 'description'}) or soup.find('meta', attrs={'property': 'og:description'})
            description = description_meta.get('content', '').strip() if description_meta else ""
            
            # Extract main content
            main_content = self._extract_main_content(soup)
            
            # Convert to markdown
            h = html2text.HTML2Text()
            h.ignore_links = False
            h.ignore_images = False
            h.body_width = 0
            markdown_content = h.handle(str(main_content))
            
            # Extract links
            links = [{'text': a.get_text().strip(), 'href': a.get('href')} 
                    for a in soup.find_all('a', href=True) if a.get_text().strip()]
            
            return {
                'success': True,
                'data': {
                    'markdown': markdown_content,
                    'html': str(main_content),
                    'metadata': {
                        'title': title_text,
                        'description': description,
                        'url': url,
                        'statusCode': 200,
                        'bypass_method': 'undetected_chrome',
                        'browser_type': 'undetected_chrome',
                        'timestamp': datetime.now().isoformat()
                    },
                    'links': links[:50]  # Limit to first 50 links
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Content processing error: {e}")
            return {
                'success': False,
                'error': f"Content processing failed: {str(e)}",
                'data': {
                    'metadata': {
                        'url': url,
                        'error': str(e)
                    }
                }
            }
    
    def _extract_main_content(self, soup: BeautifulSoup) -> BeautifulSoup:
        """Extract main content from page"""
        
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            element.decompose()
        
        # Try to find main content areas
        main_selectors = [
            'main', 'article', '.main-content', '#main-content',
            '.post-content', '.entry-content', '.content',
            '.container .row', 'body'
        ]
        
        for selector in main_selectors:
            if '.' in selector or '#' in selector:
                # CSS selector
                elements = soup.select(selector)
                if elements and len(str(elements[0])) > 500:
                    return elements[0]
            else:
                # Tag selector
                element = soup.find(selector)
                if element and len(str(element)) > 500:
                    return element
        
        return soup  # Fallback to entire soup
    
    async def _check_cache(self, url: str) -> Optional[Dict[str, Any]]:
        """Check if URL result is cached"""
        if not self.cache_service:
            return None
        
        try:
            cache_key = f"cloudflare_bypass:{url}"
            cached_data = await self.cache_service.get(cache_key)
            return cached_data
        except Exception as e:
            logger.warning(f"⚠️ Cache check error: {e}")
            return None
    
    async def _cache_result(self, url: str, result: Dict[str, Any]):
        """Cache successful result"""
        if not self.cache_service:
            return
        
        try:
            cache_key = f"cloudflare_bypass:{url}"
            # Cache for 1 hour
            await self.cache_service.set(cache_key, result, expire=3600)
            logger.info(f"💾 Result cached for: {url}")
        except Exception as e:
            logger.warning(f"⚠️ Cache save error: {e}")
    
    async def _cleanup_driver(self, driver: uc.Chrome):
        """Clean up driver resources"""
        try:
            driver.quit()
            logger.info("🧹 Driver cleaned up successfully")
        except Exception as e:
            logger.warning(f"⚠️ Driver cleanup warning: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get bypass statistics"""
        total = self.success_count + self.failure_count
        success_rate = (self.success_count / total * 100) if total > 0 else 0
        
        return {
            'total_attempts': total,
            'successful_bypasses': self.success_count,
            'failed_bypasses': self.failure_count,
            'success_rate': f"{success_rate:.1f}%"
        }