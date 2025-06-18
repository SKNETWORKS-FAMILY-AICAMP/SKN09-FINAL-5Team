import os
import json
import time
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

# === 설정 및 환경변수 로드 ===
API_KEY = "MY_YOUTUBE_API_KEY"  # 여기에 자신의 YouTube API 키를 입력하세요

if not API_KEY:
    API_KEY = input("Enter your YouTube API key: ").strip()
if not API_KEY:
    raise RuntimeError("YOUTUBE_API_KEY가 설정되지 않았습니다.")

# 채널명(표시용) -> 핸들(@로 시작 또는 미포함)
CHANNEL_HANDLES = {
    "안될과학": "@Unrealscience",
    "에스오디": "@softdragon",
    "우주먼지의 현자타임즈": "@wz_mz",
    "지식인미나니": "@iamminani",
    "지식은 날리지": "@jisikisknowledge1620",
    "보다": "@보다BODA",
    "과학드림": "@ScienceDream",
    "한눈에 보는 세상": "@kurzgesagt_kr",
    "1분과학": "@1minscience",
    "과학쿠키": "@snceckie",
    "긱블": "@geekble_kr",
    "이준석": "@junseoktube"
}

OUTPUT_FILE = "./02_data_preprocessing/youtube_scripts.jsonl"
DELAY = 0.3  # API 호출 간 대기 시간 (초)

# YouTube Data API 클라이언트
youtube = build('youtube', 'v3', developerKey=API_KEY)

# === 1. 핸들로부터 채널 ID 가져오기 & 검증 ===
def get_channel_id(handle: str) -> str:
    """
    @handle 또는 handle 그대로 사용.
    반환: 채널 ID(UCxxx)
    """
    h = handle.lstrip('@')
    resp = youtube.channels().list(
        part="id, snippet",
        forHandle=h
    ).execute()
    items = resp.get('items', [])
    if not items:
        raise ValueError(f"핸들 '{handle}'에 해당하는 채널을 찾을 수 없습니다.")
    channel = items[0]
    cid = channel['id']
    # 검증: 반환된 스니펫의 customUrl 혹은 title 확인
    title = channel['snippet'].get('title', '')
    print(f"[OK] 핸들 {handle} -> 채널ID {cid} (채널명: '{title}')")
    return cid

# === 2. 업로드 플레이리스트 ID 조회 ===
def get_uploads_playlist_id(channel_id: str) -> str:
    resp = youtube.channels().list(
        part="contentDetails",
        id=channel_id
    ).execute()
    items = resp.get('items', [])
    if not items:
        raise ValueError(f"채널ID '{channel_id}'에 대한 콘텐츠 상세 정보가 없습니다.")
    uploads_pl = items[0]['contentDetails']['relatedPlaylists']['uploads']
    print(f"[OK] 채널ID {channel_id} -> 업로드 목록 플레이리스트ID {uploads_pl}")
    return uploads_pl

# === 3. 플레이리스트에서 영상 ID 수집 ===
def fetch_video_ids(playlist_id: str) -> list[str]:
    ids = []
    req = youtube.playlistItems().list(
        part="contentDetails",
        playlistId=playlist_id,
        maxResults=50
    )
    while req:
        res = req.execute()
        for it in res.get('items', []):
            vid = it['contentDetails']['videoId']
            ids.append(vid)
        time.sleep(DELAY)
        req = youtube.playlistItems().list_next(req, res)
    print(f"[OK] 플레이리스트 {playlist_id}에서 {len(ids)}개 영상 ID 수집")
    return ids

# === 4. 영상 제목 조회 ===
def get_video_title(video_id: str) -> str:
    resp = youtube.videos().list(
        part="snippet",
        id=video_id
    ).execute()
    items = resp.get('items', [])
    if not items:
        return None
    return items[0]['snippet']['title']

# === 5. 영상 스크립트 추출 ===
def fetch_transcript(video_id: str, langs=['ko', 'en']) -> str:
    try:
        segs = YouTubeTranscriptApi.get_transcript(video_id, languages=langs)
        text = ' '.join(s['text'] for s in segs)
        time.sleep(DELAY)
        return text
    except (TranscriptsDisabled, NoTranscriptFound) as e:
        print(f"[WARN] 자막 없음: {video_id} -> {e}")
        return None
    except Exception as e:
        print(f"[ERROR] 스크립트 추출 실패: {video_id} -> {e}")
        return None

# === 메인 실행 흐름 ===
def main():
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as fout:
        for channel_name, handle in CHANNEL_HANDLES.items():
            try:
                cid = get_channel_id(handle)
                upl_pl = get_uploads_playlist_id(cid)
            except Exception as e:
                print(f"[SKIP] 채널 처리 실패: {channel_name} ({handle}) -> {e}")
                continue
            video_ids = fetch_video_ids(upl_pl)
            for vid in video_ids:
                title = get_video_title(vid)
                script = fetch_transcript(vid)
                if not title or not script:
                    continue
                rec = {"input": title, "output": script}
                fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
                print(f"[SAVE] {channel_name} - {title} 저장 완료")
    print(f">> 완료: {OUTPUT_FILE} 생성됨")

if __name__ == '__main__':
    main()
