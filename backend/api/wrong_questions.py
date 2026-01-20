"""
错题本 API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from models.database import get_db
from models.exam import WrongQuestion
from models.question import Question
from api.auth import get_current_user

router = APIRouter(prefix="/api/wrong-questions", tags=["wrong-questions"])


# ============ Schemas ============

class WrongQuestionResponse(BaseModel):
    id: str
    question_id: str
    exam_id: str
    user_answer: Optional[str]
    correct_answer: Optional[str]
    wrong_count: int
    mastered: int
    last_wrong_time: datetime
    created_at: datetime
    
    # 关联的题目信息
    question: Optional[dict] = None
    
    class Config:
        from_attributes = True


# ============ API Endpoints ============

@router.get("", response_model=List[WrongQuestionResponse])
def list_wrong_questions(
    mastered: Optional[int] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取错题列表"""
    query = db.query(WrongQuestion)
    
    if mastered is not None:
        query = query.filter(WrongQuestion.mastered == mastered)
    
    wrong_questions = query.order_by(
        WrongQuestion.last_wrong_time.desc()
    ).offset(skip).limit(limit).all()
    
    # 加载题目信息
    result = []
    for wq in wrong_questions:
        question = db.query(Question).filter(Question.id == wq.question_id).first()
        wq_dict = {
            "id": wq.id,
            "question_id": wq.question_id,
            "exam_id": wq.exam_id,
            "user_answer": wq.user_answer,
            "correct_answer": wq.correct_answer,
            "wrong_count": wq.wrong_count,
            "mastered": wq.mastered,
            "last_wrong_time": wq.last_wrong_time,
            "created_at": wq.created_at,
            "question": {
                "id": question.id,
                "type": question.type,
                "difficulty": question.difficulty,
                "content": question.content,
                "options": question.options,
                "answer": question.answer,
                "explanation": question.explanation
            } if question else None
        }
        result.append(wq_dict)
    
    return result


@router.get("/{wrong_question_id}", response_model=WrongQuestionResponse)
def get_wrong_question(
    wrong_question_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取错题详情"""
    wq = db.query(WrongQuestion).filter(WrongQuestion.id == wrong_question_id).first()
    if not wq:
        raise HTTPException(status_code=404, detail="错题不存在")
    
    # 加载题目信息
    question = db.query(Question).filter(Question.id == wq.question_id).first()
    
    return {
        "id": wq.id,
        "question_id": wq.question_id,
        "exam_id": wq.exam_id,
        "user_answer": wq.user_answer,
        "correct_answer": wq.correct_answer,
        "wrong_count": wq.wrong_count,
        "mastered": wq.mastered,
        "last_wrong_time": wq.last_wrong_time,
        "created_at": wq.created_at,
        "question": {
            "id": question.id,
            "type": question.type,
            "difficulty": question.difficulty,
            "content": question.content,
            "options": question.options,
            "answer": question.answer,
            "explanation": question.explanation
        } if question else None
    }


@router.put("/{wrong_question_id}/master")
def mark_as_mastered(
    wrong_question_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """标记为已掌握"""
    wq = db.query(WrongQuestion).filter(WrongQuestion.id == wrong_question_id).first()
    if not wq:
        raise HTTPException(status_code=404, detail="错题不存在")
    
    wq.mastered = 1
    db.commit()
    
    return {"message": "已标记为掌握"}


@router.put("/{wrong_question_id}/unmaster")
def mark_as_unmastered(
    wrong_question_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """取消掌握标记"""
    wq = db.query(WrongQuestion).filter(WrongQuestion.id == wrong_question_id).first()
    if not wq:
        raise HTTPException(status_code=404, detail="错题不存在")
    
    wq.mastered = 0
    db.commit()
    
    return {"message": "已取消掌握标记"}


@router.delete("/{wrong_question_id}")
def delete_wrong_question(
    wrong_question_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """删除错题"""
    wq = db.query(WrongQuestion).filter(WrongQuestion.id == wrong_question_id).first()
    if not wq:
        raise HTTPException(status_code=404, detail="错题不存在")
    
    db.delete(wq)
    db.commit()
    
    return {"message": "删除成功"}


@router.get("/stats/overview")
def get_wrong_questions_stats(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取错题统计"""
    total = db.query(WrongQuestion).count()
    mastered = db.query(WrongQuestion).filter(WrongQuestion.mastered == 1).count()
    unmastered = total - mastered
    
    return {
        "total": total,
        "mastered": mastered,
        "unmastered": unmastered
    }
