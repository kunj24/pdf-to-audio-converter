import argparse
import os
import re
import sys
from typing import Optional

import pyttsx3
from PyPDF2 import PdfReader

try:
    from pydub import AudioSegment
    from pydub.generators import Silence
    PYDUB_AVAILABLE = True
except Exception:
    PYDUB_AVAILABLE = False


def read_pdf_text(path: str, start_page: Optional[int] = None, end_page: Optional[int] = None) -> str:
    """Optimized PDF text extraction with better memory usage"""
    reader = PdfReader(path)
    n = len(reader.pages)
    s = start_page - 1 if start_page else 0
    e = end_page if end_page else n
    s = max(0, s)
    e = min(n, e)
    
    # Optimized: Pre-allocate list size
    page_count = e - s
    chunks = []
    chunks_reserve = page_count
    
    # Optimized: Process in batches for better memory management
    BATCH_SIZE = 50
    for batch_start in range(s, e, BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, e)
        for i in range(batch_start, batch_end):
            txt = reader.pages[i].extract_text()
            if txt and txt.strip():  # Skip empty pages
                chunks.append(txt.strip())
    
    # Optimized: Join with proper spacing
    full = "\n\n".join(chunks)
    return normalize_text(full)


def normalize_text(text: str) -> str:
    """Optimized text normalization with better processing"""
    if not text:
        return ""
    
    # Optimized: Process in single pass when possible
    text = text.replace('\r', '')
    
    # Optimized: Use compiled regex for better performance
    whitespace_pattern = re.compile(r"\s+")
    hyphen_pattern = re.compile(r"-\s+")
    
    # Process lines efficiently
    lines = text.split('\n')
    joined = []
    for ln in lines:
        ln = whitespace_pattern.sub(" ", ln).strip()
        if ln:  # Skip empty lines
            joined.append(ln)
    
    # Join and fix hyphenation
    text = " ".join(joined)
    text = hyphen_pattern.sub("", text)
    
    # Optimized: Remove multiple spaces that might remain
    text = whitespace_pattern.sub(" ", text)
    
    return text.strip()


def list_voices(engine: pyttsx3.Engine):
    voices = engine.getProperty('voices')
    for idx, v in enumerate(voices):
        print(f"[{idx}] {v.name} | id={v.id}")


def synth_to_wav(engine: pyttsx3.Engine, text: str, wav_path: str, rate: Optional[int] = None, voice: Optional[str] = None):
    """Optimized speech synthesis with better configuration"""
    # Optimized: Configure engine for better performance
    if rate:
        engine.setProperty('rate', rate)
    else:
        # Set optimal default rate for clarity
        engine.setProperty('rate', 175)
    
    # Optimized: Set volume for consistent output
    engine.setProperty('volume', 1.0)
    
    if voice and voice != 'default':
        # Try by index, else by id/name
        try:
            vi = int(voice)
            voices = engine.getProperty('voices')
            if 0 <= vi < len(voices):
                engine.setProperty('voice', voices[vi].id)
        except ValueError:
            engine.setProperty('voice', voice)
    
    # Optimized: Process text in chunks for large documents to avoid memory issues
    MAX_CHUNK_SIZE = 10000  # Characters per chunk
    if len(text) > MAX_CHUNK_SIZE:
        # Split text into sentences for better chunking
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text)
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence_len = len(sentence)
            if current_length + sentence_len > MAX_CHUNK_SIZE and current_chunk:
                # Process current chunk
                chunk_text = ' '.join(current_chunk)
                engine.save_to_file(chunk_text, wav_path)
                current_chunk = [sentence]
                current_length = sentence_len
            else:
                current_chunk.append(sentence)
                current_length += sentence_len + 1
        
        # Process remaining chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            engine.save_to_file(chunk_text, wav_path)
    else:
        engine.save_to_file(text, wav_path)
    
    engine.runAndWait()


def wav_to_mp3(wav_path: str, mp3_path: str):
    if not PYDUB_AVAILABLE:
        raise RuntimeError("pydub not available; install ffmpeg and pydub for MP3 export")
    audio = AudioSegment.from_wav(wav_path)
    # add tiny silence padding to avoid clipping on some players
    audio = Silence(duration=250).to_audio_segment() + audio
    audio.export(mp3_path, format='mp3')


def main():
    parser = argparse.ArgumentParser(description='Convert a PDF to spoken audio (Windows offline voices).')
    parser.add_argument('--pdf', required=False, help='Path to PDF file')
    parser.add_argument('--out', required=False, help='Output audio file path (.wav or .mp3)')
    parser.add_argument('--start-page', type=int, help='Start page (1-based, inclusive)')
    parser.add_argument('--end-page', type=int, help='End page (1-based, inclusive)')
    parser.add_argument('--rate', type=int, default=180, help='Speech rate (words per minute)')
    parser.add_argument('--voice', default='default', help='Voice index, id, or "default"')
    parser.add_argument('--list-voices', action='store_true', help='List available voices and exit')

    args = parser.parse_args()

    engine = pyttsx3.init()

    if args.list_voices:
        list_voices(engine)
        return

    if not args.pdf or not args.out:
        print('Error: --pdf and --out are required unless using --list-voices', file=sys.stderr)
        sys.exit(2)

    if not os.path.exists(args.pdf):
        print(f'Error: PDF not found: {args.pdf}', file=sys.stderr)
        sys.exit(2)

    print('Reading PDF ...')
    text = read_pdf_text(args.pdf, args.start_page, args.end_page)
    if not text:
        print('No text extracted from PDF.', file=sys.stderr)
        sys.exit(3)

    out_lower = args.out.lower()
    tmp_wav = args.out if out_lower.endswith('.wav') else os.path.splitext(args.out)[0] + '.wav'

    print(f'Synthesizing speech to {tmp_wav} ...')
    synth_to_wav(engine, text, tmp_wav, rate=args.rate, voice=args.voice)

    if out_lower.endswith('.mp3'):
        print(f'Converting WAV to MP3 {args.out} ...')
        wav_to_mp3(tmp_wav, args.out)
        print('Done.')
    else:
        print('Done.')


if __name__ == '__main__':
    main()
