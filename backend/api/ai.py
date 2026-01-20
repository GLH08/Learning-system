"""
AI API endpoints
"""
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, List
import json
from datetime import datetime

from models.database import get_db
from models.question import Question
from models.ai_task import AITask
from schemas.common import Response
from pydantic import BaseModel
from utils.security import get_current_user
from utils.exceptions import NotFoundError, ParameterError
from utils.helpers import to_json, from_json
from services.ai_service import get_ai_service, AIService

router = APIRouter()


class AICompleteRequest(BaseModel):
    questionId: str
    type: str

@router.post("/complete")
async def complete_question(
    request: AICompleteRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """AI complete single question"""
    question_id = request.questionId
    type = request.type
    
    # Validate question
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise NotFoundError("题目不存在")
    
    # Validate type
    if type not in ['answer', 'explanation', 'both']:
        raise ParameterError("无效的补全类型")
    
    # Get AI service
    try:
        ai_service = get_ai_service(db)
    except ValueError as e:
        raise ParameterError(str(e))
    
    # Generate content
    try:
        if type == 'answer':
            answer = await ai_service.generate_answer(question)
            question.answer = answer
            question.answer_status = 'ai_generated'
            result = {"answer": answer}
        
        elif type == 'explanation':
            explanation = await ai_service.generate_explanation(question)
            question.explanation = explanation
            question.explanation_status = 'ai_generated'
            result = {"explanation": explanation}
        
        else:  # both
            both = await ai_service.generate_both(question)
            question.answer = both['answer']
            question.answer_status = 'ai_generated'
            question.explanation = both['explanation']
            question.explanation_status = 'ai_generated'
            result = both
        
        db.commit()
        db.refresh(question)
        
        return Response(
            code=0,
            message="生成成功",
            data={
                "questionId": question.id,
                "answerStatus": question.answer_status,
                "explanationStatus": question.explanation_status,
                **result
            }
        )
    
    except Exception as e:
        db.rollback()
        error_msg = str(e)
        if "429" in error_msg or "quota" in error_msg.lower():
            # Raise 429 so frontend can detect it
            from fastapi import HTTPException
            raise HTTPException(status_code=429, detail="AI Service Rate Limit Exceeded")
        if "404" in error_msg:
             from fastapi import HTTPException
             raise HTTPException(status_code=404, detail="AI Model Not Found")
             
        raise ParameterError(f"AI error: {error_msg}")


@router.post("/batch-complete")
async def batch_complete_questions(
    question_ids: Optional[List[str]] = None,
    type: str = "both",
    filter: Optional[dict] = None,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create batch completion task"""
    # Validate type
    if type not in ['answer', 'explanation', 'both']:
        raise ParameterError("无效的补全类型")
    
    # Get questions to process
    if question_ids:
        questions = db.query(Question).filter(Question.id.in_(question_ids)).all()
    else:
        # Use filter
        query = db.query(Question)
        if filter:
            if filter.get('categoryId'):
                query = query.filter(Question.category_id == filter['categoryId'])
            if filter.get('answerStatus'):
                query = query.filter(Question.answer_status == filter['answerStatus'])
            if filter.get('explanationStatus'):
                query = query.filter(Question.explanation_status == filter['explanationStatus'])
        
        questions = query.all()
    
    if not questions:
        raise ParameterError("没有找到需要补全的题目")
    
    # Create task
    task = AITask(
        type=type,
        status="pending",
        question_ids=to_json([q.id for q in questions]),
        total_count=len(questions)
    )
    
    db.add(task)
    db.commit()
    db.refresh(task)
    
    # Start background task
    background_tasks.add_task(process_batch_task, task.id, db)
    
    return Response(
        code=0,
        message="任务已创建",
        data={
            "taskId": task.id,
            "type": type,
            "totalCount": len(questions),
            "status": "pending",
            "createdAt": task.created_at.isoformat()
        }
    )


async def process_batch_task(task_id: str, db: Session):
    """Process batch completion task in background"""
    task = db.query(AITask).filter(AITask.id == task_id).first()
    if not task:
        return
    
    # Update status
    task.status = "running"
    task.started_at = datetime.utcnow()
    db.commit()
    
    # Get AI service
    try:
        ai_service = get_ai_service(db)
    except Exception as e:
        task.status = "failed"
        task.error_message = str(e)
        db.commit()
        return
    
    # Get questions
    question_ids = from_json(task.question_ids, [])
    
    # Process each question
    for question_id in question_ids:
        # Check if task is cancelled or paused
        db.refresh(task)
        if task.status in ['cancelled', 'paused']:
            break
        
        task.current_question_id = question_id
        db.commit()
        
        question = db.query(Question).filter(Question.id == question_id).first()
        if not question:
            task.failed_count += 1
            continue
        
        try:
            if task.type == 'answer':
                answer = await ai_service.generate_answer(question)
                question.answer = answer
                question.answer_status = 'ai_generated'
            
            elif task.type == 'explanation':
                explanation = await ai_service.generate_explanation(question)
                question.explanation = explanation
                question.explanation_status = 'ai_generated'
            
            else:  # both
                both = await ai_service.generate_both(question)
                question.answer = both['answer']
                question.answer_status = 'ai_generated'
                question.explanation = both['explanation']
                question.explanation_status = 'ai_generated'
            
            task.completed_count += 1
            db.commit()
        
        except Exception as e:
            task.failed_count += 1
            db.commit()
    
    # Update final status
    if task.status == 'running':
        task.status = 'completed'
        task.completed_at = datetime.utcnow()
    
    task.current_question_id = None
    db.commit()


@router.get("/tasks")
async def get_tasks(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get AI tasks list"""
    query = db.query(AITask)
    
    if status and status != 'all':
        query = query.filter(AITask.status == status)
    
    tasks = query.order_by(AITask.created_at.desc()).all()
    
    items = [
        {
            "id": task.id,
            "type": task.type,
            "status": task.status,
            "totalCount": task.total_count,
            "completedCount": task.completed_count,
            "failedCount": task.failed_count,
            "progress": task.completed_count / task.total_count if task.total_count > 0 else 0,
            "currentQuestionId": task.current_question_id,
            "createdAt": task.created_at.isoformat() if task.created_at else None,
            "startedAt": task.started_at.isoformat() if task.started_at else None,
            "updatedAt": task.updated_at.isoformat() if task.updated_at else None,
            "completedAt": task.completed_at.isoformat() if task.completed_at else None
        }
        for task in tasks
    ]
    
    return Response(
        code=0,
        message="success",
        data={
            "items": items,
            "total": len(items)
        }
    )


@router.get("/tasks/{task_id}")
async def get_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get AI task details"""
    task = db.query(AITask).filter(AITask.id == task_id).first()
    if not task:
        raise NotFoundError("任务不存在")
    
    return Response(
        code=0,
        message="success",
        data={
            "id": task.id,
            "type": task.type,
            "status": task.status,
            "totalCount": task.total_count,
            "completedCount": task.completed_count,
            "failedCount": task.failed_count,
            "progress": task.completed_count / task.total_count if task.total_count > 0 else 0,
            "questionIds": from_json(task.question_ids, []),
            "currentQuestionId": task.current_question_id,
            "errorMessage": task.error_message,
            "createdAt": task.created_at.isoformat() if task.created_at else None,
            "startedAt": task.started_at.isoformat() if task.started_at else None,
            "updatedAt": task.updated_at.isoformat() if task.updated_at else None,
            "completedAt": task.completed_at.isoformat() if task.completed_at else None
        }
    )


@router.put("/tasks/{task_id}/pause")
async def pause_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Pause AI task"""
    task = db.query(AITask).filter(AITask.id == task_id).first()
    if not task:
        raise NotFoundError("任务不存在")
    
    if task.status != 'running':
        raise ParameterError("只能暂停运行中的任务")
    
    task.status = 'paused'
    db.commit()
    
    return Response(
        code=0,
        message="任务已暂停",
        data={
            "id": task.id,
            "status": task.status,
            "completedCount": task.completed_count
        }
    )


@router.put("/tasks/{task_id}/resume")
async def resume_task(
    task_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Resume AI task"""
    task = db.query(AITask).filter(AITask.id == task_id).first()
    if not task:
        raise NotFoundError("任务不存在")
    
    if task.status != 'paused':
        raise ParameterError("只能恢复已暂停的任务")
    
    task.status = 'running'
    db.commit()
    
    # Resume background task
    background_tasks.add_task(process_batch_task, task.id, db)
    
    return Response(
        code=0,
        message="任务已恢复",
        data={
            "id": task.id,
            "status": task.status
        }
    )


@router.put("/tasks/{task_id}/cancel")
async def cancel_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Cancel AI task"""
    task = db.query(AITask).filter(AITask.id == task_id).first()
    if not task:
        raise NotFoundError("任务不存在")
    
    if task.status in ['completed', 'failed', 'cancelled']:
        raise ParameterError("任务已结束，无法取消")
    
    task.status = 'cancelled'
    task.completed_at = datetime.utcnow()
    db.commit()
    
    return Response(
        code=0,
        message="任务已取消",
        data={
            "id": task.id,
            "status": task.status,
            "completedCount": task.completed_count
        }
    )



class GenerateReportRequest(BaseModel):
    examId: str


@router.post("/generate-report")
async def generate_learning_report(
    request: GenerateReportRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Generate AI learning analysis report"""
    from models.exam import Exam, WrongQuestion
    
    exam_id = request.examId

    
    # Get exam
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise NotFoundError("考试不存在")
    
    if exam.status != "completed":
        raise ParameterError("只能为已完成的考试生成报告")
    
    # Get wrong questions
    wrong_questions = db.query(WrongQuestion).filter(
        WrongQuestion.exam_id == exam_id
    ).all()
    
    # Get question details
    wrong_question_data = []
    for wq in wrong_questions:
        question = db.query(Question).filter(Question.id == wq.question_id).first()
        if question:
            tags = from_json(question.tags) if question.tags else []
            wrong_question_data.append({
                "content": question.content,
                "type": question.type,
                "tags": tags,
                "user_answer": wq.user_answer,
                "correct_answer": wq.correct_answer
            })
    
    # Prepare exam data
    correct_rate = (exam.correct_count / exam.total_count) if exam.total_count > 0 else 0
    exam_data = {
        "score": exam.score,
        "total_score": exam.total_score,
        "correct_count": exam.correct_count,
        "wrong_count": exam.wrong_count,
        "correct_rate": correct_rate,
        "wrong_questions": wrong_question_data
    }
    
    # Get AI service
    try:
        ai_service = get_ai_service(db)
    except ValueError as e:
        raise ParameterError(str(e))
    
    # Generate report
    try:
        report = await ai_service.generate_report(exam_data)
        return Response(data={"report": report})
    except Exception as e:
        raise ParameterError(f"生成报告失败: {str(e)}")
