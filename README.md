# AI Skill Extractor 🛠️

A powerful, multimodal tool designed to automatically extract, analyze, and translate AI Agent system prompts (skills) from dynamic web platforms like **Xiaohongshu (Little Red Book)** and **WeChat Official Accounts**.

## 🌟 Key Features

1. **Multimodal Extraction (OCR)**: Integrates with Google's Gemini 3.5 Flash Vision to perform high-accuracy OCR on images within posts. This perfectly captures complex system prompts that authors often share as screenshots instead of text.
2. **Lightning-Fast Xiaohongshu Scraper**: Bypasses the need for headless browsers by directly parsing Xiaohongshu's `window.__INITIAL_STATE__` API payload. Extracts high-res images and full text in milliseconds, completely avoiding login walls.
3. **Automatic Translation & Formatting**: Instantly translates complex English system prompts into professional Simplified Chinese and packages them into clean, ready-to-use `.md` files.
4. **Seamless Local Installation**: Built with Streamlit for a smooth UI experience. Easily download extracted skills with a single click and import them directly into tools like Claude Code, Cursor, or Dify.

## 🚀 Installation & Usage

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/ai-skill-extractor.git
   cd ai-skill-extractor
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Streamlit App**:
   ```bash
   streamlit run app.py
   ```

4. **Start Extracting**:
   - Open the web interface (usually `http://localhost:8501`).
   - Paste your Google Gemini API Key in the sidebar.
   - Enter a Xiaohongshu or WeChat link and click **Extract Skills**.
   - Download the generated `.md` system prompt!

## 🛡️ Privacy & Security
Your API key is securely stored in a local `config.txt` file and is never uploaded to any remote server. All scraped images are temporarily stored in `temp_images/` and handled securely on your local machine.
