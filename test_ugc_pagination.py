"""
Test script to check UGC pagination detection
"""
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_ugc_pagination():
    """Test if UGC website has detectable pagination"""
    url = "https://www.ugc.gov.in/"
    
    print("="*60)
    print("Testing UGC Website Pagination Detection")
    print("="*60)
    print(f"URL: {url}\n")
    
    try:
        # Fetch the page
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        print("✅ Page fetched successfully\n")
        
        # Count document links
        doc_extensions = ['.pdf', '.docx', '.doc', '.pptx']
        doc_links = []
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            absolute_url = urljoin(url, href)
            if any(absolute_url.lower().endswith(ext) for ext in doc_extensions):
                doc_links.append({
                    'url': absolute_url,
                    'text': link.get_text(strip=True)
                })
        
        print(f"📄 Documents found on first page: {len(doc_links)}")
        print("\nSample documents:")
        for i, doc in enumerate(doc_links[:5], 1):
            print(f"  {i}. {doc['text'][:60]}...")
        
        # Look for pagination links
        print("\n" + "="*60)
        print("Searching for pagination patterns...")
        print("="*60 + "\n")
        
        pagination_found = False
        
        # Pattern 1: Look for "Next" links
        next_links = []
        for link in soup.find_all('a', href=True):
            text = link.get_text(strip=True).lower()
            if any(keyword in text for keyword in ['next', 'अगला', '»', '>', 'next page']):
                next_links.append({
                    'text': link.get_text(strip=True),
                    'href': link['href'],
                    'absolute': urljoin(url, link['href'])
                })
        
        if next_links:
            print(f"✅ Found {len(next_links)} 'Next' links:")
            for link in next_links[:3]:
                print(f"   - Text: '{link['text']}'")
                print(f"     URL: {link['absolute']}")
            pagination_found = True
        else:
            print("❌ No 'Next' links found")
        
        # Pattern 2: Look for numbered page links
        print("\n")
        page_links = []
        for link in soup.find_all('a', href=True):
            text = link.get_text(strip=True)
            href = link['href']
            # Check if text is a number or contains "page"
            if text.isdigit() or 'page' in text.lower():
                page_links.append({
                    'text': text,
                    'href': href,
                    'absolute': urljoin(url, href)
                })
        
        if page_links:
            print(f"✅ Found {len(page_links)} numbered page links:")
            for link in page_links[:5]:
                print(f"   - Text: '{link['text']}'")
                print(f"     URL: {link['absolute']}")
            pagination_found = True
        else:
            print("❌ No numbered page links found")
        
        # Pattern 3: Look for query parameters
        print("\n")
        query_param_links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if any(param in href.lower() for param in ['page=', 'p=', 'pg=', 'pagenum=']):
                query_param_links.append({
                    'text': link.get_text(strip=True),
                    'href': href,
                    'absolute': urljoin(url, href)
                })
        
        if query_param_links:
            print(f"✅ Found {len(query_param_links)} query parameter pagination links:")
            for link in query_param_links[:5]:
                print(f"   - Text: '{link['text']}'")
                print(f"     URL: {link['absolute']}")
            pagination_found = True
        else:
            print("❌ No query parameter pagination found")
        
        # Summary
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        print(f"Documents on first page: {len(doc_links)}")
        print(f"Pagination detected: {'✅ YES' if pagination_found else '❌ NO'}")
        
        if not pagination_found:
            print("\n⚠️  WARNING: No pagination detected!")
            print("This means the scraper will only get documents from the first page.")
            print("\nPossible reasons:")
            print("1. Website uses JavaScript pagination (not supported)")
            print("2. All documents are on a single page")
            print("3. Pagination uses a non-standard pattern")
            print("\nRecommendation:")
            print("- Check if the website has a 'Documents' or 'Publications' section")
            print("- Try scraping specific document listing pages")
            print("- Consider using the website's search/filter functionality")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ugc_pagination()
