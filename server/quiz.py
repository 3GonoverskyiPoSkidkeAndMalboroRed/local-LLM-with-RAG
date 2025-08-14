from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, Integer
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import datetime
import json

from database import get_db
from models_db import Quiz, Question, UserQuizAttempt, UserAnswer, User, Department, Access
# ✅ Добавляем импорт для аутентификации
from routes.user_routes import get_current_user, require_admin, is_admin

router = APIRouter(prefix="/quiz", tags=["quiz"])

# Pydantic модели для запросов и ответов

class OptionBase(BaseModel):
    id: int
    text: str

class QuestionCreate(BaseModel):
    text: str
    question_type: str  # single_choice, multiple_choice, text
    options: Optional[List[Dict[str, Any]]] = None
    correct_answer: Optional[Any] = None
    order: Optional[int] = 0

class QuestionResponse(BaseModel):
    id: int
    text: str
    question_type: str
    options: Optional[List[Dict[str, Any]]] = None
    correct_answer: Optional[Any] = None
    order: int
    
    class Config:
        from_attributes = True

class QuizCreate(BaseModel):
    title: str
    description: Optional[str] = None
    is_test: bool = False
    department_id: Optional[int] = None
    access_level: Optional[int] = None
    questions: List[QuestionCreate]

class QuizResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    is_test: bool
    department_id: Optional[int] = None
    access_level: Optional[int] = None
    created_at: datetime.datetime
    questions: List[QuestionResponse]
    
    class Config:
        from_attributes = True

