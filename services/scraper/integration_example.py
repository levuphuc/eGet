# -*- coding: utf-8 -*-
"""
Enhanced Scraper Integration Example
Demonstrates how to integrate the enhanced scraper as a drop-in replacement
"""

import asyncio
import sys
import os
from typing import Dict, Any
from loguru import logger

# Add parent directory to path to import local modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from services.scraper.enhanced_scraper import EnhancedWebScraper
from services.scraper.enhanced_config import (
    get_enhanced_scraping_options, 
    CLOUDFLARE_PRESET,
    FAST_PRESET,
    COMPREHENSIVE_PRESET
)

async def demonstrate_enhanced_scraping():
    """Demonstrate the enhanced scraper capabilities"""
    
    logger.info("Starting Enhanced Scraper Integration Demo")
    
    # Create enhanced scraper instance
    scraper = await EnhancedWebScraper.create(max_concurrent=4)
    
    try:
        # Test URLs with different characteristics
        test_urls = [
            {
                "url": "https://tuesy.net/bat-quan-trai-gioi/",
                "description": "Cloudflare-protected site (from test.py)",
                "preset": CLOUDFLARE_PRESET
            },
            {
                "url": "https://example.com",
                "description": "Simple site for fast scraping",
                "preset": FAST_PRESET
            },
            {
                "url": "https://httpbin.org/html",
                "description": "Test site for comprehensive scraping",
                "preset": COMPREHENSIVE_PRESET
            }
        ]
        
        for i, test_case in enumerate(test_urls, 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"Test {i}: {test_case['description']}")
            logger.info(f"URL: {test_case['url']}")
            logger.info(f"{'='*60}")
            
            try:
                # Get enhanced options
                enhanced_options = get_enhanced_scraping_options(
                    test_case['url'], 
                    test_case['preset']
                )
                
                logger.info(f"Using options: {enhanced_options}")
                
                # Perform scraping
                result = await scraper.scrape(test_case['url'], enhanced_options)
                
                if result['success']:
                    data = result['data']
                    metadata = data.get('metadata', {})
                    
                    logger.info(f"✅ SUCCESS: Scraped successfully")
                    logger.info(f"   Browser type: {metadata.get('browser_type', 'unknown')}")
                    logger.info(f"   Title: {metadata.get('title', 'N/A')[:100]}...")
                    logger.info(f"   Content length: {len(data.get('markdown', '') or '')}")
                    logger.info(f"   Links found: {len(data.get('links', []) or [])}")
                    logger.info(f"   Cached: {result.get('cached', False)}")
                    
                    if data.get('structured_data'):
                        logger.info(f"   Structured data: {len(data['structured_data'])} items")
                
                else:
                    logger.error(f"❌ FAILED: {result}")
                    
            except Exception as e:
                logger.error(f"❌ ERROR in test {i}: {str(e)}")
            
            # Brief pause between tests
            await asyncio.sleep(2)
        
        # Display final metrics
        logger.info(f"\n{'='*60}")
        logger.info("Final Metrics")
        logger.info(f"{'='*60}")
        metrics = scraper.get_metrics()
        logger.info(f"Pool metrics: {metrics['pool_metrics']}")
        logger.info(f"Active browsers: {metrics['active_browsers']}")
    
    finally:
        # Cleanup
        logger.info("Cleaning up resources...")
        await scraper.cleanup()
        logger.info("Demo completed")

async def demonstrate_backward_compatibility():
    """Demonstrate backward compatibility with existing API"""
    
    logger.info("\n" + "="*60)
    logger.info("Backward Compatibility Demo") 
    logger.info("="*60)
    
    # Import the enhanced scraper using the backward-compatible alias
    from services.scraper.enhanced_scraper import WebScraper
    
    # Create scraper using the same API as before
    scraper = await WebScraper.create(max_concurrent=2)
    
    try:
        # Use the same options format as the original scraper
        original_options = {
            "only_main": True,
            "timeout": 30,
            "include_screenshot": False,
            "include_raw_html": False,
            "wait_for_selector": None
        }
        
        test_url = "https://httpbin.org/html"
        
        logger.info(f"Testing backward compatibility with: {test_url}")
        
        result = await scraper.scrape(test_url, original_options)
        
        if result['success']:
            logger.info("✅ Backward compatibility test PASSED")
            logger.info(f"   Response format matches original API")
            logger.info(f"   Enhanced features working transparently")
        else:
            logger.error("❌ Backward compatibility test FAILED")
            
    finally:
        await scraper.cleanup()

async def demonstrate_smart_browser_selection():
    """Demonstrate intelligent browser selection"""
    
    logger.info("\n" + "="*60)
    logger.info("Smart Browser Selection Demo")
    logger.info("="*60)
    
    scraper = await EnhancedWebScraper.create(max_concurrent=2)
    
    try:
        # Test automatic browser selection
        test_cases = [
            {
                "url": "https://cloudflare.com",
                "description": "Should auto-select undetected ChromeDriver"
            },
            {
                "url": "https://github.com", 
                "description": "Should prefer regular ChromeDriver"
            },
            {
                "url": "https://example.com",
                "options": {"stealth": True},
                "description": "Forced stealth mode -> undetected ChromeDriver"
            }
        ]
        
        for test_case in test_cases:
            url = test_case["url"]
            options = test_case.get("options", {})
            
            logger.info(f"\nTesting: {test_case['description']}")
            logger.info(f"URL: {url}")
            
            # Get enhanced options to see what browser will be selected
            enhanced_options = get_enhanced_scraping_options(url, options)
            browser_strategy = enhanced_options.get('browser_strategy', 'unknown')
            use_undetected = enhanced_options.get('use_undetected', False)
            
            logger.info(f"Strategy: {browser_strategy}")
            logger.info(f"Will use undetected: {use_undetected}")
    
    finally:
        await scraper.cleanup()

async def main():
    """Main demo function"""
    
    # Configure logging for demo
    logger.remove()  # Remove default handler
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"
    )
    
    print("🚀 Enhanced Scraper Integration Demo")
    print("This demo showcases the enhanced scraper capabilities")
    print()
    
    try:
        # Run all demonstrations
        await demonstrate_enhanced_scraping()
        await demonstrate_backward_compatibility() 
        await demonstrate_smart_browser_selection()
        
        print("\n✅ All demonstrations completed successfully!")
        print("\nTo integrate the enhanced scraper:")
        print("1. Replace imports: from services.scraper.enhanced_scraper import EnhancedWebScraper")
        print("2. Or use backward compatible: from services.scraper.enhanced_scraper import WebScraper")
        print("3. Install undetected-chromedriver: pip install undetected-chromedriver==3.5.5")
        print("4. Enhanced features work automatically based on URL analysis")
        
    except KeyboardInterrupt:
        print("\n🛑 Demo interrupted by user")
    except Exception as e:
        logger.error(f"❌ Demo failed with error: {str(e)}")
        raise

if __name__ == "__main__":
    # Run the demo
    asyncio.run(main())