import os

INSTALL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "installed_skills")

def install_skill(skill_name: str, raw_markdown: str) -> str:
    """
    Saves the skill markdown content to the local installed_skills directory.
    Returns the path of the saved file or an error message.
    """
    try:
        if not os.path.exists(INSTALL_DIR):
            os.makedirs(INSTALL_DIR)
            
        # Clean the filename
        safe_name = "".join([c for c in skill_name if c.isalpha() or c.isdigit() or c==' ']).rstrip()
        safe_name = safe_name.replace(' ', '_').lower()
        if not safe_name:
            safe_name = "unnamed_skill"
            
        filename = f"{safe_name}.md"
        filepath = os.path.join(INSTALL_DIR, filename)
        
        # Avoid overwriting directly by appending a number if it exists
        counter = 1
        while os.path.exists(filepath):
            filename = f"{safe_name}_{counter}.md"
            filepath = os.path.join(INSTALL_DIR, filename)
            counter += 1
            
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(raw_markdown)
            
        return filepath
    except Exception as e:
        return f"Error installing skill: {e}"

if __name__ == "__main__":
    pass
