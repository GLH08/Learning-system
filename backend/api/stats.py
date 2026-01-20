"""
学习统计 API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json

from models.database import get_db
from models.exam import Exam, WrongQuestion
from models.question import Question
from models.category import Category
from api.auth import get_current_user

router = APIRouter(prefix="/api/stats", tags=["stats"])


# ============ Schemas ============

class OverviewStats(BaseModel):
    total_questions: int
    total_exams: int
    total_practice_time: int  # 秒
    average_score: float
    overall_accuracy: float
    total_wrong_questions: int
    mastered_wrong_questions: int


class DailyStats(BaseModel):
    date: str
    exam_count: int
    question_count: int
    correct_count: int
    wrong_count: int
    accuracy: float
    average_score: float


class CategoryStats(BaseModel):
    category_id: str
    category_name: str
    total_count: int
    correct_count: int
    wrong_count: int
    accuracy: float


class WeakPoint(BaseModel):
    category_id: str
    category_name: str
    accuracy: float
    wrong_count: int


# ============ API Endpoints ============

@router.get("/overview", response_model=OverviewStats)
def get_overview_stats(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取学习概览统计"""
    
    # 总题目数
    total_questions = db.query(Question).count()
    
    # 总考试数
    total_exams = db.query(Exam).filter(Exam.status == "completed").count()
    
    # 总练习时间
    total_time = db.query(func.sum(Exam.time_used)).filter(
        Exam.status == "completed"
    ).scalar() or 0
    
    # 平均分数
    avg_score_result = db.query(
        func.avg(Exam.score * 100.0 / Exam.total_score)
    ).filter(
        and_(
            Exam.status == "completed",
            Exam.total_score > 0
        )
    ).scalar()
    average_score = round(avg_score_result, 2) if avg_score_result else 0
    
    # 总体正确率
    total_correct = db.query(func.sum(Exam.correct_count)).filter(
        Exam.status == "completed"
    ).scalar() or 0
    total_answered = db.query(func.sum(Exam.total_count)).filter(
        Exam.status == "completed"
    ).scalar() or 0
    overall_accuracy = round((total_correct / total_answered * 100), 2) if total_answered > 0 else 0
    
    # 错题统计
    total_wrong = db.query(WrongQuestion).count()
    mastered_wrong = db.query(WrongQuestion).filter(WrongQuestion.mastered == 1).count()
    
    return {
        "total_questions": total_questions,
        "total_exams": total_exams,
        "total_practice_time": total_time,
        "average_score": average_score,
        "overall_accuracy": overall_accuracy,
        "total_wrong_questions": total_wrong,
        "mastered_wrong_questions": mastered_wrong
    }


@router.get("/daily", response_model=List[DailyStats])
def get_daily_stats(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取每日学习统计"""
    
    # 计算日期范围
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days - 1)
    
    # 查询每日考试数据
    exams = db.query(Exam).filter(
        and_(
            Exam.status == "completed",
            func.date(Exam.submit_time) >= start_date,
            func.date(Exam.submit_time) <= end_date
        )
    ).all()
    
    # 按日期分组统计
    daily_data: Dict[str, Dict] = {}
    
    # 初始化所有日期
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        daily_data[date_str] = {
            "date": date_str,
            "exam_count": 0,
            "question_count": 0,
            "correct_count": 0,
            "wrong_count": 0,
            "total_score": 0,
            "score_sum": 0
        }
        current_date += timedelta(days=1)
    
    # 统计数据
    for exam in exams:
        if not exam.submit_time:
            continue
        
        date_str = exam.submit_time.date().strftime("%Y-%m-%d")
        if date_str in daily_data:
            daily_data[date_str]["exam_count"] += 1
            daily_data[date_str]["question_count"] += exam.total_count
            daily_data[date_str]["correct_count"] += exam.correct_count
            daily_data[date_str]["wrong_count"] += exam.wrong_count
            daily_data[date_str]["total_score"] += exam.total_score
            daily_data[date_str]["score_sum"] += exam.score
    
    # 计算正确率和平均分
    result = []
    for date_str in sorted(daily_data.keys()):
        data = daily_data[date_str]
        accuracy = (data["correct_count"] / data["question_count"] * 100) if data["question_count"] > 0 else 0
        avg_score = (data["score_sum"] / data["total_score"] * 100) if data["total_score"] > 0 else 0
        
        result.append({
            "date": date_str,
            "exam_count": data["exam_count"],
            "question_count": data["question_count"],
            "correct_count": data["correct_count"],
            "wrong_count": data["wrong_count"],
            "accuracy": round(accuracy, 2),
            "average_score": round(avg_score, 2)
        })
    
    return result


@router.get("/category", response_model=List[CategoryStats])
def get_category_stats(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取分类正确率统计"""
    
    # 获取所有已完成的考试
    exams = db.query(Exam).filter(Exam.status == "completed").all()
    
    # 统计每个分类的答题情况
    category_data: Dict[str, Dict] = {}
    
    for exam in exams:
        if not exam.question_ids or not exam.answers:
            continue
        
        question_ids = json.loads(exam.question_ids)
        answers = json.loads(exam.answers)
        
        # 获取题目信息
        questions = db.query(Question).filter(Question.id.in_(question_ids)).all()
        
        for question in questions:
            if not question.category_id:
                continue
            
            category_id = question.category_id
            
            if category_id not in category_data:
                category_data[category_id] = {
                    "total_count": 0,
                    "correct_count": 0,
                    "wrong_count": 0
                }
            
            category_data[category_id]["total_count"] += 1
            
            # 检查答案是否正确
            user_answer = answers.get(question.id, "")
            if user_answer:
                is_correct = check_answer(question, user_answer)
                if is_correct:
                    category_data[category_id]["correct_count"] += 1
                else:
                    category_data[category_id]["wrong_count"] += 1
    
    # 获取分类信息并计算正确率
    result = []
    for category_id, data in category_data.items():
        category = db.query(Category).filter(Category.id == category_id).first()
        if not category:
            continue
        
        accuracy = (data["correct_count"] / data["total_count"] * 100) if data["total_count"] > 0 else 0
        
        result.append({
            "category_id": category_id,
            "category_name": category.name,
            "total_count": data["total_count"],
            "correct_count": data["correct_count"],
            "wrong_count": data["wrong_count"],
            "accuracy": round(accuracy, 2)
        })
    
    # 按正确率排序
    result.sort(key=lambda x: x["accuracy"])
    
    return result


@router.get("/weak-points", response_model=List[WeakPoint])
def get_weak_points(
    limit: int = 5,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取薄弱知识点"""
    
    # 获取分类统计
    category_stats = get_category_stats(db, current_user)
    
    # 筛选正确率低于60%的分类
    weak_points = [
        {
            "category_id": stat["category_id"],
            "category_name": stat["category_name"],
            "accuracy": stat["accuracy"],
            "wrong_count": stat["wrong_count"]
        }
        for stat in category_stats
        if stat["accuracy"] < 60 and stat["total_count"] >= 3  # 至少答过3题
    ]
    
    # 按错误数量排序，取前N个
    weak_points.sort(key=lambda x: x["wrong_count"], reverse=True)
    
    return weak_points[:limit]


def check_answer(question: Question, user_answer: str) -> bool:
    """检查答案是否正确（简化版本）"""
    if not user_answer or not question.answer:
        return False
    
    correct = question.answer.upper().strip()
    user = user_answer.upper().strip()
    
    if question.type == "multiple":
        correct_set = set(correct.replace(",", "").replace(" ", ""))
        user_set = set(user.replace(",", "").replace(" ", ""))
        return correct_set == user_set
    
    return user == correct
