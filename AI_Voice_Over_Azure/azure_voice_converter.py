#!/usr/bin/env python3
"""
Azure AI Voice-Over Conversion Script
Automates the process of replacing human voice with AI voice in videos using only Azure services
"""

import os
import sys
import time
import requests
import logging
from typing import Optional, Dict
import azure.cognitiveservices.speech as speechsdk
from azure.storage.blob import BlobServiceClient, BlobClient
from azure.core.exceptions import AzureError
from moviepy.editor import VideoFileClip, AudioFileClip
from tqdm import tqdm
import tempfile
import uuid

# Import configuration
from config import *

class AzureVoiceConverter:
    def __init__(self):
        """Initialize the Azure Voice Converter with Azure configurations"""
        self.setup_logging()
        self.setup_azure_clients()
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
        
    def setup_azure_clients(self):
        """Setup Azure service clients"""
        try:
            # Validate Azure Speech credentials
            if not AZURE_SPEECH_KEY or AZURE_SPEECH_KEY == "your_azure_speech_key_here":
                raise ValueError("Azure Speech key not configured. Please update config.py with your Azure Speech Services key.")

            if not AZURE_SPEECH_REGION:
                raise ValueError("Azure Speech region not configured. Please update config.py with your Azure region.")

            self.logger.info(f"Initializing Azure Speech Services in region: {AZURE_SPEECH_REGION}")

            # Azure Speech Service client
            self.speech_config = speechsdk.SpeechConfig(
                subscription=AZURE_SPEECH_KEY,
                region=AZURE_SPEECH_REGION
            )

            # Test Azure Speech Services connection
            self.logger.info("Testing Azure Speech Services connection...")
            try:
                # Simple test to validate credentials
                test_config = speechsdk.SpeechConfig(
                    subscription=AZURE_SPEECH_KEY,
                    region=AZURE_SPEECH_REGION
                )
                test_config.speech_recognition_language = "en-US"
                self.logger.info("Azure Speech Services credentials validated")
            except Exception as speech_error:
                self.logger.error(f"Azure Speech Services validation failed: {speech_error}")
                raise

            # Azure Blob Storage client
            self.blob_service_client = BlobServiceClient.from_connection_string(
                AZURE_STORAGE_CONNECTION_STRING
            )

            # Create containers if they don't exist
            self.ensure_containers_exist()

            self.logger.info("Azure clients initialized successfully")

        except Exception as e:
            self.logger.error(f"Error setting up Azure clients: {str(e)}")
            self.logger.error("Please verify your Azure credentials in config.py")
            raise
            
    def ensure_containers_exist(self):
        """Ensure required blob containers exist"""
        containers = [AZURE_CONTAINER_VIDEOS, AZURE_CONTAINER_AUDIO, AZURE_CONTAINER_OUTPUT]
        
        for container_name in containers:
            try:
                container_client = self.blob_service_client.get_container_client(container_name)
                if not container_client.exists():
                    container_client.create_container()
                    self.logger.info(f"Created container: {container_name}")
            except Exception as e:
                self.logger.warning(f"Could not create container {container_name}: {str(e)}")
        
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

            if not os.path.exists(video_path):
                self.logger.error(f"Video file not found: {video_path}")
                return False

            file_size = os.path.getsize(video_path)
            if file_size == 0:
                self.logger.error(f"Video file is empty: {video_path}")
                return False

            self.logger.info(f"Video file size: {file_size / (1024*1024):.2f} MB")

            video = VideoFileClip(video_path)

            if video.audio is None:
                self.logger.error("Video file has no audio track")
                video.close()
                return False

            audio = video.audio

            # Extract audio with Azure-optimized parameters
            # Azure Speech Services works best with WAV format
            audio.write_audiofile(
                audio_path,
                verbose=False,
                logger=None,
                codec='pcm_s16le',  # 16-bit PCM for Azure Speech
                ffmpeg_params=['-ar', '16000', '-ac', '1']  # 16kHz mono for Azure Speech
            )

            video.close()
            audio.close()

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
            
    def upload_to_azure_blob(self, file_path: str, container_name: str, blob_name: str = None) -> Optional[str]:
        """Upload file to Azure Blob Storage and return blob URL"""
        try:
            if blob_name is None:
                blob_name = os.path.basename(file_path)
                
            self.logger.info(f"Uploading {file_path} to Azure Blob Storage...")
            
            blob_client = self.blob_service_client.get_blob_client(
                container=container_name, 
                blob=blob_name
            )
            
            with open(file_path, 'rb') as data:
                blob_client.upload_blob(data, overwrite=True)
            
            blob_url = blob_client.url
            self.logger.info(f"File uploaded successfully: {blob_url}")
            return blob_url
            
        except Exception as e:
            self.logger.error(f"Error uploading to Azure Blob: {str(e)}")
            return None

    def transcribe_audio_azure(self, audio_path: str) -> Optional[str]:
        """Transcribe audio using Azure Speech Services"""
        try:
            self.logger.info("Starting Azure Speech-to-Text transcription...")

            # Validate audio file exists
            if not os.path.exists(audio_path):
                self.logger.error(f"Audio file not found: {audio_path}")
                return None

            # Configure speech recognition
            self.speech_config.speech_recognition_language = AZURE_SPEECH_STT_CONFIG["language"]

            # Create audio configuration from file
            # Convert path to absolute path to avoid issues
            abs_audio_path = os.path.abspath(audio_path)
            self.logger.info(f"Using absolute audio path: {abs_audio_path}")

            audio_config = speechsdk.audio.AudioConfig(filename=abs_audio_path)

            # Create speech recognizer
            speech_recognizer = speechsdk.SpeechRecognizer(
                speech_config=self.speech_config,
                audio_config=audio_config
            )

            self.logger.info("Processing audio transcription...")

            # For shorter audio files, use single recognition
            # For longer files, we'll use continuous recognition
            audio_size = os.path.getsize(audio_path)
            self.logger.info(f"Audio file size: {audio_size / (1024*1024):.2f} MB")

            if audio_size < 10 * 1024 * 1024:  # Less than 10MB, use single recognition
                self.logger.info("Using single recognition for short audio")
                result = speech_recognizer.recognize_once()

                if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                    self.logger.info("Azure transcription completed successfully")
                    self.logger.info(f"Transcript length: {len(result.text)} characters")
                    return result.text
                elif result.reason == speechsdk.ResultReason.NoMatch:
                    self.logger.error("No speech could be recognized")
                    return None
                elif result.reason == speechsdk.ResultReason.Canceled:
                    cancellation_details = result.cancellation_details
                    self.logger.error(f"Speech recognition canceled: {cancellation_details.reason}")
                    if cancellation_details.error_details:
                        self.logger.error(f"Error details: {cancellation_details.error_details}")
                    return None
            else:
                # Use continuous recognition for longer files
                self.logger.info("Using continuous recognition for long audio")
                done = False
                transcript_parts = []

                def stop_cb(evt):
                    nonlocal done
                    done = True

                def recognized_cb(evt):
                    if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
                        transcript_parts.append(evt.result.text)
                        self.logger.info(f"Recognized: {evt.result.text[:100]}...")

                # Connect callbacks
                speech_recognizer.recognized.connect(recognized_cb)
                speech_recognizer.session_stopped.connect(stop_cb)
                speech_recognizer.canceled.connect(stop_cb)

                # Start continuous recognition
                speech_recognizer.start_continuous_recognition()

                # Wait for completion
                start_time = time.time()
                while not done and (time.time() - start_time) < MAX_WAIT_TIME:
                    time.sleep(0.5)

                speech_recognizer.stop_continuous_recognition()

                if not transcript_parts:
                    self.logger.error("No speech recognized in audio")
                    return None

                full_transcript = " ".join(transcript_parts)
                self.logger.info("Azure transcription completed successfully")
                self.logger.info(f"Transcript length: {len(full_transcript)} characters")

                return full_transcript

        except Exception as e:
            self.logger.error(f"Error in Azure transcription: {str(e)}")
            self.logger.error(f"Exception type: {type(e).__name__}")
            return None

    def generate_ai_voice_azure(self, text: str, output_path: str, voice_name: str = None) -> bool:
        """Generate AI voice using Azure Speech Services"""
        try:
            if voice_name is None:
                voice_name = AZURE_SPEECH_TTS_CONFIG["voice_name"]

            self.logger.info("Generating AI voice with Azure Speech Services...")
            self.logger.info(f"Text length: {len(text)} characters")
            self.logger.info(f"Voice: {voice_name}")

            # Configure speech synthesis
            self.speech_config.speech_synthesis_voice_name = voice_name

            # Create audio configuration for file output
            audio_config = speechsdk.audio.AudioOutputConfig(filename=output_path)

            # Create speech synthesizer
            speech_synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=self.speech_config,
                audio_config=audio_config
            )

            # Generate speech
            self.logger.info("Synthesizing speech...")
            result = speech_synthesizer.speak_text_async(text).get()

            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                self.logger.info(f"AI voice generated successfully: {output_path}")
                return True
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation_details = result.cancellation_details
                self.logger.error(f"Speech synthesis canceled: {cancellation_details.reason}")
                if cancellation_details.error_details:
                    self.logger.error(f"Error details: {cancellation_details.error_details}")
                return False
            else:
                self.logger.error(f"Speech synthesis failed: {result.reason}")
                return False

        except Exception as e:
            self.logger.error(f"Error generating AI voice with Azure: {str(e)}")
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
                new_audio = new_audio.subclip(0, video.duration)
                self.logger.info("Audio trimmed to match video duration")
            elif new_audio.duration < video.duration:
                self.logger.info("Audio is shorter than video - using as-is")

            final_video = video.set_audio(new_audio)
            final_video.write_videofile(
                output_path,
                verbose=False,
                logger=None,
                audio_codec='aac',
                codec='libx264'
            )

            video.close()
            new_audio.close()
            final_video.close()

            self.logger.info(f"Video with AI voice created: {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error replacing audio in video: {str(e)}")
            return False

    def cleanup_temp_files(self, *file_paths):
        """Clean up temporary files"""
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    self.logger.info(f"Cleaned up: {file_path}")
            except Exception as e:
                self.logger.warning(f"Could not clean up {file_path}: {str(e)}")

    def process_video(self, video_url: str, voice_name: str = None) -> Optional[str]:
        """Main method to process video with Azure AI voice conversion"""
        try:
            # Generate unique filenames
            timestamp = int(time.time())
            unique_id = str(uuid.uuid4())[:8]
            video_filename = f"video_{timestamp}_{unique_id}.mp4"
            audio_filename = f"audio_{timestamp}_{unique_id}.wav"  # Changed to WAV for Azure Speech
            ai_audio_filename = f"ai_audio_{timestamp}_{unique_id}.mp3"
            output_filename = f"azure_ai_voice_video_{timestamp}_{unique_id}.mp4"

            # File paths
            video_path = os.path.join(TEMP_FOLDER, video_filename)
            audio_path = os.path.join(TEMP_FOLDER, audio_filename)
            ai_audio_path = os.path.join(TEMP_FOLDER, ai_audio_filename)
            output_path = os.path.join(OUTPUT_FOLDER, output_filename)

            self.logger.info("Starting Azure AI voice conversion process...")

            # Step 1: Download video
            if not self.download_video(video_url, video_path):
                return None

            # Step 2: Extract audio
            if not self.extract_audio(video_path, audio_path):
                self.cleanup_temp_files(video_path)
                return None

            # Step 3: Transcribe audio using Azure Speech Services
            transcript = self.transcribe_audio_azure(audio_path)
            if not transcript:
                self.cleanup_temp_files(video_path, audio_path)
                return None

            self.logger.info(f"Transcript: {transcript[:100]}...")

            # Step 4: Generate AI voice using Azure Speech Services
            if not self.generate_ai_voice_azure(transcript, ai_audio_path, voice_name):
                self.cleanup_temp_files(video_path, audio_path)
                return None

            # Step 5: Replace audio in video
            if not self.replace_audio_in_video(video_path, ai_audio_path, output_path):
                self.cleanup_temp_files(video_path, audio_path, ai_audio_path)
                return None

            # Step 6: Upload final video to Azure Blob Storage
            blob_url = self.upload_to_azure_blob(
                output_path,
                AZURE_CONTAINER_OUTPUT,
                output_filename
            )

            # Step 7: Cleanup temporary files
            self.cleanup_temp_files(video_path, audio_path, ai_audio_path)

            self.logger.info("Azure AI voice conversion completed successfully!")
            return blob_url or output_path

        except Exception as e:
            self.logger.error(f"Error in process_video: {str(e)}")
            return None
