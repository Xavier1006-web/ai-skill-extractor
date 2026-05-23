import streamlit as st
import json
import os
import re
from scraper import scrape_wechat, scrape_xiaohongshu
from skill_extractor import extract_skills_from_text
from installer import install_skill

st.set_page_config(page_title="AI Skill Extractor", page_icon="🤖", layout="wide")

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.txt")

def load_key():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return f.read().strip()
    return ""

def save_key(key):
    with open(CONFIG_FILE, "w") as f:
        f.write(key.strip())

st.title("🤖 AI Skill Extractor")
st.markdown("Extract, evaluate, and install AI `.md` skills from Xiaohongshu notes/videos and WeChat articles.")

# Sidebar for configuration
with st.sidebar:
    st.header("Configuration")
    saved_key = load_key()
    api_key = st.text_input("Google Gemini API Key", value=saved_key, type="password", help="Required to analyze text and extract skills.")
    
    if api_key and api_key != saved_key:
        save_key(api_key)
        
    if not api_key:
        st.warning("Please enter your Gemini API Key to continue.")
        
    st.markdown("---")
    st.markdown("""
    ### Supported Platforms:
    - **Xiaohongshu (Little Red Book)**: Paste a post or video link. It will extract the text, video description, and top comments.
    - **WeChat Official Accounts**: Paste an article link.
    """)

# Main Input
if 'skills' not in st.session_state:
    st.session_state.skills = None
    st.session_state.combined_text = ""
    st.session_state.image_paths = []
    st.session_state.has_scraped = False
    
url = st.text_input("Enter URL (Xiaohongshu or WeChat):", placeholder="https://...")

if st.button("Extract Skills", type="primary"):
    if not url:
        st.error("Please enter a URL.")
    elif not api_key:
        st.error("Please enter your Google Gemini API Key in the sidebar.")
    else:
        with st.spinner("Scraping content... This might take a few seconds (especially for Xiaohongshu)..."):
            if 'mp.weixin.qq.com' in url:
                scrape_result = scrape_wechat(url)
                scrape_result['platform'] = 'wechat'
            elif 'xiaohongshu.com' in url or 'xhslink.com' in url:
                scrape_result = scrape_xiaohongshu(url)
                scrape_result['platform'] = 'xiaohongshu'
            else:
                scrape_result = {'error': 'Unsupported URL format. Please enter a Xiaohongshu or WeChat Official Account link.'}
                scrape_result['platform'] = 'unsupported'
            
        if 'error' in scrape_result:
            st.error(f"Scraping failed: {scrape_result['error']}")
        else:
            st.success("Successfully scraped content!")
            
            # Combine text for LLM
            combined_text = ""
            image_paths = []
            
            if scrape_result.get('platform') in ['wechat', 'xiaohongshu', 'dynamic']:
                if 'error' in scrape_result:
                    st.warning(f"Scraper returned a warning: {scrape_result['error']}")
                combined_text += f"Title: {scrape_result.get('title', '')}\n\n"
                combined_text += f"Content: {scrape_result.get('content', '')}\n\n"
                if scrape_result.get('comments'):
                    combined_text += "Comments:\n" + "\n".join(scrape_result['comments'])
                if scrape_result.get('images'):
                    image_paths = scrape_result['images']
            
            st.markdown("---")
            st.header("Extracted Skills")
            
            with st.spinner("Analyzing text and images with LLM to find AI skills (OCR in progress)..."):
                skills = extract_skills_from_text(combined_text, api_key, image_paths=image_paths)
                
            st.session_state.skills = skills
            st.session_state.combined_text = combined_text
            st.session_state.image_paths = image_paths
            st.session_state.has_scraped = True

if st.session_state.has_scraped:
    combined_text = st.session_state.combined_text
    image_paths = st.session_state.image_paths
    skills = st.session_state.skills
    
    with st.expander("View Raw Scraped Text & Images"):
        st.text(combined_text[:2000] + ("..." if len(combined_text) > 2000 else ""))
        if image_paths:
            st.markdown("**Downloaded Images:**")
            cols = st.columns(min(len(image_paths), 4))
            for i, img_path in enumerate(image_paths[:12]): # Max 12 preview
                with cols[i % len(cols)]:
                    st.image(img_path, use_container_width=True)
                    
    st.markdown("---")
    st.header("Extracted Skills")
    
    if not skills:
        st.info("No skills found in this content.")
    elif isinstance(skills, list) and len(skills) > 0 and 'error' in skills[0]:
        st.error(f"Extraction Error: {skills[0]['error']}")
    else:
        for i, skill in enumerate(skills):
                    st.subheader(f"🛠️ {skill.get('name', 'Unnamed Skill')}")
                    st.write(skill.get('description', 'No description provided.'))
                    
                    if skill.get('worth_installing'):
                        st.success(f"✅ **Worth Installing**: {skill.get('reason', 'Good skill.')}")
                    else:
                        st.warning(f"⚠️ **Not Recommended**: {skill.get('reason', 'May be incomplete.')}")
                        
                    with st.expander("View Prompt / Markdown Content"):
                        st.markdown(f"```markdown\n{skill.get('raw_markdown', '')}\n```")
                        
                    # Create a safe filename for the markdown file
                    safe_name = re.sub(r'[^a-zA-Z0-9_\u4e00-\u9fa5]', '_', skill.get('name', 'skill'))
                    file_name = f"{safe_name}.md"
                    
                    st.download_button(
                        label=f"⬇️ Download & Install '{skill.get('name', 'Skill')}'",
                        data=skill.get('raw_markdown', ''),
                        file_name=file_name,
                        mime="text/markdown",
                        key=f"download_{i}",
                        type="primary"
                    )
                    st.markdown("---")
