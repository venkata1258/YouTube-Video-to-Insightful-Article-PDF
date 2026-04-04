from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
import re


def extract_video_id(url: str) -> str | None:
    """Extract the YouTube video ID from various URL formats."""
    patterns = [
        r"(?:v=|\/)([0-9A-Za-z_-]{11}).*",
        r"(?:youtu\.be\/)([0-9A-Za-z_-]{11})",
        r"(?:embed\/)([0-9A-Za-z_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def get_transcript(url: str):
    """
    Fetch the transcript for a YouTube video.
    Returns:
        (transcript_text, video_title_or_error_message)
    """
    video_id = extract_video_id(url)

    if not video_id:
        return None, "Invalid YouTube URL. Please check and try again."

    try:
        # ✅ NEW API (v1.2.4)
        api = YouTubeTranscriptApi()
        transcript = api.fetch(video_id)

        # Convert transcript objects to text
        full_text = " ".join([entry.text for entry in transcript])

        # Clean transcript
        full_text = re.sub(r'\[.*?\]', '', full_text)
        full_text = re.sub(r'\s+', ' ', full_text).strip()

        video_title = f"YouTube Video ({video_id})"

        return full_text, video_title

    except TranscriptsDisabled:
        return None, "Transcripts are disabled for this video."
    except NoTranscriptFound:
        return None, "No transcript found for this video."
    except Exception as e:
        return None, f"Error fetching transcript: {str(e)}"


# ✅ TEST BLOCK (VERY IMPORTANT)
if __name__ == "__main__":
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    text, title = get_transcript(url)

    print("TITLE:", title)

    if text:
        print("\nTRANSCRIPT SAMPLE:\n")
        print(text[:500])
    else:
        print("\nNo transcript available.")