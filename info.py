from dotenv import load_dotenv
import os
load_dotenv()

useragent = os.getenv("useragent")
client_id = os.getenv("client_id")
client_secret = os.getenv("client_secret")
bot_username = os.getenv("bot_username")
bot_pass = os.getenv("bot_pass")
