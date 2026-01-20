"""
AI Service for question completion and analysis
"""
from openai import OpenAI, AsyncOpenAI
from typing import Optional, Dict, Any
import json
import logging

from models.question import Question
from models.setting import Setting
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class AIConfig:
    """AI Configuration"""
    def __init__(
        self,
        api_url: str = "https://api.openai.com/v1",
        api_key: str = "",
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: int = 8192  # 单次输出 token 限制
    ):
        self.api_url = api_url
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
    
    @classmethod
    def from_db(cls, db: Session) -> "AIConfig":
        """Load configuration from database"""
        settings = {
            s.key: s.value 
            for s in db.query(Setting).filter(
                Setting.key.in_([
                    'ai_api_url', 'ai_api_key', 'ai_model',
                    'ai_temperature', 'ai_max_tokens'
                ])
            ).all()
        }
        
        return cls(
            api_url=settings.get('ai_api_url', 'https://api.openai.com/v1'),
            api_key=settings.get('ai_api_key', ''),
            model=settings.get('ai_model', 'gpt-4o-mini'),
            temperature=float(settings.get('ai_temperature', '0.7')),
            max_tokens=int(settings.get('ai_max_tokens', '8192'))
        )


class AIService:
    """AI Service for question completion"""
    
    def __init__(self, config: AIConfig):
        self.config = config
        if not config.api_key:
            raise ValueError("AI API key is not configured")
        
        self.client = AsyncOpenAI(
            api_key=config.api_key,
            base_url=config.api_url
        )
        self.sync_client = OpenAI(
            api_key=config.api_key,
            base_url=config.api_url
        )
    
    def test_connection(self) -> bool:
        """Test AI API connection"""
        try:
            response = self.sync_client.chat.completions.create(
                model=self.config.model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
            return True
        except Exception as e:
            logger.error(f"AI connection test failed: {e}")
            return False
    
    async def generate_answer(self, question: Question) -> str:
        """Generate answer for a question"""
        prompt = self._build_answer_prompt(question)
        
        try:
            response = await self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个专业的题目答案生成助手。请根据题目内容和选项，给出准确的答案。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )
            
            answer = response.choices[0].message.content.strip()
            return self._extract_answer(answer, question.type)
        
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to generate answer: {e}")
            
            # Map specific errors to HTTP status codes
            if "429" in error_msg or "Resource has been exhausted" in error_msg:
                return Response(code=429, message="AI服务繁忙(429), 请稍后重试", data=None)
            if "404" in error_msg or "not found" in error_msg.lower():
                 return Response(code=404, message="AI模型配置错误(404)", data=None)
                 
            raise ParameterError(f"AI生成答案失败: {error_msg}")
    
    async def generate_explanation(self, question: Question, answer: Optional[str] = None) -> str:
        """Generate explanation for a question"""
        prompt = self._build_explanation_prompt(question, answer)
        
        try:
            response = await self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个专业的题目解析生成助手。请提供简洁、清晰的解析。要求：1. 直接给出核心解释，不要使用Markdown格式；2. 控制在200字以内；3. 使用纯文本，可以换行但不要用特殊符号。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )
            
            explanation = response.choices[0].message.content.strip()
            return explanation
        
        except Exception as e:
            logger.error(f"Failed to generate explanation: {e}")
            raise Exception(f"AI生成解析失败: {str(e)}")
    
    async def generate_both(self, question: Question) -> Dict[str, str]:
        """Generate both answer and explanation"""
        answer = await self.generate_answer(question)
        explanation = await self.generate_explanation(question, answer)
        
        return {
            "answer": answer,
            "explanation": explanation
        }
    
    async def generate_report(self, exam_data: Dict[str, Any]) -> str:
        """Generate learning analysis report"""
        prompt = self._build_report_prompt(exam_data)
        
        try:
            response = await self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个专业的学习分析助手。请根据考试结果，生成详细的学习分析报告，包括错题分析、薄弱知识点和学习建议。使用Markdown格式。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens  # Use configured limit directly
            )
            
            report = response.choices[0].message.content.strip()
            return report
        
        except Exception as e:
            logger.error(f"Failed to generate report: {e}")
            raise Exception(f"AI生成报告失败: {str(e)}")
    
    def _build_answer_prompt(self, question: Question) -> str:
        """Build prompt for answer generation"""
        type_map = {
            'single': '单选题',
            'multiple': '多选题',
            'judge': '判断题',
            'essay': '简述题'
        }
        
        prompt = f"题型：{type_map.get(question.type, question.type)}\n"
        prompt += f"题目：{question.content}\n"
        
        if question.options:
            options = json.loads(question.options) if isinstance(question.options, str) else question.options
            prompt += "选项：\n"
            for key, value in options.items():
                prompt += f"{key}. {value}\n"
        
        if question.type == 'single':
            prompt += "\n请直接给出正确答案的选项字母（如：A）"
        elif question.type == 'multiple':
            prompt += "\n请直接给出所有正确答案的选项字母（如：ACD）"
        elif question.type == 'judge':
            prompt += "\n请直接回答：正确 或 错误"
        else:  # essay
            prompt += "\n请给出简洁的答案要点"
        
        return prompt
    
    def _build_explanation_prompt(self, question: Question, answer: Optional[str] = None) -> str:
        """Build prompt for explanation generation"""
        type_map = {
            'single': '单选题',
            'multiple': '多选题',
            'judge': '判断题',
            'essay': '简述题'
        }
        
        prompt = f"题型：{type_map.get(question.type, question.type)}\n"
        prompt += f"题目：{question.content}\n"
        
        if question.options:
            options = json.loads(question.options) if isinstance(question.options, str) else question.options
            prompt += "选项：\n"
            for key, value in options.items():
                prompt += f"{key}. {value}\n"
        
        if answer:
            prompt += f"\n正确答案：{answer}\n"
        elif question.answer:
            prompt += f"\n正确答案：{question.answer}\n"
        
        prompt += "\n请提供详细的解析，说明为什么这是正确答案，以及相关的知识点。"
        
        return prompt
    
    def _build_report_prompt(self, exam_data: Dict[str, Any]) -> str:
        """Build prompt for report generation"""
        prompt = "# 考试结果分析\n\n"
        prompt += f"总分：{exam_data.get('score', 0)}/{exam_data.get('total_score', 0)}\n"
        prompt += f"正确数：{exam_data.get('correct_count', 0)}\n"
        prompt += f"错误数：{exam_data.get('wrong_count', 0)}\n"
        prompt += f"正确率：{exam_data.get('correct_rate', 0):.1%}\n\n"
        
        if exam_data.get('wrong_questions'):
            prompt += "## 错题列表\n\n"
            for i, q in enumerate(exam_data['wrong_questions'][:10], 1):  # Limit to 10
                prompt += f"{i}. {q.get('content', '')[:50]}...\n"
                prompt += f"   知识点：{', '.join(q.get('tags', []))}\n\n"
        
        prompt += "\n请生成一份学习分析报告，包括：\n"
        prompt += "1. 总体评价\n"
        prompt += "2. 错题知识点统计\n"
        prompt += "3. 薄弱知识点分析\n"
        prompt += "4. 学习建议\n"
        prompt += "\n使用Markdown格式，要专业、详细、有针对性。"
        
        return prompt
    
    def _extract_answer(self, raw_answer: str, question_type: str) -> str:
        """Extract clean answer from AI response"""
        # Remove common prefixes
        answer = raw_answer.replace("答案：", "").replace("答案:", "")
        answer = answer.replace("正确答案：", "").replace("正确答案:", "")
        answer = answer.strip()
        
        # For single/multiple choice, extract only letters
        if question_type in ['single', 'multiple']:
            import re
            letters = re.findall(r'[A-Z]', answer)
            if letters:
                answer = ''.join(letters)
        
        # For judge questions, normalize
        elif question_type == 'judge':
            if '正确' in answer or '对' in answer or 'True' in answer.upper():
                answer = '正确'
            elif '错误' in answer or '错' in answer or 'False' in answer.upper():
                answer = '错误'
        
        return answer


def get_ai_service(db: Session) -> AIService:
    """Get AI service instance"""
    config = AIConfig.from_db(db)
    return AIService(config)
