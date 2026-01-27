from flask import Flask, render_template, request, send_file, jsonify, flash, redirect, url_for
import os
import tempfile
import uuid
from werkzeug.utils import secure_filename
import threading
import time
from datetime import datetime, timedelta

# Import our PDF-to-audio conversion functions
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from pdf_to_audio import read_pdf_text, synth_to_wav, wav_to_mp3
import pyttsx3

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'

# Configuration
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'pdf'}

# Create directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Store conversion jobs and their status
conversion_jobs = {}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
        return voice_list
    except Exception as e:
        return [{'index': 0, 'name': 'Default Voice', 'id': 'default'}]

def convert_pdf_to_audio(job_id, pdf_path, output_path, voice_index, rate, start_page, end_page, output_format):
    """Background task to convert PDF to audio"""
    try:
        conversion_jobs[job_id]['status'] = 'processing'
        conversion_jobs[job_id]['progress'] = 0
        
        # Step 1: Extract text from PDF
        conversion_jobs[job_id]['current_step'] = 'Extracting text from PDF...'
        conversion_jobs[job_id]['progress'] = 20
        
        text = read_pdf_text(pdf_path, start_page, end_page)
        if not text:
            raise Exception("No text found in PDF")
        
        # Step 2: Initialize TTS engine
        conversion_jobs[job_id]['current_step'] = 'Initializing text-to-speech...'
        conversion_jobs[job_id]['progress'] = 40
        
        engine = pyttsx3.init()
        
        # Step 3: Convert to speech
        conversion_jobs[job_id]['current_step'] = 'Converting text to speech...'
        conversion_jobs[job_id]['progress'] = 60
        
        # Create temporary WAV file
        temp_wav = output_path.replace('.mp3', '.wav') if output_format == 'mp3' else output_path
        
        synth_to_wav(engine, text, temp_wav, rate=rate, voice=str(voice_index) if voice_index != 'default' else None)
        
        # Step 4: Convert to MP3 if requested
        if output_format == 'mp3':
            conversion_jobs[job_id]['current_step'] = 'Converting to MP3...'
            conversion_jobs[job_id]['progress'] = 80
            wav_to_mp3(temp_wav, output_path)
            # Clean up temporary WAV file
            if os.path.exists(temp_wav):
                os.remove(temp_wav)
        
        # Step 5: Complete
        conversion_jobs[job_id]['status'] = 'completed'
        conversion_jobs[job_id]['current_step'] = 'Conversion completed!'
        conversion_jobs[job_id]['progress'] = 100
        conversion_jobs[job_id]['output_file'] = os.path.basename(output_path)
        
    except Exception as e:
        conversion_jobs[job_id]['status'] = 'failed'
        conversion_jobs[job_id]['error'] = str(e)
        conversion_jobs[job_id]['progress'] = 0

@app.route('/')
def index():
    voices = get_available_voices()
    return render_template('index.html', voices=voices)

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file selected'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Only PDF files are allowed'}), 400
        
        # Get form parameters
        voice_index = request.form.get('voice', 'default')
        rate = int(request.form.get('rate', 180))
        start_page = int(request.form.get('start_page', 0)) if request.form.get('start_page') else None
        end_page = int(request.form.get('end_page', 0)) if request.form.get('end_page') else None
        output_format = request.form.get('format', 'wav')
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        job_id = str(uuid.uuid4())
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{job_id}_{filename}")
        file.save(pdf_path)
        
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
            'output_format': output_format
        }
        
        # Start conversion in background thread
        thread = threading.Thread(
            target=convert_pdf_to_audio,
            args=(job_id, pdf_path, output_path, voice_index, rate, start_page, end_page, output_format)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({'job_id': job_id, 'message': 'Conversion started'}), 200
    
    except Exception as e:
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
        return jsonify({'error': f'Status check failed: {str(e)}'}), 500

@app.route('/download/<job_id>')
def download_file(job_id):
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
    
    return send_file(
        file_path,
        as_attachment=True,
        download_name=f"converted_{job['pdf_filename'].replace('.pdf', '')}.{job['output_format']}",
        mimetype='audio/wav' if job['output_format'] == 'wav' else 'audio/mpeg'
    )

@app.route('/cleanup')
def cleanup_old_files():
    """Clean up old files (older than 1 hour)"""
    cutoff_time = datetime.now() - timedelta(hours=1)
    cleaned_count = 0
    
    # Clean up old jobs and files
    jobs_to_remove = []
    for job_id, job in conversion_jobs.items():
        if job['created_at'] < cutoff_time:
            jobs_to_remove.append(job_id)
            
            # Remove associated files
            for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER]:
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
    
    return jsonify({'message': f'Cleaned up {cleaned_count} old files and {len(jobs_to_remove)} jobs'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)