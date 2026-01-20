"""
考试管理 API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime
import json

from models.database import get_db
from models.exam import Exam, WrongQuestion
from models.question import Question
from services.exam_service import ExamService, ExamConfig
from services.grading_service import GradingService
from api.auth import get_current_user

router = APIRouter(prefix="/exams", tags=["exams"])


# ============ Schemas ============

class QuickExamRequest(BaseModel):
    count: int = 20
    shuffle_options: bool = True


class TypeCount(BaseModel):
    type: str
    count: int


class CustomExamRequest(BaseModel):
    title: str = "自定义测试"
    mode: str = "exam"  # exam/practice/review
    category_ids: Optional[List[str]] = None
    question_types: Optional[List[str]] = None
    difficulties: Optional[List[str]] = None
    type_counts: Optional[List[TypeCount]] = None
    time_limit: Optional[int] = None
    shuffle_options: bool = True
    shuffle_questions: bool = True


class SaveAnswerRequest(BaseModel):
    question_id: str
    answer: str


class SubmitExamRequest(BaseModel):
    answers: Dict[str, str]


class WrongQuestionExamRequest(BaseModel):
    title: str = "错题专项练习"
    mode: str = "practice"
    mastered: Optional[int] = None
    limit: Optional[int] = None


class ExamResponse(BaseModel):
    id: str
    title: str
    mode: str
    status: str
    total_count: int
    total_score: int
    score: int
    correct_count: int
    wrong_count: int
    time_limit: Optional[int]
    start_time: Optional[datetime]
    submit_time: Optional[datetime]
    time_used: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True


class ExamDetailResponse(ExamResponse):
    config: Optional[str]
    question_ids: str
    answers: Optional[str]


class QuestionInExam(BaseModel):
    id: str
    type: str
    difficulty: str
    content: str
    options: Optional[str]
    answer: Optional[str] = None  # 练习模式才返回
    explanation: Optional[str] = None  # 练习模式才返回
    user_answer: Optional[str] = None


class ExamQuestionsResponse(BaseModel):
    exam: ExamResponse
    questions: List[QuestionInExam]


class GradingResult(BaseModel):
    score: int
    total_score: int
    correct_count: int
    wrong_count: int
    results: Dict[str, Dict]


# ============ API Endpoints ============

@router.post("/generate/quick", response_model=ExamResponse)
def generate_quick_exam(
    request: QuickExamRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """快速组卷"""
    try:
        service = ExamService(db)
        exam = service.generate_quick_exam(
            count=request.count,
            shuffle_options=request.shuffle_options
        )
        return exam
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成试卷失败: {str(e)}")


@router.post("/generate/custom", response_model=ExamResponse)
def generate_custom_exam(
    request: CustomExamRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """自定义组卷"""
    try:
        # 转换 type_counts
        type_counts = {}
        if request.type_counts:
            for tc in request.type_counts:
                type_counts[tc.type] = tc.count
        
        config = ExamConfig(
            title=request.title,
            mode=request.mode,
            category_ids=request.category_ids,
            question_types=request.question_types,
            difficulties=request.difficulties,
            type_counts=type_counts,
            time_limit=request.time_limit,
            shuffle_options=request.shuffle_options,
            shuffle_questions=request.shuffle_questions
        )
        
        service = ExamService(db)
        exam = service.generate_custom_exam(config)
        return exam
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成试卷失败: {str(e)}")


@router.get("", response_model=List[ExamResponse])
def list_exams(
    status: Optional[str] = None,
    mode: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取考试列表"""
    query = db.query(Exam)
    
    if status:
        query = query.filter(Exam.status == status)
    if mode:
        query = query.filter(Exam.mode == mode)
    
    exams = query.order_by(Exam.created_at.desc()).offset(skip).limit(limit).all()
    return exams


