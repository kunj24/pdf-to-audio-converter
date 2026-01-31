"""Test script to verify smart features work correctly"""
import requests
import time
import os

BASE_URL = 'http://127.0.0.1:5000'

def test_modes():
    print('=== Testing Server ===')
    try:
        r = requests.get(f'{BASE_URL}/api/stats', timeout=5)
        stats = r.json()
        print(f"Stats: {stats}")
        print(f"Smart Features Available: {stats['features'].get('smart_features', False)}")
        print(f"Translator Available: {stats['features'].get('translator', False)}")
    except Exception as e:
        print(f'Server error: {e}')
        return

    print('\n=== Testing File Upload with Different Modes ===')

    pdf_path = r'e:\PDF to Audio\sample_large.pdf'
    if not os.path.exists(pdf_path):
        print(f'ERROR: {pdf_path} not found!')
        return
    
    modes = ['full', 'summary', 'keypoints']
    results = {}

    for mode in modes:
        print(f'\n--- Testing mode: {mode} ---')
        
        with open(pdf_path, 'rb') as f:
            files = {'file': ('sample.pdf', f, 'application/pdf')}
            data = {
                'voice': '0',
                'rate': '180',
                'format': 'wav',
                'mode': mode,
                'target_lang': ''
            }
            r = requests.post(f'{BASE_URL}/upload', files=files, data=data)
        
        if r.status_code != 200:
            print(f'Upload failed: {r.text}')
            continue
        
        job_id = r.json()['job_id']
        print(f'Job ID: {job_id}')
        
        # Wait for completion
        last_progress = -1
        for i in range(120):
            time.sleep(1)
            status = requests.get(f'{BASE_URL}/status/{job_id}').json()
            
            # Print progress updates
            if status['progress'] != last_progress:
                print(f"  {status['progress']}% - {status.get('current_step', '')}")
                last_progress = status['progress']
            
            if status['status'] == 'completed':
                output_file = status.get('output_file', 'N/A')
                file_path = f'e:/PDF to Audio/output/{output_file}'
                if os.path.exists(file_path):
                    size = os.path.getsize(file_path)
                    results[mode] = {'file': output_file, 'size_kb': size // 1024}
                    print(f'  DONE! File: {output_file}, Size: {size // 1024} KB')
                else:
                    print(f'  File not found: {file_path}')
                break
            elif status['status'] == 'failed':
                print(f"  FAILED: {status.get('error', 'Unknown')}")
                break
        else:
            print('  Timeout!')

    print('\n' + '='*50)
    print('=== RESULTS COMPARISON ===')
    print('='*50)
    for mode, info in results.items():
        print(f"  {mode.upper():15} : {info['size_kb']:6} KB")
    
    print('\n=== ANALYSIS ===')
    if 'full' in results and 'summary' in results:
        ratio = results['summary']['size_kb'] / results['full']['size_kb'] * 100
        print(f"Summary is {ratio:.1f}% of full document")
        if ratio > 50:
            print("WARNING: Summary should be ~30% but is larger!")
    
    if 'full' in results and 'keypoints' in results:
        ratio = results['keypoints']['size_kb'] / results['full']['size_kb'] * 100
        print(f"Key points is {ratio:.1f}% of full document")
        if ratio > 30:
            print("WARNING: Key points should be very short but is larger!")

if __name__ == '__main__':
    test_modes()
