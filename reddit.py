import os
from dotenv import load_dotenv
import praw
from orders import process_order, process_user
from logger import logger

def initialize_reddit_client() -> praw.Reddit:
    required_vars = [
        "REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET", 
        "REDDIT_USERNAME", "REDDIT_PASSWORD", 
        "REDDIT_USER_AGENT"
    ]
    
    missing_vars = [var for var in required_vars if os.getenv(var) is None]
    
    if missing_vars:
        error_message = f"Missing environment variables: {', '.join(missing_vars)}"
        logger.error(error_message)
        raise ValueError(error_message)

    client_id: str = os.getenv("REDDIT_CLIENT_ID")
    client_secret: str = os.getenv("REDDIT_CLIENT_SECRET")
    username: str = os.getenv("REDDIT_USERNAME")
    password: str = os.getenv("REDDIT_PASSWORD")
    user_agent: str = os.getenv("REDDIT_USER_AGENT")

    try:
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            username=username,
            password=password,
            user_agent=user_agent
        )
        
        logger.info("Successfully initialized Reddit client.")
        return reddit
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

def monitor_subreddit():
    subreddit_name = os.getenv("SUBREDDIT_NAME")
    if subreddit_name is None:
        logger.error(f"Missing environment variable: SUBREDDIT_NAME")
    subreddit = reddit.subreddit(SUBREDDIT_NAME)
    for post in subreddit.stream.submissions(skip_existing=True):
        client = post.author
        if "buy" in post.title.lower() or "sell" in post.title.lower():
            verdict = process_order(post.title, client.name)
            print(verdict)
            if "success" in verdict:
                post.author.message(subject="Congrats !!", message=verdict["success"])
                post.reply(f"Congrats!!: {verdict['success']}")
            else:
                post.author.message(subject="BROKEN :(", message=verdict["error"])
                post.mod.remove()
        
        elif "MY!" == post.title:
            result = process_user(client.name)
            print(result)
            if "error" in result:
                post.author.message(subject="BROKEN :(", message=result["error"])
                post.mod.remove()
            else:
                post.reply(result)
        elif "LEADERBOARD" in post.title:
            print("LEADERBOARD OF THE DAY")
        else:
            post.author.message(subject="BROKEN :(", message="Please send a proper request to the bot!!")
            post.mod.remove()

if __name__ == "__main__":
    print("Bot is running...")
    load_dotenv(dotenv_path=".env")
    monitor_subreddit()