class QuizListItem(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    is_test: bool
    department_id: Optional[int] = None
    access_level: Optional[int] = None
    created_at: datetime.datetime
    question_count: int
    
    class Config:
        from_attributes = True

class UserAnswerCreate(BaseModel):
    question_id: int
    answer: Any  # Может быть строкой, числом или списком (в зависимости от типа вопроса)

class AttemptCreate(BaseModel):
    quiz_id: int
    answers: List[UserAnswerCreate]

class UserAnswerResponse(BaseModel):
    id: int
    question_id: int
    answer: Any
    is_correct: Optional[bool] = None
    
    class Config:
        from_attributes = True

class AttemptResponse(BaseModel):
    id: int
    user_id: int
    quiz_id: int
    started_at: datetime.datetime
    completed_at: Optional[datetime.datetime] = None
    score: Optional[int] = None
    answers: List[UserAnswerResponse]
    
    class Config:
        from_attributes = True

class AttemptListItem(BaseModel):
    id: int
    quiz_id: int
    quiz_title: str
    started_at: datetime.datetime
    completed_at: Optional[datetime.datetime] = None
    score: Optional[int] = None
    total_questions: int
    correct_answers: Optional[int] = None
    
    class Config:
        from_attributes = True

# Функции для работы с тестами и анкетами

def check_user_access(user_id: int, quiz: Quiz, db: Session) -> bool:
    """Проверяет, имеет ли пользователь доступ к тесту/анкете"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False
    
    # Если тест/анкета не имеет ограничений по отделу и уровню доступа
    if quiz.department_id is None and quiz.access_level is None:
        return True
    
    # Проверка по отделу
    if quiz.department_id is not None and user.department_id != quiz.department_id:
        return False
    
    # Проверка по уровню доступа
    if quiz.access_level is not None and user.access_id < quiz.access_level:
        return False
    
    return True

def calculate_score(attempt_id: int, db: Session) -> int:
    """Рассчитывает количество баллов за тест"""
    attempt = db.query(UserQuizAttempt).filter(UserQuizAttempt.id == attempt_id).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Попытка не найдена")
    
    quiz = db.query(Quiz).filter(Quiz.id == attempt.quiz_id).first()
    if not quiz.is_test:
        return None  # Для анкет нет баллов
    
    correct_answers = db.query(UserAnswer).filter(
        UserAnswer.attempt_id == attempt_id,
        UserAnswer.is_correct == True
    ).count()
    
    return correct_answers

# Эндпоинты для работы с тестами и анкетами

@router.post("/create", response_model=QuizResponse, status_code=status.HTTP_201_CREATED)
def create_quiz(
    quiz_data: QuizCreate, 
    db: Session = Depends(get_db),
    # ✅ Добавляем аутентификацию - только админы могут создавать тесты
    current_user: User = Depends(require_admin)
):
    """Создание нового теста или анкеты (только для администраторов)"""
    # Проверка существования отдела и уровня доступа, если указаны
    if quiz_data.department_id:
        department = db.query(Department).filter(Department.id == quiz_data.department_id).first()
        if not department:
            raise HTTPException(status_code=404, detail="Указанный отдел не найден")
    
    if quiz_data.access_level:
        access = db.query(Access).filter(Access.id == quiz_data.access_level).first()
        if not access:
            raise HTTPException(status_code=404, detail="Указанный уровень доступа не найден")
    
    # Создаем новый тест/анкету
    new_quiz = Quiz(
        title=quiz_data.title,
        description=quiz_data.description,
        is_test=quiz_data.is_test,
        department_id=quiz_data.department_id,
        access_level=quiz_data.access_level
    )
    
    db.add(new_quiz)
    db.flush()  # Чтобы получить ID нового теста/анкеты
    
    # Добавляем вопросы
    for i, question_data in enumerate(quiz_data.questions):
        # Преобразуем options и correct_answer в JSON, если они есть
        options_json = None
        if question_data.options:
            options_json = question_data.options
        
        correct_answer_json = None
        if question_data.correct_answer is not None:
            correct_answer_json = question_data.correct_answer
        
        new_question = Question(
            quiz_id=new_quiz.id,
            text=question_data.text,
            question_type=question_data.question_type,
            options=options_json,
            correct_answer=correct_answer_json,
            order=question_data.order or i
        )
        db.add(new_question)
    
    db.commit()
    
    # Получаем созданный тест/анкету со всеми вопросами
    created_quiz = db.query(Quiz).filter(Quiz.id == new_quiz.id).first()
    questions = db.query(Question).filter(Question.quiz_id == new_quiz.id).order_by(Question.order).all()
    
    # Формируем ответ
    result = QuizResponse(
        id=created_quiz.id,
        title=created_quiz.title,
        description=created_quiz.description,
        is_test=created_quiz.is_test,
        department_id=created_quiz.department_id,
        access_level=created_quiz.access_level,
        created_at=created_quiz.created_at,
        questions=[
            QuestionResponse(
                id=q.id,
                text=q.text,
                question_type=q.question_type,
                options=q.options,
                correct_answer=q.correct_answer,
                order=q.order
            ) for q in questions
        ]
    )
    
    return result

@router.get("/list", response_model=List[QuizListItem])
def list_quizzes(
    # ✅ Убираем user_id из параметров - используем текущего пользователя
    is_test: Optional[bool] = None,
    department_id: Optional[int] = None,
    db: Session = Depends(get_db),
    # ✅ Добавляем аутентификацию
    current_user: User = Depends(get_current_user)
):
    """Получение списка тестов и анкет с учетом прав доступа пользователя"""
    # ✅ Используем текущего пользователя вместо user_id из параметров
    user = current_user
    
    # Базовый запрос
    query = db.query(
        Quiz,
        func.count(Question.id).label("question_count")
    ).outerjoin(Question, Quiz.id == Question.quiz_id).group_by(Quiz.id)
    
    # ✅ Добавляем проверку прав доступа
    # Админ видит все тесты, обычный пользователь только доступные ему
    if not is_admin(user):
        # Пользователь видит только тесты для своего отдела и уровня доступа
        query = query.filter(
            (Quiz.department_id == user.department_id) | (Quiz.department_id.is_(None))
        ).filter(
            (Quiz.access_level == user.access_id) | (Quiz.access_level.is_(None))
        )
    
    # Фильтр по типу (тест или анкета)
    if is_test is not None:
        query = query.filter(Quiz.is_test == is_test)
    
    # Фильтр по отделу
    if department_id is not None:
        query = query.filter(Quiz.department_id == department_id)
    
    # Выполняем запрос
    results = query.all()
    
    # Формируем ответ
    quiz_list = []
    for quiz, question_count in results:
        quiz_list.append(QuizListItem(
            id=quiz.id,
            title=quiz.title,
            description=quiz.description,
            is_test=quiz.is_test,
            department_id=quiz.department_id,
            access_level=quiz.access_level,
            created_at=quiz.created_at,
            question_count=question_count
        ))
    
    return quiz_list

@router.get("/{quiz_id}", response_model=QuizResponse)
def get_quiz(
    quiz_id: int, 
    # ✅ Убираем user_id из параметров
    db: Session = Depends(get_db),
    # ✅ Добавляем аутентификацию
    current_user: User = Depends(get_current_user)
):
    """Получение конкретного теста или анкеты"""
    # ✅ Используем текущего пользователя
    user = current_user
    
    # Получаем тест/анкету
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Тест или анкета не найдены")
    
    # ✅ Добавляем проверку прав доступа
    if not is_admin(user):
        # Проверяем доступ пользователя к тесту
        if quiz.department_id and quiz.department_id != user.department_id:
            raise HTTPException(status_code=403, detail="Нет доступа к этому тесту")
        
        if quiz.access_level and quiz.access_level != user.access_id:
            raise HTTPException(status_code=403, detail="Нет доступа к этому тесту")
    
    # Получаем вопросы
    questions = db.query(Question).filter(Question.quiz_id == quiz_id).order_by(Question.order).all()
    
    # ✅ Скрываем правильные ответы для обычных пользователей
    questions_response = []
    for q in questions:
        question_data = {
            "id": q.id,
            "text": q.text,
            "question_type": q.question_type,
            "options": q.options,
            "order": q.order
        }
        
        # Показываем правильные ответы только админам или если это не тест
        if is_admin(user) or not quiz.is_test:
            question_data["correct_answer"] = q.correct_answer
        
        questions_response.append(QuestionResponse(**question_data))
    
    return QuizResponse(
        id=quiz.id,
        title=quiz.title,
        description=quiz.description,
        is_test=quiz.is_test,
        department_id=quiz.department_id,
        access_level=quiz.access_level,
        created_at=quiz.created_at,
        questions=questions_response
    )

@router.post("/attempt", response_model=AttemptResponse, status_code=status.HTTP_201_CREATED)
def submit_attempt(
    attempt_data: AttemptCreate, 
    # ✅ Убираем user_id из параметров
    db: Session = Depends(get_db),
    # ✅ Добавляем аутентификацию
    current_user: User = Depends(get_current_user)
):
    """Отправка ответов на тест или анкету"""
    # ✅ Используем текущего пользователя
    user = current_user
    
    # Получаем тест/анкету
    quiz = db.query(Quiz).filter(Quiz.id == attempt_data.quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Тест или анкета не найдены")
    
    # ✅ Добавляем проверку прав доступа
    if not is_admin(user):
        if quiz.department_id and quiz.department_id != user.department_id:
            raise HTTPException(status_code=403, detail="Нет доступа к этому тесту")
        
        if quiz.access_level and quiz.access_level != user.access_id:
            raise HTTPException(status_code=403, detail="Нет доступа к этому тесту")
    
    # Проверяем, не проходил ли пользователь этот тест ранее
    existing_attempt = db.query(UserQuizAttempt).filter(
        UserQuizAttempt.user_id == user.id,
        UserQuizAttempt.quiz_id == attempt_data.quiz_id
    ).first()
    
    if existing_attempt:
        raise HTTPException(status_code=400, detail="Вы уже проходили этот тест")
    
    # Создаем новую попытку
    new_attempt = UserQuizAttempt(
        user_id=user.id,
        quiz_id=attempt_data.quiz_id,
        started_at=datetime.datetime.utcnow(),
        completed_at=datetime.datetime.utcnow()
    )
    
    db.add(new_attempt)
    db.flush()
    
    # Обрабатываем ответы
    answers = []
    total_score = 0
    total_questions = 0
    
    for answer_data in attempt_data.answers:
        # Получаем вопрос
        question = db.query(Question).filter(Question.id == answer_data.question_id).first()
        if not question:
            raise HTTPException(status_code=404, detail=f"Вопрос с ID {answer_data.question_id} не найден")
        
        # Проверяем, что вопрос принадлежит этому тесту
        if question.quiz_id != attempt_data.quiz_id:
            raise HTTPException(status_code=400, detail="Вопрос не принадлежит этому тесту")
        
        # Проверяем правильность ответа (только для тестов)
        is_correct = None
        if quiz.is_test and question.correct_answer is not None:
            is_correct = answer_data.answer == question.correct_answer
            if is_correct:
                total_score += 1
            total_questions += 1
        
        # Создаем запись ответа
        new_answer = UserAnswer(
            attempt_id=new_attempt.id,
            question_id=answer_data.question_id,
            answer=answer_data.answer,
            is_correct=is_correct
        )
        
        db.add(new_answer)
        answers.append(new_answer)
    
    # Обновляем результат попытки (только для тестов)
    if quiz.is_test and total_questions > 0:
        new_attempt.score = int((total_score / total_questions) * 100)
    
    db.commit()
    
    # Формируем ответ
    return AttemptResponse(
        id=new_attempt.id,
        user_id=new_attempt.user_id,
        quiz_id=new_attempt.quiz_id,
        started_at=new_attempt.started_at,
        completed_at=new_attempt.completed_at,
        score=new_attempt.score,
        answers=[
            UserAnswerResponse(
                id=answer.id,
                question_id=answer.question_id,
                answer=answer.answer,
                is_correct=answer.is_correct
            ) for answer in answers
        ]
    )

@router.get("/attempts/{user_id}", response_model=List[AttemptListItem])
def get_user_attempts(
    user_id: int, 
    quiz_id: Optional[int] = None, 
    db: Session = Depends(get_db),
    # ✅ Добавляем аутентификацию
    current_user: User = Depends(get_current_user)
):
    """Получение попыток пользователя"""
    # ✅ Проверяем права: пользователь может видеть только свои попытки или админ
    if not (is_admin(current_user) or current_user.id == user_id):
        raise HTTPException(status_code=403, detail="Недостаточно прав для просмотра попыток другого пользователя")
    
    # Получаем попытки
    query = db.query(UserQuizAttempt).filter(UserQuizAttempt.user_id == user_id)
    
    if quiz_id:
        query = query.filter(UserQuizAttempt.quiz_id == quiz_id)
    
    attempts = query.all()
    
    # Формируем ответ
    attempt_list = []
    for attempt in attempts:
        # Получаем информацию о тесте
        quiz = db.query(Quiz).filter(Quiz.id == attempt.quiz_id).first()
        
        attempt_list.append(AttemptListItem(
            id=attempt.id,
            quiz_title=quiz.title if quiz else "Неизвестный тест",
            started_at=attempt.started_at,
            completed_at=attempt.completed_at,
            score=attempt.score
        ))
    
    return attempt_list

@router.get("/attempt/{attempt_id}", response_model=AttemptResponse)
def get_attempt_details(
    attempt_id: int, 
    # ✅ Убираем user_id из параметров
    db: Session = Depends(get_db),
    # ✅ Добавляем аутентификацию
    current_user: User = Depends(get_current_user)
):
    """Получение деталей конкретной попытки"""
    # ✅ Используем текущего пользователя
    user = current_user
    
    # Получаем попытку
    attempt = db.query(UserQuizAttempt).filter(UserQuizAttempt.id == attempt_id).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Попытка не найдена")
    
    # ✅ Проверяем права: пользователь может видеть только свои попытки или админ
    if not (is_admin(user) or attempt.user_id == user.id):
        raise HTTPException(status_code=403, detail="Недостаточно прав для просмотра этой попытки")
    
    # Получаем ответы
    answers = db.query(UserAnswer).filter(UserAnswer.attempt_id == attempt_id).all()
    
    return AttemptResponse(
        id=attempt.id,
        user_id=attempt.user_id,
        quiz_id=attempt.quiz_id,
        started_at=attempt.started_at,
        completed_at=attempt.completed_at,
        score=attempt.score,
        answers=[
            UserAnswerResponse(
                id=answer.id,
                question_id=answer.question_id,
                answer=answer.answer,
                is_correct=answer.is_correct
            ) for answer in answers
        ]
    )

@router.get("/stats/{quiz_id}")
def get_quiz_statistics(
    quiz_id: int, 
    db: Session = Depends(get_db),
    # ✅ Добавляем аутентификацию - только админы
    current_user: User = Depends(require_admin)
):
    """Получение статистики по тесту (только для администраторов)"""
    # Получаем тест
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Тест не найден")
    
    # Получаем все попытки
    attempts = db.query(UserQuizAttempt).filter(UserQuizAttempt.quiz_id == quiz_id).all()
    
    if not attempts:
        return {
            "quiz_id": quiz_id,
            "total_attempts": 0,
            "average_score": 0,
            "min_score": 0,
            "max_score": 0,
            "completion_rate": 0
        }
    
    # Вычисляем статистику
    scores = [attempt.score for attempt in attempts if attempt.score is not None]
    
    stats = {
        "quiz_id": quiz_id,
        "total_attempts": len(attempts),
        "completed_attempts": len(scores),
        "average_score": sum(scores) / len(scores) if scores else 0,
        "min_score": min(scores) if scores else 0,
        "max_score": max(scores) if scores else 0,
        "completion_rate": (len(scores) / len(attempts)) * 100 if attempts else 0
    }
    
    return stats

@router.delete("/{quiz_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_quiz(
    quiz_id: int, 
    # ✅ Убираем user_id из параметров
    db: Session = Depends(get_db),
    # ✅ Добавляем аутентификацию - только админы
    current_user: User = Depends(require_admin)
):
    """Удаление теста или анкеты (только для администраторов)"""
    # ✅ Используем текущего пользователя
    user = current_user
    
    # Получаем тест
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Тест не найден")
    
    # Удаляем тест (каскадное удаление через SQLAlchemy)
    db.delete(quiz)
    db.commit()

@router.get("/admin/list", response_model=List[QuizListItem])
def admin_list_quizzes(
    db: Session = Depends(get_db),
    # ✅ Добавляем аутентификацию - только админы
    current_user: User = Depends(require_admin)
):
    """Получение списка всех тестов (только для администраторов)"""
    # Получаем все тесты
    results = db.query(
        Quiz,
        func.count(Question.id).label("question_count")
    ).outerjoin(Question, Quiz.id == Question.quiz_id).group_by(Quiz.id).all()
    
    # Формируем ответ
    quiz_list = []
    for quiz, question_count in results:
        quiz_list.append(QuizListItem(
            id=quiz.id,
            title=quiz.title,
            description=quiz.description,
            is_test=quiz.is_test,
            department_id=quiz.department_id,
            access_level=quiz.access_level,
            created_at=quiz.created_at,
            question_count=question_count
        ))
    
    return quiz_list 