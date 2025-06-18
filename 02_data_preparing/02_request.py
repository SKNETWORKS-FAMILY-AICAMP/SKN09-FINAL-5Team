import requests

redirect_uri = "http://localhost:8080"
client_id = "MY_GOOGLE_CLIENT_ID"  # 자신의 Google OAuth 클라이언트 ID로 변경
client_secret = "MY_GOOGLE_CLIENT_SECRET"  # 자신의 Google OAuth 클라이언트 시크릿으로 변경
auth_code = "MY_GOOGLE_AUTH_TOKEN=https://www.googleapis.com/auth/youtube.readonly"
token_url = "https://oauth2.googleapis.com/token"

data = {
    "code": auth_code,
    "client_id": client_id,
    "client_secret": client_secret,
    "redirect_uri": redirect_uri,
    "grant_type": "authorization_code"
}

res = requests.post(token_url, data=data)
tokens = res.json()
access_token = tokens["access_token"]
refresh_token = tokens.get("refresh_token")

print("Access Token:", access_token)
print("Refresh Token:", refresh_token)
