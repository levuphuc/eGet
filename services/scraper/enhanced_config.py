# -*- coding: utf-8 -*-
"""
Enhanced Scraper Configuration
Provides configuration settings and utilities for the enhanced scraper service
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

class BrowserStrategy(Enum):
    """Browser strategy enumeration"""
    UNDETECTED_ONLY = "undetected_only"
    REGULAR_ONLY = "regular_only" 
    SMART_FALLBACK = "smart_fallback"
    UNDETECTED_PREFERRED = "undetected_preferred"
    REGULAR_PREFERRED = "regular_preferred"

@dataclass
class CloudflareConfig:
    """Cloudflare bypass configuration"""
    wait_time: int = 35  # Proven 35-second wait time
    max_retries: int = 3
    challenge_timeout: int = 60
    use_version_139: bool = True  # Use Chrome version 139 for better bypass
    enable_stealth_mode: bool = True
    human_behavior_simulation: bool = True

@dataclass
class BrowserPoolConfig:
    """Browser pool configuration"""
    max_browsers: int = 8
    max_undetected: int = 4
    max_regular: int = 4
    browser_timeout: int = 300  # 5 minutes
    health_check_interval: int = 60  # 1 minute
    cleanup_interval: int = 600  # 10 minutes

@dataclass
class ScrapingConfig:
    """General scraping configuration"""
    default_timeout: int = 35  # Match successful bypass timeout
    max_concurrent: int = 8
    default_wait_for: int = 5000  # milliseconds
    enable_screenshots: bool = False
    enable_caching: bool = True
    cache_ttl: int = 86400  # 24 hours
    retry_attempts: int = 2

class EnhancedScraperSettings:
    """Enhanced scraper settings and configuration"""
    
    def __init__(self):
        self.cloudflare = CloudflareConfig()
        self.browser_pool = BrowserPoolConfig()
        self.scraping = ScrapingConfig()
        
        # Known Cloudflare-protected domains (add more as needed)
        self.cloudflare_domains = [
            'cloudflare.com',
            'tuesy.net',  # From test.py
            'discord.com',
            'reddit.com',
            'coinbase.com',
            'binance.com',
            'medium.com'
        ]
        
        # Domains that work better with regular selenium
        self.regular_domains = [
            'google.com',
            'wikipedia.org',
            'github.com',
            'stackoverflow.com',
            'docs.python.org',
            'httpbin.org'
        ]
        
        # User agents optimized for undetected mode
        self.undetected_user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36", 
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
    
    def should_use_undetected(self, url: str, options: Dict[str, Any]) -> bool:
        """Determine if undetected ChromeDriver should be used for a URL"""
        # Explicit option override
        if 'use_undetected' in options:
            return options['use_undetected']
        
        # Check for stealth mode request
        if options.get('stealth', False):
            return True
            
        # Check against known Cloudflare domains
        for domain in self.cloudflare_domains:
            if domain in url.lower():
                return True
        
        # Check against regular domains
        for domain in self.regular_domains:
            if domain in url.lower():
                return False
        
        # Default strategy - prefer regular scraper unless explicitly requested
        return options.get('prefer_undetected', False)
    
    def get_browser_strategy(self, url: str, options: Dict[str, Any]) -> BrowserStrategy:
        """Get the optimal browser strategy for a URL"""
        # Check explicit strategy in options
        strategy_name = options.get('browser_strategy')
        if strategy_name:
            try:
                return BrowserStrategy(strategy_name)
            except ValueError:
                pass
        
        # Automatic strategy selection
        if self.should_use_undetected(url, options):
            return BrowserStrategy.UNDETECTED_PREFERRED
        else:
            return BrowserStrategy.SMART_FALLBACK
    
    def get_optimal_timeout(self, url: str, options: Dict[str, Any]) -> int:
        """Get optimal timeout for a URL"""
        # Check for Cloudflare domains - use proven 35s timeout
        for domain in self.cloudflare_domains:
            if domain in url.lower():
                return max(self.cloudflare.wait_time, options.get('timeout', 35))
        
        # Regular timeout for other domains
        return options.get('timeout', self.scraping.default_timeout)
    
    def get_enhanced_options(self, url: str, base_options: Dict[str, Any]) -> Dict[str, Any]:
        """Get enhanced scraping options for a URL"""
        enhanced = base_options.copy()
        
        # Apply optimal timeout
        enhanced['timeout'] = self.get_optimal_timeout(url, base_options)
        
        # Apply browser strategy
        enhanced['browser_strategy'] = self.get_browser_strategy(url, base_options).value
        
        # Apply Cloudflare-specific settings
        if self.should_use_undetected(url, base_options):
            enhanced.update({
                'use_undetected': True,
                'stealth': True,
                'human_behavior': True,
                'challenge_timeout': self.cloudflare.challenge_timeout,
                'wait_for_stability': True
            })
            
            # Add proven actions for Cloudflare bypass
            if 'actions' not in enhanced:
                enhanced['actions'] = []
            
            # Add stability actions
            stability_actions = [
                {"type": "wait", "selector": "body", "milliseconds": 3000},
                {"type": "scroll", "selector": "body", "direction": "down", "amount": 100, "milliseconds": 1000},
                {"type": "wait", "selector": "body", "milliseconds": 2000}
            ]
            enhanced['actions'].extend(stability_actions)
        
        return enhanced
    
    def get_headers_for_domain(self, url: str) -> Dict[str, str]:
        """Get optimized headers for a domain"""
        base_headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Cache-Control": "no-cache",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate", 
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1"
        }
        
        # Add domain-specific headers
        if any(domain in url.lower() for domain in self.cloudflare_domains):
            base_headers.update({
                "sec-ch-ua": '"Chromium";v="120", "Not_A Brand";v="8", "Google Chrome";v="120"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
                "DNT": "1"
            })
        
        return base_headers

# Global settings instance
enhanced_settings = EnhancedScraperSettings()

# Utility functions
def get_enhanced_scraping_options(url: str, options: Dict[str, Any]) -> Dict[str, Any]:
    """Get enhanced scraping options for any URL"""
    return enhanced_settings.get_enhanced_options(url, options)

def should_use_undetected_for_url(url: str, options: Dict[str, Any] = None) -> bool:
    """Check if undetected ChromeDriver should be used for a URL"""
    if options is None:
        options = {}
    return enhanced_settings.should_use_undetected(url, options)

def get_optimal_headers(url: str) -> Dict[str, str]:
    """Get optimal headers for a URL"""
    return enhanced_settings.get_headers_for_domain(url)

# Configuration presets for common scenarios
CLOUDFLARE_PRESET = {
    "browser_strategy": BrowserStrategy.UNDETECTED_PREFERRED.value,
    "timeout": 35,
    "waitFor": 5000,
    "stealth": True,
    "use_undetected": True,
    "max_retries": 3,
    "actions": [
        {"type": "wait", "selector": "body", "milliseconds": 5000},
        {"type": "scroll", "selector": "body", "direction": "down", "amount": 500, "milliseconds": 1000},
        {"type": "wait", "selector": "body", "milliseconds": 3000}
    ]
}

FAST_PRESET = {
    "browser_strategy": BrowserStrategy.REGULAR_PREFERRED.value,
    "timeout": 15,
    "waitFor": 1000,
    "stealth": False,
    "use_undetected": False
}

COMPREHENSIVE_PRESET = {
    "browser_strategy": BrowserStrategy.SMART_FALLBACK.value,
    "timeout": 30,
    "waitFor": 3000,
    "stealth": True,
    "includeScreenshot": True,
    "includeRawHtml": True,
    "extract_structured_data": True
}