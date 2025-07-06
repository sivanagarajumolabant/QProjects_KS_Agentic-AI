# Configuration file for Azure AI Voice-Over Conversion
import os

# Azure Speech Services Configuration
AZURE_SPEECH_KEY = "7vEN1vU4kDITosB5kdtfro11U330ybXV2dZYzJZaCj66B7Y09Q2fJQQJ99BGACYeBjFXJ3w3AAAYACOGbGQD"
AZURE_SPEECH_REGION = "eastus"  # e.g., eastus, westus2, etc.
AZURE_SPEECH_ENDPOINT = f"https://{AZURE_SPEECH_REGION}.api.cognitive.microsoft.com"

# Azure Storage Configuration
AZURE_STORAGE_ACCOUNT_NAME = "qmigstg1137"
AZURE_STORAGE_ACCOUNT_KEY = "798dOb0MWQHF2eaHgMgmjJNw8pg1MIv7IXGWMB6ZZORNu3rNwDM2QbsNhwzFjw/0CK1kie648Zkf+ASt851p7w=="
AZURE_STORAGE_CONNECTION_STRING = f"DefaultEndpointsProtocol=https;AccountName={AZURE_STORAGE_ACCOUNT_NAME};AccountKey={AZURE_STORAGE_ACCOUNT_KEY};EndpointSuffix=core.windows.net"

# Azure Blob Storage Containers
AZURE_CONTAINER_VIDEOS = "qmvideos"
AZURE_CONTAINER_AUDIO = "qmaudio"
AZURE_CONTAINER_OUTPUT = "qmoutput"

# Azure CDN Configuration (optional)
AZURE_CDN_ENDPOINT = "ai-voice-endpoint-eeg4h9bud7e3hcad.z02.azurefd.net"
AZURE_CDN_PROFILE = "ai-voice-cdn"

# Azure Speech Services Settings
AZURE_SPEECH_STT_CONFIG = {
    "language": "en-US",
    "format": "detailed",
    "profanity_filter": "masked"
}

AZURE_SPEECH_TTS_CONFIG = {
    "voice_name": "en-US-AriaNeural",  # High-quality neural voice
    "language": "en-US",
    "output_format": "audio-24khz-48kbitrate-mono-mp3"
}

# Alternative voice options
AZURE_VOICE_OPTIONS = {
    "aria": "en-US-AriaNeural",
    "jenny": "en-US-JennyNeural", 
    "guy": "en-US-GuyNeural",
    "davis": "en-US-DavisNeural",
    "jane": "en-US-JaneNeural"
}

# Processing Settings
MAX_FILE_SIZE_MB = 200  # Azure supports larger files
SUPPORTED_VIDEO_FORMATS = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.wmv']
SUPPORTED_AUDIO_FORMATS = ['.mp3', '.wav', '.m4a', '.flac', '.aac']

# Output Settings
OUTPUT_FOLDER = "output"
TEMP_FOLDER = "temp"
LOG_FILE = "azure_voice_conversion.log"

# Processing Settings
CHUNK_SIZE = 8192
POLLING_INTERVAL = 2  # Azure is typically faster
MAX_WAIT_TIME = 600  # 10 minutes for larger files

# Azure Speech Service Limits
AZURE_STT_MAX_FILE_SIZE = 200 * 1024 * 1024  # 200MB
AZURE_TTS_MAX_TEXT_LENGTH = 10000  # 10K characters per request
AZURE_TTS_SSML_MAX_LENGTH = 40000  # 40K characters with SSML

# Create necessary directories
def create_directories():
    """Create necessary directories if they don't exist"""
    directories = [OUTPUT_FOLDER, TEMP_FOLDER]
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Created directory: {directory}")

# Azure Resource Group and Subscription (for advanced features)
AZURE_SUBSCRIPTION_ID = "fa58c1ad-8aa3-4326-b2e2-c60d54678fe7"
AZURE_RESOURCE_GROUP = "Qmig-AI"

if __name__ == "__main__":
    create_directories()
