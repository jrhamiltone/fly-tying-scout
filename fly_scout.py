import requests
import feedparser
import json
import os
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- UPDATED CONFIGURATION ---
import os

# Secrets are read from the environment variables now
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")

# If these are None, the script will fail, so let's check
if not EMAIL_PASSWORD:
    print("❌ Error: EMAIL_PASSWORD not found in environment variables.")
    exit(1)

# 2. Search Settings
REGIONS = [
    'sfbay', 'sacramento', 'goldcountry', 'humboldt', 'redding', 
    'chico', 'mendocino', 'modesto', 'stockton', 'yubasutter'
]
QUERIES = ["fly tying", "fly tying materials", "fly tying vise"]
MEMORY_FILE = "seen_posts.json"

# --- HELPER FUNCTIONS ---

def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, 'r') as f:
            return json.load(f)
    return []

def save_memory(seen_ids):
    with open(MEMORY_FILE, 'w') as f:
        json.dump(seen_ids, f)

def send_email_alert(new_items):
    if not new_items:
        return

    print("📧 Sending email alert...")
    
    # Create the email content
    subject = f"🎣 {len(new_items)} New Fly Tying Finds (NorCal)"
    
    # HTML Body for a clickable email
    body = "<h2>New Items Found:</h2><ul>"
    for item in new_items:
        body += f"<li><b>{item['title']}</b><br><a href='{item['link']}'>{item['link']}</a><br><i>({item['region']})</i></li><br>"
    body += "</ul>"

    msg = MIMEMultipart()
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'html'))

    try:
        # Connect to Gmail Server
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        text = msg.as_string()
        server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, text)
        server.quit()
        print("✅ Email sent successfully!")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

# --- MAIN AGENT LOOP ---

# ... (Keep your existing configuration and helper functions) ...

def check_craigslist():
    print(f"🕵️  Agent starting scan...")
    seen_ids = load_memory()
    new_finds = []

    # 1. DEFINE HEADERS (This makes us look like a Chrome Browser)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    for region in REGIONS:
        for query in QUERIES:
            clean_query = query.replace(" ", "+")
            rss_url = f"https://{region}.craigslist.org/search/sss?query={clean_query}&format=rss"
            
            try:
                # 2. FETCH WITH REQUESTS FIRST
                response = requests.get(rss_url, headers=headers, timeout=10)
                
                # Only parse if the request was successful
                if response.status_code == 200:
                    # Pass the raw XML content to feedparser
                    feed = feedparser.parse(response.content)
                    
                    for entry in feed.entries:
                        post_id = entry.link
                        if post_id not in seen_ids:
                            item_data = {
                                "title": entry.title,
                                "link": entry.link,
                                "region": region
                            }
                            print(f"Found: {entry.title}")
                            seen_ids.append(post_id)
                            new_finds.append(item_data)
                else:
                    print(f"⚠️ Blocked or failed for {region} (Status: {response.status_code})")
                        
            except Exception as e:
                print(f"Error checking {region}: {e}")
            
            time.sleep(2) # Increased sleep slightly to be safer

    save_memory(seen_ids)
    
    # 3. FORCE A DEBUG EMAIL (Optional: Uncomment next line to test email even if list is empty)
    # new_finds.append({"title": "Test Item", "link": "http://google.com", "region": "Test"})

    if new_finds:
        send_email_alert(new_finds)
    else:
        print("No new items found today.")

if __name__ == "__main__":
    check_craigslist()
