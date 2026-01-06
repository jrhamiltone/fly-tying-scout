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

def check_craigslist():
    print(f"🕵️  Agent starting scan...")
    seen_ids = load_memory()
    new_finds = []

    for region in REGIONS:
        for query in QUERIES:
            clean_query = query.replace(" ", "+")
            rss_url = f"https://{region}.craigslist.org/search/sss?query={clean_query}&format=rss"
            
            try:
                feed = feedparser.parse(rss_url)
                
                for entry in feed.entries:
                    post_id = entry.link
                    
                    if post_id not in seen_ids:
                        # Store clean data for the email
                        item_data = {
                            "title": entry.title,
                            "link": entry.link,
                            "region": region
                        }
                        
                        print(f"Found: {entry.title}")
                        seen_ids.append(post_id)
                        new_finds.append(item_data)
                        
            except Exception as e:
                print(f"Error checking {region}: {e}")
            
            time.sleep(1) # Be polite to servers

    # Update memory
    save_memory(seen_ids)
    
    # If we found anything, email it
    if new_finds:
        send_email_alert(new_finds)
    else:
        print("No new items found today.")

if __name__ == "__main__":
    check_craigslist()
