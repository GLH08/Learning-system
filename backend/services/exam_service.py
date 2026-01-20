"""
考试服务 - 智能组卷算法
"""
import random
import json
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from models.question import Question
from models.exam import Exam


class ExamConfig:
    """组卷配置"""
    def __init__(
        self,
        title: str = "快速测试",
        mode: str = "exam",
        category_ids: Optional[List[str]] = None,
        question_types: Optional[List[str]] = None,
        difficulties: Optional[List[str]] = None,
        type_counts: Optional[Dict[str, int]] = None,
        time_limit: Optional[int] = None,
        shuffle_options: bool = True,
        shuffle_questions: bool = True
    ):
        self.title = title
        self.mode = mode  # exam/practice/review
        self.category_ids = category_ids or []
        self.question_types = question_types or []
        self.difficulties = difficulties or []
        self.type_counts = type_counts or {}  # {type: count}
        self.time_limit = time_limit
        self.shuffle_options = shuffle_options
        self.shuffle_questions = shuffle_questions


class ExamService:
    """考试服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def generate_quick_exam(
        self,
        count: int = 20,
        shuffle_options: bool = True
    ) -> Exam:
        """
        快速组卷 - 随机选择题目
        
        Args:
            count: 题目数量
            shuffle_options: 是否打乱选项
        
        Returns:
            Exam: 考试记录
        """
        config = ExamConfig(
            title="快速测试",
            mode="practice",
            shuffle_options=shuffle_options,
            shuffle_questions=True
        )
        
        # 查询所有已完成的题目（answer_status 不为 none）
        questions = self.db.query(Question).filter(
            Question.answer_status != "none"
        ).all()
        
        if len(questions) < count:
            raise ValueError(f"题库中只有 {len(questions)} 道题目有答案，无法生成 {count} 道题的试卷。请先补全题目答案。")
        
        # 随机选择题目
        selected = random.sample(questions, count)
        
        return self._create_exam(config, selected)
    
    def generate_custom_exam(self, config: ExamConfig) -> Exam:
        """
        自定义组卷 - 按条件筛选题目
        
        Args:
            config: 组卷配置
        
        Returns:
            Exam: 考试记录
        """
        # 构建查询条件 - 只选择有答案的题目
        filters = [
            Question.answer_status != "none"
        ]
        
        # 分类筛选
        if config.category_ids:
            filters.append(Question.category_id.in_(config.category_ids))
        
        # 题型筛选
        if config.question_types:
            filters.append(Question.type.in_(config.question_types))
        
        # 难度筛选
        if config.difficulties:
            filters.append(Question.difficulty.in_(config.difficulties))
        
        # 查询符合条件的题目
        questions = self.db.query(Question).filter(and_(*filters)).all()
        
        # 按题型分组
        questions_by_type = {}
        for q in questions:
            if q.type not in questions_by_type:
                questions_by_type[q.type] = []
            questions_by_type[q.type].append(q)
        
        # 按配置选择题目
        selected = []
        
        if config.type_counts:
            # 按题型数量选择
            for qtype, count in config.type_counts.items():
                if qtype not in questions_by_type:
                    raise ValueError(f"没有找到类型为 {qtype} 的题目")
                
                available = questions_by_type[qtype]
                if len(available) < count:
                    raise ValueError(f"类型 {qtype} 只有 {len(available)} 道题目，无法选择 {count} 道")
                
                selected.extend(random.sample(available, count))
        else:
            # 随机选择所有符合条件的题目
            if not questions:
                raise ValueError("没有找到符合条件的题目")
            selected = questions
        
        return self._create_exam(config, selected)
    
    def _create_exam(self, config: ExamConfig, questions: List[Question]) -> Exam:
        """
        创建考试记录
        
        Args:
            config: 组卷配置
            questions: 题目列表
        
        Returns:
            Exam: 考试记录
        """
        # 打乱题目顺序
        if config.shuffle_questions:
            random.shuffle(questions)
        
        # 打乱选项顺序
        question_ids = []
        for q in questions:
            question_ids.append(q.id)
            
            if config.shuffle_options and q.options:
                try:
                    options = json.loads(q.options)
                    if isinstance(options, dict):
                        # 保存原始答案
                        original_answer = q.answer
                        
                        # 获取选项列表
                        items = list(options.items())
                        random.shuffle(items)
                        
                        # 创建新的选项映射
                        new_options = {}
                        answer_mapping = {}
                        labels = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
                        
                        for i, (old_label, value) in enumerate(items):
                            new_label = labels[i]
                            new_options[new_label] = value
                            answer_mapping[old_label] = new_label
                        
                        # 更新选项
                        q.options = json.dumps(new_options, ensure_ascii=False)
                        
                        # 更新答案映射
                        if q.type == "single":
                            q.answer = answer_mapping.get(original_answer, original_answer)
                        elif q.type == "multiple":
                            # 多选题答案可能是 "ABC" 或 "A,B,C"
                            if "," in original_answer:
                                old_answers = original_answer.split(",")
                                new_answers = [answer_mapping.get(a.strip(), a.strip()) for a in old_answers]
                                q.answer = ",".join(sorted(new_answers))
                            else:
                                new_answers = [answer_mapping.get(a, a) for a in original_answer]
                                q.answer = "".join(sorted(new_answers))
                except:
                    pass
        
        # 计算总分（每题1分）
        total_score = len(questions)
        
        # 创建考试记录
        exam = Exam(
            title=config.title,
            mode=config.mode,
            config=json.dumps({
                "category_ids": config.category_ids,
                "question_types": config.question_types,
                "difficulties": config.difficulties,
                "type_counts": config.type_counts,
                "shuffle_options": config.shuffle_options,
                "shuffle_questions": config.shuffle_questions
            }, ensure_ascii=False),
            question_ids=json.dumps(question_ids),
            total_count=len(questions),
            total_score=total_score,
            time_limit=config.time_limit,
            status="in_progress"
        )
        
        self.db.add(exam)
        self.db.commit()
        self.db.refresh(exam)
        
        return exam
    
    def get_exam_questions(self, exam: Exam) -> List[Question]:
        """
        获取考试题目列表
        
        Args:
            exam: 考试记录
        
        Returns:
            List[Question]: 题目列表
        """
        question_ids = json.loads(exam.question_ids)
        questions = self.db.query(Question).filter(Question.id.in_(question_ids)).all()
        
        # 按照试卷中的顺序排序
        question_map = {q.id: q for q in questions}
        ordered_questions = [question_map[qid] for qid in question_ids if qid in question_map]
        
        return ordered_questions

    
    def generate_wrong_question_exam(
        self,
        title: str = "错题专项练习",
        mode: str = "practice",
        mastered: Optional[int] = None,
        limit: Optional[int] = None
    ) -> Exam:
        """
        生成错题试卷
        
        Args:
            title: 试卷标题
            mode: 答题模式
            mastered: 掌握状态筛选（0: 未掌握, 1: 已掌握, None: 全部）
            limit: 题目数量限制
        
        Returns:
            Exam: 考试记录
        """
        from models.exam import WrongQuestion
        
        # 查询错题
        query = self.db.query(WrongQuestion)
        
        if mastered is not None:
            query = query.filter(WrongQuestion.mastered == mastered)
        
        wrong_questions = query.all()
        
        if not wrong_questions:
            raise ValueError("没有找到错题")
        
        # 获取题目ID
        question_ids = [wq.question_id for wq in wrong_questions]
        
        # 限制数量
        if limit and len(question_ids) > limit:
            import random
            question_ids = random.sample(question_ids, limit)
        
        # 获取题目
        questions = self.db.query(Question).filter(Question.id.in_(question_ids)).all()
        
        if not questions:
            raise ValueError("错题对应的题目不存在")
        
        # 创建配置
        config = ExamConfig(
            title=title,
            mode=mode,
            shuffle_questions=True,
            shuffle_options=True
        )
        
        return self._create_exam(config, questions)
