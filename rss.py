import asyncio
import telegram
from ntscraper import Nitter
import time

BOT_TOKEN = '7801655479:AAHXYk2f0Hn8jKlUSQnWbpeNNv8fwCLWTDI'
CHAT_ID = '-1003270118980'
TARGET_USERNAMES = ['tv9kannada', 'IamHCB', 'SpaceX']
SLEEP_INTERVAL = 900
SLEEP_BETWEEN_ACCOUNTS = 30

scraper = Nitter(log_level=1, skip_instance_check=False)

async def check_account(bot, username):
    sent_file = f"sent_posts_{username}.txt"
    
    try:
        with open(sent_file, 'r') as f:
            sent_links = set(line.strip() for line in f)
    except FileNotFoundError:
        print(f"
--- First run: {username} ---")
        sent_links = set()
    
    print(f"
--- Checking: {username} ---")
    
    try:
        tweets = scraper.get_tweets(username, mode='user', number=20)
        
        if not tweets or 'tweets' not in tweets:
            print(f"No tweets found")
            return
        
        new = []
        for t in tweets['tweets']:
            link = t.get('link', '')
            if link and link not in sent_links:
                new.append({'link': link, 'text': t.get('text', '')})
        
        if not new:
            print(f"No new tweets")
            return
        
        print(f"Found {len(new)} new tweets")
        
        for post in new:
            msg = f"New tweet from @{username}

{post['text']}

{post['link']}"
            try:
                await bot.send_message(chat_id=CHAT_ID, text=msg[:4096])
                sent_links.add(post['link'])
                print(f"Posted successfully")
            except Exception as e:
                print(f"Error posting: {e}")
            await asyncio.sleep(2)
        
        with open(sent_file, 'w') as f:
            for link in sent_links:
                f.write(link + '
')
    
    except Exception as e:
        print(f"Error: {e}")

async def main():
    bot = telegram.Bot(token=BOT_TOKEN)
    print("Bot started!")
    
    while True:
        print(f"
{'='*40}
Cycle: {time.strftime('%H:%M:%S')}")
        for user in TARGET_USERNAMES:
            await check_account(bot, user)
            await asyncio.sleep(SLEEP_BETWEEN_ACCOUNTS)
        print(f"
Sleeping {SLEEP_INTERVAL//60} minutes...")
        await asyncio.sleep(SLEEP_INTERVAL)

if __name__ == '__main__':
    asyncio.run(main())
