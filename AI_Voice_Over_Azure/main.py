#!/usr/bin/env python3
"""
Azure AI Voice-Over Conversion Tool - Main Entry Point
Command-line interface for the Azure-based voice conversion system
"""

import sys
import argparse
from azure_voice_converter import AzureVoiceConverter
from config import AZURE_VOICE_OPTIONS

def print_banner():
    """Print application banner"""
    print("🎬 Azure AI Voice-Over Conversion Tool")
    print("=" * 50)

def print_voice_options():
    """Print available voice options"""
    print("\n🎤 Available Azure Neural Voices:")
    for key, voice_name in AZURE_VOICE_OPTIONS.items():
        print(f"  {key}: {voice_name}")
    print()

def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Convert human voice to AI voice in videos using Azure services",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py "https://example.com/video.mp4"
  python main.py "https://example.com/video.mp4" --voice aria
  python main.py "https://example.com/video.mp4" --voice jenny
  python main.py --list-voices
        """
    )
    
    parser.add_argument(
        "video_url", 
        nargs='?',
        help="URL of the video to process"
    )
    
    parser.add_argument(
        "--voice", 
        choices=list(AZURE_VOICE_OPTIONS.keys()),
        default="aria",
        help="Azure neural voice to use (default: aria)"
    )
    
    parser.add_argument(
        "--list-voices",
        action="store_true",
        help="List available Azure neural voices"
    )
    
    args = parser.parse_args()
    
    print_banner()
    
    if args.list_voices:
        print_voice_options()
        return
    
    if not args.video_url:
        print("❌ Error: Video URL is required")
        parser.print_help()
        sys.exit(1)
    
    # Get the full voice name from the key
    voice_name = AZURE_VOICE_OPTIONS.get(args.voice)
    
    print(f"Video URL: {args.video_url}")
    print(f"Voice: {voice_name}")
    print("=" * 50)
    
    try:
        # Initialize converter
        converter = AzureVoiceConverter()
        
        # Process video
        result_url = converter.process_video(args.video_url, voice_name)
        
        if result_url:
            print("\n✅ SUCCESS!")
            print(f"📁 Output: {result_url}")
            print("🌐 Video processed with Azure AI voice")
        else:
            print("\n❌ FAILED!")
            print("Check the logs for more details.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️ Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
