import asyncio
import telegram
from ntscraper import Nitter
import time

# Configuration
BOT_TOKEN = '7801655479:AAHXYk2f0Hn8jKlUSQnWbpeNNv8fwCLWTDI'
CHAT_ID = '-1003270118980'
TARGET_USERNAMES = ['tv9kannada', 'IamHCB', 'SpaceX']
SLEEP_INTERVAL = 180  # 15 minutes
SLEEP_BETWEEN_ACCOUNTS = 30

# Initialize scraper
scraper = Nitter(log_level=1, skip_instance_check=False)

async def check_account(bot, username):
    sent_posts_file = f"sent_posts_{username}.txt"
    
    # Load memory
    try:
        with open(sent_posts_file, 'r') as f:
            sent_post_links = set(line.strip() for line in f)
    except FileNotFoundError:
        print(f"-> First run for {username}. Populating memory...")
        sent_post_links = set()
    
    print(f"
--- Checking account: {username} ---")
    
    try:
        # Scrape tweets using ntscraper
        tweets = scraper.get_tweets(username, mode='user', number=20)
        
        if not tweets or 'tweets' not in tweets:
            print(f"-> No tweets found for {username}")
            return
        
        new_posts = []
        for tweet in tweets['tweets']:
            tweet_link = tweet.get('link', '')
            if not tweet_link or tweet_link in sent_post_links:
                continue
            
            new_posts.append({
                'link': tweet_link,
                'text': tweet.get('text', ''),
                'date': tweet.get('date', '')
            })
        
        if not new_posts:
            print(f"-> No new tweets for {username}")
            return
        
        print(f"-> Found {len(new_posts)} new tweets")
        
        # Post to Telegram
        for post in new_posts:
            message = f"🐦 New tweet from @{username}

{post['text']}

🔗 {post['link']}"
            try:
                await bot.send_message(chat_id=CHAT_ID, text=message)
                sent_post_links.add(post['link'])
                print(f"✅ Posted: {post['link']}")
            except Exception as e:
                print(f"❌ Failed to post: {e}")
            
            await asyncio.sleep(2)
        
        # Save memory
        with open(sent_posts_file, 'w') as f:
            for link in sent_post_links:
                f.write(link + '
')
    
    except Exception as e:
        print(f"-> Error checking {username}: {e}")

async def main():
    bot = telegram.Bot(token=BOT_TOKEN)
    
    while True:
        for username in TARGET_USERNAMES:
            await check_account(bot, username)
            await asyncio.sleep(SLEEP_BETWEEN_ACCOUNTS)
        
        print(f"
💤 Sleeping for {SLEEP_INTERVAL} seconds...")
        await asyncio.sleep(SLEEP_INTERVAL)

if __name__ == '__main__':
    asyncio.run(main())
