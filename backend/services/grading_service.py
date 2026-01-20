"""
评分服务 - 自动评分算法
"""
import json
from typing import Dict, List, Tuple
from sqlalchemy.orm import Session
from datetime import datetime

from models.question import Question
from models.exam import Exam, WrongQuestion


class GradingService:
    """评分服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def grade_exam(self, exam: Exam, answers: Dict[str, str]) -> Dict:
        """
        评分考试
        
        Args:
            exam: 考试记录
            answers: 用户答案 {questionId: answer}
        
        Returns:
            Dict: 评分结果
        """
        question_ids = json.loads(exam.question_ids)
        questions = self.db.query(Question).filter(Question.id.in_(question_ids)).all()
        question_map = {q.id: q for q in questions}
        
        correct_count = 0
        wrong_count = 0
        results = {}
        wrong_questions = []
        
        for qid in question_ids:
            if qid not in question_map:
                continue
            
            question = question_map[qid]
            user_answer = answers.get(qid, "")
            
            # 评分
            is_correct = self._check_answer(question, user_answer)
            
            results[qid] = {
                "correct": is_correct,
                "user_answer": user_answer,
                "correct_answer": question.answer
            }
            
            if is_correct:
                correct_count += 1
            else:
                wrong_count += 1
                # 记录错题
                wrong_questions.append({
                    "question_id": qid,
                    "user_answer": user_answer,
                    "correct_answer": question.answer
                })
        
        # 计算分数（每题1分）
        score = correct_count
        
        # 更新考试记录
        exam.answers = json.dumps(answers, ensure_ascii=False)
        exam.status = "completed"
        exam.score = score
        exam.correct_count = correct_count
        exam.wrong_count = wrong_count
        exam.submit_time = datetime.now()
        
        # 计算用时
        if exam.start_time:
            time_used = int((exam.submit_time - exam.start_time).total_seconds())
            exam.time_used = time_used
        
        self.db.commit()
        
        # 保存错题
        self._save_wrong_questions(exam.id, wrong_questions)
        
        return {
            "score": score,
            "total_score": exam.total_score,
            "correct_count": correct_count,
            "wrong_count": wrong_count,
            "results": results
        }
    
    def _check_answer(self, question: Question, user_answer: str) -> bool:
        """
        检查答案是否正确
        
        Args:
            question: 题目
            user_answer: 用户答案
        
        Returns:
            bool: 是否正确
        """
        if not user_answer or not question.answer:
            return False
        
        # 标准化答案
        correct = self._normalize_answer(question.answer)
        user = self._normalize_answer(user_answer)
        
        if question.type == "single":
            # 单选题：完全匹配
            return user == correct
        
        elif question.type == "multiple":
            # 多选题：完全匹配（顺序无关）
            correct_set = set(correct.replace(",", "").replace(" ", ""))
            user_set = set(user.replace(",", "").replace(" ", ""))
            return correct_set == user_set
        
        elif question.type == "judge":
            # 判断题：完全匹配
            return user == correct
        
        elif question.type == "essay":
            # 简述题：暂不自动评分
            return False
        
        return False
    
    def _normalize_answer(self, answer: str) -> str:
        """
        标准化答案
        
        Args:
            answer: 原始答案
        
        Returns:
            str: 标准化后的答案
        """
        if not answer:
            return ""
        
        # 转大写
        answer = answer.upper().strip()
        
        # 处理判断题的多种表达
        if answer in ["TRUE", "T", "正确", "对", "是", "√", "✓"]:
            return "TRUE"
        if answer in ["FALSE", "F", "错误", "错", "否", "×", "✗"]:
            return "FALSE"
        
        return answer
    
    def _save_wrong_questions(self, exam_id: str, wrong_questions: List[Dict]):
        """
        保存错题记录
        
        Args:
            exam_id: 考试ID
            wrong_questions: 错题列表
        """
        for wq in wrong_questions:
            # 检查是否已存在错题记录
            existing = self.db.query(WrongQuestion).filter(
                WrongQuestion.question_id == wq["question_id"]
            ).first()
            
            if existing:
                # 更新错误次数
                existing.wrong_count += 1
                existing.last_wrong_time = datetime.now()
                existing.user_answer = wq["user_answer"]
            else:
                # 创建新记录
                wrong_question = WrongQuestion(
                    question_id=wq["question_id"],
                    exam_id=exam_id,
                    user_answer=wq["user_answer"],
                    correct_answer=wq["correct_answer"],
                    wrong_count=1
                )
                self.db.add(wrong_question)
        
        self.db.commit()
