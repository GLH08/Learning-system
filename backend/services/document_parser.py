"""
Document Parser Service for importing questions from various formats
"""
from typing import List, Dict, Any, Optional
import re
import json
from io import BytesIO

from docx import Document
from openpyxl import load_workbook
import logging

logger = logging.getLogger(__name__)


class ParsedQuestion:
    """Parsed question data structure"""
    def __init__(
        self,
        index: int,
        type: str = "unknown",
        content: str = "",
        options: Optional[Dict[str, str]] = None,
        answer: Optional[str] = None,
        explanation: Optional[str] = None,
        difficulty: str = "medium",
        tags: Optional[List[str]] = None,
        source: Optional[str] = None,
        parse_status: str = "success",
        parse_message: Optional[str] = None
    ):
        self.index = index
        self.type = type
        self.content = content
        self.options = options or {}
        self.answer = answer
        self.explanation = explanation
        self.difficulty = difficulty
        self.tags = tags or []
        self.source = source
        self.parse_status = parse_status
        self.parse_message = parse_message
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "type": self.type,
            "content": self.content,
            "options": self.options if self.options else None,
            "answer": self.answer,
            "explanation": self.explanation,
            "difficulty": self.difficulty,
            "tags": self.tags,
            "source": self.source,
            "hasAnswer": bool(self.answer),
            "hasExplanation": bool(self.explanation),
            "parseStatus": self.parse_status,
            "parseMessage": self.parse_message
        }


