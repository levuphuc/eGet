# Enhanced Scraper Service

The Enhanced Scraper Service integrates undetected-chromedriver as an alternative browser strategy for improved Cloudflare bypass capabilities while maintaining full backward compatibility with the existing API.

## Key Features

### 🔧 Undetected ChromeDriver Integration
- **Primary Option**: Uses undetected-chromedriver for Cloudflare-protected sites
- **Proven Techniques**: Implements successful bypass methods (35s wait time, version control, etc.)
- **Anti-Detection**: Advanced stealth measures and human behavior simulation

### 🔄 Intelligent Fallback Strategy
- **Smart Selection**: Automatically chooses optimal browser based on URL analysis
- **Graceful Fallback**: Falls back to regular selenium if undetected fails
- **Dual Pool Management**: Maintains separate pools for undetected and regular browsers

### 🔒 Advanced Cloudflare Bypass
- **Multiple Challenge Types**: Handles Turnstile, traditional, and iframe challenges
- **Proven Wait Times**: Uses 35-second timeout based on successful test results
- **Human Simulation**: Mimics human browsing patterns and interactions

### 🔧 Backward Compatibility
- **Drop-in Replacement**: Can replace existing scraper without code changes
- **API Compatibility**: Maintains all existing method signatures and return formats
- **Configuration**: Supports all original configuration options

## Installation

Add the undetected-chromedriver dependency:

```bash
pip install undetected-chromedriver==3.5.5
```

## Usage

### Basic Integration (Drop-in Replacement)

```python
# Replace this import:
# from services.scraper.scraper import WebScraper

# With this:
from services.scraper.enhanced_scraper import WebScraper

# Everything else remains the same
scraper = await WebScraper.create(max_concurrent=8)
result = await scraper.scrape(url, options)
```

### Advanced Usage with Enhanced Features

```python
from services.scraper.enhanced_scraper import EnhancedWebScraper
from services.scraper.enhanced_config import CLOUDFLARE_PRESET, get_enhanced_scraping_options

# Create enhanced scraper
scraper = await EnhancedWebScraper.create(max_concurrent=8)

# Use automatic enhancement
enhanced_options = get_enhanced_scraping_options(url, base_options)
result = await scraper.scrape(url, enhanced_options)

# Or use presets for specific scenarios
result = await scraper.scrape(cloudflare_url, CLOUDFLARE_PRESET)
```

### Configuration Options

#### Browser Strategy Options
```python
options = {
    # Browser selection
    "use_undetected": True,           # Force undetected ChromeDriver
    "prefer_undetected": True,        # Prefer but allow fallback
    "browser_strategy": "smart_fallback",  # Auto-select with fallback
    
    # Cloudflare bypass
    "stealth": True,                  # Enable stealth mode
    "timeout": 35,                    # Proven timeout for CF bypass
    "challenge_timeout": 60,          # Max time to wait for challenges
    
    # Human behavior simulation
    "human_behavior": True,           # Enable human-like interactions
    "wait_for_stability": True,       # Wait for page stability
}
```

#### Action Sequences for Cloudflare
```python
cloudflare_actions = [
    {"type": "wait", "selector": "body", "milliseconds": 5000},
    {"type": "scroll", "selector": "body", "direction": "down", "amount": 500, "milliseconds": 1000},
    {"type": "wait", "selector": "body", "milliseconds": 3000}
]
```

## Configuration Presets

### CLOUDFLARE_PRESET
Optimized for Cloudflare-protected sites:
- Uses undetected ChromeDriver
- 35-second timeout
- Human behavior simulation
- Stability actions

### FAST_PRESET  
Optimized for speed on simple sites:
- Uses regular ChromeDriver
- 15-second timeout
- Minimal actions

### COMPREHENSIVE_PRESET
Balanced approach with full feature set:
- Smart fallback strategy
- Screenshots and raw HTML
- Structured data extraction

## Advanced Features

### Intelligent Browser Selection

The enhanced scraper automatically selects the optimal browser strategy based on:

1. **URL Analysis**: Known Cloudflare domains trigger undetected mode
2. **Explicit Options**: `stealth`, `use_undetected` flags
3. **Domain Patterns**: Predefined lists of protected vs. regular domains

```python
# These URLs automatically use undetected ChromeDriver:
cloudflare_urls = [
    "https://tuesy.net/...",        # From successful test
    "https://discord.com/...", 
    "https://reddit.com/...",
    "https://medium.com/..."
]

# These URLs prefer regular ChromeDriver:
regular_urls = [
    "https://github.com/...",
    "https://stackoverflow.com/...",
    "https://docs.python.org/..."
]
```

### Enhanced Challenge Handling

#### Turnstile Challenges
- Automatic iframe detection and switching
- Checkbox interaction with human-like delays
- Success verification

#### Traditional Challenges
- Form submission handling
- Progressive waiting strategies
- Multiple retry attempts

#### Success Indicators
- Content length analysis
- Challenge element absence
- Page stability verification

### Browser Pool Management

