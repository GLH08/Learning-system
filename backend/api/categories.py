from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from models.database import get_db
from models.category import Category
from models.question import Question
from schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse
from schemas.common import Response
from utils.security import get_current_user
from utils.exceptions import NotFoundError

router = APIRouter()


def build_category_tree(categories: List[Category], parent_id: str = None) -> List[dict]:
    """Build category tree structure"""
    tree = []
    for cat in categories:
        if cat.parent_id == parent_id:
            # Count questions
            question_count = len(cat.questions) if cat.questions else 0
            
            # Build node
            node = {
                "id": cat.id,
                "name": cat.name,
                "parentId": cat.parent_id,
                "description": cat.description,
                "sortOrder": cat.sort_order,
                "questionCount": question_count,
                "createdAt": cat.created_at,
                "updatedAt": cat.updated_at,
                "children": build_category_tree(categories, cat.id)
            }
            tree.append(node)
    
    # Sort by sort_order
    tree.sort(key=lambda x: x["sortOrder"])
    return tree


@router.get("", response_model=Response[List[CategoryResponse]])
async def get_categories(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get category tree"""
    categories = db.query(Category).all()
    tree = build_category_tree(categories)
    
    return Response(code=0, message="success", data=tree)


@router.get("/{category_id}", response_model=Response[CategoryResponse])
async def get_category(
    category_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get category details"""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise NotFoundError("分类不存在")
    
    question_count = db.query(Question).filter(Question.category_id == category_id).count()
    
    return Response(
        code=0,
        message="success",
        data={
            "id": category.id,
            "name": category.name,
            "parentId": category.parent_id,
            "description": category.description,
            "sortOrder": category.sort_order,
            "questionCount": question_count,
            "createdAt": category.created_at,
            "updatedAt": category.updated_at,
            "children": []
        }
    )


@router.post("", response_model=Response[CategoryResponse])
async def create_category(
    category: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create category"""
    # Check if parent exists
    if category.parentId:
        parent = db.query(Category).filter(Category.id == category.parentId).first()
        if not parent:
            raise NotFoundError("父分类不存在")
    
    # Create category
    db_category = Category(
        name=category.name,
        parent_id=category.parentId,
        description=category.description,
        sort_order=category.sortOrder
    )
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    
    return Response(
        code=0,
        message="创建成功",
        data={
            "id": db_category.id,
            "name": db_category.name,
            "parentId": db_category.parent_id,
            "description": db_category.description,
            "sortOrder": db_category.sort_order,
            "questionCount": 0,
            "createdAt": db_category.created_at,
            "updatedAt": db_category.updated_at,
            "children": []
        }
    )


@router.put("/{category_id}", response_model=Response[CategoryResponse])
async def update_category(
    category_id: str,
    category: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update category"""
    db_category = db.query(Category).filter(Category.id == category_id).first()
    if not db_category:
        raise NotFoundError("分类不存在")
    
    # Update fields
    if category.name is not None:
        db_category.name = category.name
    if category.parentId is not None:
        # Check if parent exists
        if category.parentId:
            parent = db.query(Category).filter(Category.id == category.parentId).first()
            if not parent:
                raise NotFoundError("父分类不存在")
        db_category.parent_id = category.parentId
    if category.description is not None:
        db_category.description = category.description
    if category.sortOrder is not None:
        db_category.sort_order = category.sortOrder
    
    db.commit()
    db.refresh(db_category)
    
    question_count = db.query(Question).filter(Question.category_id == category_id).count()
    
    return Response(
        code=0,
        message="更新成功",
        data={
            "id": db_category.id,
            "name": db_category.name,
            "parentId": db_category.parent_id,
            "description": db_category.description,
            "sortOrder": db_category.sort_order,
            "questionCount": question_count,
            "createdAt": db_category.created_at,
            "updatedAt": db_category.updated_at,
            "children": []
        }
    )


@router.delete("/{category_id}", response_model=Response)
async def delete_category(
    category_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete category"""
    if category_id == "default":
        raise NotFoundError("默认分类不能删除")
    
    db_category = db.query(Category).filter(Category.id == category_id).first()
    if not db_category:
        raise NotFoundError("分类不存在")
    
    # Move questions to default category
    moved_count = db.query(Question).filter(Question.category_id == category_id).update(
        {"category_id": "default"}
    )
    
    # Delete category
    db.delete(db_category)
    db.commit()
    
    return Response(
        code=0,
        message=f"删除成功，该分类下的{moved_count}道题目已移至未分类",
        data={"movedQuestions": moved_count}
    )
