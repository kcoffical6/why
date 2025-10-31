import asyncio
import telegram
import requests
from bs4 import BeautifulSoup
from html import unescape
import time
import sys
from urllib.parse import urljoin

# --- CONFIGURATION ---
# IMPORTANT: Fill these variables before running!

# 1. Telegram Config
BOT_TOKEN = 'YOUR_BOT_TOKEN'
CHAT_ID = 'YOUR_CHAT_ID'

# 2. Nitter Config
NITTER_INSTANCE_URL = 'https://nitter.net'

# 3. <<-- ADD ALL YOUR ACCOUNTS HERE -->>
TARGET_USERNAMES = [
    'NASA',
    'IamHCB',
    'SpaceX' 
]

# --- ADVANCED CONFIGURATION ---
SLEEP_INTERVAL = 900  # 15 minutes
SLEEP_BETWEEN_ACCOUNTS = 10 # 10 seconds

# --- SCRIPT ---

def get_full_nitter_url(base_url, path):
    return urljoin(base_url, path)

async def check_account(bot, username):
    sent_posts_file = f"sent_posts_{username}.txt"
    sent_post_links = set()
    
    target_url = f"{NITTER_INSTANCE_URL}/{username}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    # --- NEW LOGIC for first run ---
    try:
        with open(sent_posts_file, 'r') as f:
            sent_post_links.update(line.strip() for line in f)
    except FileNotFoundError:
        print(f"\n--- First run for account: {username} ---")
        print(f"-> '{sent_posts_file}' not found. Populating memory without posting...")
        try:
            response = requests.get(target_url, headers=headers, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                tweets = soup.find_all('div', class_='timeline-item')
                initial_links = set()
                for tweet in tweets:
                    link_tag = tweet.find('a', class_='tweet-link')
                    if link_tag and 'href' in link_tag.attrs:
                        initial_links.add(get_full_nitter_url(NITTER_INSTANCE_URL, link_tag['href']))
                
                with open(sent_posts_file, 'w') as f:
                    for link in initial_links:
                        f.write(f"{link}\n")
                print(f"-> Memory populated with {len(initial_links)} initial posts. Normal checking will begin on the next cycle.")
            else:
                print(f"-> Could not fetch initial posts for {username}. Status: {response.status_code}")
        except Exception as e:
            print(f"-> An error occurred during initial population for {username}: {e}")
        return # IMPORTANT: Stop processing this account for this cycle

    # --- Regular Check (if memory file exists) ---
    print(f"\n--- Checking account: {username} ---")
    print(f"URL: {target_url}")

    try:
        response = requests.get(target_url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"-> Error: Nitter returned status {response.status_code}. Skipping.")
            return

        soup = BeautifulSoup(response.content, 'html.parser')
        tweets = soup.find_all('div', class_='timeline-item')
        
        if not tweets:
            print("-> No tweets found on page.")
            return

        new_posts_found = 0
        for tweet in reversed(tweets):
            if tweet.find('div', class_='retweet-header'):
                continue

            link_tag = tweet.find('a', class_='tweet-link')
            if not link_tag or 'href' not in link_tag.attrs:
                continue

            post_full_link = get_full_nitter_url(NITTER_INSTANCE_URL, link_tag['href'])

            if post_full_link not in sent_post_links:
                new_posts_found += 1
                
                content_div = tweet.find('div', class_='tweet-content')
                post_text = unescape(content_div.get_text(strip=True)) if content_div else ""
                
                image_tags = tweet.find_all('a', class_='still-image')
                image_urls = [get_full_nitter_url(NITTER_INSTANCE_URL, tag['href']) for tag in image_tags]
                num_images = len(image_urls)
                
                print(f"-> New post found for {username}: '{post_text[:60]}...' ({num_images} images)")
                
                try:
                    if num_images > 1:
                        caption_text = post_text[:1020] + '...' if len(post_text) > 1024 else post_text
                        media_group = [telegram.InputMediaPhoto(media=image_urls[0], caption=caption_text)]
                        media_group.extend([telegram.InputMediaPhoto(media=url) for url in image_urls[1:]])
                        await bot.send_media_group(chat_id=CHAT_ID, media=media_group)
                        print("   ...Sent as a media group.")
                    elif num_images == 1:
                        caption_text = post_text[:1020] + '...' if len(post_text) > 1024 else post_text
                        await bot.send_photo(chat_id=CHAT_ID, photo=image_urls[0], caption=caption_text)
                        print("   ...Sent with a single image.")
                    elif post_text:
                        message_text = post_text[:4090] + '...' if len(post_text) > 4096 else post_text
                        await bot.send_message(chat_id=CHAT_ID, text=message_text)
                        print("   ...Sent as text-only.")

                    with open(sent_posts_file, 'a') as f:
                        f.write(f"{post_full_link}\n")
                    sent_post_links.add(post_full_link)
                    await asyncio.sleep(5)

                except Exception as e:
                    print(f"   !!! Telegram API Error for {username}: {e}")
        
        if new_posts_found == 0:
            print("-> No new posts found for this account.")

    except Exception as e:
        print(f"!!! An unexpected error occurred while checking {username}: {e}")


async def main():
    if 'YOUR_' in BOT_TOKEN or 'YOUR_' in CHAT_ID:
        print("!!! ERROR: Please edit the script and fill in your BOT_TOKEN and CHAT_ID.")
        sys.exit(1)

    bot = telegram.Bot(token=BOT_TOKEN)
    print("Multi-Account Master Bot started!")

    while True:
        print("\n=========================================")
        print(f"Starting new check cycle at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        for username in TARGET_USERNAMES:
            await check_account(bot, username)
            print(f"Waiting for {SLEEP_BETWEEN_ACCOUNTS} seconds before next account...")
            await asyncio.sleep(SLEEP_BETWEEN_ACCOUNTS)
        
        print("\nFinished checking all accounts.")
        print(f"Sleeping for {SLEEP_INTERVAL / 60:.0f} minutes...")
        print("=========================================")
        await asyncio.sleep(SLEEP_INTERVAL)

if __name__ == '__main__':
    asyncio.run(main())