#### Dual Pool Strategy
```python
pool_config = {
    "max_browsers": 8,
    "max_undetected": 4,  # Half for undetected
    "max_regular": 4,     # Half for regular
    "health_check_interval": 60
}
```

#### Health Monitoring
- Memory usage tracking
- Response time monitoring
- Automatic cleanup of unhealthy browsers

## Migration Guide

### From Original Scraper

#### Step 1: Update Import
```python
# Before
from services.scraper.scraper import WebScraper

# After
from services.scraper.enhanced_scraper import WebScraper  # Drop-in replacement
# OR
from services.scraper.enhanced_scraper import EnhancedWebScraper  # Full features
```

#### Step 2: Install Dependency
```bash
pip install undetected-chromedriver==3.5.5
```

#### Step 3: Optional Enhancements
```python
# Add enhanced options for better Cloudflare handling
from services.scraper.enhanced_config import get_enhanced_scraping_options

# Before
result = await scraper.scrape(url, options)

# After (enhanced)
enhanced_options = get_enhanced_scraping_options(url, options)
result = await scraper.scrape(url, enhanced_options)
```

### Configuration Migration

Original options are fully supported. New options can be added incrementally:

```python
# Original options work as-is
original_options = {
    "only_main": True,
    "timeout": 30,
    "include_screenshot": False,
    "wait_for_selector": ".content"
}

# Enhanced options (optional)
enhanced_options = {
    **original_options,
    "use_undetected": True,      # New
    "stealth": True,             # New
    "human_behavior": True,      # New
}
```

## Troubleshooting

### Common Issues

#### 1. Undetected ChromeDriver Installation
```bash
# Install specific version for compatibility
pip install undetected-chromedriver==3.5.5

# If Chrome version mismatch:
pip install --upgrade undetected-chromedriver
```

#### 2. Chrome Version Conflicts
```python
# Force specific Chrome version
browser_options = {
    "uc_version": 120,  # Match your Chrome installation
    "use_subprocess": True
}
```

#### 3. Memory Issues with Large Pools
```python
# Reduce pool size for memory-constrained environments
scraper = await EnhancedWebScraper.create(max_concurrent=4)
```

#### 4. Cloudflare Still Blocking
```python
# Increase timeout and add more human behavior
options = {
    "timeout": 45,              # Longer timeout
    "challenge_timeout": 90,    # More challenge time
    "human_behavior": True,     # Enable simulation
    "actions": [                # More interaction
        {"type": "wait", "milliseconds": 8000},
        {"type": "scroll", "direction": "down", "amount": 300},
        {"type": "wait", "milliseconds": 5000}
    ]
}
```

### Performance Optimization

#### 1. Browser Pool Tuning
```python
# For high-volume scraping
pool_config = {
    "max_browsers": 12,
    "max_undetected": 8,
    "max_regular": 4,
    "health_check_interval": 30
}
```

#### 2. Selective Enhancement
```python
# Only use undetected for known problematic domains
def should_enhance(url):
    problematic_domains = ['cloudflare.com', 'protected-site.com']
    return any(domain in url for domain in problematic_domains)

if should_enhance(url):
    result = await scraper.scrape(url, CLOUDFLARE_PRESET)
else:
    result = await scraper.scrape(url, FAST_PRESET)
```

## Metrics and Monitoring

### Browser Pool Metrics
```python
metrics = scraper.get_metrics()
print(f"Undetected browsers: {metrics['pool_metrics']['available_undetected']}")
print(f"Regular browsers: {metrics['pool_metrics']['available_regular']}")
print(f"Success rate: {metrics['pool_metrics']['reused_undetected']}")
```

### Prometheus Integration
The enhanced scraper maintains all existing Prometheus metrics plus new ones:
- `browser_type_usage_total`
- `cloudflare_challenge_types_total`
- `undetected_browser_success_rate`

## Best Practices

### 1. URL-Based Strategy Selection
```python
# Let the scraper decide automatically
enhanced_options = get_enhanced_scraping_options(url, base_options)
```

### 2. Gradual Migration
```python
# Phase 1: Drop-in replacement
from services.scraper.enhanced_scraper import WebScraper

# Phase 2: Add enhanced options for problematic URLs
if is_problematic_url(url):
    options.update({"stealth": True, "timeout": 35})

# Phase 3: Full enhancement
enhanced_options = get_enhanced_scraping_options(url, options)
```

### 3. Resource Management
```python
# Always cleanup resources
try:
    result = await scraper.scrape(url, options)
finally:
    await scraper.cleanup()
```

### 4. Error Handling
```python
try:
    result = await scraper.scrape(url, enhanced_options)
    if not result['success']:
        # Handle scraping failure
        logger.error(f"Scraping failed: {result['data']['metadata']['error']}")
except Exception as e:
    # Handle unexpected errors
    logger.exception(f"Unexpected error: {e}")
```

## Contributing

When adding new domains or bypass techniques:

1. Update `enhanced_config.py` with new domain lists
2. Add new challenge handlers in `enhanced_scraper.py`
3. Test with the integration example
4. Update documentation

## License

This enhanced scraper maintains the same license as the original project.