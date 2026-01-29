import os
from flask import Flask, render_template, request, send_file, jsonify
import tempfile
import uuid
from werkzeug.utils import secure_filename
import threading
import time
from datetime import datetime, timedelta
import logging
from logging.handlers import RotatingFileHandler

# Import our PDF-to-audio conversion functions
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from pdf_to_audio import read_pdf_text, synth_to_wav, wav_to_mp3
import pyttsx3

# Import enhanced modules
try:
    from text_processor import text_processor, content_analyzer
    TEXT_PROCESSOR_AVAILABLE = True
except ImportError:
    TEXT_PROCESSOR_AVAILABLE = False

try:
    from audio_processor import audio_processor, AudioQuality, AudioFormat
    AUDIO_PROCESSOR_AVAILABLE = True
except ImportError:
    AUDIO_PROCESSOR_AVAILABLE = False

try:
    from document_converter import document_converter, DocumentFormat
    DOCUMENT_CONVERTER_AVAILABLE = True
    # Print document converter status at import time
    print(f"✅ Document converter loaded. Supported: {document_converter.supported_formats}")
except ImportError as e:
    DOCUMENT_CONVERTER_AVAILABLE = False
    print(f"❌ Document converter not available: {e}")

try:
    from job_queue import job_queue, rate_limiter, JobPriority
    JOB_QUEUE_AVAILABLE = True
except ImportError:
    JOB_QUEUE_AVAILABLE = False

try:
    from translator import translator
    TRANSLATOR_AVAILABLE = True
    print(f"✅ Translator loaded. Supported languages: {len(translator.get_popular_languages())}")
except ImportError as e:
    TRANSLATOR_AVAILABLE = False
    print(f"⚠️ Translator not available: {e}")

try:
    from smart_features import smart_features
    SMART_FEATURES_AVAILABLE = True
    print(f"✅ Smart features loaded (summarize, chapters, key points)")
except ImportError as e:
    SMART_FEATURES_AVAILABLE = False
    print(f"⚠️ Smart features not available: {e}")

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size (increased for more formats)
    app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', 'uploads')
    app.config['OUTPUT_FOLDER'] = os.environ.get('OUTPUT_FOLDER', 'output')
    
    # Create directories
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)
    
    # Set up logging
    if not app.debug:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/pdf_audio_converter.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('PDF Audio Converter startup')
    
    return app

app = create_app()

# Store conversion jobs and their status
conversion_jobs = {}
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'epub', 'html', 'htm', 'jpg', 'jpeg', 'png', 'bmp', 'tiff'}

def allowed_file(filename):
    """
    Check if file has allowed extension (case-insensitive)
    Handles files with multiple dots in name (e.g., my.document.pdf)
    """
    if not filename or '.' not in filename:
        return False
    
    # Get extension (everything after last dot)
    ext = filename.rsplit('.', 1)[1].lower().strip()
    
    # Remove any special characters from extension
    ext = ''.join(c for c in ext if c.isalnum())
    
    return ext in ALLOWED_EXTENSIONS

def get_available_voices():
    """Get list of available TTS voices"""
    try:
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        voice_list = []
        for idx, voice in enumerate(voices):
            voice_list.append({
                'index': idx,
                'name': voice.name,
                'id': voice.id
            })
        engine.stop()
        return voice_list
    except Exception as e:
        app.logger.error(f"Error getting voices: {e}")
        return [{'index': 0, 'name': 'Default Voice', 'id': 'default'}]

