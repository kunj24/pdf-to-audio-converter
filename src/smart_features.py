"""
Smart Features Module
Auto-summarize, chapter detection, key points extraction
"""

import re
import logging
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from collections import Counter

logger = logging.getLogger(__name__)

@dataclass
class Chapter:
    """Represents a chapter or section"""
    title: str
    start_position: int
    end_position: int
    content: str
    level: int = 1  # Heading level (1=main, 2=sub, etc.)

@dataclass
class KeyPoint:
    """Represents an extracted key point"""
    text: str
    importance: float
    category: str = "general"  # general, definition, instruction, etc.

@dataclass
class QAPair:
    """Represents a question-answer pair"""
    question: str
    answer: str
    confidence: float = 0.0

class SmartFeatures:
    """Smart text analysis and processing features"""
    
    def __init__(self):
        # Patterns for chapter detection
        self.chapter_patterns = [
            re.compile(r'^Chapter\s+\d+[:\s\-]', re.IGNORECASE | re.MULTILINE),
            re.compile(r'^CHAPTER\s+[IVXLCDM]+[:\s\-]', re.MULTILINE),
            re.compile(r'^Section\s+\d+[:\s\-]', re.IGNORECASE | re.MULTILINE),
            re.compile(r'^Part\s+\d+[:\s\-]', re.IGNORECASE | re.MULTILINE),
            re.compile(r'^\d+\.\s+[A-Z][a-z]+', re.MULTILINE),
            re.compile(r'^[A-Z][A-Z\s]{3,}$', re.MULTILINE),  # ALL CAPS titles
        ]
        
        # Keywords that indicate importance
        self.importance_keywords = {
            'high': ['important', 'critical', 'essential', 'key', 'must', 'required', 'significant'],
            'medium': ['should', 'recommend', 'suggest', 'consider', 'note', 'remember'],
            'definitions': ['is defined as', 'refers to', 'means', 'is called', 'is known as'],
        }
        
        # Sentence patterns that indicate key points
        self.keypoint_patterns = [
            re.compile(r'(The main|The key|The primary|The most important)\s+\w+\s+(is|are)', re.IGNORECASE),
            re.compile(r'In (conclusion|summary)', re.IGNORECASE),
            re.compile(r'(It is important|It is essential|It is critical) to', re.IGNORECASE),
            re.compile(r'\b(Remember|Note|Keep in mind) that', re.IGNORECASE),
        ]
        
        # Question patterns
        self.question_patterns = [
            re.compile(r'^[Qq]\d*[\.:)]\s*(.+\?)'),  # Q1: Question?
            re.compile(r'^Question\s*\d*[:\.]?\s*(.+\?)', re.IGNORECASE),
            re.compile(r'^(What|When|Where|Who|Why|How|Which|Can|Could|Would|Should|Is|Are|Do|Does|Did)\s+.+\?', re.MULTILINE),
            re.compile(r'.+\?$', re.MULTILINE),  # Any sentence ending with ?
        ]
        
        # Answer patterns
        self.answer_patterns = [
            re.compile(r'^[Aa]\d*[\.:)]\s*(.+)', re.MULTILINE),  # A1: Answer
            re.compile(r'^Answer\s*\d*[:\.]?\s*(.+)', re.IGNORECASE | re.MULTILINE),
        ]
    
    def detect_chapters(self, text: str, min_chapter_length: int = 500) -> List[Chapter]:
        """
        Detect chapters/sections in text
        
        Args:
            text: Input text
            min_chapter_length: Minimum length for a chapter
        
        Returns:
            List of detected chapters
        """
        chapters = []
        lines = text.split('\n')
        
        # Find potential chapter headings
        potential_headings = []
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            if not line_stripped:
                continue
            
            # Check against chapter patterns
            for pattern in self.chapter_patterns:
                if pattern.match(line_stripped):
                    potential_headings.append({
                        'line_num': i,
                        'title': line_stripped,
                        'position': text.find(line)
                    })
                    break
        
        # If no chapters found, try to split by major paragraph breaks
        if not potential_headings:
            paragraphs = text.split('\n\n')
            if len(paragraphs) > 3:
                pos = 0
                for i, para in enumerate(paragraphs):
                    if len(para) > min_chapter_length:
                        first_line = para.split('\n')[0][:50]
                        chapters.append(Chapter(
                            title=f"Section {i+1}: {first_line}...",
                            start_position=pos,
                            end_position=pos + len(para),
                            content=para,
                            level=1
                        ))
                    pos += len(para) + 2
            else:
                # Single chapter - entire document
                chapters.append(Chapter(
                    title="Full Document",
                    start_position=0,
                    end_position=len(text),
                    content=text,
                    level=1
                ))
            return chapters
        
        # Create chapters from headings
        for i, heading in enumerate(potential_headings):
            start_pos = heading['position']
            
            # End position is start of next chapter or end of text
            if i < len(potential_headings) - 1:
                end_pos = potential_headings[i + 1]['position']
            else:
                end_pos = len(text)
            
            content = text[start_pos:end_pos].strip()
            
            if len(content) >= min_chapter_length:
                chapters.append(Chapter(
                    title=heading['title'],
                    start_position=start_pos,
                    end_position=end_pos,
                    content=content,
                    level=1
                ))
        
        return chapters if chapters else [Chapter(
            title="Full Document",
            start_position=0,
            end_position=len(text),
            content=text,
            level=1
        )]
    
    def extract_key_points(
        self,
        text: str,
        max_points: int = 10,
        min_importance: float = 0.5
    ) -> List[KeyPoint]:
        """
        Extract key points from text
        
        Args:
            text: Input text
            max_points: Maximum number of key points
            min_importance: Minimum importance score (0-1)
        
        Returns:
            List of key points sorted by importance
        """
        sentences = self._split_into_sentences(text)
        scored_sentences = []
        
        for sentence in sentences:
            score = self._calculate_importance(sentence)
            category = self._categorize_sentence(sentence)
            
            if score >= min_importance and len(sentence.split()) >= 5:
                scored_sentences.append(KeyPoint(
                    text=sentence.strip(),
                    importance=score,
                    category=category
                ))
        
        # Sort by importance
        scored_sentences.sort(key=lambda x: x.importance, reverse=True)
        
        # Return top points
        return scored_sentences[:max_points]
    
    def summarize(
        self,
        text: str,
        ratio: float = 0.2,
        max_sentences: int = 5
    ) -> str:
        """
        Create summary of text
        
        Args:
            text: Input text
            ratio: Ratio of original length (0.1 = 10%)
            max_sentences: Maximum sentences in summary
        
        Returns:
            Summarized text
        """
        sentences = self._split_into_sentences(text)
        
        if len(sentences) <= max_sentences:
            return text
        
        # Score sentences
        scored = []
        for i, sentence in enumerate(sentences):
            score = self._calculate_importance(sentence)
            # Boost score for sentences at beginning and end
            if i < 3:
                score *= 1.2
            elif i >= len(sentences) - 3:
                score *= 1.1
            scored.append((sentence, score, i))
        
        # Sort by score
        scored.sort(key=lambda x: x[1], reverse=True)
        
        # Take top sentences based on ratio or max_sentences
        target_count = min(
            max_sentences,
            max(3, int(len(sentences) * ratio))
        )
        
        top_sentences = scored[:target_count]
        
        # Sort by original position to maintain flow
        top_sentences.sort(key=lambda x: x[2])
        
        # Combine sentences
        summary = ' '.join(sent[0] for sent in top_sentences)
        
        return summary
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitter
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _calculate_importance(self, sentence: str) -> float:
        """Calculate importance score for a sentence"""
        score = 0.0
        sentence_lower = sentence.lower()
        
        # Check for importance keywords
        for level, keywords in self.importance_keywords.items():
            for keyword in keywords:
                if keyword in sentence_lower:
                    if level == 'high':
                        score += 0.3
                    elif level == 'medium':
                        score += 0.2
                    elif level == 'definitions':
                        score += 0.25
        
        # Check for key point patterns
        for pattern in self.keypoint_patterns:
            if pattern.search(sentence):
                score += 0.25
        
        # Length factor (prefer medium-length sentences)
        words = len(sentence.split())
        if 10 <= words <= 30:
            score += 0.1
        elif words < 5:
            score -= 0.2
        
        # Has numbers or data
        if re.search(r'\d+', sentence):
            score += 0.1
        
        # Has quotes
        if '"' in sentence or "'" in sentence:
            score += 0.05
        
        # Title case words (proper nouns, important terms)
        title_case_words = len([w for w in sentence.split() if w[0].isupper() and len(w) > 1])
        score += min(0.15, title_case_words * 0.03)
        
        return min(1.0, max(0.0, score))
    
    def _categorize_sentence(self, sentence: str) -> str:
        """Categorize a sentence"""
        sentence_lower = sentence.lower()
        
        if any(word in sentence_lower for word in ['is defined as', 'refers to', 'means']):
            return 'definition'
        elif any(word in sentence_lower for word in ['must', 'should', 'required']):
            return 'instruction'
        elif any(word in sentence_lower for word in ['important', 'critical', 'essential']):
            return 'important'
        elif any(word in sentence_lower for word in ['example', 'for instance', 'such as']):
            return 'example'
        else:
            return 'general'

    def extract_qa_pairs(self, text: str) -> List[QAPair]:
        """
        Extract question-answer pairs from text
        
        Args:
            text: Input text
        
        Returns:
            List of Q&A pairs
        """
        qa_pairs = []
        lines = text.split('\n')
        
        # Method 1: Find explicit Q: A: format
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Check if line is a question
            question_match = None
            for pattern in self.question_patterns[:2]:  # Only Q1: and Question: patterns
                match = pattern.match(line)
                if match:
                    question_match = match
                    break
            
            if question_match:
                question_text = question_match.group(1) if question_match.lastindex else line
                
                # Look for answer in next few lines
                answer_text = ""
                j = i + 1
                while j < len(lines) and j < i + 5:
                    next_line = lines[j].strip()
                    if not next_line:
                        j += 1
                        continue
                    
                    # Check if it's an explicit answer
                    answer_match = None
                    for pattern in self.answer_patterns:
                        match = pattern.match(next_line)
                        if match:
                            answer_match = match
                            break
                    
                    if answer_match:
                        answer_text = answer_match.group(1) if answer_match.lastindex else next_line
                        break
                    elif not any(p.match(next_line) for p in self.question_patterns[:2]):
                        # If not a new question, consider it an answer
                        answer_text = next_line
                        break
                    else:
                        break
                    j += 1
                
                if answer_text:
                    qa_pairs.append(QAPair(
                        question=question_text,
                        answer=answer_text,
                        confidence=0.9
                    ))
                    i = j + 1
                    continue
            
            i += 1
        
        # Method 2: Find standalone questions and nearby context as answers
        if len(qa_pairs) < 3:
            paragraphs = text.split('\n\n')
            for para in paragraphs:
                sentences = self._split_into_sentences(para)
                
                for i, sentence in enumerate(sentences):
                    # Check if sentence is a question
                    if sentence.strip().endswith('?'):
                        # Check if it matches question patterns
                        is_question = False
                        for pattern in self.question_patterns[2:]:  # What/When/Where patterns
                            if pattern.match(sentence):
                                is_question = True
                                break
                        
                        if is_question:
                            # Take next 1-3 sentences as answer
                            answer_sentences = sentences[i+1:min(i+4, len(sentences))]
                            if answer_sentences:
                                answer_text = ' '.join(answer_sentences)
                                qa_pairs.append(QAPair(
                                    question=sentence.strip(),
                                    answer=answer_text.strip(),
                                    confidence=0.7
                                ))
        
        return qa_pairs

# Global instance
smart_features = SmartFeatures()
