# -*- coding: utf-8 -*-
# ============================================================================
# CẤU HÌNH - THAY ĐỔI URL Ở ĐÂY
# ============================================================================
TARGET_URL = "https://tuesy.net/phat-day-chan-trau/"  # ← Test với URL đơn giản trước
# ============================================================================

import sys
import os
sys.stdout.reconfigure(encoding='utf-8')
import requests
import json
from datetime import datetime

def scrape_page():
    api_url = "http://localhost:8000/api/v1/scrape"
    
    # Configure scraping options với cải thiện cho Cloudflare
    payload = {
        "url": TARGET_URL,
        "formats": ["markdown", "html"],
        "onlyMainContent": True,
        "includeScreenshot": False,
        "includeRawHtml": False,
        "waitFor": 30000,  # Tăng thời gian chờ lên 30 giây cho Cloudflare
        "timeout": 120,    # Tăng timeout request lên 2 phút
        "extract": {
            "custom_config": {
                "remove_ads": True,
                "extract_tables": True,
                "handle_cloudflare": True,
                "max_retries": 3
            }
        },
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Cache-Control": "no-cache",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1"
        },
        "proxy": None,
        "stealth": True,
        "actions": [
            {"type": "wait", "selector": "body", "milliseconds": 5000},
            {"type": "scroll", "selector": "body", "direction": "down", "amount": 500, "milliseconds": 1000},
            {"type": "wait", "selector": "body", "milliseconds": 3000}
        ]
    }
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Đang gửi request đến: {api_url}")
    print(f"[{datetime.now().strftime('%H:%M:%S')}] URL cần crawl: {TARGET_URL}")
    print("-" * 80)
    
    try:
        response = requests.post(api_url, json=payload, timeout=150)  # Tăng timeout lên 2.5 phút
        
        # Kiểm tra status code
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get("success"):
                print(f"[{datetime.now().strftime('%H:%M:%S')}] SUCCESS: Crawl thành công!")
                print("-" * 80)
                
                # Access extracted content
                data = result.get("data", {})
                markdown_content = data.get("markdown", "")
                html_content = data.get("html", "")
                metadata = data.get("metadata", {})
                structured_data = data.get("structured_data", {})
                
                # In thông tin metadata
                print("\nMETADATA:")
                print(f"  - Title: {metadata.get('title', 'N/A')}")
                print(f"  - Description: {metadata.get('description', 'N/A')}")
                print(f"  - Language: {metadata.get('language', 'N/A')}")
                print(f"  - URL: {metadata.get('url', 'N/A')}")
                
                # In preview nội dung Markdown
                print("\nNOI DUNG MARKDOWN (500 ký tự đầu):")
                print("-" * 40)
                if markdown_content:
                    print(markdown_content[:500])
                    print("..." if len(markdown_content) > 500 else "")
                else:
                    print("Không có nội dung markdown")
                
                # Thống kê
                print("\nTHONG KE:")
                print(f"  - Độ dài Markdown: {len(markdown_content)} ký tự")
                print(f"  - Độ dài HTML: {len(html_content)} ký tự")
                print(f"  - Có structured data: {'Có' if structured_data else 'Không'}")
                
                # Tự động lưu kết quả vào file
                print("\nTự động lưu kết quả...")
                save_results(result, TARGET_URL)
                
                return result
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR: Crawl thất bại!")
                print(f"Error: {result.get('error', 'Unknown error')}")
                print(f"Full response: {json.dumps(result, indent=2, ensure_ascii=False)[:1000]}")
                
        else:
            print(f"ERROR: Lỗi HTTP: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            
    except requests.exceptions.ConnectionError:
        print(f"ERROR: Không thể kết nối đến server!")
        print("Hãy đảm bảo rằng:")
        print("1. Server eGet-Crawler đang chạy (npm start)")
        print("2. Server đang lắng nghe ở port 8000")
        print("3. Không có firewall chặn kết nối")
        
    except requests.exceptions.Timeout:
        print(f"ERROR: Request timeout sau 150 giây!")
        print("Website có thể mất quá lâu để load hoặc server quá tải.")
        
    except Exception as e:
        print(f"ERROR: Lỗi không xác định: {str(e)}")
    
    return None

def save_results(result, url):
    """Lưu kết quả crawl vào file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Tạo tên file từ URL
    try:
        # Lấy phần cuối của URL làm tên file
        url_part = url.rstrip('/').split('/')[-1]
        if not url_part or url_part == url.split('//')[-1].split('/')[0]:
            url_part = "crawled_content"
    except:
        url_part = "crawled_content"
    
    data = result.get("data", {})
    metadata = data.get("metadata", {})
    
    # Lưu Markdown với format đẹp
    markdown_content = data.get("markdown", "")
    if markdown_content:
        md_filename = f"{url_part}_{timestamp}.md"
        with open(md_filename, 'w', encoding='utf-8') as f:
            f.write(f"# {metadata.get('title', 'Tuesy.net Content')}\\n\\n")
            f.write(f"**URL**: {url}\\n")
            f.write(f"**Crawl time**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n")
            f.write(f"**Duration**: Completed successfully\\n\\n")
            f.write("---\\n\\n")
            f.write(markdown_content)
        print(f"✅ SUCCESS: Đã lưu Markdown vào: {md_filename}")
    
    # Lưu JSON đầy đủ (optional)
    json_filename = f"{url_part}_full_{timestamp}.json"
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"📄 SUCCESS: Đã lưu JSON vào: {json_filename}")

def test_server_connection():
    """Kiểm tra kết nối đến server"""
    print("\nKiểm tra kết nối server...")
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        print(f"Response status: {response.status_code}")
        if response.status_code == 200:
            print("SUCCESS: Server đang hoạt động!")
            return True
    except Exception as e:
        print(f"Connection error: {e}")
    
    print("ERROR: Không thể kết nối đến server!")
    return False

if __name__ == "__main__":
    print("=" * 80)
    print("EGET-CRAWLER TEST SCRIPT")
    print("=" * 80)
    
    # Kiểm tra server trước
    if test_server_connection():
        print("\nBắt đầu crawl dữ liệu...")
        print("=" * 80)
        scrape_page()
    else:
        print("\nWARNING: Hướng dẫn khởi động server:")
        print("1. Mở terminal mới")
        print("2. Cd đến thư mục eGet-Crawler-for-ai")
        print("3. Chạy lệnh: npm start")
        print("4. Đợi server khởi động xong (thường ở port 8000)")
        print("5. Chạy lại script này")
    
    print("\n" + "=" * 80)
    print("Hoàn thành!")