def convert_pdf_to_audio(job_id, pdf_path, output_path, voice_index, rate, start_page, end_page, output_format, options=None):
    """Optimized background task to convert document to audio with enhanced processing"""
    options = options or {}
    engine = None  # For cleanup
    
    try:
        conversion_jobs[job_id]['status'] = 'processing'
        conversion_jobs[job_id]['progress'] = 0
        
        # Step 1: Extract text from document (Optimized)
        conversion_jobs[job_id]['current_step'] = 'Reading document...'
        conversion_jobs[job_id]['progress'] = 10
        
        # Use enhanced document converter if available
        use_ocr = options.get('use_ocr', False)
        
        if DOCUMENT_CONVERTER_AVAILABLE:
            text, doc_info = document_converter.convert(pdf_path, start_page, end_page, use_ocr=use_ocr)
            conversion_jobs[job_id]['document_info'] = {
                'page_count': doc_info.page_count,
                'word_count': doc_info.word_count,
                'is_scanned': doc_info.is_scanned
            }
        else:
            text = read_pdf_text(pdf_path, start_page, end_page)
        
        # Optimized: Early validation
        if not text or not text.strip():
            raise Exception("No text found in document")
        
        conversion_jobs[job_id]['progress'] = 20
        
        # Step 1.5: Smart Features (if enabled)
        if SMART_FEATURES_AVAILABLE:
            mode = options.get('mode', 'full')  # full, summary, keypoints, chapters, qa
            
            if mode == 'summary':
                conversion_jobs[job_id]['current_step'] = 'Creating summary...'
                summary_ratio = float(options.get('summary_ratio', 0.3))
                text = smart_features.summarize(text, ratio=summary_ratio, max_sentences=10)
                conversion_jobs[job_id]['processing_mode'] = 'Summary Mode'
            
            elif mode == 'keypoints':
                conversion_jobs[job_id]['current_step'] = 'Extracting key points...'
                max_points = int(options.get('max_keypoints', 10))
                key_points = smart_features.extract_key_points(text, max_points=max_points)
                text = '\n\n'.join([f"Key point {i+1}: {kp.text}" for i, kp in enumerate(key_points)])
                conversion_jobs[job_id]['processing_mode'] = f'Key Points Mode ({len(key_points)} points)'
            
            elif mode == 'chapters':
                conversion_jobs[job_id]['current_step'] = 'Detecting chapters...'
                chapters = smart_features.detect_chapters(text)
                # Add chapter markers for better audio navigation
                chapter_texts = []
                for i, chapter in enumerate(chapters):
                    chapter_texts.append(f"Chapter {i+1}: {chapter.title}. {chapter.content}")
                text = '\n\n'.join(chapter_texts)
                conversion_jobs[job_id]['processing_mode'] = f'Chapters Mode ({len(chapters)} chapters)'
            
            elif mode == 'qa':
                conversion_jobs[job_id]['current_step'] = 'Extracting Q&A pairs...'
                qa_pairs = smart_features.extract_qa_pairs(text)
                # Format Q&A for audio
                qa_texts = []
                for i, qa in enumerate(qa_pairs):
                    qa_texts.append(f"Question {i+1}: {qa.question}")
                    qa_texts.append(f"Answer: {qa.answer}")
                    qa_texts.append("")  # Add pause
                text = '\n\n'.join(qa_texts)
                conversion_jobs[job_id]['processing_mode'] = f'Q&A Mode ({len(qa_pairs)} pairs)'
        
        conversion_jobs[job_id]['progress'] = 25
        
        # Step 2: Translation (if enabled)
        if TRANSLATOR_AVAILABLE:
            target_lang = options.get('translate_to', '')
            if target_lang and target_lang != 'none' and target_lang != 'en':
                conversion_jobs[job_id]['current_step'] = f'Translating to {target_lang}...'
                conversion_jobs[job_id]['progress'] = 30
                
                try:
                    translation_result = translator.translate(text, target_lang=target_lang)
                    text = translation_result.text
                    conversion_jobs[job_id]['translation'] = {
                        'source': translation_result.source_lang,
                        'target': translation_result.target_lang,
                        'confidence': translation_result.confidence
                    }
                except Exception as e:
                    app.logger.warning(f"Translation failed: {e}")
        
        conversion_jobs[job_id]['progress'] = 35
        
        # Step 3: Process text with AI enhancements (Optimized)
        conversion_jobs[job_id]['current_step'] = 'Processing text...'
        
        if TEXT_PROCESSOR_AVAILABLE:
            processing_options = {
                'expand_tech_terms': options.get('expand_tech_terms', True),
                'add_pauses': options.get('add_pauses', True),
            }
            text = text_processor.process(text, processing_options)
            
            # Analyze content (parallel with processing if possible)
            analysis = content_analyzer.analyze(text)
            conversion_jobs[job_id]['analysis'] = {
                'word_count': analysis['word_count'],
                'estimated_duration': analysis['estimated_audio_duration'],
                'language': analysis['language']
            }
        
        conversion_jobs[job_id]['progress'] = 45
        
        # Step 3: Initialize TTS engine (Optimized with better settings)
        conversion_jobs[job_id]['current_step'] = 'Initializing text-to-speech...'
        conversion_jobs[job_id]['progress'] = 50
        
        engine = pyttsx3.init()
        
        # Optimized: Configure engine once
        if rate:
            engine.setProperty('rate', rate)
        engine.setProperty('volume', 1.0)
        
        # Step 4: Convert to speech (Optimized)
        conversion_jobs[job_id]['current_step'] = 'Generating speech...'
        conversion_jobs[job_id]['progress'] = 60
        
        # Create temporary WAV file
        temp_wav = output_path.replace('.mp3', '.wav') if output_format == 'mp3' else output_path
        
        synth_to_wav(engine, text, temp_wav, rate=rate, voice=str(voice_index) if voice_index != 'default' else None)
        
        conversion_jobs[job_id]['progress'] = 75
        
        # Step 5: Process audio with enhancements
        if AUDIO_PROCESSOR_AVAILABLE and os.path.exists(temp_wav):
            conversion_jobs[job_id]['current_step'] = 'Enhancing audio...'
            conversion_jobs[job_id]['progress'] = 80
            
            # Normalize audio volume
            if options.get('normalize_audio', True):
                try:
                    audio_processor.normalize_audio(temp_wav)
                except Exception as e:
                    app.logger.warning(f"Audio normalization failed: {e}")
            
            # Trim silence
            if options.get('trim_silence', False):
                try:
                    audio_processor.trim_silence(temp_wav)
                except Exception as e:
                    app.logger.warning(f"Silence trimming failed: {e}")
        
        # Step 6: Convert to MP3 if requested
        if output_format == 'mp3':
            conversion_jobs[job_id]['current_step'] = 'Converting to MP3...'
            conversion_jobs[job_id]['progress'] = 85
            try:
                wav_to_mp3(temp_wav, output_path)
                # Clean up temporary WAV file
                if os.path.exists(temp_wav):
                    os.remove(temp_wav)
            except Exception as mp3_error:
                app.logger.warning(f"MP3 conversion failed: {mp3_error}, keeping WAV format")
                # Keep WAV file if MP3 conversion fails
                if os.path.exists(temp_wav):
                    os.rename(temp_wav, output_path.replace('.mp3', '.wav'))
                    conversion_jobs[job_id]['output_format'] = 'wav'
        
        # Step 7: Complete
        # Determine the actual output file (may be WAV if MP3 conversion failed)
        final_output = output_path if os.path.exists(output_path) else output_path.replace('.mp3', '.wav')
        
        conversion_jobs[job_id]['status'] = 'completed'
        conversion_jobs[job_id]['current_step'] = 'Conversion completed!'
        conversion_jobs[job_id]['progress'] = 100
        conversion_jobs[job_id]['output_file'] = os.path.basename(final_output)  # Use actual file
        
        # Get audio metadata if available
        if AUDIO_PROCESSOR_AVAILABLE and os.path.exists(final_output):
            try:
                metadata = audio_processor.get_metadata(final_output)
                conversion_jobs[job_id]['audio_metadata'] = {
                    'duration': metadata.duration_formatted,
                    'duration_seconds': metadata.duration_seconds,
                    'file_size': metadata.file_size_formatted,
                    'format': metadata.format
                }
            except Exception as e:
                app.logger.warning(f"Could not get audio metadata: {e}")
        
        engine.stop()
        
    except Exception as e:
        conversion_jobs[job_id]['status'] = 'failed'
        conversion_jobs[job_id]['error'] = str(e)
        conversion_jobs[job_id]['progress'] = 0
        app.logger.error(f"Conversion failed for job {job_id}: {e}")

