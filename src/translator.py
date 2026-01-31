"""
Language Translation Module
Supports 50+ languages with auto-detection
"""

import logging
from typing import Optional, Tuple, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Try to import translation libraries
try:
    from googletrans import Translator as GoogleTranslator, LANGUAGES
    GOOGLETRANS_AVAILABLE = True
except ImportError:
    GOOGLETRANS_AVAILABLE = False
    logger.warning("googletrans not available - translation disabled")

@dataclass
class TranslationResult:
    """Translation result with metadata"""
    text: str
    source_lang: str
    target_lang: str
    confidence: float = 0.0
    char_count: int = 0

class Translator:
    """Handle text translation with caching"""
    
    def __init__(self):
        self.available = GOOGLETRANS_AVAILABLE
        if self.available:
            self.translator = GoogleTranslator()
        
        # Popular languages
        self.popular_languages = {
            'en': 'English',
            'es': 'Spanish',
            'fr': 'French',
            'de': 'German',
            'it': 'Italian',
            'pt': 'Portuguese',
            'ru': 'Russian',
            'ja': 'Japanese',
            'ko': 'Korean',
            'zh-cn': 'Chinese (Simplified)',
            'zh-tw': 'Chinese (Traditional)',
            'ar': 'Arabic',
            'hi': 'Hindi',
            'bn': 'Bengali',
            'te': 'Telugu',
            'mr': 'Marathi',
            'ta': 'Tamil',
            'ur': 'Urdu',
            'gu': 'Gujarati',
            'kn': 'Kannada',
            'ml': 'Malayalam',
            'pa': 'Punjabi',
            'or': 'Odia',
            'as': 'Assamese',
            'mai': 'Maithili',
            'sd': 'Sindhi',
            'ne': 'Nepali',
            'sa': 'Sanskrit',
            'ks': 'Kashmiri',
            'hi': 'Hindi',
            'bn': 'Bengali',
            'ur': 'Urdu',
            'tr': 'Turkish',
            'nl': 'Dutch',
            'pl': 'Polish',
            'sv': 'Swedish',
            'da': 'Danish',
            'no': 'Norwegian',
            'fi': 'Finnish',
        }
    
    def get_available_languages(self) -> dict:
        """Get all available languages"""
        if not self.available:
            return {}
        return LANGUAGES
    
    def get_popular_languages(self) -> dict:
        """Get popular languages for quick selection"""
        return self.popular_languages
    
    def detect_language(self, text: str) -> Tuple[str, float]:
        """
        Detect language of text
        
        Returns:
            Tuple of (language_code, confidence)
        """
        if not self.available:
            return ('en', 0.0)
        
        try:
            # Take sample for detection (first 1000 chars)
            sample = text[:1000] if len(text) > 1000 else text
            detection = self.translator.detect(sample)
            return (detection.lang, detection.confidence)
        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            return ('en', 0.0)
    
    def translate(
        self,
        text: str,
        target_lang: str = 'en',
        source_lang: str = 'auto',
        chunk_size: int = 2000  # Smaller chunks for better reliability
    ) -> TranslationResult:
        """
        Translate text to target language
        
        Args:
            text: Text to translate
            target_lang: Target language code (e.g., 'en', 'es', 'fr')
            source_lang: Source language ('auto' for auto-detection)
            chunk_size: Characters per chunk (Google Translate has limits)
        
        Returns:
            TranslationResult with translated text
        """
        if not self.available:
            raise RuntimeError("Translation not available - install googletrans==4.0.0-rc1")
        
        if not text or not text.strip():
            return TranslationResult(
                text="",
                source_lang=source_lang,
                target_lang=target_lang,
                confidence=0.0,
                char_count=0
            )
        
        try:
            # Split into chunks if text is large
            if len(text) <= chunk_size:
                result = self._translate_chunk(text, target_lang, source_lang)
            else:
                result = self._translate_large_text(text, target_lang, source_lang, chunk_size)
            
            return result
            
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            raise RuntimeError(f"Translation failed: {e}")
    
    def _translate_chunk(self, text: str, target_lang: str, source_lang: str, max_retries: int = 3) -> TranslationResult:
        """Translate a single chunk of text with retry logic"""
        import time
        
        for attempt in range(max_retries):
            try:
                # Reinitialize translator on retry to get fresh connection
                if attempt > 0:
                    self.translator = GoogleTranslator()
                    time.sleep(1)  # Brief pause between retries
                
                translation = self.translator.translate(
                    text,
                    dest=target_lang,
                    src=source_lang
                )
                
                return TranslationResult(
                    text=translation.text,
                    source_lang=translation.src,
                    target_lang=translation.dest,
                    confidence=getattr(translation.extra_data, 'confidence', 0.0),
                    char_count=len(translation.text)
                )
            except Exception as e:
                logger.warning(f"Translation attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    raise
        
        # Should not reach here, but just in case
        raise RuntimeError("Translation failed after all retries")
    
    def _translate_large_text(
        self,
        text: str,
        target_lang: str,
        source_lang: str,
        chunk_size: int
    ) -> TranslationResult:
        """Translate large text by splitting into chunks"""
        # Split by paragraphs first
        paragraphs = text.split('\n\n')
        translated_paragraphs = []
        detected_lang = source_lang
        total_confidence = 0.0
        chunk_count = 0
        
        current_chunk = []
        current_size = 0
        
        for para in paragraphs:
            para_size = len(para)
            
            # If single paragraph is too large, split by sentences
            if para_size > chunk_size:
                if current_chunk:
                    chunk_text = '\n\n'.join(current_chunk)
                    result = self._translate_chunk(chunk_text, target_lang, source_lang)
                    translated_paragraphs.append(result.text)
                    if chunk_count == 0:
                        detected_lang = result.source_lang
                    total_confidence += result.confidence
                    chunk_count += 1
                    current_chunk = []
                    current_size = 0
                
                # Split large paragraph by sentences
                sentences = para.split('. ')
                for i, sent in enumerate(sentences):
                    if i < len(sentences) - 1:
                        sent += '. '
                    result = self._translate_chunk(sent, target_lang, source_lang)
                    translated_paragraphs.append(result.text)
                    if chunk_count == 0:
                        detected_lang = result.source_lang
                    total_confidence += result.confidence
                    chunk_count += 1
            
            # Add paragraph to current chunk
            elif current_size + para_size > chunk_size:
                # Translate current chunk
                chunk_text = '\n\n'.join(current_chunk)
                result = self._translate_chunk(chunk_text, target_lang, source_lang)
                translated_paragraphs.append(result.text)
                if chunk_count == 0:
                    detected_lang = result.source_lang
                total_confidence += result.confidence
                chunk_count += 1
                
                # Start new chunk
                current_chunk = [para]
                current_size = para_size
            else:
                current_chunk.append(para)
                current_size += para_size
        
        # Translate remaining chunk
        if current_chunk:
            chunk_text = '\n\n'.join(current_chunk)
            result = self._translate_chunk(chunk_text, target_lang, source_lang)
            translated_paragraphs.append(result.text)
            if chunk_count == 0:
                detected_lang = result.source_lang
            total_confidence += result.confidence
            chunk_count += 1
        
        # Combine all translated paragraphs
        full_translation = '\n\n'.join(translated_paragraphs)
        avg_confidence = total_confidence / chunk_count if chunk_count > 0 else 0.0
        
        return TranslationResult(
            text=full_translation,
            source_lang=detected_lang,
            target_lang=target_lang,
            confidence=avg_confidence,
            char_count=len(full_translation)
        )

# Global instance
translator = Translator()
