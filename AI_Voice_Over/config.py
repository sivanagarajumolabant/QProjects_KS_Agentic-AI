# Configuration file for AI Voice-Over Conversion
import os

# API Keys and Credentials
ASSEMBLYAI_API_KEY = "e2cfa8e3ab8e437084a8058a364bdd4c"
ELEVENLABS_API_KEY = "sk_ce4e5f98f87394c7110637cf52bc0b5b0b99e81a0aa1374e"

# Cloudinary Configuration
# TODO: Replace with your actual Cloudinary cloud name from dashboard
CLOUDINARY_CLOUD_NAME = "dbrdhflda"  # REQUIRED: Get this from your Cloudinary dashboard
CLOUDINARY_API_KEY = "196451171995424"
CLOUDINARY_API_SECRET = "pbl_EktMbeY32OZIycKG4Dtq8Bo"

# API Endpoints
ASSEMBLYAI_UPLOAD_URL = "https://api.assemblyai.com/v2/upload"
ASSEMBLYAI_TRANSCRIPT_URL = "https://api.assemblyai.com/v2/transcript"
ELEVENLABS_TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech"
CLOUDINARY_UPLOAD_URL = f"https://api.cloudinary.com/v1_1/{CLOUDINARY_CLOUD_NAME}/video/upload"

# Default Settings
DEFAULT_VOICE_ID = "9BWtsMINqrJLrRacOk9x"  # Aria voice (available in your account)
DEFAULT_MODEL_ID = "eleven_monolingual_v1"  # Free tier model
MAX_FILE_SIZE_MB = 100  # Maximum file size for processing
SUPPORTED_VIDEO_FORMATS = ['.mp4', '.avi', '.mov', '.mkv', '.webm']
SUPPORTED_AUDIO_FORMATS = ['.mp3', '.wav', '.m4a', '.flac']

# Output Settings
OUTPUT_FOLDER = "output"
TEMP_FOLDER = "temp"
LOG_FILE = "voice_conversion.log"

# Processing Settings
CHUNK_SIZE = 8192  # For file uploads
POLLING_INTERVAL = 5  # Seconds to wait between transcript status checks
MAX_WAIT_TIME = 300  # Maximum time to wait for transcription (5 minutes)

# Voice Settings (Free tier compatible)
VOICE_SETTINGS = {
    "stability": 0.5,
    "similarity_boost": 0.5
}

# Create necessary directories
def create_directories():
    """Create necessary directories if they don't exist"""
    directories = [OUTPUT_FOLDER, TEMP_FOLDER]
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Created directory: {directory}")

if __name__ == "__main__":
    create_directories()