@app.route('/')
def index():
    voices = get_available_voices()
    return render_template('index.html', voices=voices)

@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file selected'}), 400
        
        file = request.files['file']
        if file.filename == '' or not file.filename:
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate filename is not empty after stripping
        if not file.filename.strip():
            return jsonify({'error': 'Invalid file name'}), 400
        
        if not allowed_file(file.filename):
            # Get the actual extension for better error message
            ext = file.filename.rsplit('.', 1)[1] if '.' in file.filename else 'unknown'
            return jsonify({
                'error': f'Unsupported file format: .{ext}',
                'supported': 'PDF, DOC, DOCX, TXT, EPUB, HTML, HTM (Images: JPG, PNG, BMP, TIFF with OCR)'
            }), 400
        
        # Get form parameters
        voice_index = request.form.get('voice', 'default')
        try:
            rate = int(request.form.get('rate', 180))
            rate = max(80, min(350, rate))  # Clamp between 80-350
        except (ValueError, TypeError):
            rate = 180
            
        start_page = None
        end_page = None
        if request.form.get('start_page'):
            try:
                start_page = max(1, int(request.form.get('start_page')))
            except (ValueError, TypeError):
                pass
                
        if request.form.get('end_page'):
            try:
                end_page = max(1, int(request.form.get('end_page')))
            except (ValueError, TypeError):
                pass
                
        output_format = request.form.get('format', 'mp3')
        if output_format not in ['wav', 'mp3']:
            output_format = 'mp3'
        
        # Get advanced options
        options = {
            'use_ocr': request.form.get('use_ocr', 'false').lower() == 'true',
            'expand_tech_terms': request.form.get('expand_tech_terms', 'true').lower() == 'true',
            'add_pauses': request.form.get('add_pauses', 'true').lower() == 'true',
            'normalize_audio': request.form.get('normalize_audio', 'true').lower() == 'true',
            'trim_silence': request.form.get('trim_silence', 'false').lower() == 'true',
            'quality': request.form.get('quality', '192'),
        }
        
        # Save uploaded file with better filename handling
        original_filename = file.filename
        # Secure filename but preserve extension
        filename = secure_filename(original_filename)
        
        # If secure_filename stripped too much, recreate with UUID
        if not filename or len(filename) < 3:
            ext = original_filename.rsplit('.', 1)[1] if '.' in original_filename else 'pdf'
            filename = f"document.{ext}"
        
        job_id = str(uuid.uuid4())
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{job_id}_{filename}")
        file.save(file_path)
        
        # Prepare output file
        output_filename = f"{job_id}_{os.path.splitext(filename)[0]}.{output_format}"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        
        # Initialize job status
        conversion_jobs[job_id] = {
            'status': 'queued',
            'progress': 0,
            'current_step': 'Queued for processing...',
            'created_at': datetime.now(),
            'pdf_filename': filename,
            'output_format': output_format,
            'options': options
        }
        
        # Start conversion in background thread
        thread = threading.Thread(
            target=convert_pdf_to_audio,
            args=(job_id, file_path, output_path, voice_index, rate, start_page, end_page, output_format, options)
        )
        thread.daemon = True
        thread.start()
        
        app.logger.info(f"Started conversion job {job_id} for file {filename}")
        return jsonify({'job_id': job_id, 'message': 'Conversion started'}), 200
    
    except Exception as e:
        app.logger.error(f"Upload failed: {e}")
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@app.route('/status/<job_id>')
def get_status(job_id):
    try:
        if job_id not in conversion_jobs:
            return jsonify({'error': 'Job not found'}), 404
        
        job = conversion_jobs[job_id]
        return jsonify({
            'status': job['status'],
            'progress': job['progress'],
            'current_step': job.get('current_step', ''),
            'output_file': job.get('output_file'),
            'error': job.get('error')
        })
    except Exception as e:
        app.logger.error(f"Status check failed for job {job_id}: {e}")
        return jsonify({'error': f'Status check failed: {str(e)}'}), 500