@router.get("/{exam_id}", response_model=ExamDetailResponse)
def get_exam(
    exam_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取考试详情"""
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")
    return exam


@router.get("/{exam_id}/questions", response_model=ExamQuestionsResponse)
def get_exam_questions(
    exam_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取考试题目"""
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")
    
    # 开始计时
    if not exam.start_time and exam.status == "in_progress":
        exam.start_time = datetime.now()
        db.commit()
    
    service = ExamService(db)
    questions = service.get_exam_questions(exam)
    
    # 获取已保存的答案
    saved_answers = {}
    if exam.answers:
        saved_answers = json.loads(exam.answers)
    
    # 构建响应
    question_list = []
    for q in questions:
        question_dict = {
            "id": q.id,
            "type": q.type,
            "difficulty": q.difficulty,
            "content": q.content,
            "options": q.options,
            "user_answer": saved_answers.get(q.id)
        }
        
        # 练习模式和背题模式显示答案和解析
        if exam.mode in ["practice", "review"]:
            question_dict["answer"] = q.answer
            question_dict["explanation"] = q.explanation
        
        question_list.append(QuestionInExam(**question_dict))
    
    return {
        "exam": exam,
        "questions": question_list
    }


@router.put("/{exam_id}/answer")
def save_answer(
    exam_id: str,
    request: SaveAnswerRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """保存答案"""
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")
    
    if exam.status != "in_progress":
        raise HTTPException(status_code=400, detail="考试已结束")
    
    # 获取当前答案
    answers = {}
    if exam.answers:
        answers = json.loads(exam.answers)
    
    # 更新答案
    answers[request.question_id] = request.answer
    exam.answers = json.dumps(answers, ensure_ascii=False)
    
    db.commit()
    
    return {"message": "答案已保存"}


@router.post("/{exam_id}/submit", response_model=GradingResult)
def submit_exam(
    exam_id: str,
    request: SubmitExamRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """提交试卷并评分"""
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")
    
    if exam.status != "in_progress":
        raise HTTPException(status_code=400, detail="考试已结束")
    
    # 评分
    grading_service = GradingService(db)
    result = grading_service.grade_exam(exam, request.answers)
    
    return result


@router.delete("/{exam_id}")
def delete_exam(
    exam_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """删除考试记录"""
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")
    
    db.delete(exam)
    db.commit()
    
    return {"message": "删除成功"}




@router.post("/generate/wrong-questions", response_model=ExamResponse)
def generate_wrong_question_exam(
    request: WrongQuestionExamRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """生成错题试卷"""
    try:
        service = ExamService(db)
        exam = service.generate_wrong_question_exam(
            title=request.title,
            mode=request.mode,
            mastered=request.mastered,
            limit=request.limit
        )
        return exam
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成试卷失败: {str(e)}")



class ManualGradeRequest(BaseModel):
    question_id: str
    score: int
    feedback: Optional[str] = None


@router.post("/{exam_id}/manual-grade")
def manual_grade_question(
    exam_id: str,
    request: ManualGradeRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """手动评分简述题"""
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")
    
    if exam.status != "completed":
        raise HTTPException(status_code=400, detail="只能为已完成的考试评分")
    
    # 验证题目是否在试卷中
    question_ids = json.loads(exam.question_ids)
    if request.question_id not in question_ids:
        raise HTTPException(status_code=400, detail="题目不在试卷中")
    
    # 获取题目
    question = db.query(Question).filter(Question.id == request.question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="题目不存在")
    
    if question.type != "essay":
        raise HTTPException(status_code=400, detail="只能为简述题手动评分")
    
    # 更新分数
    # 先获取旧的评分信息
    config = json.loads(exam.config) if exam.config else {}
    manual_grades = config.get("manual_grades", {})
    
    old_grade = manual_grades.get(request.question_id)
    old_score = old_grade.get("score", 0) if old_grade else 0
    
    # 更新总分：减去旧分，加上新分
    exam.score = exam.score - old_score + request.score
    
    # 可以将评分信息存储在 config 中
    config = json.loads(exam.config) if exam.config else {}
    if "manual_grades" not in config:
        config["manual_grades"] = {}
    
    config["manual_grades"][request.question_id] = {
        "score": request.score,
        "feedback": request.feedback,
        "graded_at": datetime.now().isoformat()
    }
    
    exam.config = json.dumps(config, ensure_ascii=False)
    db.commit()
    
    return {"message": "评分成功", "score": request.score}
