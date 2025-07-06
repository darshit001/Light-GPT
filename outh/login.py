import asyncio
from httpx_oauth.clients.google import GoogleOAuth2
from dotenv import load_dotenv
import os
load_dotenv()
# Load environment variables
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")

google_client = GoogleOAuth2(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    scopes=["openid", "email", "profile"]
)

async def get_authorization_url():
    return await google_client.get_authorization_url(redirect_uri=REDIRECT_URI, state="secure")

async def get_access_token(code: str):
    return await google_client.get_access_token(code=code, redirect_uri=REDIRECT_URI)

async def get_user_info(access_token: str):
    async with google_client.get_httpx_client() as client:
        resp = await client.get(
            "https://www.googleapis.com/oauth2/v1/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        return resp.json()