@app.route('/download/<job_id>')
def download_file(job_id):
    try:
        if job_id not in conversion_jobs:
            return "File not found", 404
        
        job = conversion_jobs[job_id]
        if job['status'] != 'completed':
            return "File not ready", 400
        
        output_file = job.get('output_file')
        if not output_file:
            return "File not found", 404
        
        file_path = os.path.join(app.config['OUTPUT_FOLDER'], output_file)
        if not os.path.exists(file_path):
            return "File not found", 404
        
        # Check if it's a download request or streaming request
        is_download = request.args.get('download', 'true').lower() == 'true'
        
        return send_file(
            file_path,
            as_attachment=is_download,
            download_name=f"converted_{job['pdf_filename'].replace('.pdf', '')}.{job['output_format']}",
            mimetype='audio/wav' if job['output_format'] == 'wav' else 'audio/mpeg'
        )
    except Exception as e:
        app.logger.error(f"Download failed for job {job_id}: {e}")
        return "Download failed", 500

@app.route('/cleanup')
def cleanup_old_files():
    """Clean up old files (older than 1 hour)"""
    try:
        cutoff_time = datetime.now() - timedelta(hours=1)
        cleaned_count = 0
        
        # Clean up old jobs and files
        jobs_to_remove = []
        for job_id, job in conversion_jobs.items():
            if job['created_at'] < cutoff_time:
                jobs_to_remove.append(job_id)
                
                # Remove associated files
                for folder in [app.config['UPLOAD_FOLDER'], app.config['OUTPUT_FOLDER']]:
                    for filename in os.listdir(folder):
                        if filename.startswith(job_id):
                            try:
                                os.remove(os.path.join(folder, filename))
                                cleaned_count += 1
                            except OSError:
                                pass
        
        # Remove old job records
        for job_id in jobs_to_remove:
            del conversion_jobs[job_id]
        
        app.logger.info(f"Cleaned up {cleaned_count} files and {len(jobs_to_remove)} jobs")
        return jsonify({'message': f'Cleaned up {cleaned_count} old files and {len(jobs_to_remove)} jobs'})
    except Exception as e:
        app.logger.error(f"Cleanup failed: {e}")
        return jsonify({'error': 'Cleanup failed'}), 500


