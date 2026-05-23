import time
import re
import os
import json
from bs4 import BeautifulSoup
import requests

def scrape_wechat(url):
    """Scrapes WeChat article content and images."""
    extracted_data = {
        'title': '',
        'content': '',
        'images': []
    }
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        title_el = soup.find('h1', class_='rich_media_title')
        if title_el:
            extracted_data['title'] = title_el.get_text(strip=True)
            
        content_div = soup.find(id='js_content')
        if not content_div:
            extracted_data['error'] = "Could not find main content in WeChat article."
            return extracted_data
        
        extracted_data['content'] = content_div.get_text(separator='\n', strip=True)
        
        temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp_images')
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
            
        images = content_div.find_all('img')
        for i, img in enumerate(images):
            img_url = img.get('data-src') or img.get('src')
            if img_url and img_url.startswith('http'):
                try:
                    resp = requests.get(img_url, timeout=10)
                    if resp.status_code == 200:
                        img_path = os.path.join(temp_dir, f"wechat_img_{i}.jpg")
                        with open(img_path, 'wb') as f:
                            f.write(resp.content)
                        extracted_data['images'].append(img_path)
                except Exception:
                    pass
                    
        return extracted_data
    except Exception as e:
        extracted_data['error'] = f"Error scraping WeChat: {e}"
        return extracted_data

def _brace_match_json(source: str, start_idx: int) -> str:
    brace = 0
    in_str = False
    esc = False
    end_idx = None
    for i, ch in enumerate(source[start_idx:], start=start_idx):
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        else:
            if ch == '"':
                in_str = True
            elif ch == "{":
                brace += 1
            elif ch == "}":
                brace -= 1
                if brace == 0:
                    end_idx = i + 1
                    break
    if end_idx is None:
        raise Exception("Failed to locate JSON object end.")
    return source[start_idx:end_idx]

DEFAULT_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/120.0.0.0"
)

def scrape_xiaohongshu(url: str):
    """Scrapes Xiaohongshu without Playwright using the fast JSON brace matcher."""
    extracted_data = {
        'title': '',
        'content': '',
        'images': []
    }
    try:
        resp = requests.get(url, allow_redirects=True, timeout=20, headers={"User-Agent": DEFAULT_UA})
        resp.raise_for_status()
        html = resp.text
        
        marker = "window.__INITIAL_STATE__="
        idx = html.find(marker)
        if idx == -1:
            raise Exception("window.__INITIAL_STATE__ not found. Page might be blocked.")
            
        start = idx + len(marker)
        raw = _brace_match_json(html, start)
        raw = re.sub(r"\bundefined\b", "null", raw)
        
        state = json.loads(raw)
        
        note_map = state.get("note", {}).get("noteDetailMap", {})
        if not note_map:
            raise Exception("noteDetailMap not found in initial state.")
            
        note_id, note_entry = next(iter(note_map.items()))
        note = (note_entry or {}).get("note", {}) or {}
        
        extracted_data['title'] = note.get("title", "")
        extracted_data['content'] = note.get("desc", "")
        
        images_list = note.get("imageList", [])
        image_urls = []
        for img in images_list:
            u = img.get("urlDefault") or img.get("url")
            if not u and img.get("infoList"):
                u = img["infoList"][0].get("url")
            if u:
                image_urls.append(u)
                
        temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp_images')
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
            
        for i, img_url in enumerate(image_urls):
            try:
                if not img_url.startswith('http'):
                    img_url = 'https:' + img_url if img_url.startswith('//') else img_url
                r = requests.get(img_url, timeout=10)
                if r.status_code == 200:
                    img_path = os.path.join(temp_dir, f"xhs_img_{i}.jpg")
                    with open(img_path, 'wb') as f:
                        f.write(r.content)
                    extracted_data['images'].append(img_path)
            except Exception:
                pass
                
        return extracted_data
    except Exception as e:
        extracted_data['error'] = f"Error scraping Xiaohongshu API: {e}"
        return extracted_data

