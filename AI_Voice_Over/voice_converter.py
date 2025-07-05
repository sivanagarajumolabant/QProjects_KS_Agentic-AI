#!/usr/bin/env python3
"""
AI Voice-Over Conversion Script
Automates the process of replacing human voice with AI voice in videos
"""

import os
import sys
import time
import json
import requests
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from urllib.parse import urlparse
import cloudinary
import cloudinary.uploader
from moviepy.editor import VideoFileClip, AudioFileClip
from tqdm import tqdm

# Import configuration
from config import *

class VoiceConverter:
    def __init__(self):
        """Initialize the Voice Converter with API configurations"""
        self.setup_logging()
        self.setup_cloudinary()
        create_directories()
        
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(LOG_FILE),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def setup_cloudinary(self):
        """Setup Cloudinary configuration"""
        cloudinary.config(
            cloud_name=CLOUDINARY_CLOUD_NAME,
            api_key=CLOUDINARY_API_KEY,
            api_secret=CLOUDINARY_API_SECRET
        )
        
    def download_video(self, video_url: str, output_path: str) -> bool:
        """Download video from URL"""
        try:
            self.logger.info(f"Downloading video from: {video_url}")
            response = requests.get(video_url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            with open(output_path, 'wb') as file, tqdm(
                desc="Downloading",
                total=total_size,
                unit='B',
                unit_scale=True,
                unit_divisor=1024,
            ) as pbar:
                for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                    if chunk:
                        file.write(chunk)
                        pbar.update(len(chunk))
                        
            self.logger.info(f"Video downloaded successfully: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error downloading video: {str(e)}")
            return False
            
    def extract_audio(self, video_path: str, audio_path: str) -> bool:
        """Extract audio from video file"""
        try:
            self.logger.info(f"Extracting audio from: {video_path}")

            # Check if video file exists and has content
            if not os.path.exists(video_path):
                self.logger.error(f"Video file not found: {video_path}")
                return False

            file_size = os.path.getsize(video_path)
            if file_size == 0:
                self.logger.error(f"Video file is empty: {video_path}")
                return False

            self.logger.info(f"Video file size: {file_size / (1024*1024):.2f} MB")

            video = VideoFileClip(video_path)

            # Check if video has audio
            if video.audio is None:
                self.logger.error("Video file has no audio track")
                video.close()
                return False

            audio = video.audio

            # Extract audio with specific parameters for better compatibility
            audio.write_audiofile(
                audio_path,
                verbose=False,
                logger=None,
                codec='mp3',  # Use MP3 codec for better compatibility with AssemblyAI
                ffmpeg_params=['-ar', '16000', '-ac', '1']  # 16kHz sample rate, mono channel
            )

            video.close()
            audio.close()

            # Verify the extracted audio file
            if not os.path.exists(audio_path):
                self.logger.error(f"Audio extraction failed - file not created: {audio_path}")
                return False

            audio_size = os.path.getsize(audio_path)
            if audio_size == 0:
                self.logger.error(f"Audio extraction failed - empty file: {audio_path}")
                return False

            self.logger.info(f"Audio extracted successfully: {audio_path} ({audio_size / (1024*1024):.2f} MB)")
            return True

        except Exception as e:
            self.logger.error(f"Error extracting audio: {str(e)}")
            return False
            
    def upload_audio_to_assemblyai(self, audio_path: str) -> Optional[str]:
        """Upload audio file to AssemblyAI and return upload URL"""
        try:
            self.logger.info("Uploading audio to AssemblyAI...")
            
            headers = {"authorization": ASSEMBLYAI_API_KEY}
            
            with open(audio_path, 'rb') as audio_file:
                response = requests.post(
                    ASSEMBLYAI_UPLOAD_URL,
                    files={'file': audio_file},
                    headers=headers
                )
                
            response.raise_for_status()
            upload_url = response.json()['upload_url']
            
            self.logger.info("Audio uploaded to AssemblyAI successfully")
            return upload_url
            
        except Exception as e:
            self.logger.error(f"Error uploading to AssemblyAI: {str(e)}")
            return None
            
    def transcribe_audio(self, upload_url: str) -> Optional[str]:
        """Transcribe audio using AssemblyAI"""
        try:
            self.logger.info("Starting transcription...")
            
            headers = {
                "authorization": ASSEMBLYAI_API_KEY,
                "content-type": "application/json"
            }
            
            # Submit transcription request
            data = {
                "audio_url": upload_url,
                "speaker_labels": True
            }
            
            response = requests.post(
                ASSEMBLYAI_TRANSCRIPT_URL,
                json=data,
                headers=headers
            )
            response.raise_for_status()
            
            transcript_id = response.json()['id']
            self.logger.info(f"Transcription submitted. ID: {transcript_id}")
            
            # Poll for completion
            return self._poll_transcription_status(transcript_id, headers)
            
        except Exception as e:
            self.logger.error(f"Error in transcription: {str(e)}")
            return None
            
    def _poll_transcription_status(self, transcript_id: str, headers: Dict) -> Optional[str]:
        """Poll AssemblyAI for transcription completion"""
        url = f"{ASSEMBLYAI_TRANSCRIPT_URL}/{transcript_id}"
        
        start_time = time.time()
        while time.time() - start_time < MAX_WAIT_TIME:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            status = result['status']
            
            if status == 'completed':
                self.logger.info("Transcription completed successfully")
                return result['text']
            elif status == 'error':
                self.logger.error(f"Transcription failed: {result.get('error', 'Unknown error')}")
                return None
            else:
                self.logger.info(f"Transcription status: {status}")
                time.sleep(POLLING_INTERVAL)
                
        self.logger.error("Transcription timed out")
        return None

    def generate_ai_voice(self, text: str, output_path: str, voice_id: str = DEFAULT_VOICE_ID) -> bool:
        """Generate AI voice using ElevenLabs"""
        try:
            self.logger.info("Generating AI voice...")
            self.logger.info(f"Text length: {len(text)} characters")

            # Check character limit and truncate if necessary
            max_chars = 4000  # Conservative limit for free tier
            if len(text) > max_chars:
                self.logger.warning(f"Text too long ({len(text)} chars), truncating to {max_chars} chars")
                # Find the last complete sentence within the limit
                truncated = text[:max_chars]
                last_period = truncated.rfind('.')
                if last_period > max_chars * 0.8:  # If we find a period in the last 20%
                    text = truncated[:last_period + 1]
                else:
                    text = truncated
                self.logger.info(f"Truncated text length: {len(text)} characters")

            self.logger.info(f"Voice ID: {voice_id}")

            url = f"{ELEVENLABS_TTS_URL}/{voice_id}"

            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": ELEVENLABS_API_KEY
            }

            data = {
                "text": text,
                "model_id": DEFAULT_MODEL_ID,
                "voice_settings": VOICE_SETTINGS
            }

            self.logger.info(f"Making request to: {url}")
            response = requests.post(url, json=data, headers=headers)
            self.logger.info(f"Response status: {response.status_code}")
            response.raise_for_status()

            with open(output_path, 'wb') as audio_file:
                audio_file.write(response.content)

            self.logger.info(f"AI voice generated successfully: {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error generating AI voice: {str(e)}")
            return False

    def replace_audio_in_video(self, video_path: str, new_audio_path: str, output_path: str) -> bool:
        """Replace audio in video with new AI-generated audio"""
        try:
            self.logger.info("Replacing audio in video...")

            video = VideoFileClip(video_path)
            new_audio = AudioFileClip(new_audio_path)

            self.logger.info(f"Video duration: {video.duration:.2f}s, Audio duration: {new_audio.duration:.2f}s")

            # Adjust audio duration to match video
            if new_audio.duration > video.duration:
                # Trim audio if it's longer than video
                new_audio = new_audio.subclip(0, video.duration)
                self.logger.info("Audio trimmed to match video duration")
            elif new_audio.duration < video.duration:
                # For shorter audio, we'll just use it as-is and let the video be longer
                # This is simpler and avoids the loop issue
                self.logger.info("Audio is shorter than video - using as-is")

            final_video = video.set_audio(new_audio)
            final_video.write_videofile(
                output_path,
                verbose=False,
                logger=None,
                audio_codec='aac',  # Use AAC codec for better compatibility
                codec='libx264'     # Use H.264 codec for video
            )

            video.close()
            new_audio.close()
            final_video.close()

            self.logger.info(f"Video with AI voice created: {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error replacing audio in video: {str(e)}")
            return False

    def upload_to_cloudinary(self, file_path: str) -> Optional[str]:
        """Upload final video to Cloudinary"""
        try:
            self.logger.info("Uploading final video to Cloudinary...")

            result = cloudinary.uploader.upload(
                file_path,
                resource_type="video",
                folder="ai_voice_over"
            )

            secure_url = result.get('secure_url')
            self.logger.info(f"Video uploaded to Cloudinary: {secure_url}")
            return secure_url

        except Exception as e:
            self.logger.error(f"Error uploading to Cloudinary: {str(e)}")
            return None

    def cleanup_temp_files(self, *file_paths):
        """Clean up temporary files"""
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    self.logger.info(f"Cleaned up: {file_path}")
            except Exception as e:
                self.logger.warning(f"Could not clean up {file_path}: {str(e)}")

    def process_video(self, video_url: str, voice_id: str = DEFAULT_VOICE_ID) -> Optional[str]:
        """Main method to process video with AI voice conversion"""
        try:
            # Generate unique filenames
            timestamp = int(time.time())
            video_filename = f"video_{timestamp}.mp4"
            audio_filename = f"audio_{timestamp}.mp3"
            ai_audio_filename = f"ai_audio_{timestamp}.mp3"
            output_filename = f"ai_voice_video_{timestamp}.mp4"

            # File paths
            video_path = os.path.join(TEMP_FOLDER, video_filename)
            audio_path = os.path.join(TEMP_FOLDER, audio_filename)
            ai_audio_path = os.path.join(TEMP_FOLDER, ai_audio_filename)
            output_path = os.path.join(OUTPUT_FOLDER, output_filename)

            self.logger.info("Starting AI voice conversion process...")

            # Step 1: Download video
            if not self.download_video(video_url, video_path):
                return None

            # Step 2: Extract audio
            if not self.extract_audio(video_path, audio_path):
                self.cleanup_temp_files(video_path)
                return None

            # Step 3: Upload audio to AssemblyAI
            upload_url = self.upload_audio_to_assemblyai(audio_path)
            if not upload_url:
                self.cleanup_temp_files(video_path, audio_path)
                return None

            # Step 4: Transcribe audio
            transcript = self.transcribe_audio(upload_url)
            if not transcript:
                self.cleanup_temp_files(video_path, audio_path)
                return None

            self.logger.info(f"Transcript: {transcript[:100]}...")

            # Step 5: Generate AI voice
            if not self.generate_ai_voice(transcript, ai_audio_path, voice_id):
                self.cleanup_temp_files(video_path, audio_path)
                return None

            # Step 6: Replace audio in video
            if not self.replace_audio_in_video(video_path, ai_audio_path, output_path):
                self.cleanup_temp_files(video_path, audio_path, ai_audio_path)
                return None

            # Step 7: Upload to Cloudinary (optional)
            cloudinary_url = self.upload_to_cloudinary(output_path)

            # Step 8: Cleanup temporary files
            self.cleanup_temp_files(video_path, audio_path, ai_audio_path)

            self.logger.info("AI voice conversion completed successfully!")
            return cloudinary_url or output_path

        except Exception as e:
            self.logger.error(f"Error in process_video: {str(e)}")
            return None
