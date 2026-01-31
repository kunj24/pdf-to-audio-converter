"""Test translation with multiple languages"""
import requests
import time

url = 'http://127.0.0.1:5000/upload'

# Test with Spanish
print('Testing translation to Spanish...')
with open('test_translate.txt', 'rb') as f:
    response = requests.post(url, files={'file': f}, data={
        'mode': 'full',
        'target_lang': 'es',
        'format': 'mp3'
    })
    job_id = response.json().get('job_id')
    print(f'Job ID: {job_id}')

for i in range(30):
    time.sleep(2)
    status = requests.get(f'http://127.0.0.1:5000/status/{job_id}').json()
    if status.get('status') == 'completed':
        trans = status.get('translation')
        if trans:
            print(f"✅ Translation: {trans['source']} -> {trans['target']}")
        else:
            print('No translation')
        break
    elif status.get('status') == 'error':
        print(f"❌ Error: {status.get('error')}")
        break
    print(f"Progress: {status.get('progress')}%")

# Test with PDF and translation
print()
print('Testing PDF with Hindi translation + Summary mode...')
with open('sample_large.pdf', 'rb') as f:
    response = requests.post(url, files={'file': f}, data={
        'mode': 'summary',
        'target_lang': 'hi',
        'format': 'mp3'
    })
    job_id = response.json().get('job_id')
    print(f'Job ID: {job_id}')

for i in range(60):
    time.sleep(2)
    status = requests.get(f'http://127.0.0.1:5000/status/{job_id}').json()
    if status.get('status') == 'completed':
        trans = status.get('translation')
        mode = status.get('processing_mode', 'N/A')
        if trans:
            print(f"✅ Mode: {mode}, Translation: {trans['source']} -> {trans['target']}")
        else:
            print(f"✅ Mode: {mode}, No translation")
        break
    elif status.get('status') == 'error':
        print(f"❌ Error: {status.get('error')}")
        break
    print(f"Progress: {status.get('progress')}% - {status.get('current_step', '')}")

print()
print('=== All translation tests completed ===')