def scrape_dynamic(url):
    """Scrapes dynamic pages (Xiaohongshu, WeChat Search) using Playwright."""
    extracted_data = {
        'title': '',
        'content': '',
        'comments': [],
        'is_video': False,
        'video_url': None,
        'images': []
    }
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
            )
            page = context.new_page()
            
            # Apply stealth to bypass anti-bot detections (like Xiaohongshu login wall)
            stealth_sync(page)
            
            # Anti-bot bypass attempts and stealth are active
            
            page.goto(url, wait_until='domcontentloaded', timeout=30000)
            
            # Wait for content to load explicitly
            try:
                page.wait_for_selector('.note-content, #detail-desc, .title, .desc, .interaction-container', state='attached', timeout=15000)
            except Exception:
                pass # Continue anyway, maybe it's WeChat search
                
            time.sleep(3) # Extra buffer for images to render
            
            # Try to extract via __INITIAL_STATE__ first (XHS specific, highly reliable)
            state_data = page.evaluate("""
            () => {
                try {
                    let state = window.__INITIAL_STATE__ || window.__INITIAL_SSR_STATE__;
                    if (state && state.note && state.note.noteDetailMap) {
                        let noteId = Object.keys(state.note.noteDetailMap)[0];
                        let noteData = state.note.noteDetailMap[noteId].note;
                        let images = [];
                        if (noteData.imageList) {
                            images = noteData.imageList.map(img => img.urlDefault || img.url || (img.infoList && img.infoList[0].url));
                        }
                        return {
                            title: noteData.title || '',
                            desc: noteData.desc || '',
                            images: images.filter(Boolean)
                        };
                    }
                } catch(e) {}
                return null;
            }
            """)
            
            image_urls = []
            
            if state_data and (state_data['title'] or state_data['desc']):
                extracted_data['title'] = state_data['title']
                extracted_data['content'] = state_data['desc']
                image_urls = state_data['images']
            else:
                # Fallback to DOM extraction
                # 1. Title
                title_el = page.query_selector('.title') or page.query_selector('#detail-title')
                if title_el:
                    extracted_data['title'] = title_el.inner_text().strip()
                else:
                    extracted_data['title'] = page.title()
                    
                # 2. Main content / description (Robust Fallback)
                extracted_data['content'] = page.evaluate("""
                () => {
                    let text = '';
                    let mainNode = document.querySelector('#detail-desc') || document.querySelector('.note-content');
                    if (mainNode && mainNode.innerText.length > 20) {
                        text = mainNode.innerText;
                    } else {
                        text = document.body.innerText;
                    }
                    return text;
                }
                """)
                
                # 4. Extract images (DOM fallback)
                js_script = """
                () => {
                    let urls = new Set();
                    document.querySelectorAll('.swiper-slide').forEach(el => {
                        let bg = el.style.backgroundImage;
                        if(bg) urls.add(bg.replace(/url\\(['"]?(.*?)['"]?\\)/i, '$1'));
                    });
                    document.querySelectorAll('img').forEach(img => {
                        if(img.src && img.src.startsWith('http')) urls.add(img.src);
                    });
                    return Array.from(urls);
                }
                """
                image_urls = page.evaluate(js_script)
                
            # 3. Check for video (DOM)
            video_el = page.query_selector('video')
            if video_el:
                extracted_data['is_video'] = True
                extracted_data['video_url'] = video_el.get_attribute('src')
            
            # Download images to a temp folder
            temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp_images')
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)
                
            for i, img_url in enumerate(image_urls):
                try:
                    resp = requests.get(img_url, timeout=10)
                    if resp.status_code == 200:
                        img_path = os.path.join(temp_dir, f"xhs_img_{i}.jpg")
                        with open(img_path, 'wb') as f:
                            f.write(resp.content)
                        extracted_data['images'].append(img_path)
                except Exception:
                    pass

            # 5. Extract comments (scroll down a bit to load)
            for _ in range(3):
                page.mouse.wheel(0, 1000)
                time.sleep(1)
                
            comment_els = page.query_selector_all('.comment-item .content')
            for el in comment_els:
                comment_text = el.inner_text().strip()
                if comment_text:
                    extracted_data['comments'].append(comment_text)
                    
            browser.close()
            
    except Exception as e:
        extracted_data['error'] = str(e)
        
    return extracted_data

def scrape_url(url):
    """Main entry point to scrape based on URL type."""
    if 'mp.weixin.qq.com' in url:
        return {'platform': 'wechat', 'data': scrape_wechat(url)}
    elif 'xiaohongshu.com' in url or 'xhslink.com' in url or 'search.weixin.qq.com' in url:
        return {'platform': 'xiaohongshu', 'data': scrape_dynamic(url)}
    else:
        return {'error': 'Unsupported platform. Please provide a WeChat or Xiaohongshu link.'}

if __name__ == "__main__":
    pass# Test script
    # print(scrape_url("https://www.xiaohongshu.com/explore/..."))
    pass
