# 🎬 Azure AI Voice-Over Conversion Tool

A complete Azure-native solution for automatically replacing human voice in videos with AI-generated voice using only Microsoft Azure services.

## 🌟 Features

- **Azure Speech Services**: Speech-to-Text and Text-to-Speech
- **Azure Blob Storage**: Secure video and audio storage
- **Azure CDN**: Global content delivery (optional)
- **High-Quality Neural Voices**: Multiple Azure neural voice options
- **Enterprise Ready**: Built on Azure's enterprise-grade infrastructure
- **Unified Management**: Single Azure subscription for all services

## 🏗️ Architecture

### Azure Services Used:
- **Azure Cognitive Services - Speech**: STT and TTS processing
- **Azure Blob Storage**: File storage and management
- **Azure CDN**: Global content delivery (optional)

### Replaced Services:
- ❌ AssemblyAI → ✅ Azure Speech Services (STT)
- ❌ ElevenLabs → ✅ Azure Speech Services (TTS)
- ❌ Cloudinary → ✅ Azure Blob Storage + CDN

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.8+
- Azure subscription
- Azure Speech Services resource
- Azure Storage Account

### 2. Azure Setup

#### Create Azure Speech Services:
```bash
# Using Azure CLI
az cognitiveservices account create \
  --name "your-speech-service" \
  --resource-group "your-resource-group" \
  --kind "SpeechServices" \
  --sku "F0" \
  --location "eastus"
```

#### Create Azure Storage Account:
```bash
# Using Azure CLI
az storage account create \
  --name "yourstorageaccount" \
  --resource-group "your-resource-group" \
  --location "eastus" \
  --sku "Standard_LRS"
```

### 3. Installation

```bash
# Clone or create the project
cd AI_Voice_Over_Azure

# Install dependencies
pip install -r requirements.txt
```

### 4. Configuration

Edit `config.py` with your Azure credentials:

```python
# Azure Speech Services
AZURE_SPEECH_KEY = "your_azure_speech_key"
AZURE_SPEECH_REGION = "eastus"

# Azure Storage
AZURE_STORAGE_ACCOUNT_NAME = "yourstorageaccount"
AZURE_STORAGE_ACCOUNT_KEY = "your_storage_key"
```

### 5. Usage

```bash
# Basic usage
python main.py "https://example.com/video.mp4"

# With specific voice
python main.py "https://example.com/video.mp4" --voice jenny

# List available voices
python main.py --list-voices
```

## 🎤 Available Voices

| Voice Key | Azure Voice Name | Description |
|-----------|------------------|-------------|
| `aria` | en-US-AriaNeural | Natural, friendly female voice |
| `jenny` | en-US-JennyNeural | Professional female voice |
| `guy` | en-US-GuyNeural | Casual male voice |
| `davis` | en-US-DavisNeural | Professional male voice |
| `jane` | en-US-JaneNeural | Warm female voice |

## 📁 Project Structure

```
AI_Voice_Over_Azure/
├── config.py                 # Azure configuration
├── azure_voice_converter.py  # Main conversion logic
├── main.py                   # CLI interface
├── requirements.txt          # Dependencies
├── README.md                 # This file
├── temp/                     # Temporary files
└── output/                   # Local output files
```

## 🔧 Configuration Options

### Azure Speech Services Settings:
```python
AZURE_SPEECH_STT_CONFIG = {
    "language": "en-US",
    "format": "detailed",
    "profanity_filter": "masked"
}

AZURE_SPEECH_TTS_CONFIG = {
    "voice_name": "en-US-AriaNeural",
    "language": "en-US",
    "output_format": "audio-24khz-48kbitrate-mono-mp3"
}
```

### Processing Limits:
- **Max File Size**: 200MB (Azure supports larger files)
- **Max Text Length**: 10,000 characters per TTS request
- **Supported Formats**: MP4, AVI, MOV, MKV, WebM, WMV

## 💰 Cost Estimation

### Azure Speech Services:
- **Speech-to-Text**: $1.00 per hour of audio
- **Text-to-Speech**: $4.00 per 1M characters

### Azure Storage:
- **Blob Storage**: $0.018 per GB/month
- **Bandwidth**: $0.087 per GB (first 5GB free)

### Example Cost for 10-minute video:
- STT: ~$0.17 (10 minutes)
- TTS: ~$0.02 (5,000 characters)
- Storage: ~$0.01 (temporary)
- **Total**: ~$0.20 per video

## 🔒 Security Features

- **Azure AD Integration**: Enterprise authentication
- **Private Endpoints**: VNet integration available
- **Encryption**: Data encrypted at rest and in transit
- **Access Control**: Role-based access control (RBAC)
- **Compliance**: SOC, ISO, HIPAA compliant

## 🚀 Advanced Features

### Custom Voice Training:
```python
# Configure custom voice (requires Azure Custom Voice)
AZURE_SPEECH_TTS_CONFIG = {
    "voice_name": "your-custom-voice-name",
    "language": "en-US"
}
```

### Batch Processing:
```python
# Process multiple videos
converter = AzureVoiceConverter()
for video_url in video_urls:
    result = converter.process_video(video_url)
```

## 🔍 Troubleshooting

### Common Issues:

1. **Authentication Error**:
   - Verify Azure Speech key and region
   - Check Azure Storage connection string

2. **File Upload Error**:
   - Ensure storage containers exist
   - Check storage account permissions

3. **Speech Recognition Failed**:
   - Verify audio quality (16kHz recommended)
   - Check for background noise

4. **Voice Synthesis Error**:
   - Verify voice name is correct
   - Check text length limits

## 📊 Monitoring

### Azure Portal Monitoring:
- Speech Services usage and costs
- Storage account metrics
- Error logs and diagnostics

### Application Logs:
```bash
# View logs
tail -f azure_voice_conversion.log
```

## 🔄 Migration from Multi-Service Version

### Key Differences:
1. **Single Provider**: All services from Azure
2. **Unified Authentication**: One set of credentials
3. **Better Integration**: Services designed to work together
4. **Enterprise Features**: Advanced security and compliance

### Migration Steps:
1. Set up Azure resources
2. Update configuration
3. Test with sample video
4. Migrate production workloads

## 📞 Support

- **Azure Documentation**: [Azure Speech Services](https://docs.microsoft.com/azure/cognitive-services/speech-service/)
- **Azure Support**: Available through Azure Portal
- **Community**: Azure forums and Stack Overflow

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Built with ❤️ using Microsoft Azure**