# ==================== NEW API ENDPOINTS ====================

@app.route('/api/features')
def get_features():
    """Get available features based on installed modules"""
    return jsonify({
        'text_processing': TEXT_PROCESSOR_AVAILABLE,
        'audio_processing': AUDIO_PROCESSOR_AVAILABLE,
        'document_converter': DOCUMENT_CONVERTER_AVAILABLE,
        'job_queue': JOB_QUEUE_AVAILABLE,
        'supported_formats': list(ALLOWED_EXTENSIONS),
        'max_file_size_mb': app.config['MAX_CONTENT_LENGTH'] // (1024 * 1024),
    })


@app.route('/api/analyze', methods=['POST'])
def analyze_document():
    """Analyze document and return metadata without conversion"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if not allowed_file(file.filename):
            return jsonify({'error': 'Unsupported file format'}), 400
        
        # Save temporarily
        filename = secure_filename(file.filename)
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], f"temp_{uuid.uuid4()}_{filename}")
        file.save(temp_path)
        
        try:
            result = {}
            
            # Get document info
            if DOCUMENT_CONVERTER_AVAILABLE:
                text, doc_info = document_converter.convert(temp_path)
                result['document'] = {
                    'format': doc_info.format.value,
                    'page_count': doc_info.page_count,
                    'word_count': doc_info.word_count,
                    'has_images': doc_info.has_images,
                    'has_tables': doc_info.has_tables,
                    'is_scanned': doc_info.is_scanned,
                    'title': doc_info.title,
                    'author': doc_info.author
                }
                
                # Analyze content
                if TEXT_PROCESSOR_AVAILABLE:
                    analysis = content_analyzer.analyze(text)
                    result['analysis'] = {
                        'word_count': analysis['word_count'],
                        'sentence_count': analysis['sentence_count'],
                        'paragraph_count': analysis['paragraph_count'],
                        'estimated_audio_duration': analysis['estimated_audio_duration'],
                        'estimated_minutes': analysis['estimated_minutes'],
                        'language': analysis['language'],
                        'chapter_count': analysis['chapter_count'],
                        'chapters': analysis['chapters'][:10],  # Limit to first 10 chapters
                    }
            else:
                # Basic analysis
                text = read_pdf_text(temp_path)
                result['document'] = {
                    'word_count': len(text.split()) if text else 0
                }
            
            return jsonify(result)
            
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    except Exception as e:
        app.logger.error(f"Analysis failed: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/voices')
def get_voices_api():
    """Get available voices as JSON"""
    voices = get_available_voices()
    return jsonify({
        'voices': voices,
        'default_voice': 0 if voices else None
    })


@app.route('/api/stats')
def get_stats():
    """Get conversion statistics"""
    total_jobs = len(conversion_jobs)
    completed = sum(1 for j in conversion_jobs.values() if j['status'] == 'completed')
    failed = sum(1 for j in conversion_jobs.values() if j['status'] == 'failed')
    processing = sum(1 for j in conversion_jobs.values() if j['status'] == 'processing')
    queued = sum(1 for j in conversion_jobs.values() if j['status'] == 'queued')
    
    return jsonify({
        'total_jobs': total_jobs,
        'completed': completed,
        'failed': failed,
        'processing': processing,
        'queued': queued,
        'features': {
            'text_processing': TEXT_PROCESSOR_AVAILABLE,
            'audio_processing': AUDIO_PROCESSOR_AVAILABLE,
            'document_converter': DOCUMENT_CONVERTER_AVAILABLE,
            'translator': TRANSLATOR_AVAILABLE,
            'smart_features': SMART_FEATURES_AVAILABLE,
        }
    })


@app.route('/api/languages')
def get_languages():
    """Get available translation languages"""
    if not TRANSLATOR_AVAILABLE:
        return jsonify({'error': 'Translation not available'}), 503
    
    return jsonify({
        'popular': translator.get_popular_languages(),
        'all': translator.get_available_languages()
    })


@app.route('/api/detect-language', methods=['POST'])
def detect_language():
    """Detect language of text"""
    if not TRANSLATOR_AVAILABLE:
        return jsonify({'error': 'Translation not available'}), 503
    
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        lang_code, confidence = translator.detect_language(text)
        lang_name = translator.get_available_languages().get(lang_code, 'Unknown')
        
        return jsonify({
            'language': lang_code,
            'language_name': lang_name,
            'confidence': confidence
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/translate-preview', methods=['POST'])
def translate_preview():
    """Preview translation of first few sentences"""
    if not TRANSLATOR_AVAILABLE:
        return jsonify({'error': 'Translation not available'}), 503
    
    try:
        data = request.get_json()
        text = data.get('text', '')[:500]  # Preview first 500 chars
        target_lang = data.get('target_lang', 'en')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        result = translator.translate(text, target_lang=target_lang)
        
        return jsonify({
            'original': text,
            'translated': result.text,
            'source_language': result.source_lang,
            'target_language': result.target_lang,
            'confidence': result.confidence
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/summarize', methods=['POST'])
def api_summarize():
    """Generate summary of text"""
    if not SMART_FEATURES_AVAILABLE:
        return jsonify({'error': 'Smart features not available'}), 503
    
    try:
        data = request.get_json()
        text = data.get('text', '')
        ratio = float(data.get('ratio', 0.3))
        max_sentences = int(data.get('max_sentences', 5))
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        summary = smart_features.summarize(text, ratio=ratio, max_sentences=max_sentences)
        
        return jsonify({
            'summary': summary,
            'original_length': len(text),
            'summary_length': len(summary),
            'compression_ratio': len(summary) / len(text)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/key-points', methods=['POST'])
def api_key_points():
    """Extract key points from text"""
    if not SMART_FEATURES_AVAILABLE:
        return jsonify({'error': 'Smart features not available'}), 503
    
    try:
        data = request.get_json()
        text = data.get('text', '')
        max_points = int(data.get('max_points', 10))
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        key_points = smart_features.extract_key_points(text, max_points=max_points)
        
        return jsonify({
            'key_points': [
                {
                    'text': kp.text,
                    'importance': kp.importance,
                    'category': kp.category
                } for kp in key_points
            ],
            'count': len(key_points)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/chapters', methods=['POST'])
def api_chapters():
    """Detect chapters in text"""
    if not SMART_FEATURES_AVAILABLE:
        return jsonify({'error': 'Smart features not available'}), 503
    
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        chapters = smart_features.detect_chapters(text)
        
        return jsonify({
            'chapters': [
                {
                    'title': ch.title,
                    'length': len(ch.content),
                    'level': ch.level
                } for ch in chapters
            ],
            'count': len(chapters)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/qa-extract', methods=['POST'])
def api_qa_extract():
    """Extract Q&A pairs from text"""
    if not SMART_FEATURES_AVAILABLE:
        return jsonify({'error': 'Smart features not available'}), 503
    
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        qa_pairs = smart_features.extract_qa_pairs(text)
        
        return jsonify({
            'qa_pairs': [
                {
                    'question': qa.question,
                    'answer': qa.answer,
                    'confidence': qa.confidence
                } for qa in qa_pairs
            ],
            'count': len(qa_pairs)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
