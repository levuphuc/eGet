# -*- coding: utf-8 -*-
"""
Enhanced Scraper Service with Undetected ChromeDriver Integration
Provides advanced Cloudflare bypass capabilities while maintaining API compatibility
"""

import sys
import asyncio
import time
import random
import base64
import json
from datetime import timedelta
from typing import Dict, Any, List, Optional, Set, Union
from functools import wraps
from concurrent.futures import ThreadPoolExecutor

# Core imports
from loguru import logger
import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    WebDriverException, TimeoutException, StaleElementReferenceException,
    NoSuchElementException, ElementNotInteractableException
)
from webdriver_manager.chrome import ChromeDriverManager

# Content processing
from bs4 import BeautifulSoup
import html2text

# Framework imports
from core.exceptions import BrowserError
from core.config import get_settings
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Service imports  
from services.cache import cache_service
from services.cache.cache_service import CacheService
from services.extractors.structured_data import StructuredDataExtractor

# Import existing components from the original scraper
from services.scraper.scraper import (
    ContentExtractor, USER_AGENTS, BOT_DETECTION_PATTERNS, 
    ENHANCED_STEALTH_JS, EnhancedBotDetectionHandler,
    # Metrics
    SCRAPE_REQUESTS, SCRAPE_ERRORS, SCRAPE_DURATION,
    BROWSER_POOL_SIZE, BROWSER_CREATION_TOTAL, BROWSER_REUSE_TOTAL,
    BROWSER_FAILURES, BROWSER_CLEANUP_TOTAL, BROWSER_MEMORY_USAGE,
    BROWSER_HEALTH_CHECK_DURATION, PAGE_LOAD_DURATION,
    NETWORK_IDLE_WAIT_DURATION, CLOUDFLARE_CHALLENGES,
    CLOUDFLARE_BYPASS_SUCCESS, CLOUDFLARE_BYPASS_FAILURE
)

settings = get_settings()

