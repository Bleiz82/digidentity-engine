"""
DigIdentity Engine — Deep Site Analysis (Premium)
Analisi approfondita multi-page del sito web.
"""

import httpx
from typing import Dict, Any, List
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import asyncio


async def scrape_site_deep(base_url: str, max_pages: int = 10) -> Dict[str, Any]:
    """
    Analisi approfondita del sito web (crawling multi-page).
    
    Analizza:
    - Struttura sito (numero pagine, profondità)
    - Contenuti (testi, immagini, video)
    - Link interni ed esterni
    - Meta tags (title, description, keywords)
    - Schema markup (JSON-LD)
    - Performance issues
    
    Args:
        base_url: URL base del sito
        max_pages: Numero massimo di pagine da analizzare
        
    Returns:
        dict: Analisi approfondita struttura e contenuti
    """
    print(f"🔍 Analisi approfondita sito: {base_url}")
    print(f"   Max pagine: {max_pages}")
    
    visited_urls = set()
    to_visit = {base_url}
    pages_data = []
    
    domain = urlparse(base_url).netloc
    
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            while to_visit and len(visited_urls) < max_pages:
                url = to_visit.pop()
                
                if url in visited_urls:
                    continue
                
                print(f"   📄 Crawling: {url}")
                
                try:
                    response = await client.get(url)
                    response.raise_for_status()
                    
                    visited_urls.add(url)
                    
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Analizza pagina
                    page_analysis = analyze_page(url, soup)
                    pages_data.append(page_analysis)
                    
                    # Trova link interni
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        absolute_url = urljoin(url, href)
                        parsed = urlparse(absolute_url)
                        
                        # Solo link interni dello stesso dominio
                        if parsed.netloc == domain and absolute_url not in visited_urls:
                            to_visit.add(absolute_url)
                
                except Exception as e:
                    print(f"   ⚠️ Errore crawling {url}: {str(e)}")
                    continue
                
                # Delay per non sovraccaricare il server
                await asyncio.sleep(0.5)
        
        # Calcola statistiche aggregate
        result = {
            "success": True,
            "base_url": base_url,
            "pages_analyzed": len(pages_data),
            "pages_data": pages_data,
            "summary": calculate_site_summary(pages_data)
        }
        
        print(f"✅ Analisi completata: {len(pages_data)} pagine")
        
        return result
    
    except Exception as e:
        error_msg = f"Errore analisi sito: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "success": False,
            "error": error_msg
        }


def analyze_page(url: str, soup: BeautifulSoup) -> Dict[str, Any]:
    """Analizza una singola pagina."""
    
    # Meta tags
    title = soup.find('title')
    meta_description = soup.find('meta', attrs={'name': 'description'})
    meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
    
    # Headings
    h1_tags = soup.find_all('h1')
    h2_tags = soup.find_all('h2')
    
    # Contenuti
    paragraphs = soup.find_all('p')
    images = soup.find_all('img')
    videos = soup.find_all('video')
    
    # Links
    internal_links = []
    external_links = []
    
    for link in soup.find_all('a', href=True):
        href = link['href']
        if href.startswith('http') and urlparse(url).netloc not in href:
            external_links.append(href)
        else:
            internal_links.append(href)
    
    # Schema markup
    schema_scripts = soup.find_all('script', type='application/ld+json')
    
    # Word count
    text = soup.get_text()
    word_count = len(text.split())
    
    return {
        "url": url,
        "title": title.text.strip() if title else None,
        "meta_description": meta_description['content'] if meta_description else None,
        "meta_keywords": meta_keywords['content'] if meta_keywords else None,
        "h1_count": len(h1_tags),
        "h1_texts": [h1.text.strip() for h1 in h1_tags[:3]],  # Prime 3
        "h2_count": len(h2_tags),
        "paragraph_count": len(paragraphs),
        "word_count": word_count,
        "image_count": len(images),
        "images_without_alt": len([img for img in images if not img.get('alt')]),
        "video_count": len(videos),
        "internal_links_count": len(internal_links),
        "external_links_count": len(external_links),
        "has_schema_markup": len(schema_scripts) > 0,
        "schema_types": [script.get('type') for script in schema_scripts]
    }


def calculate_site_summary(pages_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calcola statistiche aggregate del sito."""
    
    if not pages_data:
        return {}
    
    total_words = sum(p['word_count'] for p in pages_data)
    total_images = sum(p['image_count'] for p in pages_data)
    images_without_alt = sum(p['images_without_alt'] for p in pages_data)
    
    pages_with_schema = sum(1 for p in pages_data if p['has_schema_markup'])
    pages_without_meta_desc = sum(1 for p in pages_data if not p['meta_description'])
    pages_with_multiple_h1 = sum(1 for p in pages_data if p['h1_count'] > 1)
    pages_without_h1 = sum(1 for p in pages_data if p['h1_count'] == 0)
    
    return {
        "total_pages": len(pages_data),
        "total_words": total_words,
        "avg_words_per_page": int(total_words / len(pages_data)),
        "total_images": total_images,
        "images_without_alt_pct": int((images_without_alt / total_images * 100)) if total_images > 0 else 0,
        "pages_with_schema_pct": int((pages_with_schema / len(pages_data) * 100)),
        "pages_without_meta_desc_pct": int((pages_without_meta_desc / len(pages_data) * 100)),
        "pages_with_multiple_h1": pages_with_multiple_h1,
        "pages_without_h1": pages_without_h1,
        "seo_issues_found": pages_without_meta_desc + pages_with_multiple_h1 + pages_without_h1
    }
