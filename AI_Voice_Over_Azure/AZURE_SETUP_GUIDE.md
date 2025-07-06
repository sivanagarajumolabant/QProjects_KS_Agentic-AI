# 🚀 Azure Setup Guide for AI Voice-Over Conversion

Complete step-by-step guide to set up Azure services for the AI Voice-Over Conversion tool.

## 📋 Prerequisites

- Azure subscription (free tier available)
- Azure CLI installed (optional but recommended)
- Python 3.8+ installed

## 🔧 Step 1: Create Azure Speech Services

### Option A: Using Azure Portal

1. **Go to Azure Portal**: https://portal.azure.com
2. **Create Resource** → Search for "Speech Services"
3. **Fill in details**:
   - **Subscription**: Your Azure subscription
   - **Resource Group**: Create new or use existing
   - **Region**: Choose closest region (e.g., East US)
   - **Name**: `your-speech-service`
   - **Pricing Tier**: F0 (Free) or S0 (Standard)
4. **Review + Create** → **Create**
5. **Get Keys**: Go to resource → Keys and Endpoint → Copy Key 1 and Region

### Option B: Using Azure CLI

```bash
# Login to Azure
az login

# Create resource group (if needed)
az group create --name "ai-voice-rg" --location "eastus"

# Create Speech Services
az cognitiveservices account create \
  --name "ai-voice-speech" \
  --resource-group "ai-voice-rg" \
  --kind "SpeechServices" \
  --sku "F0" \
  --location "eastus"

# Get keys
az cognitiveservices account keys list \
  --name "ai-voice-speech" \
  --resource-group "ai-voice-rg"
```

### Free Tier Limits:
- **Speech-to-Text**: 5 hours per month
- **Text-to-Speech**: 0.5 million characters per month
- **Custom Voice**: Not available in free tier

## 💾 Step 2: Create Azure Storage Account

### Option A: Using Azure Portal

1. **Create Resource** → Search for "Storage Account"
2. **Fill in details**:
   - **Subscription**: Your Azure subscription
   - **Resource Group**: Same as Speech Services
   - **Storage Account Name**: `aivoicestorage` (must be globally unique)
   - **Region**: Same as Speech Services
   - **Performance**: Standard
   - **Redundancy**: LRS (Locally Redundant Storage)
3. **Review + Create** → **Create**
4. **Get Keys**: Go to resource → Access Keys → Copy key1

### Option B: Using Azure CLI

```bash
# Create storage account
az storage account create \
  --name "aivoicestorage123" \
  --resource-group "ai-voice-rg" \
  --location "eastus" \
  --sku "Standard_LRS"

# Get connection string
az storage account show-connection-string \
  --name "aivoicestorage123" \
  --resource-group "ai-voice-rg"
```

### Create Blob Containers:

```bash
# Get storage key
STORAGE_KEY=$(az storage account keys list \
  --account-name "aivoicestorage123" \
  --resource-group "ai-voice-rg" \
  --query "[0].value" -o tsv)

# Create containers
az storage container create \
  --name "videos" \
  --account-name "aivoicestorage123" \
  --account-key "$STORAGE_KEY"

az storage container create \
  --name "audio" \
  --account-name "aivoicestorage123" \
  --account-key "$STORAGE_KEY"

az storage container create \
  --name "output" \
  --account-name "aivoicestorage123" \
  --account-key "$STORAGE_KEY"
```

## 🌐 Step 3: Create Azure CDN (Optional)

### Using Azure Portal:

1. **Create Resource** → Search for "CDN Profile"
2. **Fill in details**:
   - **Name**: `ai-voice-cdn`
   - **Pricing Tier**: Standard Microsoft
   - **Resource Group**: Same as above
3. **Create Endpoint**:
   - **Name**: `ai-voice-endpoint`
   - **Origin Type**: Storage
   - **Origin Hostname**: Your storage account blob endpoint

### Using Azure CLI:

```bash
# Create CDN profile
az cdn profile create \
  --name "ai-voice-cdn" \
  --resource-group "ai-voice-rg" \
  --sku "Standard_Microsoft"

# Create CDN endpoint
az cdn endpoint create \
  --name "ai-voice-endpoint" \
  --profile-name "ai-voice-cdn" \
  --resource-group "ai-voice-rg" \
  --origin "aivoicestorage123.blob.core.windows.net"
```

## 🔑 Step 4: Configure Application

### Update config.py:

```python
# Azure Speech Services
AZURE_SPEECH_KEY = "your_speech_key_from_step_1"
AZURE_SPEECH_REGION = "eastus"  # Your chosen region

# Azure Storage
AZURE_STORAGE_ACCOUNT_NAME = "aivoicestorage123"
AZURE_STORAGE_ACCOUNT_KEY = "your_storage_key_from_step_2"

# Optional: Azure CDN
AZURE_CDN_ENDPOINT = "ai-voice-endpoint.azureedge.net"
```

### Or use .env file:

```bash
# Copy example file
cp .env.example .env

# Edit .env with your credentials
nano .env
```

## 🧪 Step 5: Test Setup

### Install Dependencies:

```bash
pip install -r requirements.txt
```

