import sys
sys.path.append('src')
from document_converter import document_converter

print("=" * 50)
print("WORD FILE SUPPORT STATUS")
print("=" * 50)
print()
print("✅ DOCX Support:", "ENABLED" if document_converter.supported_formats.get('docx') else "DISABLED")
print("✅ DOC Support:", "ENABLED" if document_converter.supported_formats.get('doc') else "DISABLED")
print("✅ EPUB Support:", "ENABLED" if document_converter.supported_formats.get('epub') else "DISABLED")
print()
print("All Supported Formats:")
for fmt, available in document_converter.supported_formats.items():
    status = "✅" if available else "❌"
    print(f"  {status} {fmt.upper()}")
print()
print("=" * 50)
