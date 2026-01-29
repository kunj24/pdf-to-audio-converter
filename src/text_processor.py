"""
AI-Powered Text Processor
Smart text processing for better audio output
"""

import re
from typing import Optional, List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class TextProcessor:
    """Advanced text processing for cleaner audio output"""
    
    def __init__(self):
        # Common abbreviations and their expansions
        self.abbreviations = {
            'Dr.': 'Doctor',
            'Mr.': 'Mister',
            'Mrs.': 'Misses',
            'Ms.': 'Miss',
            'Prof.': 'Professor',
            'Jr.': 'Junior',
            'Sr.': 'Senior',
            'vs.': 'versus',
            'etc.': 'etcetera',
            'e.g.': 'for example',
            'i.e.': 'that is',
            'approx.': 'approximately',
            'Inc.': 'Incorporated',
            'Corp.': 'Corporation',
            'Ltd.': 'Limited',
            'No.': 'Number',
            'St.': 'Street',
            'Ave.': 'Avenue',
            'Blvd.': 'Boulevard',
            'Fig.': 'Figure',
            'Vol.': 'Volume',
            'pg.': 'page',
            'pp.': 'pages',
            'Jan.': 'January',
            'Feb.': 'February',
            'Mar.': 'March',
            'Apr.': 'April',
            'Jun.': 'June',
            'Jul.': 'July',
            'Aug.': 'August',
            'Sep.': 'September',
            'Oct.': 'October',
            'Nov.': 'November',
            'Dec.': 'December',
        }
        
        # Technical terms pronunciation
        self.tech_terms = {
            'API': 'A P I',
            'URL': 'U R L',
            'HTML': 'H T M L',
            'CSS': 'C S S',
            'JSON': 'Jason',
            'SQL': 'S Q L',
            'PDF': 'P D F',
            'AI': 'A I',
            'ML': 'M L',
            'GPU': 'G P U',
            'CPU': 'C P U',
            'RAM': 'Ram',
            'ROM': 'Rom',
            'USB': 'U S B',
            'WiFi': 'Wi-Fi',
            'IoT': 'I o T',
            'FAQ': 'F A Q',
            'CEO': 'C E O',
            'CTO': 'C T O',
            'CFO': 'C F O',
        }
    
    def process(self, text: str, options: Optional[Dict] = None) -> str:
        """
        Main processing pipeline for text with optimized caching
        
        Args:
            text: Raw text from PDF
            options: Processing options dict
        
        Returns:
            Processed text optimized for TTS
        """
        options = options or {}
        
        # Optimized: Quick exit for empty text
        if not text or not text.strip():
            return ""
        
        # Optimized: Pre-compile patterns if not cached
        if not hasattr(self, '_patterns_compiled'):
            self._compile_patterns()
        
        # Apply processing steps in optimized order
        text = self.clean_whitespace(text)  # Do first for better processing
        text = self.fix_hyphenation(text)
        text = self.remove_headers_footers(text)
        
        # Optimized: Batch similar operations
        text = self.expand_abbreviations(text)
        if options.get('expand_tech_terms', True):
            text = self.expand_tech_terms(text)
        
        text = self.handle_numbers(text)
        text = self.handle_special_characters(text)
        text = self.handle_urls_emails(text)
        text = self.handle_lists(text)
        text = self.improve_punctuation(text)
        
        if options.get('add_pauses', True):
            text = self.add_natural_pauses(text)
        
        return text.strip()
    
    def _compile_patterns(self):
        """Pre-compile regex patterns for better performance"""
        self._patterns_compiled = True
        self._page_num_pattern = re.compile(r'^-?\s*\d+\s*-?$')
        self._page_label_pattern = re.compile(r'^Page\s+\d+(\s+of\s+\d+)?$', re.IGNORECASE)
        self._whitespace_pattern = re.compile(r' +')
        self._multi_newline_pattern = re.compile(r'\n{3,}')
        self._hyphen_pattern = re.compile(r'(\w+)-\s*\n\s*(\w+)')
        self._currency_patterns = [
            (re.compile(r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)'), r'\1 dollars'),
            (re.compile(r'€(\d+(?:,\d{3})*(?:\.\d{2})?)'), r'\1 euros'),
            (re.compile(r'£(\d+(?:,\d{3})*(?:\.\d{2})?)'), r'\1 pounds'),
        ]
        self._percent_pattern = re.compile(r'(\d+(?:\.\d+)?)\s*%')
    
    def remove_headers_footers(self, text: str) -> str:
        """Optimized header/footer removal"""
        if not text:
            return ""
        
        lines = text.split('\n')
        cleaned_lines = []
        
        # Pre-compile patterns if not using cached ones
        page_num = self._page_num_pattern if hasattr(self, '_page_num_pattern') else re.compile(r'^-?\s*\d+\s*-?$')
        page_label = self._page_label_pattern if hasattr(self, '_page_label_pattern') else re.compile(r'^Page\s+\d+(\s+of\s+\d+)?$', re.IGNORECASE)
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            # Skip empty lines
            if not line_stripped:
                continue
            
            # Skip page numbers
            if page_num.match(line_stripped) or page_label.match(line_stripped):
                continue
            
            # Skip common header/footer patterns
            if re.match(r'^\d+\s*/\s*\d+$', line_stripped):  # "1/10" format
                continue
            if re.match(r'^©|^Copyright|^All Rights Reserved', line_stripped, re.IGNORECASE):
                continue
            
            # Skip very short repeated lines (likely headers)
            if len(line_stripped) < 5 and 0 < i < len(lines) - 1:
                continue
            
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def clean_whitespace(self, text: str) -> str:
        """Optimized whitespace cleanup"""
        if not text:
            return ""
        
        # Remove carriage returns
        text = text.replace('\r', '')
        
        # Use pre-compiled patterns if available
        if hasattr(self, '_whitespace_pattern'):
            text = self._whitespace_pattern.sub(' ', text)
            text = self._multi_newline_pattern.sub('\n\n', text)
        else:
            text = re.sub(r' +', ' ', text)
            text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Optimized: Process lines in batch
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        text = '\n'.join(lines)
        
        return text
    
    def fix_hyphenation(self, text: str) -> str:
        """Optimized hyphenation fixing"""
        if not text:
            return ""
        
        # Use pre-compiled pattern if available
        if hasattr(self, '_hyphen_pattern'):
            text = self._hyphen_pattern.sub(r'\1\2', text)
        else:
            text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)
        return text
    
    def expand_abbreviations(self, text: str) -> str:
        """Expand common abbreviations for better speech"""
        for abbrev, expansion in self.abbreviations.items():
            # Use word boundaries to avoid partial matches
            pattern = re.escape(abbrev)
            text = re.sub(rf'\b{pattern}', expansion, text)
        return text
    
    def expand_tech_terms(self, text: str) -> str:
        """Expand technical acronyms for proper pronunciation"""
        for term, pronunciation in self.tech_terms.items():
            pattern = rf'\b{term}\b'
            text = re.sub(pattern, pronunciation, text)
        return text
    
    def handle_numbers(self, text: str) -> str:
        """Optimized number conversion to spoken form"""
        if not text:
            return ""
        
        # Use pre-compiled patterns if available
        if hasattr(self, '_currency_patterns'):
            for pattern, replacement in self._currency_patterns:
                text = pattern.sub(replacement, text)
            text = self._percent_pattern.sub(r'\1 percent', text)
        else:
            # Handle currency
            text = re.sub(r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)', r'\1 dollars', text)
            text = re.sub(r'€(\d+(?:,\d{3})*(?:\.\d{2})?)', r'\1 euros', text)
            text = re.sub(r'£(\d+(?:,\d{3})*(?:\.\d{2})?)', r'\1 pounds', text)
            text = re.sub(r'(\d+(?:\.\d+)?)\s*%', r'\1 percent', text)
        
        # Handle ordinals (optimized with fewer regex calls)
        ordinal_map = {'1st': 'first', '2nd': 'second', '3rd': 'third'}
        for ordinal, word in ordinal_map.items():
            text = text.replace(f' {ordinal} ', f' {word} ')
            text = text.replace(f' {ordinal},', f' {word},')
            text = text.replace(f' {ordinal}.', f' {word}.')
        
        # Handle times
        text = re.sub(r'(\d{1,2}):(\d{2})\s*(AM|PM|am|pm)', r'\1 \2 \3', text)
        
        # Handle dates (MM/DD/YYYY or DD/MM/YYYY)
        text = re.sub(r'(\d{1,2})/(\d{1,2})/(\d{4})', r'\1 \2 \3', text)
        
        return text
    
    def handle_special_characters(self, text: str) -> str:
        """Handle special characters for better speech"""
        
        # Replace common symbols
        replacements = {
            '&': ' and ',
            '@': ' at ',
            '#': ' number ',
            '+': ' plus ',
            '=': ' equals ',
            '<': ' less than ',
            '>': ' greater than ',
            '~': ' approximately ',
            '°': ' degrees ',
            '™': '',
            '®': '',
            '©': '',
            '•': ', ',
            '→': ' leads to ',
            '←': ' from ',
            '↔': ' both ways ',
            '…': '...',
            '"': '"',
            '"': '"',
            ''': "'",
            ''': "'",
            '–': '-',
            '—': ' - ',
        }
        
        for char, replacement in replacements.items():
            text = text.replace(char, replacement)
        
        return text
    
    def improve_punctuation(self, text: str) -> str:
        """Improve punctuation for natural speech pauses"""
        
        # Ensure space after punctuation
        text = re.sub(r'([.!?])([A-Z])', r'\1 \2', text)
        
        # Add slight pause indicators (semicolons for TTS)
        text = re.sub(r'\s*;\s*', '; ', text)
        
        # Handle parenthetical content
        text = re.sub(r'\s*\(\s*', ' (', text)
        text = re.sub(r'\s*\)\s*', ') ', text)
        
        return text
    
    def handle_urls_emails(self, text: str) -> str:
        """Handle URLs and emails for speech"""
        
        # Replace URLs with "link" or skip
        text = re.sub(
            r'https?://[^\s<>"{}|\\^`\[\]]+',
            ' (link) ',
            text
        )
        
        # Handle email addresses
        text = re.sub(
            r'[\w.+-]+@[\w-]+\.[\w.-]+',
            ' (email address) ',
            text
        )
        
        return text
    
    def handle_lists(self, text: str) -> str:
        """Format lists for better audio"""
        
        # Handle numbered lists
        text = re.sub(r'^(\d+)\.\s+', r'Item \1: ', text, flags=re.MULTILINE)
        
        # Handle bullet points (various forms)
        text = re.sub(r'^[-•*]\s+', 'Point: ', text, flags=re.MULTILINE)
        
        return text
    
    def add_natural_pauses(self, text: str) -> str:
        """Add markers for natural pauses in speech"""
        
        # Add pause after periods (paragraph breaks)
        text = re.sub(r'\.\s*\n\n', '.\n\n', text)
        
        # Ensure proper pauses at sentence ends
        text = re.sub(r'([.!?])\s+', r'\1 ', text)
        
        return text
    
    def summarize(self, text: str, max_sentences: int = 10) -> str:
        """
        Generate a simple extractive summary
        
        Args:
            text: Full text
            max_sentences: Maximum sentences in summary
        
        Returns:
            Summarized text
        """
        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        if len(sentences) <= max_sentences:
            return text
        
        # Simple scoring based on position and length
        scored_sentences = []
        for i, sentence in enumerate(sentences):
            score = 0
            
            # First and last sentences often important
            if i < 3:
                score += 3 - i
            if i >= len(sentences) - 3:
                score += 1
            
            # Longer sentences often more informative
            word_count = len(sentence.split())
            if 10 <= word_count <= 30:
                score += 2
            elif word_count > 30:
                score += 1
            
            # Sentences with key phrases
            key_phrases = ['important', 'significant', 'conclude', 'result', 'therefore', 'however', 'main']
            for phrase in key_phrases:
                if phrase.lower() in sentence.lower():
                    score += 1
            
            scored_sentences.append((i, sentence, score))
        
        # Sort by score and take top sentences
        scored_sentences.sort(key=lambda x: x[2], reverse=True)
        top_sentences = scored_sentences[:max_sentences]
        
        # Re-order by original position
        top_sentences.sort(key=lambda x: x[0])
        
        return ' '.join([s[1] for s in top_sentences])
    
    def detect_language(self, text: str) -> str:
        """
        Simple language detection based on common words
        
        Returns:
            Language code (en, es, fr, de, etc.)
        """
        # Sample common words for each language
        lang_indicators = {
            'en': ['the', 'and', 'is', 'are', 'was', 'were', 'have', 'has', 'been', 'will'],
            'es': ['el', 'la', 'de', 'que', 'y', 'en', 'un', 'una', 'es', 'por'],
            'fr': ['le', 'la', 'de', 'et', 'est', 'un', 'une', 'que', 'en', 'les'],
            'de': ['der', 'die', 'und', 'in', 'den', 'von', 'zu', 'das', 'mit', 'ist'],
            'it': ['il', 'di', 'che', 'e', 'la', 'un', 'per', 'non', 'una', 'sono'],
            'pt': ['de', 'que', 'e', 'do', 'da', 'em', 'um', 'para', 'com', 'uma'],
        }
        
        text_lower = text.lower()
        words = set(re.findall(r'\b\w+\b', text_lower))
        
        scores = {}
        for lang, indicators in lang_indicators.items():
            score = sum(1 for word in indicators if word in words)
            scores[lang] = score
        
        if not scores:
            return 'en'
        
        return max(scores, key=scores.get)
    
    def extract_chapters(self, text: str) -> List[Dict]:
        """
        Detect chapter/section boundaries
        
        Returns:
            List of chapters with title and content
        """
        chapters = []
        
        # Common chapter patterns
        patterns = [
            r'^Chapter\s+\d+[:.]\s*(.*)$',
            r'^CHAPTER\s+\d+[:.]\s*(.*)$',
            r'^\d+\.\s+([A-Z][^.]+)$',
            r'^Part\s+\d+[:.]\s*(.*)$',
            r'^Section\s+\d+[:.]\s*(.*)$',
        ]
        
        lines = text.split('\n')
        current_chapter = {'title': 'Introduction', 'content': [], 'start_line': 0}
        
        for i, line in enumerate(lines):
            is_chapter_start = False
            chapter_title = None
            
            for pattern in patterns:
                match = re.match(pattern, line.strip(), re.MULTILINE)
                if match:
                    is_chapter_start = True
                    chapter_title = match.group(1) if match.groups() else line.strip()
                    break
            
            if is_chapter_start:
                # Save previous chapter
                if current_chapter['content']:
                    current_chapter['content'] = '\n'.join(current_chapter['content'])
                    chapters.append(current_chapter)
                
                # Start new chapter
                current_chapter = {
                    'title': chapter_title or f'Chapter {len(chapters) + 1}',
                    'content': [],
                    'start_line': i
                }
            else:
                current_chapter['content'].append(line)
        
        # Add last chapter
        if current_chapter['content']:
            current_chapter['content'] = '\n'.join(current_chapter['content'])
            chapters.append(current_chapter)
        
        return chapters