class EnhancedBrowserContext:
    """Enhanced browser context with undetected-chromedriver integration"""
    
    def __init__(self, browser: Union[uc.Chrome, webdriver.Chrome], config: Dict[str, Any], browser_type: str = "undetected"):
        logger.info(f"Initializing enhanced browser context with {browser_type} driver")
        self.browser = browser
        self.config = config
        self.browser_type = browser_type
        self.bot_detection_handler = EnhancedBotDetectionHandler()
        self.original_window = browser.current_window_handle
        self.user_agent = random.choice(USER_AGENTS)
        self._setup_browser()

    def _setup_browser(self):
        """Configure browser with advanced anti-detection measures"""
        logger.debug(f"Setting up {self.browser_type} browser with anti-detection")
        try:
            # Basic window setup
            self.browser.set_window_size(
                self.config.get('window_width', 1920),
                self.config.get('window_height', 1080)
            )
            
            if self.browser_type == "undetected":
                # Undetected ChromeDriver specific setup
                logger.info("Applying undetected-chromedriver optimizations")
                
                # Enhanced stealth mode for undetected driver
                self.browser.execute_cdp_cmd('Network.enable', {})
                self.browser.execute_cdp_cmd('Network.setBypassServiceWorker', {'bypass': True})
                self.browser.execute_cdp_cmd('Page.enable', {})
                
                # Advanced anti-detection script injection
                enhanced_undetected_script = f"""
                {ENHANCED_STEALTH_JS}
                
                // Additional undetected-chromedriver specific measures
                Object.defineProperty(navigator, 'webdriver', {{
                    get: () => false
                }});
                
                // Override chrome runtime to appear more legitimate
                if (!window.chrome) {{
                    window.chrome = {{}};
                }}
                window.chrome.runtime = {{
                    onConnect: null,
                    onMessage: null,
                    onConnectExternal: null,
                    onMessageExternal: null,
                    onInstalled: null,
                    onStartup: null,
                    onSuspend: null,
                    onSuspendCanceled: null,
                    onUpdateAvailable: null
                }};
                
                // Override the permissions API more thoroughly
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({{ state: 'denied' }}) :
                        originalQuery(parameters)
                );
                
                // Advanced memory fingerprint randomization
                Object.defineProperty(window.navigator, 'deviceMemory', {{
                    get: () => Math.pow(2, Math.floor(Math.random() * 3) + 2)
                }});
                
                // Randomize hardware concurrency
                Object.defineProperty(window.navigator, 'hardwareConcurrency', {{
                    get: () => Math.floor(Math.random() * 8) + 2
                }});
                """
                
                self.browser.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                    "source": enhanced_undetected_script
                })
                
                # Set realistic headers for undetected mode
                self.browser.execute_cdp_cmd('Network.setExtraHTTPHeaders', {
                    "headers": {
                        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                        "accept-language": "en-US,en;q=0.9",
                        "accept-encoding": "gzip, deflate, br",
                        "sec-ch-ua": '"Chromium";v="120", "Not_A Brand";v="8", "Google Chrome";v="120"',
                        "sec-ch-ua-mobile": "?0",
                        "sec-ch-ua-platform": '"Windows"',
                        "sec-fetch-dest": "document",
                        "sec-fetch-mode": "navigate",
                        "sec-fetch-site": "none",
                        "sec-fetch-user": "?1",
                        "upgrade-insecure-requests": "1",
                        "cache-control": "max-age=0",
                        "dnt": "1"
                    }
                })
            else:
                # Regular selenium setup with enhanced stealth
                self.browser.execute_cdp_cmd('Network.enable', {})
                self.browser.execute_cdp_cmd('Network.setBypassServiceWorker', {'bypass': True})
                self.browser.execute_cdp_cmd('Page.enable', {})
                
                self.browser.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                    "source": ENHANCED_STEALTH_JS
                })
                
                # Set user agent and platform
                platform = self._get_platform_from_user_agent(self.user_agent)
                self.browser.execute_cdp_cmd('Network.setUserAgentOverride', {
                    "userAgent": self.user_agent,
                    "platform": platform
                })
            
            logger.info(f"{self.browser_type.capitalize()} browser setup completed successfully")
            
        except Exception as e:
            logger.error(f"Failed to setup {self.browser_type} browser: {str(e)}")
            raise

    def _get_platform_from_user_agent(self, user_agent: str) -> str:
        """Extract platform from user agent string"""
        user_agent_lower = user_agent.lower()
        if 'windows' in user_agent_lower:
            return 'Windows'
        elif 'macintosh' in user_agent_lower or 'mac os x' in user_agent_lower:
            return 'Mac'
        elif 'linux' in user_agent_lower:
            return 'Linux'
        else:
            return 'Windows'  # Default fallback

    async def navigate(self, url: str, timeout: int = 30):
        """Enhanced navigation with advanced Cloudflare bypass techniques"""
        logger.info(f"Enhanced navigation to URL: {url} with {timeout}s timeout")
        start_time = time.time()
        
        try:
            # Set page load timeout
            self.browser.set_page_load_timeout(timeout)
            
            # Pre-navigation setup for better success rate
            if self.browser_type == "undetected":
                # Add random delay to mimic human behavior
                await asyncio.sleep(random.uniform(1, 3))
                
                # Execute pre-navigation JavaScript to prepare the environment
                pre_nav_script = """
                // Clear any existing detection artifacts
                delete window.navigator.__proto__.webdriver;
                delete window.webdriver;
                delete window._Selenium_IDE_Recorder;
                delete window._selenium;
                delete window.__selenium_unwrapped;
                delete window.__selenium_evaluate;
                delete window.__webdriver_evaluate;
                delete window.__driver_unwrapped;
                delete window.__webdriver_unwrapped;
                delete window.__driver_evaluate;
                delete window.__webdriver_script_function;
                delete window.__webdriver_script_func;
                delete window.__webdriver_script_fn;
                
                // Set realistic screen properties
                Object.defineProperty(screen, 'availHeight', { get: () => 1040 });
                Object.defineProperty(screen, 'availWidth', { get: () => 1920 });
                
                // Prepare for potential challenges
                window.challengeResolved = false;
                """
                
                try:
                    self.browser.execute_script(pre_nav_script)
                except:
                    pass  # Continue if script execution fails
            
            # Navigate to the URL
            logger.info(f"Navigating to {url}")
            self.browser.get(url)
            
            # Initial wait for page load
            await asyncio.sleep(random.uniform(2, 4))
            
            # Enhanced bot detection and challenge handling
            bot_detection = await self.bot_detection_handler.detect_bot_protection(self.browser)
            
            if bot_detection['detected']:
                logger.info(f"Detected {bot_detection['type']} protection with confidence {bot_detection['confidence']}")
                CLOUDFLARE_CHALLENGES.inc()
                
                # Apply specific handling based on detection
                if bot_detection['type'] == 'cloudflare':
                    success = await self._handle_cloudflare_challenge(timeout)
                else:
                    success = await self.bot_detection_handler.wait_for_challenge_completion(
                        self.browser, timeout=timeout
                    )
                
                if not success:
                    raise Exception(f"Failed to bypass {bot_detection['type']} challenge")
                
                CLOUDFLARE_BYPASS_SUCCESS.inc()
            
            # Wait for network idle and page stability
            await self._wait_for_page_stability()
            
            elapsed = time.time() - start_time
            logger.info(f"Enhanced navigation completed in {elapsed:.2f}s")
            
        except TimeoutException:
            logger.warning(f"Navigation timeout for {url}, attempting recovery")
            try:
                # Stop page loading and try to continue
                self.browser.execute_script("window.stop();")
                await asyncio.sleep(2)
                
                # Check if we got a partial page that might be workable
                current_url = self.browser.current_url
                if current_url and current_url != "about:blank":
                    logger.info("Partial page load detected, attempting to continue")
                    # Check for protection systems on partial page
                    bot_detection = await self.bot_detection_handler.detect_bot_protection(self.browser)
                    if bot_detection['detected']:
                        await self._handle_cloudflare_challenge(timeout // 2)
                else:
                    raise TimeoutException(f"Complete navigation failure for {url}")
                    
            except Exception as recovery_error:
                logger.error(f"Navigation recovery failed: {str(recovery_error)}")
                raise
        
        except Exception as e:
            logger.error(f"Enhanced navigation failed: {str(e)}")
            raise

    async def _handle_cloudflare_challenge(self, timeout: int = 35) -> bool:
        """Advanced Cloudflare challenge handling with proven techniques"""
        logger.info("Applying advanced Cloudflare bypass techniques")
        
        try:
            # Wait for the challenge to fully load
            await asyncio.sleep(random.uniform(3, 5))
            
            # Check for different types of Cloudflare challenges
            challenge_types = [
                # New Turnstile challenges
                (".cf-turnstile", "turnstile"),
                ("iframe[src*='cloudflare.com']", "iframe_turnstile"),
                # Traditional challenges
                ("#challenge-form", "traditional"),
                (".cf-browser-verification", "verification"),
                ("#cf-challenge-running", "running"),
                (".cf-checking-browser", "checking")
            ]
            
            challenge_found = False
            challenge_type = None
            
            for selector, c_type in challenge_types:
                try:
                    element = self.browser.find_element(By.CSS_SELECTOR, selector)
                    if element and element.is_displayed():
                        challenge_found = True
                        challenge_type = c_type
                        logger.info(f"Found {c_type} challenge: {selector}")
                        break
                except:
                    continue
            
            if not challenge_found:
                logger.info("No visible challenge elements found, waiting for automatic resolution")
                await asyncio.sleep(5)
                return True
            
            # Handle different challenge types
            if challenge_type in ["turnstile", "iframe_turnstile"]:
                return await self._handle_turnstile_challenge(timeout)
            else:
                return await self._handle_traditional_challenge(timeout)
                
        except Exception as e:
            logger.error(f"Error in Cloudflare challenge handling: {str(e)}")
            return False

    async def _handle_turnstile_challenge(self, timeout: int) -> bool:
        """Handle Cloudflare Turnstile challenges"""
        logger.info("Handling Turnstile challenge")
        
        try:
            # Look for Turnstile iframe
            iframe_selectors = [
                "iframe[src*='cloudflare.com']",
                "iframe[src*='challenges.cloudflare.com']",
                ".cf-turnstile iframe"
            ]
            
            for iframe_selector in iframe_selectors:
                try:
                    iframe = WebDriverWait(self.browser, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, iframe_selector))
                    )
                    
                    if iframe.is_displayed():
                        logger.info(f"Found Turnstile iframe: {iframe_selector}")
                        
                        # Switch to iframe
                        self.browser.switch_to.frame(iframe)
                        
                        # Look for checkbox in iframe
                        checkbox_selectors = [
                            "input[type='checkbox']",
                            ".checkbox",
                            "[role='checkbox']",
                            ".cb-i"
                        ]
                        
                        for checkbox_selector in checkbox_selectors:
                            try:
                                checkbox = WebDriverWait(self.browser, 5).until(
                                    EC.element_to_be_clickable((By.CSS_SELECTOR, checkbox_selector))
                                )
                                
                                if checkbox.is_displayed() and checkbox.is_enabled():
                                    # Human-like interaction
                                    await asyncio.sleep(random.uniform(2, 4))
                                    self.browser.execute_script("arguments[0].click();", checkbox)
                                    logger.info("Clicked Turnstile checkbox")
                                    break
                            except:
                                continue
                        
                        # Switch back to default content
                        self.browser.switch_to.default_content()
                        break
                        
                except:
                    continue
            
            # Wait for challenge completion with the proven 35-second technique
            logger.info("Waiting for Turnstile challenge completion (up to 35 seconds)")
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                # Check if challenge is resolved
                current_url = self.browser.current_url
                page_source = self.browser.page_source.lower()
                
                # Success indicators
                if not any(indicator in page_source for indicator in [
                    'cloudflare', 'challenge', 'checking your browser', 'just a moment'
                ]):
                    logger.info("Turnstile challenge appears to be resolved")
                    return True
                
                # Wait before next check
                await asyncio.sleep(2)
            
            # Final verification
            await asyncio.sleep(3)
            detection = await self.bot_detection_handler.detect_bot_protection(self.browser)
            return not detection['detected']
            
        except Exception as e:
            logger.error(f"Error handling Turnstile challenge: {str(e)}")
            return False

    async def _handle_traditional_challenge(self, timeout: int) -> bool:
        """Handle traditional Cloudflare challenges"""
        logger.info("Handling traditional Cloudflare challenge")
        
        try:
            # Wait for challenge form to be ready
            await asyncio.sleep(random.uniform(3, 5))
            
            # Look for challenge elements
            challenge_selectors = [
                "#challenge-form input[type='submit']",
                "#challenge-form button",
                ".cf-browser-verification input",
                ".cf-browser-verification button",
                "input[name='jschl-answer']"
            ]
            
            for selector in challenge_selectors:
                try:
                    element = WebDriverWait(self.browser, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    
                    if element.is_displayed():
                        logger.info(f"Found challenge element: {selector}")
                        
                        # Wait before interacting (human-like behavior)
                        await asyncio.sleep(random.uniform(2, 4))
                        
                        if element.tag_name.lower() == 'input' and element.get_attribute('type') == 'submit':
                            element.click()
                        elif element.tag_name.lower() == 'button':
                            element.click()
                        
                        logger.info("Submitted challenge form")
                        break
                        
                except:
                    continue
            
            # Wait for resolution with progressive checking
            return await self._wait_for_challenge_resolution(timeout)
            
        except Exception as e:
            logger.error(f"Error handling traditional challenge: {str(e)}")
            return False

    async def _wait_for_challenge_resolution(self, timeout: int) -> bool:
        """Wait for challenge resolution with smart detection"""
        logger.info(f"Waiting for challenge resolution (timeout: {timeout}s)")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # Check multiple indicators of success
                current_url = self.browser.current_url
                page_source = self.browser.page_source.lower()
                title = self.browser.title.lower()
                
                # Success indicators
                success_indicators = [
                    'challenge' not in page_source,
                    'cloudflare' not in title,
                    'just a moment' not in page_source,
                    'checking your browser' not in page_source,
                    len(page_source) > 10000  # Substantial page content
                ]
                
                if sum(success_indicators) >= 3:
                    logger.info("Challenge resolution detected")
                    await asyncio.sleep(2)  # Brief stabilization wait
                    return True
                
                # Progressive waiting
                wait_time = min(2 + (time.time() - start_time) / 10, 5)
                await asyncio.sleep(wait_time)
                
            except Exception as e:
                logger.warning(f"Error during challenge resolution check: {str(e)}")
                await asyncio.sleep(2)
        
        logger.warning(f"Challenge resolution timeout after {timeout}s")
        return False

    async def _wait_for_page_stability(self):
        """Wait for page stability with enhanced detection"""
        logger.debug("Waiting for page stability")
        
        try:
            # Wait for document ready state
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: WebDriverWait(self.browser, 10).until(
                    lambda driver: driver.execute_script("return document.readyState") == "complete"
                )
            )
            
            # Additional stability checks
            stability_script = """
            return new Promise((resolve) => {
                let checks = 0;
                let maxChecks = 20;
                
                const checkStability = () => {
                    checks++;
                    
                    // Check if page is still loading
                    if (document.readyState !== 'complete') {
                        if (checks < maxChecks) {
                            setTimeout(checkStability, 250);
                        } else {
                            resolve({stable: false, reason: 'readyState'});
                        }
                        return;
                    }
                    
                    // Check for ongoing requests
                    if (performance.getEntriesByType('navigation').length > 0) {
                        const nav = performance.getEntriesByType('navigation')[0];
                        if (nav.loadEventEnd === 0 && checks < maxChecks) {
                            setTimeout(checkStability, 250);
                            return;
                        }
                    }
                    
                    resolve({stable: true, checks: checks});
                };
                
                checkStability();
            });
            """
            
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.browser.execute_script(stability_script)
            )
            
            if result.get('stable'):
                logger.debug(f"Page stability confirmed after {result.get('checks', 0)} checks")
            else:
                logger.warning(f"Page stability check failed: {result.get('reason', 'unknown')}")
            
        except Exception as e:
            logger.warning(f"Page stability check error: {str(e)}")
        
        # Final brief wait
        await asyncio.sleep(1)

    async def get_page_source(self) -> str:
        """Get page source with enhanced error handling"""
        logger.debug("Getting page source")
        
        for attempt in range(3):
            try:
                source = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.browser.page_source
                )
                
                if len(source) < 100:
                    logger.warning(f"Suspiciously short page source ({len(source)} chars) on attempt {attempt + 1}")
                    if attempt < 2:
                        await asyncio.sleep(1)
                        continue
                
                logger.debug(f"Page source retrieved: {len(source)} characters")
                return source
                
            except Exception as e:
                logger.warning(f"Page source retrieval attempt {attempt + 1} failed: {str(e)}")
                if attempt == 2:
                    raise
                await asyncio.sleep(0.5)

    async def take_screenshot(self) -> Optional[str]:
        """Take screenshot with enhanced error handling"""
        logger.debug("Taking screenshot")
        try:
            screenshot = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.browser.get_screenshot_as_png()
            )
            encoded = base64.b64encode(screenshot).decode('utf-8')
            logger.debug(f"Screenshot captured: {len(encoded)} bytes")
            return encoded
        except Exception as e:
            logger.error(f"Screenshot failed: {str(e)}")
            return None

    async def cleanup(self):
        """Enhanced cleanup with better resource management"""
        logger.debug(f"Cleaning up {self.browser_type} browser context")
        try:
            # Clear cookies and storage
            self.browser.delete_all_cookies()
            self.browser.execute_script("window.localStorage.clear();")
            self.browser.execute_script("window.sessionStorage.clear();")
            
            # Navigate to blank page
            self.browser.get("about:blank")
            
            logger.info(f"{self.browser_type.capitalize()} browser context cleanup completed")
        except Exception as e:
            logger.warning(f"Cleanup error: {str(e)}")


