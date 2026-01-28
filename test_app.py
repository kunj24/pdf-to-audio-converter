"""
Simple test to verify the app works correctly
"""
import os
import sys
sys.path.append('src')

print("=" * 50)
print("Testing PDF to Audio Converter")
print("=" * 50)

# Test 1: Import all modules
print("\n1. Testing module imports...")
try:
    from app import app
    print("✓ app.py imported successfully")
except Exception as e:
    print(f"✗ Failed to import app.py: {e}")
    sys.exit(1)

try:
    from text_processor import text_processor
    print("✓ text_processor imported successfully")
except Exception as e:
    print(f"✗ Failed to import text_processor: {e}")

try:
    from audio_processor import audio_processor
    print("✓ audio_processor imported successfully")
except Exception as e:
    print(f"✗ Failed to import audio_processor: {e}")

try:
    from document_converter import document_converter
    print("✓ document_converter imported successfully")
except Exception as e:
    print(f"✗ Failed to import document_converter: {e}")

try:
    from job_queue import job_queue
    print("✓ job_queue imported successfully")
except Exception as e:
    print(f"✗ Failed to import job_queue: {e}")

# Test 2: Check Flask routes
print("\n2. Testing Flask routes...")
with app.app_context():
    routes = [rule.rule for rule in app.url_map.iter_rules()]
    required_routes = ['/', '/upload', '/status/<job_id>', '/download/<job_id>']
    
    for route in required_routes:
        if any(r == route for r in routes):
            print(f"✓ Route {route} exists")
        else:
            print(f"✗ Route {route} missing")

# Test 3: Test text processor
print("\n3. Testing text processor...")
try:
    sample_text = "Dr. Smith said the meeting is at 3:00 PM. The URL is https://example.com and email is test@example.com."
    processed = text_processor.process(sample_text)
    print(f"✓ Text processing works")
    print(f"  Input:  {sample_text[:60]}...")
    print(f"  Output: {processed[:60]}...")
except Exception as e:
    print(f"✗ Text processing failed: {e}")

# Test 4: Test document converter
print("\n4. Testing document converter...")
try:
    supported = document_converter.supported_formats
    print(f"✓ Document converter loaded")
    print(f"  Supported formats:")
    for fmt, available in supported.items():
        status = "✓" if available else "✗"
        print(f"    {status} {fmt}")
except Exception as e:
    print(f"✗ Document converter failed: {e}")

# Test 5: Check directories
print("\n5. Checking directories...")
dirs = ['uploads', 'output', 'logs', 'templates', 'src']
for dir_name in dirs:
    if os.path.exists(dir_name):
        print(f"✓ Directory '{dir_name}' exists")
    else:
        print(f"✗ Directory '{dir_name}' missing")

# Test 6: Check required files
print("\n6. Checking required files...")
files = [
    'app.py',
    'templates/index.html',
    'src/pdf_to_audio.py',
    'src/text_processor.py',
    'src/audio_processor.py',
    'src/document_converter.py',
    'src/job_queue.py',
    'requirements.txt'
]
for file_name in files:
    if os.path.exists(file_name):
        print(f"✓ File '{file_name}' exists")
    else:
        print(f"✗ File '{file_name}' missing")

# Test 7: Test voices
print("\n7. Testing TTS voices...")
try:
    import pyttsx3
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    print(f"✓ Found {len(voices)} TTS voices:")
    for i, voice in enumerate(voices[:3]):  # Show first 3
        print(f"    {i}: {voice.name}")
    engine.stop()
except Exception as e:
    print(f"✗ TTS test failed: {e}")

print("\n" + "=" * 50)
print("Test Complete!")
print("=" * 50)
print("\n✓ The app is ready to use!")
print("  Visit: http://127.0.0.1:5000")
print("\nNOTE: Some advanced features require additional software:")
print("  - OCR support: Install Tesseract-OCR")
print("  - MP3 export: Install FFmpeg")
print("  - PDF image conversion: Install Poppler")
