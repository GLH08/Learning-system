from fastapi import APIRouter

from api import auth, categories, questions, ai, exams, wrong_questions, stats, settings

api_router = APIRouter()

# Include sub-routers
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(categories.router, prefix="/categories", tags=["分类"])
api_router.include_router(questions.router, prefix="/questions", tags=["题目"])
api_router.include_router(ai.router, prefix="/ai", tags=["AI"])
api_router.include_router(exams.router, tags=["考试"])
api_router.include_router(wrong_questions.router, tags=["错题本"])
api_router.include_router(stats.router, tags=["统计"])
api_router.include_router(settings.router, tags=["设置"])
