"""
Premium Audio Features
Advanced audio processing and enhancement
"""

import os
import wave
import struct
import math
import logging
from typing import Optional, List, Tuple, Dict
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

# Check for pydub availability
try:
    from pydub import AudioSegment
    from pydub.effects import normalize, compress_dynamic_range
    from pydub.generators import Sine, Silence
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    logger.warning("pydub not available - some audio features will be disabled")


class AudioQuality(Enum):
    """Audio quality presets"""
    LOW = {'bitrate': '64k', 'sample_rate': 22050}
    MEDIUM = {'bitrate': '128k', 'sample_rate': 44100}
    HIGH = {'bitrate': '192k', 'sample_rate': 44100}
    ULTRA = {'bitrate': '320k', 'sample_rate': 48000}


class AudioFormat(Enum):
    """Supported output formats"""
    WAV = 'wav'
    MP3 = 'mp3'
    OGG = 'ogg'
    FLAC = 'flac'
    M4A = 'm4a'


@dataclass
class AudioMetadata:
    """Audio file metadata"""
    duration_seconds: float
    sample_rate: int
    channels: int
    bitrate: Optional[int]
    format: str
    file_size_bytes: int
    
    @property
    def duration_formatted(self) -> str:
        """Return duration as HH:MM:SS"""
        hours = int(self.duration_seconds // 3600)
        minutes = int((self.duration_seconds % 3600) // 60)
        seconds = int(self.duration_seconds % 60)
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes}:{seconds:02d}"
    
    @property
    def file_size_formatted(self) -> str:
        """Return file size in human readable format"""
        size = self.file_size_bytes
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


class AudioProcessor:
    """Advanced audio processing capabilities"""
    
    def __init__(self):
        self.pydub_available = PYDUB_AVAILABLE
    
    def get_metadata(self, audio_path: str) -> AudioMetadata:
        """Get audio file metadata"""
        file_size = os.path.getsize(audio_path)
        
        if audio_path.lower().endswith('.wav'):
            return self._get_wav_metadata(audio_path, file_size)
        elif self.pydub_available:
            return self._get_pydub_metadata(audio_path, file_size)
        else:
            # Return basic metadata
            return AudioMetadata(
                duration_seconds=0,
                sample_rate=44100,
                channels=1,
                bitrate=None,
                format=os.path.splitext(audio_path)[1][1:],
                file_size_bytes=file_size
            )
    
    def _get_wav_metadata(self, wav_path: str, file_size: int) -> AudioMetadata:
        """Get WAV file metadata"""
        with wave.open(wav_path, 'rb') as wav_file:
            frames = wav_file.getnframes()
            rate = wav_file.getframerate()
            channels = wav_file.getnchannels()
            duration = frames / float(rate)
            
            return AudioMetadata(
                duration_seconds=duration,
                sample_rate=rate,
                channels=channels,
                bitrate=rate * channels * 16,  # Assuming 16-bit audio
                format='wav',
                file_size_bytes=file_size
            )
    
    def _get_pydub_metadata(self, audio_path: str, file_size: int) -> AudioMetadata:
        """Get metadata using pydub"""
        audio = AudioSegment.from_file(audio_path)
        
        return AudioMetadata(
            duration_seconds=len(audio) / 1000.0,
            sample_rate=audio.frame_rate,
            channels=audio.channels,
            bitrate=None,
            format=os.path.splitext(audio_path)[1][1:],
            file_size_bytes=file_size
        )
    
    def convert_format(
        self,
        input_path: str,
        output_path: str,
        format: AudioFormat = AudioFormat.MP3,
        quality: AudioQuality = AudioQuality.HIGH
    ) -> str:
        """Convert audio to different format"""
        if not self.pydub_available:
            raise RuntimeError("pydub required for format conversion")
        
        audio = AudioSegment.from_file(input_path)
        
        # Apply quality settings
        audio = audio.set_frame_rate(quality.value['sample_rate'])
        
        # Export with appropriate settings
        export_params = {
            'format': format.value,
        }
        
        if format == AudioFormat.MP3:
            export_params['bitrate'] = quality.value['bitrate']
        elif format == AudioFormat.FLAC:
            export_params['parameters'] = ['-compression_level', '8']
        
        audio.export(output_path, **export_params)
        return output_path
    
    def normalize_audio(self, audio_path: str, output_path: Optional[str] = None) -> str:
        """Normalize audio volume"""
        if not self.pydub_available:
            raise RuntimeError("pydub required for audio normalization")
        
        output_path = output_path or audio_path
        audio = AudioSegment.from_file(audio_path)
        
        # Normalize to -3dB
        normalized = normalize(audio, headroom=3.0)
        
        # Export
        format = os.path.splitext(output_path)[1][1:]
        normalized.export(output_path, format=format)
        return output_path
    
    def add_background_music(
        self,
        speech_path: str,
        music_path: str,
        output_path: str,
        music_volume: float = -20  # dB relative to speech
    ) -> str:
        """Add background music to speech"""
        if not self.pydub_available:
            raise RuntimeError("pydub required for background music")
        
        speech = AudioSegment.from_file(speech_path)
        music = AudioSegment.from_file(music_path)
        
        # Loop music if shorter than speech
        if len(music) < len(speech):
            loops_needed = int(len(speech) / len(music)) + 1
            music = music * loops_needed
        
        # Trim music to speech length
        music = music[:len(speech)]
        
        # Reduce music volume
        music = music + music_volume
        
        # Overlay
        combined = speech.overlay(music)
        
        format = os.path.splitext(output_path)[1][1:]
        combined.export(output_path, format=format)
        return output_path
    
    def add_intro_outro(
        self,
        audio_path: str,
        output_path: str,
        intro_path: Optional[str] = None,
        outro_path: Optional[str] = None,
        intro_text: Optional[str] = None,
        outro_text: Optional[str] = None,
        fade_duration: int = 1000  # ms
    ) -> str:
        """Add intro and/or outro to audio"""
        if not self.pydub_available:
            raise RuntimeError("pydub required for intro/outro")
        
        main_audio = AudioSegment.from_file(audio_path)
        
        # Apply fade in to main audio
        main_audio = main_audio.fade_in(fade_duration)
        
        # Add intro
        if intro_path and os.path.exists(intro_path):
            intro = AudioSegment.from_file(intro_path)
            intro = intro.fade_out(fade_duration // 2)
            main_audio = intro + main_audio
        
        # Add outro
        if outro_path and os.path.exists(outro_path):
            outro = AudioSegment.from_file(outro_path)
            outro = outro.fade_in(fade_duration // 2)
            main_audio = main_audio.fade_out(fade_duration)
            main_audio = main_audio + outro
        else:
            main_audio = main_audio.fade_out(fade_duration)
        
        format = os.path.splitext(output_path)[1][1:]
        main_audio.export(output_path, format=format)
        return output_path
    
    def add_chapter_markers(
        self,
        audio_path: str,
        output_path: str,
        chapters: List[Dict],  # [{'title': str, 'time_seconds': float}]
        beep_frequency: int = 880,  # Hz
        beep_duration: int = 200  # ms
    ) -> Tuple[str, List[Dict]]:
        """Add chapter markers with optional beep sounds"""
        if not self.pydub_available:
            raise RuntimeError("pydub required for chapter markers")
        
        audio = AudioSegment.from_file(audio_path)
        
        # Create chapter beep
        beep = Sine(beep_frequency).to_audio_segment(duration=beep_duration)
        beep = beep.fade_in(50).fade_out(50)
        beep = beep - 10  # Reduce volume
        
        # Sort chapters by time
        chapters = sorted(chapters, key=lambda x: x['time_seconds'], reverse=True)
        
        # Insert beeps at chapter points (reverse order to maintain positions)
        for chapter in chapters:
            position_ms = int(chapter['time_seconds'] * 1000)
            if 0 < position_ms < len(audio):
                audio = audio[:position_ms] + beep + audio[position_ms:]
        
        format = os.path.splitext(output_path)[1][1:]
        audio.export(output_path, format=format)
        
        return output_path, chapters
    
    def adjust_speed(
        self,
        audio_path: str,
        output_path: str,
        speed_factor: float = 1.0  # 0.5 = half speed, 2.0 = double speed
    ) -> str:
        """Adjust audio playback speed"""
        if not self.pydub_available:
            raise RuntimeError("pydub required for speed adjustment")
        
        if speed_factor <= 0:
            raise ValueError("Speed factor must be positive")
        
        audio = AudioSegment.from_file(audio_path)
        
        # Change speed by changing frame rate
        # This also changes pitch - for pitch-preserving speed change,
        # more advanced libraries like librosa would be needed
        new_frame_rate = int(audio.frame_rate * speed_factor)
        
        # Change frame rate and convert back
        audio_speed = audio._spawn(
            audio.raw_data,
            overrides={'frame_rate': new_frame_rate}
        )
        audio_speed = audio_speed.set_frame_rate(audio.frame_rate)
        
        format = os.path.splitext(output_path)[1][1:]
        audio_speed.export(output_path, format=format)
        return output_path
    
    def trim_silence(
        self,
        audio_path: str,
        output_path: Optional[str] = None,
        silence_threshold: int = -50,  # dB
        min_silence_len: int = 500  # ms
    ) -> str:
        """Trim silence from beginning and end of audio"""
        if not self.pydub_available:
            raise RuntimeError("pydub required for silence trimming")
        
        from pydub.silence import detect_leading_silence
        
        output_path = output_path or audio_path
        audio = AudioSegment.from_file(audio_path)
        
        # Detect and trim leading silence
        start_trim = detect_leading_silence(audio, silence_threshold, chunk_size=10)
        
        # Detect and trim trailing silence
        end_trim = detect_leading_silence(audio.reverse(), silence_threshold, chunk_size=10)
        
        # Apply trimming
        if start_trim > 0 or end_trim > 0:
            audio = audio[start_trim:len(audio) - end_trim]
        
        format = os.path.splitext(output_path)[1][1:]
        audio.export(output_path, format=format)
        return output_path
    
    def split_by_duration(
        self,
        audio_path: str,
        output_dir: str,
        segment_duration: int = 300000  # 5 minutes in ms
    ) -> List[str]:
        """Split audio into segments of specified duration"""
        if not self.pydub_available:
            raise RuntimeError("pydub required for audio splitting")
        
        os.makedirs(output_dir, exist_ok=True)
        audio = AudioSegment.from_file(audio_path)
        
        base_name = os.path.splitext(os.path.basename(audio_path))[0]
        format = os.path.splitext(audio_path)[1][1:]
        
        segments = []
        for i, start in enumerate(range(0, len(audio), segment_duration)):
            segment = audio[start:start + segment_duration]
            segment_path = os.path.join(output_dir, f"{base_name}_part{i + 1:03d}.{format}")
            segment.export(segment_path, format=format)
            segments.append(segment_path)
        
        return segments
    
    def apply_eq(
        self,
        audio_path: str,
        output_path: str,
        bass_gain: float = 0,
        mid_gain: float = 0,
        treble_gain: float = 0
    ) -> str:
        """Apply simple EQ adjustments"""
        if not self.pydub_available:
            raise RuntimeError("pydub required for EQ")
        
        audio = AudioSegment.from_file(audio_path)
        
        # Apply basic filtering using pydub
        if bass_gain != 0:
            audio = audio.low_pass_filter(300)
            if bass_gain > 0:
                audio = audio + bass_gain
        
        if treble_gain != 0:
            audio = audio.high_pass_filter(3000)
            if treble_gain > 0:
                audio = audio + treble_gain
        
        format = os.path.splitext(output_path)[1][1:]
        audio.export(output_path, format=format)
        return output_path
    
    def create_audiobook_package(
        self,
        audio_path: str,
        output_dir: str,
        title: str,
        author: str = "Unknown",
        chapters: Optional[List[Dict]] = None
    ) -> Dict:
        """Create a complete audiobook package with metadata"""
        if not self.pydub_available:
            raise RuntimeError("pydub required for audiobook creation")
        
        os.makedirs(output_dir, exist_ok=True)
        
        audio = AudioSegment.from_file(audio_path)
        metadata = self.get_metadata(audio_path)
        
        # Create package info
        package = {
            'title': title,
            'author': author,
            'duration': metadata.duration_formatted,
            'format': 'mp3',
            'files': []
        }
        
        # If chapters provided, split by chapters
        if chapters:
            for i, chapter in enumerate(chapters):
                start_ms = int(chapter.get('start_seconds', 0) * 1000)
                end_ms = int(chapter.get('end_seconds', len(audio) / 1000) * 1000)
                
                segment = audio[start_ms:end_ms]
                chapter_file = f"{i + 1:02d}_{chapter['title'][:50].replace(' ', '_')}.mp3"
                chapter_path = os.path.join(output_dir, chapter_file)
                
                segment.export(
                    chapter_path,
                    format='mp3',
                    tags={
                        'title': chapter['title'],
                        'artist': author,
                        'album': title,
                        'track': str(i + 1)
                    }
                )
                
                package['files'].append({
                    'filename': chapter_file,
                    'title': chapter['title'],
                    'duration_seconds': len(segment) / 1000
                })
        else:
            # Export as single file
            output_file = f"{title[:50].replace(' ', '_')}.mp3"
            output_path = os.path.join(output_dir, output_file)
            
            audio.export(
                output_path,
                format='mp3',
                tags={
                    'title': title,
                    'artist': author,
                    'album': title
                }
            )
            
            package['files'].append({
                'filename': output_file,
                'title': title,
                'duration_seconds': len(audio) / 1000
            })
        
        return package


# Singleton instance
audio_processor = AudioProcessor()
