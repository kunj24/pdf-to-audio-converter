"""Test translation feature"""
import requests
import time

# Test translation via web endpoint
print('Testing translation via web upload...')
url = 'http://127.0.0.1:5000/upload'

# Create a test file
with open('test_translate.txt', 'w', encoding='utf-8') as f:
    f.write('Hello World. This is a test document for translation. Python is a great programming language.')

# Upload with translation to Hindi
print("Testing translation to Hindi...")
with open('test_translate.txt', 'rb') as f:
    response = requests.post(url, files={'file': f}, data={
        'mode': 'full',
        'target_lang': 'hi',
        'format': 'mp3'
    })
    print('Response:', response.status_code)
    data = response.json()
    print('Job ID:', data.get('job_id'))
    job_id = data.get('job_id')

# Poll for status
for i in range(45):
    time.sleep(2)
    status = requests.get(f'http://127.0.0.1:5000/status/{job_id}').json()
    step = status.get('current_step', '')
    progress = status.get('progress', 0)
    print(f"Status: {status.get('status')} - {step} - Progress: {progress}%")
    
    if 'translation' in status and status['translation']:
        print('Translation info:', status.get('translation'))
    
    if status.get('status') == 'completed':
        print('✅ Conversion completed!')
        trans = status.get('translation')
        if trans:
            print(f"   Translated: {trans['source']} → {trans['target']}")
        else:
            print('   No translation applied')
        break
    elif status.get('status') == 'error':
        print('❌ Error:', status.get('error'))
        break
