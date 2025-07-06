import asyncio
from httpx_oauth.clients.google import GoogleOAuth2

CLIENT_ID = "40788949411-sd1ebbdqnrb8phbhke29pupbqq6c1lp7.apps.googleusercontent.com"
CLIENT_SECRET = "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"
REDIRECT_URI = "http://localhost:8501"

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