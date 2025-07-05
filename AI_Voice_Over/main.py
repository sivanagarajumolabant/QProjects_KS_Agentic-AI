#!/usr/bin/env python3
"""
Main script for AI Voice-Over Conversion
Usage: python main.py <video_url> [voice_id]
"""

import sys
import argparse
from voice_converter import VoiceConverter
from config import DEFAULT_VOICE_ID

def main():
    """Main function to run the AI voice conversion"""
    parser = argparse.ArgumentParser(description='Convert video with AI voice-over')
    parser.add_argument('video_url', help='URL of the video to process')
    parser.add_argument('--voice-id', default=DEFAULT_VOICE_ID, 
                       help=f'ElevenLabs voice ID (default: {DEFAULT_VOICE_ID})')
    parser.add_argument('--output-only', action='store_true',
                       help='Save to local output folder only (skip Cloudinary upload)')
    
    args = parser.parse_args()
    
    # Initialize converter
    converter = VoiceConverter()
    
    print("🎬 AI Voice-Over Conversion Tool")
    print("=" * 50)
    print(f"Video URL: {args.video_url}")
    print(f"Voice ID: {args.voice_id}")
    print("=" * 50)
    
    # Process the video
    result = converter.process_video(args.video_url, args.voice_id)
    
    if result:
        print("\n✅ SUCCESS!")
        print(f"📁 Output: {result}")
        
        if result.startswith('http'):
            print("🌐 Video uploaded to Cloudinary")
        else:
            print("💾 Video saved locally")
            
    else:
        print("\n❌ FAILED!")
        print("Check the logs for more details.")
        sys.exit(1)

if __name__ == "__main__":
    main()
