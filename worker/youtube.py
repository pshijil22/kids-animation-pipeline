"""
YouTube upload - Upload finished videos to YouTube using OAuth 2.0
"""
import os
import json
import logging
from pathlib import Path
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

logger = logging.getLogger(__name__)

CREDENTIALS_DIR = Path("/app/credentials")

# YouTube API scope
YOUTUBE_SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


async def upload_to_youtube(video_file: str, metadata: dict) -> dict:
    """
    Upload finished video to YouTube.
    
    Args:
        video_file: Path to MP4 file
        metadata: Video metadata (title, description, tags, etc.)
    
    Returns:
        dict: Upload result with video_id and status
    """
    
    # Create credentials directory on first use
    CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"YouTube upload starting for: {metadata['title']}")
    
    # Check if uploads are enabled
    generate_only = os.getenv('GENERATE_ONLY', 'true').lower() == 'true'
    if generate_only:
        logger.info("GENERATE_ONLY=true, skipping YouTube upload")
        return {
            'status': 'skipped',
            'reason': 'GENERATE_ONLY mode',
            'video_file': video_file
        }
    
    try:
        # Get OAuth credentials
        credentials = get_youtube_credentials()
        
        if not credentials:
            logger.warning("No YouTube credentials available, skipping upload")
            return {
                'status': 'skipped',
                'reason': 'No OAuth credentials',
                'video_file': video_file
            }
        
        # Build YouTube API client
        youtube = build('youtube', 'v3', credentials=credentials)
        
        # Prepare video metadata
        body = {
            'snippet': {
                'title': metadata.get('title', 'Untitled')[:100],
                'description': metadata.get('description', '')[:5000],
                'tags': metadata.get('tags', ['children', 'animation'])[:500],
                'categoryId': '15',  # Category 15 = Kids
                'defaultLanguage': 'en',
                'defaultAudioLanguage': 'en'
            },
            'status': {
                'privacyStatus': metadata.get('privacy_status', 'private'),  # private, unlisted, or public
                'madeForKids': True,
                'embeddable': True,
                'publicStatsViewable': True
            },
            'processingDetails': {
                'processingProgress': {
                    'partsProcessed': 0,
                    'partsTotal': 1
                }
            }
        }
        
        logger.info(f"Uploading video: {metadata.get('title')}")
        logger.info(f"Privacy status: {metadata.get('privacy_status', 'private')}")
        
        # Upload video
        media_body = MediaFileUpload(
            video_file,
            mimetype='video/mp4',
            resumable=True,
            chunksize=10 * 1024 * 1024  # 10 MB chunks
        )
        
        request = youtube.videos().insert(
            part='snippet,status,processingDetails',
            body=body,
            media_body=media_body
        )
        
        # Execute with resumable upload
        response = None
        while response is None:
            try:
                status, response = request.next_chunk()
                if status:
                    percent = int(status.progress() * 100)
                    logger.info(f"Upload progress: {percent}%")
            except Exception as e:
                logger.error(f"Upload chunk failed: {e}")
                raise
        
        video_id = response['id']
        logger.info(f"Video uploaded successfully! Video ID: {video_id}")
        
        return {
            'status': 'success',
            'video_id': video_id,
            'url': f'https://www.youtube.com/watch?v={video_id}',
            'video_file': video_file
        }
        
    except Exception as e:
        logger.error(f"YouTube upload failed: {e}")
        return {
            'status': 'failed',
            'error': str(e),
            'video_file': video_file
        }


def get_youtube_credentials():
    """
    Get valid YouTube API credentials.
    Uses token.json if available, otherwise prompts for OAuth.
    
    Returns:
        Credentials object or None if unavailable
    """
    
    token_file = CREDENTIALS_DIR / 'youtube_token.json'
    creds_file = CREDENTIALS_DIR / 'client_secret.json'
    
    # Load existing token
    if token_file.exists():
        creds = Credentials.from_authorized_user_file(str(token_file), YOUTUBE_SCOPES)
        
        # Refresh if expired
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            
            # Save refreshed token
            with open(token_file, 'w') as f:
                f.write(creds.to_json())
        
        return creds
    
    # No credentials available
    logger.warning("No YouTube credentials found. To enable uploads, set up OAuth:")
    logger.warning(f"1. Place client_secret.json in {CREDENTIALS_DIR}")
    logger.warning(f"2. Run the OAuth flow to generate {token_file}")
    
    return None


def setup_youtube_oauth(client_secret_path: str):
    """
    Set up YouTube OAuth credentials (run once during setup).
    
    Args:
        client_secret_path: Path to client_secret.json from Google Cloud Console
    """
    
    logger.info("Setting up YouTube OAuth...")
    
    # Copy client secret
    import shutil
    shutil.copy(client_secret_path, CREDENTIALS_DIR / 'client_secret.json')
    
    # Run OAuth flow
    flow = InstalledAppFlow.from_client_secrets_file(
        str(CREDENTIALS_DIR / 'client_secret.json'),
        YOUTUBE_SCOPES
    )
    
    creds = flow.run_local_server(port=8080)
    
    # Save token
    token_file = CREDENTIALS_DIR / 'youtube_token.json'
    with open(token_file, 'w') as f:
        f.write(creds.to_json())
    
    logger.info(f"YouTube OAuth set up successfully! Token saved to {token_file}")
