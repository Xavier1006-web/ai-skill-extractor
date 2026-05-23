from scraper import scrape_dynamic
import json
url = "https://www.xiaohongshu.com/explore/65e9c704000000000d00f7e1"
print(json.dumps(scrape_dynamic(url), ensure_ascii=False, indent=2))