class ContentAnalyzer:
    """Analyze document content for smart processing"""
    
    def __init__(self):
        self.processor = TextProcessor()
    
    def analyze(self, text: str) -> Dict:
        """
        Analyze text and return metadata
        
        Returns:
            Dict with analysis results
        """
        words = text.split()
        sentences = re.split(r'[.!?]+', text)
        paragraphs = text.split('\n\n')
        
        # Estimate reading time (average 150 WPM for TTS)
        word_count = len(words)
        reading_time_minutes = word_count / 150
        
        # Detect language
        language = self.processor.detect_language(text)
        
        # Extract chapters
        chapters = self.processor.extract_chapters(text)
        
        return {
            'word_count': word_count,
            'sentence_count': len([s for s in sentences if s.strip()]),
            'paragraph_count': len([p for p in paragraphs if p.strip()]),
            'estimated_audio_duration': f"{int(reading_time_minutes)}:{int((reading_time_minutes % 1) * 60):02d}",
            'estimated_minutes': round(reading_time_minutes, 1),
            'language': language,
            'chapter_count': len(chapters),
            'chapters': [{'title': c['title'], 'word_count': len(c['content'].split())} for c in chapters],
            'has_urls': bool(re.search(r'https?://', text)),
            'has_emails': bool(re.search(r'[\w.+-]+@[\w-]+\.[\w.-]+', text)),
            'has_tables': bool(re.search(r'\t.*\t', text)),
        }


# Singleton instances
text_processor = TextProcessor()
content_analyzer = ContentAnalyzer()
