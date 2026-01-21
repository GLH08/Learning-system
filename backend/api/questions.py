from fastapi import APIRouter, Depends, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import Optional, List
import math
import json
import io
from datetime import datetime

from models.database import get_db
from models.question import Question
from models.category import Category
from schemas.question import (
    QuestionCreate, QuestionUpdate, QuestionResponse,
    QuestionListQuery, QuestionStatsResponse, BatchUpdateCategoryRequest
)
from schemas.common import Response, PageResponse
from utils.security import get_current_user
from utils.exceptions import NotFoundError, ParameterError
from utils.helpers import to_json, from_json
from services.document_parser import get_document_parser

router = APIRouter()


def question_to_dict(question: Question) -> dict:
    """Convert Question model to dict"""
    return {
        "id": question.id,
        "categoryId": question.category_id,
        "type": question.type,
        "difficulty": question.difficulty,
        "content": question.content,
        "options": from_json(question.options, {}),
        "answer": question.answer,
        "answerStatus": question.answer_status,
        "explanation": question.explanation,
        "explanationStatus": question.explanation_status,
        "tags": from_json(question.tags, []),
        "source": question.source,
        "createdAt": question.created_at,
        "updatedAt": question.updated_at
    }


@router.get("", response_model=Response[PageResponse])
async def get_questions(
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = None,
    categoryId: Optional[str] = None,
    type: Optional[str] = None,
    difficulty: Optional[str] = None,
    status: Optional[str] = None,
    answerStatus: Optional[str] = None,
    explanationStatus: Optional[str] = None,
    sortBy: str = "createdAt",
    sortOrder: str = "desc",
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get question list with pagination and filters"""
    query = db.query(Question)
    
    # Apply filters
    if keyword:
        query = query.filter(Question.content.like(f"%{keyword}%"))
    
    if categoryId:
        query = query.filter(Question.category_id == categoryId)
    
    if type:
        query = query.filter(Question.type == type)
    
    if difficulty:
        query = query.filter(Question.difficulty == difficulty)
    
    if status:
        if status == "complete":
            # 答案和解析都不是 none 则视为完成 (包括 confirmed 和 ai_generated)
            query = query.filter(
                and_(
                    Question.answer_status != "none",
                    Question.explanation_status != "none"
                )
            )
        elif status == "incomplete":
            # 只要有一个是 none 则视为未完成
            query = query.filter(
                or_(
                    Question.answer_status == "none",
                    Question.explanation_status == "none"
                )
            )
    
    if answerStatus:
        query = query.filter(Question.answer_status == answerStatus)
    
    if explanationStatus:
        query = query.filter(Question.explanation_status == explanationStatus)
    
    # Get total count
    total = query.count()
    
    # Apply sorting
    if sortBy == "createdAt":
        query = query.order_by(Question.created_at.desc() if sortOrder == "desc" else Question.created_at.asc())
    elif sortBy == "updatedAt":
        query = query.order_by(Question.updated_at.desc() if sortOrder == "desc" else Question.updated_at.asc())
    
    # Apply pagination
    offset = (page - 1) * pageSize
    questions = query.offset(offset).limit(pageSize).all()
    
    # Convert to dict
    items = [question_to_dict(q) for q in questions]
    
    return Response(
        code=0,
        message="success",
        data={
            "items": items,
            "total": total,
            "page": page,
            "pageSize": pageSize,
            "totalPages": math.ceil(total / pageSize) if total > 0 else 0
        }
    )


@router.get("/stats", response_model=Response[QuestionStatsResponse])
async def get_question_stats(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get question statistics"""
    total = db.query(Question).count()
    
    # By type
    by_type = {}
    for type_name in ["single", "multiple", "judge", "essay"]:
        count = db.query(Question).filter(Question.type == type_name).count()
        by_type[type_name] = count
    
    # By difficulty
    by_difficulty = {}
    for diff in ["easy", "medium", "hard"]:
        count = db.query(Question).filter(Question.difficulty == diff).count()
        by_difficulty[diff] = count
    
    # By status - 只有 none 状态才算待补全
    incomplete = db.query(Question).filter(
        or_(
            Question.answer_status == "none",
            Question.explanation_status == "none"
        )
    ).count()
    
    complete = total - incomplete
    
    by_status = {
        "complete": complete,
        "incomplete": incomplete
    }
    
    return Response(
        code=0,
        message="success",
        data={
            "total": total,
            "byType": by_type,
            "byDifficulty": by_difficulty,
            "byStatus": by_status,
            "incomplete": incomplete
        }
    )


@router.get("/{question_id}", response_model=Response[QuestionResponse])
async def get_question(
    question_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get question details"""
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise NotFoundError("题目不存在")
    
    return Response(code=0, message="success", data=question_to_dict(question))


@router.post("", response_model=Response[QuestionResponse])
async def create_question(
    question: QuestionCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create question"""
    # Validate category
    if question.categoryId:
        category = db.query(Category).filter(Category.id == question.categoryId).first()
        if not category:
            raise NotFoundError("分类不存在")
    
    # Determine status
    answer_status = "confirmed" if question.answer else "none"
    explanation_status = "confirmed" if question.explanation else "none"
    
    # Create question
    db_question = Question(
        category_id=question.categoryId or "default",
        type=question.type,
        difficulty=question.difficulty,
        content=question.content,
        options=to_json(question.options),
        answer=question.answer,
        answer_status=answer_status,
        explanation=question.explanation,
        explanation_status=explanation_status,
        tags=to_json(question.tags),
        source=question.source
    )
    
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    
    return Response(code=0, message="创建成功", data=question_to_dict(db_question))


@router.put("/{question_id}", response_model=Response[QuestionResponse])
async def update_question(
    question_id: str,
    question: QuestionUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update question"""
    db_question = db.query(Question).filter(Question.id == question_id).first()
    if not db_question:
        raise NotFoundError("题目不存在")
    
    # Update fields
    if question.categoryId is not None:
        if question.categoryId:
            category = db.query(Category).filter(Category.id == question.categoryId).first()
            if not category:
                raise NotFoundError("分类不存在")
        db_question.category_id = question.categoryId or "default"
    
    if question.type is not None:
        db_question.type = question.type
    
    if question.difficulty is not None:
        db_question.difficulty = question.difficulty
    
    if question.content is not None:
        db_question.content = question.content
    
    if question.options is not None:
        db_question.options = to_json(question.options)
    
    if question.answer is not None:
        db_question.answer = question.answer
        if db_question.answer_status == "none":
            db_question.answer_status = "confirmed"
    
    if question.explanation is not None:
        db_question.explanation = question.explanation
        if db_question.explanation_status == "none":
            db_question.explanation_status = "confirmed"
    
    if question.tags is not None:
        db_question.tags = to_json(question.tags)
    
    if question.source is not None:
        db_question.source = question.source
    
    db.commit()
    db.refresh(db_question)
    
    return Response(code=0, message="更新成功", data=question_to_dict(db_question))


@router.post("/batch-update-category", response_model=Response)
async def batch_update_category(
    request: BatchUpdateCategoryRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Batch update questions category"""
    if not request.question_ids:
        raise ParameterError("请选择要更新的题目")

    # Validate category
    if request.category_id and request.category_id != "default":
        category = db.query(Category).filter(Category.id == request.category_id).first()
        if not category:
            raise NotFoundError("分类不存在")

    # Update questions
    updated_count = db.query(Question).filter(Question.id.in_(request.question_ids)).update(
        {"category_id": request.category_id or "default"},
        synchronize_session=False
    )
    db.commit()

    return Response(code=0, message=f"成功更新 {updated_count} 道题目的分类", data={"updated": updated_count})


@router.post("/batch-delete", response_model=Response)
async def batch_delete_questions(
    question_ids: list[str],
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Batch delete questions"""
    if not question_ids:
        raise ParameterError("请选择要删除的题目")

    # Delete questions
    deleted_count = db.query(Question).filter(Question.id.in_(question_ids)).delete(synchronize_session=False)
    db.commit()

    return Response(code=0, message=f"成功删除 {deleted_count} 道题目", data={"deleted": deleted_count})


@router.delete("/{question_id}", response_model=Response)
async def delete_question(
    question_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete question"""
    db_question = db.query(Question).filter(Question.id == question_id).first()
    if not db_question:
        raise NotFoundError("题目不存在")
    
    db.delete(db_question)
    db.commit()
    
    return Response(code=0, message="删除成功")


@router.put("/{question_id}/confirm-answer", response_model=Response[QuestionResponse])
async def confirm_answer(
    question_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Confirm AI generated answer"""
    db_question = db.query(Question).filter(Question.id == question_id).first()
    if not db_question:
        raise NotFoundError("题目不存在")
    
    if db_question.answer_status == "ai_generated":
        db_question.answer_status = "confirmed"
        db.commit()
        db.refresh(db_question)
    
    return Response(code=0, message="确认成功", data=question_to_dict(db_question))


@router.put("/{question_id}/confirm-explanation", response_model=Response[QuestionResponse])
async def confirm_explanation(
    question_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Confirm AI generated explanation"""
    db_question = db.query(Question).filter(Question.id == question_id).first()
    if not db_question:
        raise NotFoundError("题目不存在")
    
    if db_question.explanation_status == "ai_generated":
        db_question.explanation_status = "confirmed"
        db.commit()
        db.refresh(db_question)
    
    return Response(code=0, message="确认成功", data=question_to_dict(db_question))


@router.get("/export/json")
async def export_questions_json(
    categoryId: Optional[str] = None,
    type: Optional[str] = None,
    difficulty: Optional[str] = None,
    includeIncomplete: bool = True,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Export questions as JSON"""
    query = db.query(Question)
    
    # Apply filters
    if categoryId:
        query = query.filter(Question.category_id == categoryId)
    
    if type:
        query = query.filter(Question.type == type)
    
    if difficulty:
        query = query.filter(Question.difficulty == difficulty)
    
    if not includeIncomplete:
        query = query.filter(
            and_(
                Question.answer_status == "confirmed",
                Question.explanation_status == "confirmed"
            )
        )
    
    questions = query.all()
    
    # Convert to export format
    export_data = {
        "exportTime": datetime.now().isoformat(),
        "totalCount": len(questions),
        "questions": [
            {
                "id": q.id,
                "type": q.type,
                "difficulty": q.difficulty,
                "content": q.content,
                "options": from_json(q.options, {}),
                "answer": q.answer,
                "explanation": q.explanation,
                "tags": from_json(q.tags, []),
                "source": q.source
            }
            for q in questions
        ]
    }
    
    # Create JSON file
    json_str = json.dumps(export_data, ensure_ascii=False, indent=2)
    json_bytes = json_str.encode('utf-8')
    
    # Create filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"questions_{timestamp}.json"
    
    return StreamingResponse(
        io.BytesIO(json_bytes),
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.post("/import/preview")
async def preview_import(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Preview imported questions"""
    # Check file type
    filename = file.filename.lower()
    if not any(filename.endswith(ext) for ext in ['.docx', '.xlsx', '.txt', '.json']):
        raise ParameterError("不支持的文件格式，仅支持 .docx, .xlsx, .txt, .json")
    
    # Read file content
    content = await file.read()
    
    # Parse document
    parser = get_document_parser()
    
    try:
        if filename.endswith('.docx'):
            parsed_questions = parser.parse_word(content)
        elif filename.endswith('.xlsx'):
            parsed_questions = parser.parse_excel(content)
        elif filename.endswith('.txt'):
            parsed_questions = parser.parse_txt(content)
        elif filename.endswith('.json'):
            # Parse JSON format
            data = json.loads(content.decode('utf-8'))
            parsed_questions = []
            for idx, q in enumerate(data.get('questions', []), 1):
                from services.document_parser import ParsedQuestion
                parsed_questions.append(ParsedQuestion(
                    index=idx,
                    type=q.get('type', 'unknown'),
                    content=q.get('content', ''),
                    options=q.get('options'),
                    answer=q.get('answer'),
                    explanation=q.get('explanation'),
                    difficulty=q.get('difficulty', 'medium'),
                    tags=q.get('tags', []),
                    source=q.get('source')
                ))
        else:
            raise ParameterError("不支持的文件格式")
        
    # Calculate statistics
        # Check for duplicates (Advanced Strategy)
        import re
        from difflib import SequenceMatcher
        
        def normalize_text(text):
            """Remove punctuation and whitespace, keep chars only"""
            if not text: return ""
            # Keep only Chinese, letters, numbers
            return re.sub(r'[^\w\u4e00-\u9fff]', '', text).lower()

        def is_similar(a, b, threshold=0.95):
            """Check if two strings are similar"""
            return SequenceMatcher(None, a, b).ratio() > threshold

        # 1. Fetch all existing question contents for comparison
        # Note: Optimization needed for very large datasets (e.g. vector search or elasticsearch)
        # For now, fetching all contents is acceptable for typical usage (<50k questions)
        all_existing_questions = db.query(Question.id, Question.content).all()

        # Build lookup maps
        # Exact map (normalized) -> list of IDs (to handle potential multiple identicals)
        norm_map = {}
        for qid, content in all_existing_questions:
            if not content: continue
            norm = normalize_text(content)
            if norm not in norm_map:
                norm_map[norm] = []
            norm_map[norm].append(qid)

        # Mark duplicates
        for q in parsed_questions:
            if not q.content: continue

            q_norm = normalize_text(q.content)
            is_dup = False
            dup_reason = ""

            # Strategy 1: Normalized Exact Match (Fast, catches punctuation/spacing diffs)
            if q_norm in norm_map:
                is_dup = True
                dup_reason = "内容完全相同（忽略标点）"

            # Strategy 2: Fuzzy Match (Slow, catches OCR typos)
            # Only apply fuzzy matching for longer texts (>20 chars after normalization)
            # to avoid false positives with short questions
            if not is_dup and len(q_norm) > 20:
                # We iterate to find a similar one.
                # Optimization: Limit comparison to same 'type' if we had that info indexed,
                # but currently we compare against all.
                # To be faster, we could check length proximity first.
                for existing_norm in norm_map.keys():
                    if abs(len(q_norm) - len(existing_norm)) > 10: continue # Length heuristic

                    if is_similar(q_norm, existing_norm, threshold=0.95):
                        is_dup = True
                        dup_reason = "内容高度相似（疑似OCR误差）"
                        break
            
            if is_dup:
                q.parse_message = f"系统已存在相似题目: {dup_reason}"
                q.parse_status = "warning"
                setattr(q, 'is_duplicate', True)
            else:
                 setattr(q, 'is_duplicate', False)

        stats = {
            "total": len(parsed_questions),
            "success": sum(1 for q in parsed_questions if q.parse_status == "success"),
            "warning": sum(1 for q in parsed_questions if q.parse_status == "warning"),
            "duplicate": sum(1 for q in parsed_questions if getattr(q, 'is_duplicate', False)),
            "complete": sum(1 for q in parsed_questions if q.answer and str(q.answer).strip() and q.explanation and str(q.explanation).strip()),
            "hasAnswer": sum(1 for q in parsed_questions if q.answer and str(q.answer).strip()),
            "onlyContent": sum(1 for q in parsed_questions if (not q.answer or not str(q.answer).strip()) and (not q.explanation or not str(q.explanation).strip())),
            "byType": {}
        }
        
        # Count by type
        for q in parsed_questions:
            stats["byType"][q.type] = stats["byType"].get(q.type, 0) + 1
        
        # Convert to dict and add isDuplicate flag
        questions_data = []
        for q in parsed_questions:
            d = q.to_dict()
            d['isDuplicate'] = getattr(q, 'is_duplicate', False)
            questions_data.append(d)

        return Response(
            code=0,
            message="success",
            data={
                "questions": questions_data,
                "statistics": stats
            }
        )
    
    except Exception as e:
        raise ParameterError(str(e))


@router.post("/import")
async def import_questions(
    questions: List[dict],
    categoryId: Optional[str] = None,
    defaultType: str = "single",
    defaultDifficulty: str = "medium",
    skipErrors: bool = True,
    skipDuplicates: bool = True,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Import questions"""
    if not questions:
        raise ParameterError("没有要导入的题目")
    
    # Check for duplicates using advanced strategy if requested
    import re
    from difflib import SequenceMatcher
    
    def normalize_text(text):
        if not text: return ""
        return re.sub(r'[^\w\u4e00-\u9fff]', '', text).lower()
        
    def is_similar(a, b, threshold=0.9):
        return SequenceMatcher(None, a, b).ratio() > threshold

    # Pre-fetch all existing question contents for duplicate check
    existing_norms = []
    if skipDuplicates:
        all_existing_questions = db.query(Question.content).all()
        existing_norms = [normalize_text(q.content) for q in all_existing_questions if q.content]

    # Validate category
    if categoryId:
        category = db.query(Category).filter(Category.id == categoryId).first()
        if not category:
            raise ParameterError("分类不存在")
    else:
        categoryId = "default"

    created = []
    errors = []
    skipped = []
    batch_norms = []  # Track normalized content in current batch to prevent self-duplication

    for idx, q_data in enumerate(questions, 1):
        try:
            # Validate required fields
            content = q_data.get('content')
            if not content:
                if skipErrors:
                    errors.append({"line": idx, "message": "题目内容为空"})
                    continue
                else:
                    raise ParameterError(f"第 {idx} 题：题目内容为空")

            # Check for duplicate
            if skipDuplicates:
                q_norm = normalize_text(content)
                is_dup = False

                # Check against existing database questions (exact match)
                if q_norm in existing_norms:
                   is_dup = True

                # Check against existing database questions (fuzzy match)
                # Only apply fuzzy matching for longer texts (>20 chars after normalization)
                # to avoid false positives with short questions
                if not is_dup and len(q_norm) > 20:
                     for existing_norm in existing_norms:
                        # Skip if length difference is too large
                        if abs(len(q_norm) - len(existing_norm)) > 10: continue
                        # Use higher threshold (0.95) for more strict matching
                        if SequenceMatcher(None, q_norm, existing_norm).ratio() > 0.95:
                            is_dup = True
                            break

                # Check against current batch to prevent self-duplication
                if not is_dup and q_norm in batch_norms:
                    is_dup = True

                if is_dup:
                    skipped.append({"line": idx, "message": "题目已存在或高度相似，跳过导入"})
                    continue

            # Determine status & Clean data
            answer = q_data.get('answer')
            if answer and str(answer).strip():
                answer_status = "confirmed"
                answer = str(answer).strip()
            else:
                answer_status = "none"
                answer = None

            explanation = q_data.get('explanation')
            if explanation and str(explanation).strip():
                explanation_status = "confirmed"
                explanation = str(explanation).strip()
            else:
                explanation_status = "none"
                explanation = None

            # Create question
            question = Question(
                category_id=categoryId,
                type=q_data.get('type', defaultType),
                difficulty=q_data.get('difficulty', defaultDifficulty),
                content=content,
                options=to_json(q_data.get('options')),
                answer=answer,
                answer_status=answer_status,
                explanation=explanation,
                explanation_status=explanation_status,
                tags=to_json(q_data.get('tags', [])),
                source=q_data.get('source')
            )

            db.add(question)
            db.flush()

            created.append({
                "id": question.id,
                "content": question.content[:50] + "..." if len(question.content) > 50 else question.content
            })

            # Add to batch cache to prevent self-duplication within same batch
            if skipDuplicates:
                batch_norms.append(normalize_text(content))
        
        except Exception as e:
            if skipErrors:
                errors.append({"line": idx, "message": str(e)})
            else:
                db.rollback()
                raise ParameterError(f"第 {idx} 题导入失败: {str(e)}")
    
    db.commit()
    
    return Response(
        code=0,
        message="导入完成",
        data={
            "total": len(questions),
            "success": len(created),
            "failed": len(errors),
            "skipped": len(skipped),
            "created": created[:10],  # Return first 10
            "importedIds": [c["id"] for c in created],  # 所有导入成功的题目ID
            "errors": errors,
            "skippedDetails": skipped
        }
    )