class DocumentParser:
    """Document parser for various formats"""
    
    def __init__(self):
        # 选项匹配模式：支持 A. A、A． A) A、（A） 等格式
        # Group 1: 选项字母, Group 2: 选项内容
        self.option_pattern = re.compile(r'^[\(（]?([A-Z])[\)）]?[.、．:\s]\s*(.+)$')
        
        # 答案匹配模式：支持多种常见格式
        self.answer_pattern = re.compile(
            r'(?:[\[【\(（]?(?:参考|正确|标准)?答案[\]】\)）]?|Answer)[:：\s]*([A-Z✓×√xTtfF]+|正确|错误|对|错)',
            re.IGNORECASE
        )
        
        # 解析匹配模式
        self.explanation_pattern = re.compile(
            r'(?:[\[【\(（]?(?:答案)?(?:解析|分析|说明|详解)[\]】\)）]?|Explanation)[:：\s]*(.+)',
            re.IGNORECASE
        )
        
        # 题目开头模式：支持各种编号格式
        self.question_start_pattern = re.compile(
            r'^(?:[\(（]?\d+[\)）]?[.、．:\s]|第\d+题[\s:：]?|题目\d+[\s:：]?|Question\s*\d+[.:\s])',
            re.IGNORECASE
        )
        
        # 题型标签模式
        self.type_label_pattern = re.compile(
            r'^[一二三四五六七八九十]+[、.．\s]|^[（(]?[一二三四五六七八九十]+[)）]?$|^(?:单选题|多选题|判断题|简答题|填空题|选择题|问答题)[:：\s]*$',
            re.IGNORECASE
        )
    
    def parse_word(self, file_content: bytes) -> List[ParsedQuestion]:
        """Parse Word document (.docx)"""
        try:
            doc = Document(BytesIO(file_content))
            questions = []
            current_question = None
            question_index = 0
            
            for para in doc.paragraphs:
                text = para.text.strip()
                if not text:
                    continue
                
                # 跳过题型标签行（如 "一、单选题"）
                if self.type_label_pattern.match(text):
                    continue
                
                # 检查是否是新题目开头（支持多种编号格式）
                if self.question_start_pattern.match(text):
                    # 保存上一题
                    if current_question:
                        questions.append(current_question)
                    
                    # 开始新题目，移除编号
                    question_index += 1
                    content = re.sub(r'^(?:[\(（]?\d+[\)）]?[.、．:\s]|第\d+题[\s:：]?|题目\d+[\s:：]?|Question\s*\d+[.:\s])', '', text, flags=re.IGNORECASE).strip()
                    current_question = ParsedQuestion(
                        index=question_index,
                        content=content
                    )
                
                # Check if it's an option
                elif current_question and self.option_pattern.match(text):
                    match = self.option_pattern.match(text)
                    if match:
                        option_key = match.group(1)
                        option_value = match.group(2).strip()
                        current_question.options[option_key] = option_value
                
                # Check if it's an answer
                elif current_question and self.answer_pattern.match(text):
                    match = self.answer_pattern.match(text)
                    if match:
                        current_question.answer = match.group(1).strip()
                
                # Check if it's an explanation
                elif current_question and self.explanation_pattern.match(text):
                    match = self.explanation_pattern.match(text)
                    if match:
                        current_question.explanation = match.group(1).strip()
                
                # Otherwise, append to current question content
                elif current_question and not current_question.options:
                    current_question.content += " " + text
            
            # Save last question
            if current_question:
                questions.append(current_question)
            
            # Determine question types
            for q in questions:
                q.type = self._determine_type(q)
            
            return questions
        
        except Exception as e:
            logger.error(f"Failed to parse Word document: {e}")
            raise Exception(f"Word文档解析失败: {str(e)}")
    
    def parse_excel(self, file_content: bytes) -> List[ParsedQuestion]:
        """Parse Excel document (.xlsx)"""
        try:
            wb = load_workbook(BytesIO(file_content))
            ws = wb.active
            questions = []
            
            # Read header row to determine column mapping
            headers = []
            for cell in ws[1]:
                headers.append(cell.value.lower() if cell.value else "")
            
            # Map columns
            col_map = self._map_excel_columns(headers)
            
            # Read data rows
            for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=1):
                if not any(row):  # Skip empty rows
                    continue
                
                question = ParsedQuestion(index=row_idx)
                
                # Extract data based on column mapping
                if col_map.get('content') is not None:
                    question.content = str(row[col_map['content']]) if row[col_map['content']] else ""
                
                if col_map.get('type') is not None:
                    question.type = self._normalize_type(str(row[col_map['type']])) if row[col_map['type']] else "unknown"
                
                if col_map.get('difficulty') is not None:
                    question.difficulty = self._normalize_difficulty(str(row[col_map['difficulty']])) if row[col_map['difficulty']] else "medium"
                
                # Parse options (A, B, C, D columns or single options column)
                if col_map.get('options') is not None:
                    options_str = str(row[col_map['options']]) if row[col_map['options']] else ""
                    question.options = self._parse_options_string(options_str)
                else:
                    # Try individual option columns
                    for opt_key in ['A', 'B', 'C', 'D', 'E', 'F']:
                        col_key = f'option_{opt_key}'
                        if col_map.get(col_key) is not None:
                            opt_value = str(row[col_map[col_key]]) if row[col_map[col_key]] else ""
                            if opt_value:
                                question.options[opt_key] = opt_value
                
                if col_map.get('answer') is not None:
                    question.answer = str(row[col_map['answer']]) if row[col_map['answer']] else None
                
                if col_map.get('explanation') is not None:
                    question.explanation = str(row[col_map['explanation']]) if row[col_map['explanation']] else None
                
                if col_map.get('source') is not None:
                    question.source = str(row[col_map['source']]) if row[col_map['source']] else None
                
                # Auto-determine type if not specified
                if question.type == "unknown":
                    question.type = self._determine_type(question)
                
                questions.append(question)
            
            return questions
        
        except Exception as e:
            logger.error(f"Failed to parse Excel document: {e}")
            raise Exception(f"Excel文档解析失败: {str(e)}")
    
    def parse_txt(self, file_content: bytes) -> List[ParsedQuestion]:
        """Parse text file (.txt)"""
        try:
            text = file_content.decode('utf-8')
            lines = text.split('\n')
            
            questions = []
            current_question = None
            question_index = 0
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # 跳过题型标签行（如 "一、单选题"）
                if self.type_label_pattern.match(line):
                    continue
                
                # 检查是否是新题目开头（支持多种编号格式）
                if self.question_start_pattern.match(line):
                    # 保存上一题
                    if current_question:
                        questions.append(current_question)
                    
                    # 开始新题目，移除编号
                    question_index += 1
                    content = re.sub(r'^(?:[\(（]?\d+[\)）]?[.、．:\s]|第\d+题[\s:：]?|题目\d+[\s:：]?|Question\s*\d+[.:\s])', '', line, flags=re.IGNORECASE).strip()
                    current_question = ParsedQuestion(
                        index=question_index,
                        content=content
                    )
                
                # Check if it's an option
                elif current_question and self.option_pattern.match(line):
                    match = self.option_pattern.match(line)
                    if match:
                        option_key = match.group(1)
                        option_value = match.group(2).strip()
                        current_question.options[option_key] = option_value
                
                # Check if it's an answer
                elif current_question and self.answer_pattern.match(line):
                    match = self.answer_pattern.match(line)
                    if match:
                        current_question.answer = match.group(1).strip()
                
                # Check if it's an explanation
                elif current_question and self.explanation_pattern.match(line):
                    match = self.explanation_pattern.match(line)
                    if match:
                        current_question.explanation = match.group(1).strip()
                
                # Otherwise, append to current question content
                elif current_question and not current_question.options:
                    current_question.content += " " + line
            
            # Save last question
            if current_question:
                questions.append(current_question)
            
            # Determine question types
            for q in questions:
                q.type = self._determine_type(q)
            
            return questions
        
        except Exception as e:
            logger.error(f"Failed to parse text file: {e}")
            raise Exception(f"文本文件解析失败: {str(e)}")
    
    def _map_excel_columns(self, headers: List[str]) -> Dict[str, int]:
        """Map Excel column headers to field names"""
        col_map = {}
        
        for idx, header in enumerate(headers):
            header_lower = header.lower()
            
            # Content
            if any(k in header_lower for k in ['题目', '内容', 'content', 'question']):
                col_map['content'] = idx
            
            # Type
            elif any(k in header_lower for k in ['题型', 'type', '类型']):
                col_map['type'] = idx
            
            # Difficulty
            elif any(k in header_lower for k in ['难度', 'difficulty', '级别']):
                col_map['difficulty'] = idx
            
            # Options
            elif any(k in header_lower for k in ['选项', 'options']):
                col_map['options'] = idx
            elif header_lower in ['a', '选项a', 'option a']:
                col_map['option_A'] = idx
            elif header_lower in ['b', '选项b', 'option b']:
                col_map['option_B'] = idx
            elif header_lower in ['c', '选项c', 'option c']:
                col_map['option_C'] = idx
            elif header_lower in ['d', '选项d', 'option d']:
                col_map['option_D'] = idx
            elif header_lower in ['e', '选项e', 'option e']:
                col_map['option_E'] = idx
            elif header_lower in ['f', '选项f', 'option f']:
                col_map['option_F'] = idx
            
            # Answer
            elif any(k in header_lower for k in ['答案', 'answer', '正确答案']):
                col_map['answer'] = idx
            
            # Explanation
            elif any(k in header_lower for k in ['解析', 'explanation', '说明']):
                col_map['explanation'] = idx
            
            # Source
            elif any(k in header_lower for k in ['来源', 'source', '出处']):
                col_map['source'] = idx
        
        return col_map
    
    def _parse_options_string(self, options_str: str) -> Dict[str, str]:
        """Parse options from a single string"""
        options = {}
        
        # Try to split by common delimiters
        parts = re.split(r'[;；\n]', options_str)
        
        for part in parts:
            part = part.strip()
            match = self.option_pattern.match(part)
            if match:
                option_key = match.group(1)
                option_value = match.group(2).strip()
                options[option_key] = option_value
        
        return options
    
    def _determine_type(self, question: ParsedQuestion) -> str:
        """Determine question type based on content and options"""
        # If has options
        if question.options:
            option_count = len(question.options)
            
            # Check if it's a judge question
            if option_count == 2:
                values = [v.lower() for v in question.options.values()]
                if any(k in ' '.join(values) for k in ['正确', '错误', '对', '错', 'true', 'false', '是', '否']):
                    return 'judge'
            
            # Check answer to determine single or multiple
            if question.answer:
                answer_clean = re.sub(r'[^A-Z]', '', question.answer.upper())
                if len(answer_clean) > 1:
                    return 'multiple'
                else:
                    return 'single'
            
            # Default to single choice
            return 'single'
        
        # No options, likely essay
        return 'essay'
    
    def _normalize_type(self, type_str: str) -> str:
        """Normalize question type string"""
        type_lower = type_str.lower()
        
        if any(k in type_lower for k in ['单选', 'single', '单项']):
            return 'single'
        elif any(k in type_lower for k in ['多选', 'multiple', '多项']):
            return 'multiple'
        elif any(k in type_lower for k in ['判断', 'judge', 'true/false', 'tf']):
            return 'judge'
        elif any(k in type_lower for k in ['简答', 'essay', '问答', '简述']):
            return 'essay'
        
        return 'unknown'
    
    def _normalize_difficulty(self, diff_str: str) -> str:
        """Normalize difficulty string"""
        diff_lower = diff_str.lower()
        
        if any(k in diff_lower for k in ['简单', 'easy', '容易', '低']):
            return 'easy'
        elif any(k in diff_lower for k in ['困难', 'hard', '难', '高']):
            return 'hard'
        else:
            return 'medium'


def get_document_parser() -> DocumentParser:
    """Get document parser instance"""
    return DocumentParser()
