import os
import json
import base64
import requests
from typing import List, Dict

import PIL.Image

def extract_skills_from_text(text_content: str, api_key: str, image_paths: List[str] = None) -> List[Dict]:
    """
    Sends the text content and optionally images to Gemini to extract and evaluate AI skills.
    Returns a list of dictionaries containing skill information.
    """
    if not api_key:
        return [{"error": "API Key is required to extract skills."}]
        
    prompt = """
    You are an expert AI agent designed to extract "skills" or "system prompts" (often written in Markdown format) from provided text and images.
    The content might be from a WeChat article or Xiaohongshu post/comments.
    IMPORTANT: If images are provided, perform OCR to read any text inside the images, as users often post their system prompts as screenshots!
    
    Your task:
    1. Identify any complete or partial AI skill definitions, system prompts, or agent personas mentioned in the text OR visible in the images.
    2. Extract the exact Markdown (.md) content of the skill, and TRANSLATE the entire prompt into Simplified Chinese (简体中文). Ensure the translated system prompt is natural and professional.
    3. Evaluate if the skill is "worth installing". A skill is worth installing if it provides a clear, actionable system prompt or a well-defined persona. Vague mentions should be marked as not worth installing.
    
    IMPORTANT: You MUST write the "name", "description", "reason", and the "raw_markdown" fields ENTIRELY in Simplified Chinese (简体中文).
    
    Respond STRICTLY with a JSON array of objects. Do not include any Markdown formatting like ```json in your response. Just the raw JSON array.
    Each object must have the following keys:
    - "name": (string) The name of the skill.
    - "description": (string) A short 1-2 sentence description of what the skill does.
    - "raw_markdown": (string) The full Markdown content of the prompt/skill. Format it nicely.
    - "worth_installing": (boolean) true or false.
    - "reason": (string) A short explanation of why it is or isn't worth installing.

    Here is the text to analyze:
    """
    
    contents = []
    
    if image_paths:
        for img_path in image_paths:
            try:
                with open(img_path, "rb") as image_file:
                    encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                    mime_type = "image/jpeg"
                    if img_path.lower().endswith(".png"):
                        mime_type = "image/png"
                    elif img_path.lower().endswith(".webp"):
                        mime_type = "image/webp"
                        
                    contents.append({
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": encoded_string
                        }
                    })
            except Exception as e:
                print(f"Error loading image {img_path}: {e}")
                
    contents.append({
        "text": prompt + "\n\n---\n" + text_content + "\n---"
    })
    
    data = {
        "contents": [{"parts": contents}]
    }
    
    headers = {"Content-Type": "application/json"}
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={api_key}"
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        
        text_response = result['candidates'][0]['content']['parts'][0]['text'].strip()
        
        # Remove markdown code blocks if the model still outputs them
        if text_response.startswith("```json"):
            text_response = text_response[7:]
        if text_response.startswith("```"):
            text_response = text_response[3:]
        if text_response.endswith("```"):
            text_response = text_response[:-3]
            
        skills_data = json.loads(text_response.strip())
        return skills_data
        
    except json.JSONDecodeError as e:
        return [{"error": f"Failed to parse LLM response into JSON: {e}\nResponse was: {text_response}"}]
    except Exception as e:
        err_detail = ""
        if 'response' in locals() and hasattr(response, 'text'):
            err_detail = response.text
        return [{"error": f"Error calling Gemini API: {str(e)}. {err_detail}"}]

if __name__ == "__main__":
    pass
