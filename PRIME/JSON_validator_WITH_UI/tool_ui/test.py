import os
from dotenv import load_dotenv


load_dotenv()


print("Sender:", os.getenv("EMAIL_SENDER"))
print("Receiver:", os.getenv("EMAIL_RECEIVER"))
print("Password:", os.getenv("EMAIL_APP_PASSWORD"))
