#!/usr/bin/env python3
"""
Test Azure Speech Services Configuration
Simple script to validate Azure Speech Services credentials and region
"""

import azure.cognitiveservices.speech as speechsdk
from config import AZURE_SPEECH_KEY, AZURE_SPEECH_REGION

def test_azure_speech_services():
    """Test Azure Speech Services configuration"""
    print("🔍 Testing Azure Speech Services Configuration")
    print("=" * 50)
    
    # Check credentials
    print(f"Speech Key: {AZURE_SPEECH_KEY[:10]}...{AZURE_SPEECH_KEY[-10:]}")
    print(f"Speech Region: {AZURE_SPEECH_REGION}")
    print()
    
    try:
        # Test 1: Create Speech Config
        print("Test 1: Creating Speech Configuration...")
        speech_config = speechsdk.SpeechConfig(
            subscription=AZURE_SPEECH_KEY, 
            region=AZURE_SPEECH_REGION
        )
        print("✅ Speech configuration created successfully")
        
        # Test 2: Test Text-to-Speech (simpler test)
        print("\nTest 2: Testing Text-to-Speech...")
        speech_config.speech_synthesis_voice_name = "en-US-AriaNeural"
        
        # Create synthesizer with no audio output (just test the connection)
        synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)
        
        # Test with a simple phrase
        test_text = "Hello, this is a test of Azure Speech Services."
        result = synthesizer.speak_text_async(test_text).get()
        
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            print("✅ Text-to-Speech test successful")
            print(f"Generated audio data: {len(result.audio_data)} bytes")
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            print(f"❌ TTS test failed: {cancellation_details.reason}")
            if cancellation_details.error_details:
                print(f"Error details: {cancellation_details.error_details}")
            return False
        
        # Test 3: Test Speech-to-Text with a simple setup
        print("\nTest 3: Testing Speech-to-Text configuration...")
        speech_config.speech_recognition_language = "en-US"
        
        # Just test creating a recognizer (without audio file)
        recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config)
        print("✅ Speech-to-Text configuration successful")
        
        print("\n🎉 All Azure Speech Services tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Azure Speech Services test failed: {e}")
        print(f"Exception type: {type(e).__name__}")
        
        # Provide troubleshooting suggestions
        print("\n🔧 Troubleshooting suggestions:")
        print("1. Verify your Azure Speech Services key is correct")
        print("2. Ensure the region matches your Azure resource region")
        print("3. Check if your Azure Speech Services resource is active")
        print("4. Verify you have sufficient quota in your Azure subscription")
        
        return False

def test_region_alternatives():
    """Test common region alternatives"""
    print("\n🌍 Testing alternative regions...")
    
    common_regions = [
        "eastus",
        "eastus2", 
        "westus",
        "westus2",
        "centralus",
        "northcentralus",
        "southcentralus",
        "westcentralus"
    ]
    
    for region in common_regions:
        if region == AZURE_SPEECH_REGION:
            continue
            
        try:
            print(f"Testing region: {region}")
            test_config = speechsdk.SpeechConfig(
                subscription=AZURE_SPEECH_KEY, 
                region=region
            )
            test_config.speech_synthesis_voice_name = "en-US-AriaNeural"
            synthesizer = speechsdk.SpeechSynthesizer(speech_config=test_config, audio_config=None)
            result = synthesizer.speak_text_async("Test").get()
            
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                print(f"✅ Region {region} works! Consider updating your config.")
                return region
                
        except Exception as e:
            print(f"❌ Region {region} failed: {str(e)[:100]}...")
            
    return None

if __name__ == "__main__":
    success = test_azure_speech_services()
    
    if not success:
        print("\n" + "="*50)
        working_region = test_region_alternatives()
        
        if working_region:
            print(f"\n💡 Found working region: {working_region}")
            print(f"Update your config.py: AZURE_SPEECH_REGION = '{working_region}'")
        else:
            print("\n❌ No working regions found. Please check your Azure Speech Services setup.")
