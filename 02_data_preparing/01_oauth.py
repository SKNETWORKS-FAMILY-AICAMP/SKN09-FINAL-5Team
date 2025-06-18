import urllib.parse

client_id = "MY_GOOGLE_CLIENT_ID"  # 자신의 Google OAuth 클라이언트 ID로 변경
redirect_uri = "http://localhost:8080"
scope = "https://www.googleapis.com/auth/youtube.readonly"
auth_url = "https://accounts.google.com/o/oauth2/v2/auth"

params = {
    "client_id": client_id,
    "redirect_uri": redirect_uri,
    "response_type": "code",
    "scope": scope,
    "access_type": "offline",  # refresh_token 받으려면 꼭 필요!!!
    "prompt": "consent"  # 강제로 동의 화면 띄우기
}

auth_request_url = f"{auth_url}?{urllib.parse.urlencode(params)}"
print("인증 URL:", auth_request_url)
