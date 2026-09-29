"""Optional YouTube uploader using OAuth 2.0.

Credentials are supplied at runtime through the YOUTUBE_TOKEN_JSON environment variable.
Never commit OAuth tokens or client secrets to the repository.
"""
import json
import logging
import os

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

logger = logging.getLogger(__name__)
YOUTUBE_SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


async def upload_to_youtube(video_file: str, metadata: dict) -> dict:
    token_json = os.getenv("YOUTUBE_TOKEN_JSON", "").strip()
    if not token_json:
        return {"status": "skipped", "reason": "YOUTUBE_TOKEN_JSON is not configured"}

    try:
        info = json.loads(token_json)
        credentials = Credentials.from_authorized_user_info(info, YOUTUBE_SCOPES)
        youtube = build("youtube", "v3", credentials=credentials)

        body = {
            "snippet": {
                "title": metadata.get("title", "Untitled")[:100],
                "description": metadata.get("description", "")[:5000],
                "tags": metadata.get("tags", ["kids", "animation", "story"])[:500],
                "categoryId": "15",
                "defaultLanguage": "en",
                "defaultAudioLanguage": "en",
            },
            "status": {
                "privacyStatus": os.getenv("YOUTUBE_PRIVACY", "private"),
                "madeForKids": True,
                "embeddable": True,
                "publicStatsViewable": True,
            },
        }

        media = MediaFileUpload(
            video_file,
            mimetype="video/mp4",
            resumable=True,
            chunksize=10 * 1024 * 1024,
        )
        request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media,
        )

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                logger.info("YouTube upload: %d%%", int(status.progress() * 100))

        video_id = response["id"]
        logger.info("YouTube upload complete: %s", video_id)
        return {
            "status": "success",
            "video_id": video_id,
            "url": f"https://www.youtube.com/watch?v={video_id}",
        }
    except Exception as exc:
        logger.exception("YouTube upload failed")
        return {"status": "failed", "error": str(exc)}
