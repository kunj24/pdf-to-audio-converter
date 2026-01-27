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
    reader = PdfReader(path)
    n = len(reader.pages)
    s = start_page - 1 if start_page else 0
    e = end_page if end_page else n
    s = max(0, s)
    e = min(n, e)
    chunks = []
    for i in range(s, e):
        txt = reader.pages[i].extract_text() or ""
        chunks.append(txt)
    full = "\n\n".join(chunks)
    return normalize_text(full)


def normalize_text(text: str) -> str:
    # Remove repeated spaces, join broken lines, fix hyphenation at EOL
    text = text.replace('\r', '')
    lines = text.split('\n')
    joined = []
    for ln in lines:
        ln = re.sub(r"\s+", " ", ln).strip()
        joined.append(ln)
    text = " ".join(joined)
    text = re.sub(r"-\s+", "", text)  # de-hyphenation
    return text.strip()


def list_voices(engine: pyttsx3.Engine):
    voices = engine.getProperty('voices')
    for idx, v in enumerate(voices):
        print(f"[{idx}] {v.name} | id={v.id}")


def synth_to_wav(engine: pyttsx3.Engine, text: str, wav_path: str, rate: Optional[int] = None, voice: Optional[str] = None):
    if rate:
        engine.setProperty('rate', rate)
    if voice and voice != 'default':
        # Try by index, else by id/name
        try:
            vi = int(voice)
            voices = engine.getProperty('voices')
            if 0 <= vi < len(voices):
                engine.setProperty('voice', voices[vi].id)
        except ValueError:
            engine.setProperty('voice', voice)
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