### Test Azure Connections:

```python
# test_azure_setup.py
from azure_voice_converter import AzureVoiceConverter

try:
    converter = AzureVoiceConverter()
    print("✅ Azure setup successful!")
except Exception as e:
    print(f"❌ Setup error: {e}")
```

### Test with Sample Video:

```bash
python main.py "https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4"
```

## 💰 Cost Management

### Set up Budget Alerts:

1. **Azure Portal** → **Cost Management + Billing**
2. **Budgets** → **Add**
3. **Set Amount**: $10/month (example)
4. **Set Alerts**: 80%, 100% of budget

### Monitor Usage:

```bash
# Check Speech Services usage
az monitor metrics list \
  --resource "/subscriptions/{subscription-id}/resourceGroups/ai-voice-rg/providers/Microsoft.CognitiveServices/accounts/ai-voice-speech" \
  --metric "TotalCalls"

# Check Storage usage
az monitor metrics list \
  --resource "/subscriptions/{subscription-id}/resourceGroups/ai-voice-rg/providers/Microsoft.Storage/storageAccounts/aivoicestorage123" \
  --metric "UsedCapacity"
```

## 🔒 Security Best Practices

### 1. Use Managed Identity (Production):

```python
from azure.identity import DefaultAzureCredential

# Instead of keys, use managed identity
credential = DefaultAzureCredential()
```

### 2. Set up Private Endpoints:

```bash
# Create private endpoint for Speech Services
az network private-endpoint create \
  --name "speech-private-endpoint" \
  --resource-group "ai-voice-rg" \
  --vnet-name "ai-voice-vnet" \
  --subnet "default" \
  --private-connection-resource-id "/subscriptions/{subscription-id}/resourceGroups/ai-voice-rg/providers/Microsoft.CognitiveServices/accounts/ai-voice-speech" \
  --group-id "account" \
  --connection-name "speech-connection"
```

### 3. Configure Firewall Rules:

```bash
# Restrict storage account access
az storage account update \
  --name "aivoicestorage123" \
  --resource-group "ai-voice-rg" \
  --default-action "Deny"

# Add your IP to allowed list
az storage account network-rule add \
  --account-name "aivoicestorage123" \
  --resource-group "ai-voice-rg" \
  --ip-address "YOUR_IP_ADDRESS"
```

## 🔍 Troubleshooting

### Common Issues:

1. **"Speech key is invalid"**:
   - Verify key and region match
   - Check if resource is properly created

2. **"Storage account not found"**:
   - Verify storage account name is correct
   - Check if containers are created

3. **"Access denied to blob storage"**:
   - Verify storage key is correct
   - Check container permissions

### Debug Commands:

```bash
# Test Speech Services
curl -X POST "https://eastus.api.cognitive.microsoft.com/sts/v1.0/issuetoken" \
  -H "Ocp-Apim-Subscription-Key: YOUR_SPEECH_KEY"

# Test Storage Account
az storage blob list \
  --container-name "videos" \
  --account-name "aivoicestorage123" \
  --account-key "YOUR_STORAGE_KEY"
```

## 📊 Monitoring and Logging

### Enable Diagnostic Logs:

```bash
# Create Log Analytics workspace
az monitor log-analytics workspace create \
  --resource-group "ai-voice-rg" \
  --workspace-name "ai-voice-logs"

# Enable diagnostics for Speech Services
az monitor diagnostic-settings create \
  --name "speech-diagnostics" \
  --resource "/subscriptions/{subscription-id}/resourceGroups/ai-voice-rg/providers/Microsoft.CognitiveServices/accounts/ai-voice-speech" \
  --workspace "/subscriptions/{subscription-id}/resourceGroups/ai-voice-rg/providers/Microsoft.OperationalInsights/workspaces/ai-voice-logs" \
  --logs '[{"category":"Audit","enabled":true}]' \
  --metrics '[{"category":"AllMetrics","enabled":true}]'
```

## 🚀 Production Deployment

### 1. Use Azure Container Instances:

```bash
# Create container group
az container create \
  --resource-group "ai-voice-rg" \
  --name "ai-voice-converter" \
  --image "your-registry/ai-voice-converter:latest" \
  --environment-variables \
    AZURE_SPEECH_KEY="$SPEECH_KEY" \
    AZURE_STORAGE_ACCOUNT_NAME="aivoicestorage123"
```

### 2. Use Azure Functions:

```python
# function_app.py
import azure.functions as func
from azure_voice_converter import AzureVoiceConverter

def main(req: func.HttpRequest) -> func.HttpResponse:
    video_url = req.params.get('video_url')
    converter = AzureVoiceConverter()
    result = converter.process_video(video_url)
    return func.HttpResponse(result)
```

## ✅ Verification Checklist

- [ ] Azure Speech Services created and keys obtained
- [ ] Azure Storage Account created with containers
- [ ] config.py updated with correct credentials
- [ ] Dependencies installed successfully
- [ ] Test conversion completed successfully
- [ ] Budget alerts configured
- [ ] Security best practices implemented

---

**🎉 Congratulations! Your Azure AI Voice-Over Conversion tool is ready to use!**
