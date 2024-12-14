import os
from dotenv import load_dotenv
import praw
from orders import process_order, process_user

load_dotenv(dotenv_path=".env")

reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    username=os.getenv("REDDIT_USERNAME"),
    password=os.getenv("REDDIT_PASSWORD"),
    user_agent=os.getenv("REDDIT_USER_AGENT")
)

SUBREDDIT_NAME = os.getenv("SUBREDDIT_NAME")

def monitor_subreddit():
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
    monitor_subreddit()