class EnhancedBrowserPool:
    """Enhanced browser pool supporting both undetected and regular Chrome drivers"""
    
    def __init__(self, max_browsers: int = 8):
        self.max_browsers = max_browsers
        self.available_undetected: List[uc.Chrome] = []
        self.available_regular: List[webdriver.Chrome] = []
        self.active_browsers: Set[Union[uc.Chrome, webdriver.Chrome]] = set()
        self.lock = asyncio.Lock()
        self.browser_metrics = {
            'created_undetected': 0,
            'created_regular': 0,
            'reused_undetected': 0,
            'reused_regular': 0,
            'failed': 0,
            'current_active': 0
        }
        # Cache services for faster creation
        self._cached_service = None
        self._uc_version = 120  # Use stable Chrome version for undetected

    def _create_undetected_browser_options(self) -> uc.ChromeOptions:
        """Create optimized options for undetected ChromeDriver"""
        options = uc.ChromeOptions()
        
        # Core undetected settings
        options.add_argument('--no-first-run')
        options.add_argument('--no-service-autorun') 
        options.add_argument('--password-store=basic')
        options.add_argument('--disable-blink-features=AutomationControlled')
        
        # Performance optimizations
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-plugins')
        
        # Anti-detection measures
        options.add_argument('--disable-web-security')
        options.add_argument('--disable-features=VizDisplayCompositor')
        options.add_argument('--disable-background-networking')
        options.add_argument('--disable-background-timer-throttling')
        options.add_argument('--disable-renderer-backgrounding')
        options.add_argument('--disable-backgrounding-occluded-windows')
        
        # Window settings
        options.add_argument('--window-size=1920,1080')
        
        # Prefs for better compatibility
        prefs = {
            "profile.default_content_setting_values": {
                "notifications": 2,
                "geolocation": 2,
                "media_stream": 2,
                "plugins": 2,
                "popups": 2,
                "javascript": 1,
                "images": 1
            },
            "profile.managed_default_content_settings": {"images": 1}
        }
        options.add_experimental_option("prefs", prefs)
        
        # Additional anti-detection
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option('useAutomationExtension', False)
        
        return options

    def _create_regular_browser_options(self) -> Options:
        """Create options for regular ChromeDriver with enhanced stealth"""
        options = Options()
        
        # Stealth mode
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option('useAutomationExtension', False)
        
        # Performance settings
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        
        # Window settings
        options.add_argument('--window-size=1920,1080')
        
        # Content settings
        prefs = {
            "profile.default_content_setting_values": {
                "notifications": 2,
                "geolocation": 2,
                "media_stream": 2,
                "plugins": 2,
                "popups": 2,
                "javascript": 1,
                "images": 1
            }
        }
        options.add_experimental_option("prefs", prefs)
        
        return options

    async def get_browser(self, prefer_undetected: bool = True) -> EnhancedBrowserContext:
        """Get a browser with preference for undetected ChromeDriver"""
        logger.info(f"Requesting browser (prefer_undetected: {prefer_undetected})")
        
        async with self.lock:
            try:
                # Try to get preferred browser type first
                if prefer_undetected and self.available_undetected:
                    browser = self.available_undetected.pop()
                    if await self._is_browser_healthy(browser):
                        self.active_browsers.add(browser)
                        self.browser_metrics['reused_undetected'] += 1
                        logger.info(f"Reusing undetected browser {id(browser)}")
                        return EnhancedBrowserContext(browser, self._get_browser_config(), "undetected")
                    else:
                        await self._safely_quit_browser(browser)
                
                # Try alternative browser type
                if not prefer_undetected and self.available_regular:
                    browser = self.available_regular.pop()
                    if await self._is_browser_healthy(browser):
                        self.active_browsers.add(browser)
                        self.browser_metrics['reused_regular'] += 1
                        logger.info(f"Reusing regular browser {id(browser)}")
                        return EnhancedBrowserContext(browser, self._get_browser_config(), "regular")
                    else:
                        await self._safely_quit_browser(browser)
                
                # Create new browser if under limit
                if len(self.active_browsers) < self.max_browsers:
                    if prefer_undetected:
                        browser = await self._create_undetected_browser()
                        browser_type = "undetected"
                    else:
                        browser = await self._create_regular_browser()
                        browser_type = "regular"
                    
                    self.active_browsers.add(browser)
                    logger.info(f"Created new {browser_type} browser {id(browser)}")
                    return EnhancedBrowserContext(browser, self._get_browser_config(), browser_type)
                else:
                    raise BrowserError(f"Max browsers ({self.max_browsers}) reached")
                    
            except Exception as e:
                logger.error(f"Browser pool error: {str(e)}")
                self.browser_metrics['failed'] += 1
                raise

    async def _create_undetected_browser(self) -> uc.Chrome:
        """Create new undetected ChromeDriver instance"""
        logger.info("Creating undetected ChromeDriver instance")
        
        try:
            options = self._create_undetected_browser_options()
            
            # Create undetected Chrome instance with version control
            browser = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: uc.Chrome(
                    options=options,
                    version_main=self._uc_version,
                    driver_executable_path=None,
                    browser_executable_path=None,
                    user_data_dir=None,
                    headless=False,
                    use_subprocess=True,
                    debug=False
                )
            )
            
            self.browser_metrics['created_undetected'] += 1
            BROWSER_CREATION_TOTAL.inc()
            logger.info("Undetected ChromeDriver created successfully")
            return browser
            
        except Exception as e:
            logger.error(f"Failed to create undetected browser: {str(e)}")
            self.browser_metrics['failed'] += 1
            BROWSER_FAILURES.inc()
            raise

    async def _create_regular_browser(self) -> webdriver.Chrome:
        """Create new regular ChromeDriver instance"""
        logger.info("Creating regular ChromeDriver instance")
        
        try:
            options = self._create_regular_browser_options()
            
            # Use cached service for faster creation
            if not self._cached_service:
                self._cached_service = Service(ChromeDriverManager().install())
            
            browser = webdriver.Chrome(service=self._cached_service, options=options)
            
            self.browser_metrics['created_regular'] += 1
            BROWSER_CREATION_TOTAL.inc()
            logger.info("Regular ChromeDriver created successfully")
            return browser
            
        except Exception as e:
            logger.error(f"Failed to create regular browser: {str(e)}")
            self.browser_metrics['failed'] += 1
            BROWSER_FAILURES.inc()
            raise

    def _get_browser_config(self) -> Dict[str, Any]:
        """Get browser configuration"""
        return {
            'window_width': 1920,
            'window_height': 1080,
            'timeout': 30
        }

    async def _is_browser_healthy(self, browser: Union[uc.Chrome, webdriver.Chrome]) -> bool:
        """Check if browser is healthy and responsive"""
        try:
            # Quick health check
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: browser.current_url
            )
            return True
        except Exception:
            return False

    async def release_browser(self, context: EnhancedBrowserContext):
        """Release browser back to pool"""
        if not context:
            return
        
        async with self.lock:
            browser = context.browser
            browser_id = id(browser)
            logger.info(f"Releasing {context.browser_type} browser {browser_id}")
            
            try:
                await context.cleanup()
                
                if browser in self.active_browsers:
                    self.active_browsers.remove(browser)
                    
                    # Return to appropriate pool if healthy and pool not full
                    max_per_type = self.max_browsers // 2
                    
                    if context.browser_type == "undetected":
                        if len(self.available_undetected) < max_per_type:
                            if await self._is_browser_healthy(browser):
                                self.available_undetected.append(browser)
                                logger.info(f"Undetected browser {browser_id} returned to pool")
                                return
                    else:
                        if len(self.available_regular) < max_per_type:
                            if await self._is_browser_healthy(browser):
                                self.available_regular.append(browser)
                                logger.info(f"Regular browser {browser_id} returned to pool")
                                return
                
                # Close browser if not returned to pool
                await self._safely_quit_browser(browser)
                
            except Exception as e:
                logger.error(f"Error releasing browser {browser_id}: {str(e)}")
                await self._safely_quit_browser(browser)

    async def _safely_quit_browser(self, browser: Union[uc.Chrome, webdriver.Chrome]):
        """Safely quit browser"""
        browser_id = id(browser)
        try:
            await asyncio.get_event_loop().run_in_executor(None, browser.quit)
            logger.info(f"Browser {browser_id} quit successfully")
        except Exception as e:
            logger.warning(f"Error quitting browser {browser_id}: {str(e)}")

    async def cleanup(self):
        """Cleanup all browsers in pool"""
        async with self.lock:
            logger.info("Starting enhanced browser pool cleanup")
            
            all_browsers = (list(self.active_browsers) + 
                           self.available_undetected + 
                           self.available_regular)
            
            if all_browsers:
                quit_tasks = [self._safely_quit_browser(browser) for browser in all_browsers]
                await asyncio.gather(*quit_tasks, return_exceptions=True)
            
            self.available_undetected.clear()
            self.available_regular.clear()
            self.active_browsers.clear()
            
            logger.info("Enhanced browser pool cleanup completed")

    def get_metrics(self) -> Dict[str, Any]:
        """Get pool metrics"""
        return {
            **self.browser_metrics,
            'available_undetected': len(self.available_undetected),
            'available_regular': len(self.available_regular),
            'active_count': len(self.active_browsers)
        }


