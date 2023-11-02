import requests
import base64
import random
import logging
from typing import Final

eng_voices: Final[tuple] = (
    "en_au_001",  # English AU - Female
    "en_au_002",  # English AU - Male
    "en_uk_001",  # English UK - Male 1
    "en_uk_003",  # English UK - Male 2
    "en_us_001",  # English US - Female (Int. 1)
    "en_us_002",  # English US - Female (Int. 2)
    "en_us_006",  # English US - Male 1
    "en_us_007",  # English US - Male 2
    "en_us_009",  # English US - Male 3
    "en_us_010",  # English US - Male 4
    "en_male_narration",  # Narrator
    "en_male_funny",  # Funny
    "en_female_emotional",  # Peaceful
    "en_male_cody",  # Serious
)

class TikTok:
    BASE_URL = "https://api16-normal-c-useast1a.tiktokv.com/media/api/text/speech/invoke/"

    def __init__(self, session_id):
        self.headers = {
            "User-Agent": "com.zhiliaoapp.musically/2022600030 (Linux; U; Android 7.1.2; es_ES; SM-G988N; Build/NRD90M;tt-ok/3.12.13.1)",
            "Cookie": f"sessionid={session_id}",
        }
        self.session = requests.Session()
        self.session.headers = self.headers

    def text_to_speech(self, text, voice=None):
        logger = logging.getLogger(__name__)
        logger.info(f"Converting text to speech: {text}")

        params = {
            "req_text": text.replace("+", "plus").replace("&", "and").replace("r/", ""),
            "speaker_map_type": 0,
            "aid": 1233
        }
        if voice:
            params["text_speaker"] = voice

        print(voice)

        try:
            response = self.session.post(self.BASE_URL, params=params)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error(f"Request to TikTok API failed: {e}")
            raise TikTokTTSException(0, "Request to TikTok API failed")

        response_data = response.json()
        logger.debug(f"TikTok API response: {response_data}")

        if response_data["status_code"] != 0:
            logger.error(f"TikTok API error: {response_data['message']}")
            raise TikTokTTSException(response_data["status_code"], response_data["message"])

        raw_audio = base64.b64decode(response_data["data"]["v_str"])
        logger.info("Text converted to speech successfully")
        return raw_audio

class TikTokTTSException(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message

    def __str__(self):
        return f"Code: {self.code}, message: {self.message}"

def random_voice(voices):
    return random.choice(voices)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


# Setup
tiktok = TikTok(session_id="82af1c15-41ed-4d7c-b5bf-7f7f670dc1bf")

# Use
text = "Hello, TikTok!"  # Just a sample text
voice = random_voice(eng_voices)  # Using the eng_voices tuple from the provided code

try:
    audio_data = tiktok.text_to_speech(text, voice)
    # Here, audio_data contains the raw audio data.
    # You'd normally save this to a file or process further
    print("Audio data retrieved successfully!")
except TikTokTTSException as e:
    print(f"An error occurred: {e}")