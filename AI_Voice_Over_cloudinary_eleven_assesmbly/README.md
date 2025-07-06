# AI Voice-Over Conversion Tool

Automate the process of replacing human voice with AI voice in videos using Python.

## Features

- 🎬 **Video Processing**: Download and process videos from URLs
- 🎤 **Speech-to-Text**: Transcribe audio using AssemblyAI
- 🤖 **AI Voice Generation**: Generate natural AI voices using ElevenLabs
- 🔄 **Audio Replacement**: Replace original audio with AI-generated voice
- ☁️ **Cloud Storage**: Upload results to Cloudinary
- 📊 **Progress Tracking**: Real-time progress updates and logging

## Prerequisites

1. **API Keys** (already configured in `config.py`):
   - AssemblyAI API Key
   - ElevenLabs API Key
   - Cloudinary credentials

2. **Python 3.7+**

## Installation

1. **Navigate to the project directory:**
   ```bash
   cd AI_Voice_Over
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Update Cloudinary cloud name in `config.py`:**
   ```python
   CLOUDINARY_CLOUD_NAME = "your_actual_cloud_name"  # Replace with your cloud name
   ```

## Usage

### Command Line Interface

**Basic usage:**
```bash
python main.py "https://example.com/video.mp4"
```

**With custom voice:**
```bash
python main.py "https://example.com/video.mp4" --voice-id "29vD33N1CtxCmqQRPOHJ"
```

**Save locally only (skip Cloudinary):**
```bash
python main.py "https://example.com/video.mp4" --output-only
```

### Python Script Usage

```python
from voice_converter import VoiceConverter

# Initialize converter
converter = VoiceConverter()

# Process video
result = converter.process_video("https://example.com/video.mp4")

if result:
    print(f"Success! Output: {result}")
else:
    print("Processing failed")
```

### Available Voices (ElevenLabs Free Tier)

- **Rachel** (Default): `21m00Tcm4TlvDq8ikWAM`
- **Drew**: `29vD33N1CtxCmqQRPOHJ`
- **Clyde**: `2EiwWnXFnvU5JabPnv8n`
- **Paul**: `5Q0t7uMcjvnagumLfvZi`

## Examples

Run the example script to see different usage patterns:
```bash
python example_usage.py
```

## File Structure

```
AI_Voice_Over/
├── config.py              # Configuration and API keys
├── voice_converter.py     # Main conversion class
├── main.py               # Command-line interface
├── example_usage.py      # Usage examples
├── requirements.txt      # Python dependencies
├── README.md            # This file
├── output/              # Generated videos (created automatically)
├── temp/                # Temporary files (created automatically)
└── voice_conversion.log # Processing logs
```

## Process Flow

1. **Download Video** → Download video from provided URL
2. **Extract Audio** → Extract audio track from video
3. **Upload to AssemblyAI** → Upload audio for transcription
4. **Transcribe** → Convert speech to text
5. **Generate AI Voice** → Create AI voice from transcript using ElevenLabs
6. **Replace Audio** → Replace original audio with AI voice in video
7. **Upload to Cloud** → Upload final video to Cloudinary
8. **Cleanup** → Remove temporary files

## API Limits (Free Tiers)

- **AssemblyAI**: 5 hours/month
- **ElevenLabs**: 10,000 characters/month
- **Cloudinary**: 25 credits/month

## Troubleshooting

1. **Check logs**: Review `voice_conversion.log` for detailed error information
2. **API limits**: Ensure you haven't exceeded free tier limits
3. **File formats**: Supported video formats: MP4, AVI, MOV, MKV, WebM
4. **Internet connection**: Ensure stable connection for API calls and downloads

## Configuration

Edit `config.py` to customize:
- Voice settings (stability, similarity boost)
- File size limits
- Processing timeouts
- Output directories

## Support

For issues or questions, check the logs first. Common issues:
- Invalid video URLs
- API key authentication errors
- Network connectivity problems
- File format compatibility