class EnhancedWebScraper:
    """Enhanced web scraper with undetected ChromeDriver integration"""
    
    def __init__(self, max_concurrent: int = 8):
        self.browser_pool = EnhancedBrowserPool(max_browsers=max_concurrent)
        self.content_extractor = ContentExtractor()
        self.structured_data_extractor = StructuredDataExtractor()
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.cache_service = None
    
    @classmethod
    async def create(cls, max_concurrent: int = 8, cache_service: Optional[CacheService] = None) -> 'EnhancedWebScraper':
        """Factory method for creating enhanced scraper"""
        instance = cls(max_concurrent=max_concurrent)
        instance.cache_service = cache_service
        if instance.cache_service:
            await instance.cache_service.connect()
        return instance
    
    async def scrape(self, url: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced scraping with intelligent browser selection"""
        SCRAPE_REQUESTS.inc()
        
        try:
            # Check cache first
            if self.cache_service and not options.get('bypass_cache'):
                cached_result = await self.cache_service.get_cached_result(url, options)
                if cached_result:
                    return {
                        'success': True,
                        'data': cached_result,
                        'cached': True
                    }
            
            async with self.semaphore:
                try:
                    with SCRAPE_DURATION.time():
                        # Intelligent browser selection based on URL characteristics
                        prefer_undetected = self._should_use_undetected(url, options)
                        
                        page_data = await self._get_page_content_enhanced(
                            url, options, prefer_undetected
                        )
                        processed_data = await self._process_page_data(page_data, options, url)
                        
                        # Cache result if enabled
                        if self.cache_service and not options.get('bypass_cache'):
                            cache_ttl = options.get('cache_ttl', getattr(settings, 'CACHE_TTL', 86400))
                            await self.cache_service.cache_result(
                                url, options, processed_data,
                                ttl=timedelta(seconds=cache_ttl)
                            )
                        
                        return {
                            'success': True,
                            'data': processed_data,
                            'cached': False
                        }
                        
                except Exception as e:
                    SCRAPE_ERRORS.inc()
                    logger.error(f"Enhanced scraping error for {url}: {str(e)}")
                    return self._create_error_response(url, str(e))
                    
        except Exception as e:
            logger.error(f"Unexpected error in enhanced scrape: {str(e)}")
            SCRAPE_ERRORS.inc()
            raise

    def _should_use_undetected(self, url: str, options: Dict[str, Any]) -> bool:
        """Determine if undetected ChromeDriver should be used"""
        # Force undetected for known Cloudflare-protected domains
        cloudflare_indicators = [
            'cloudflare',
            'cf-ray',
            'ddos-guard',
            'incapsula'
        ]
        
        # Check URL for known protection indicators
        url_lower = url.lower()
        if any(indicator in url_lower for indicator in cloudflare_indicators):
            return True
        
        # Check options for stealth mode request
        if options.get('stealth', False):
            return True
            
        # Check for explicit undetected request
        if options.get('use_undetected', False):
            return True
        
        # Default to undetected for better success rate
        return options.get('prefer_undetected', True)

    async def _get_page_content_enhanced(self, url: str, options: Dict[str, Any], 
                                       prefer_undetected: bool = True) -> Dict[str, Any]:
        """Enhanced page content retrieval with failover strategy"""
        primary_error = None
        
        try:
            # Primary attempt with preferred browser type
            return await self._attempt_scrape(url, options, prefer_undetected)
            
        except Exception as e:
            primary_error = e
            logger.warning(f"Primary scrape attempt failed: {str(e)}")
            
            # Fallback attempt with alternative browser type
            try:
                logger.info("Attempting fallback with alternative browser type")
                return await self._attempt_scrape(url, options, not prefer_undetected)
                
            except Exception as fallback_error:
                logger.error(f"Fallback attempt also failed: {str(fallback_error)}")
                # Raise the original error for better debugging
                raise primary_error

    async def _attempt_scrape(self, url: str, options: Dict[str, Any], 
                            use_undetected: bool) -> Dict[str, Any]:
        """Attempt to scrape with specified browser type"""
        context = await self.browser_pool.get_browser(prefer_undetected=use_undetected)
        
        try:
            # Enhanced navigation with longer timeout for Cloudflare
            timeout = options.get('timeout', 35)  # Use proven 35s timeout
            await context.navigate(url, timeout=timeout)
            
            # Wait for specific selector if requested
            if options.get('wait_for_selector'):
                try:
                    WebDriverWait(context.browser, timeout).until(
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR, options['wait_for_selector'])
                        )
                    )
                except TimeoutException:
                    logger.warning(f"Selector wait timeout: {options['wait_for_selector']}")
            
            # Additional wait time if specified (for Cloudflare)
            wait_time = options.get('waitFor', 0)
            if wait_time > 0:
                logger.info(f"Additional wait time: {wait_time}ms")
                await asyncio.sleep(wait_time / 1000)
            
            # Execute custom actions if provided
            if options.get('actions'):
                await self._execute_actions(context, options['actions'])
            
            # Get page content
            page_source = await context.get_page_source()
            
            # Take screenshot if requested
            screenshot = None
            if options.get('include_screenshot'):
                screenshot = await context.take_screenshot()
            
            # Extract links
            links = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: context.browser.execute_script("""
                    return Array.from(document.getElementsByTagName('a')).map(a => ({
                        href: a.href,
                        text: a.textContent.trim(),
                        rel: a.rel
                    }));
                """)
            )
            
            return {
                'content': page_source,
                'raw_content': page_source if options.get('include_raw_html') else None,
                'status': 200,
                'screenshot': screenshot,
                'links': links,
                'headers': {},
                'browser_type': context.browser_type
            }
            
        finally:
            await self.browser_pool.release_browser(context)

    async def _execute_actions(self, context: EnhancedBrowserContext, actions: List[Dict[str, Any]]):
        """Execute custom actions on the page"""
        for action in actions:
            try:
                action_type = action.get('type')
                
                if action_type == 'wait':
                    wait_time = action.get('milliseconds', 1000) / 1000
                    await asyncio.sleep(wait_time)
                
                elif action_type == 'scroll':
                    direction = action.get('direction', 'down')
                    amount = action.get('amount', 500)
                    
                    if direction == 'down':
                        context.browser.execute_script(f"window.scrollBy(0, {amount});")
                    elif direction == 'up':
                        context.browser.execute_script(f"window.scrollBy(0, -{amount});")
                    
                    # Wait after scroll
                    scroll_wait = action.get('milliseconds', 1000) / 1000
                    await asyncio.sleep(scroll_wait)
                
                elif action_type == 'click':
                    selector = action.get('selector')
                    if selector:
                        element = WebDriverWait(context.browser, 10).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                        element.click()
                        
                        # Wait after click
                        click_wait = action.get('milliseconds', 500) / 1000
                        await asyncio.sleep(click_wait)
                
            except Exception as e:
                logger.warning(f"Action execution failed: {action_type} - {str(e)}")

    async def _process_page_data(self, page_data: Dict[str, Any], 
                               options: Dict[str, Any], url: str) -> Dict[str, Any]:
        """Process page data with enhanced content extraction"""
        try:
            # Extract content
            content_task = self.content_extractor.extract_content(
                page_data['content'],
                options.get('only_main', True)
            )
            
            # Extract structured data
            structured_data_task = asyncio.get_event_loop().run_in_executor(
                None,
                self.structured_data_extractor.extract_all,
                page_data['content']
            )
            
            # Wait for both tasks
            processed_content, structured_data = await asyncio.gather(
                content_task,
                structured_data_task
            )
            
            # Build metadata
            metadata = {
                'title': None,
                'description': None,
                'language': None,
                'sourceURL': url,
                'statusCode': page_data['status'],
                'error': None,
                'browser_type': page_data.get('browser_type', 'unknown')
            }
            
            if processed_content.get('metadata'):
                metadata.update(processed_content['metadata'])
            
            # Format links
            formatted_links = None
            if page_data.get('links'):
                formatted_links = [
                    link['href'] for link in page_data['links']
                    if link.get('href') and link['href'].startswith('http')
                ]
            
            return {
                'markdown': processed_content['markdown'],
                'html': processed_content['html'],
                'rawHtml': page_data['raw_content'],
                'screenshot': None,
                'links': formatted_links,
                'actions': ({'screenshots': [page_data['screenshot']]} 
                          if page_data.get('screenshot') else None),
                'metadata': metadata,
                'llm_extraction': None,
                'warning': None,
                'structured_data': structured_data
            }
            
        except Exception as e:
            logger.error(f"Enhanced data processing error: {str(e)}")
            raise

    def _create_error_response(self, url: str, error_msg: str) -> Dict[str, Any]:
        """Create standardized error response"""
        return {
            'success': False,
            'data': {
                'markdown': None,
                'html': None,
                'rawHtml': None,
                'screenshot': None,
                'links': None,
                'actions': None,
                'metadata': {
                    'title': None,
                    'description': None,
                    'language': None,
                    'sourceURL': url,
                    'statusCode': 500,
                    'error': error_msg
                },
                'llm_extraction': None,
                'warning': error_msg,
                'structured_data': None
            }
        }

    async def cleanup(self):
        """Cleanup all resources"""
        await self.browser_pool.cleanup()
        if self.cache_service:
            await self.cache_service.disconnect()

    def get_metrics(self) -> Dict[str, Any]:
        """Get scraper metrics"""
        return {
            'pool_metrics': self.browser_pool.get_metrics(),
            'active_browsers': len(self.browser_pool.active_browsers),
            'semaphore_value': self.semaphore._value
        }


# Maintain backward compatibility with existing API
WebScraper = EnhancedWebScraper  # Alias for drop-in replacement

# Export main classes for external use
__all__ = [
    'EnhancedWebScraper',
    'EnhancedBrowserPool', 
    'EnhancedBrowserContext',
    'WebScraper'  # Backward compatibility
]