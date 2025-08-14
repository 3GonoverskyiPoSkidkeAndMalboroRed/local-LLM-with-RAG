from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, status, Request
from fastapi.security import OAuth2PasswordBearer
import secrets
from passlib.context import CryptContext
import os
from datetime import datetime, timedelta
import jwt
from slowapi import Limiter
from slowapi.util import get_remote_address

from sqlalchemy.orm import Session
from database import get_db
from models_db import Access, Content, User, Department
from pydantic import BaseModel
from dotenv import load_dotenv

# Загружаем переменные окружения из .env, если запускается локально
load_dotenv()

router = APIRouter(prefix="/user", tags=["user"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# Настройки JWT (жёсткая проверка наличия переменных окружения)
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")
_JWT_EXPIRE_MINUTES_RAW = os.getenv("JWT_EXPIRE_MINUTES")

if not JWT_SECRET or not JWT_ALGORITHM or _JWT_EXPIRE_MINUTES_RAW is None:
    raise RuntimeError(
        "Отсутствуют обязательные переменные окружения JWT: требуется JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRE_MINUTES"
    )

try:
    ACCESS_TOKEN_EXPIRE_MINUTES = int(_JWT_EXPIRE_MINUTES_RAW)
except ValueError as e:
    raise RuntimeError("JWT_EXPIRE_MINUTES должен быть целым числом") from e

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/user/login")


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось проверить учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Срок действия токена истек",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise credentials_exception

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    return user


# Админ-помощники
def is_admin(user: User) -> bool:
    # Принято считать роль администратора role_id = 1
    return int(user.role_id or 0) == 1


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if not is_admin(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Доступ только для администраторов")
    return current_user

class UserCreate(BaseModel):
    login: str
    password: str
    role_id: int
    department_id: int
    access_id: int
    full_name: str = None

@router.post("/register")
async def register(user: UserCreate, db: Session = Depends(get_db)):
    # Проверка существования пользователя
    existing_user = db.query(User).filter(User.login == user.login).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Пользователь уже существует")

    # Хеширование пароля
    hashed_password = pwd_context.hash(user.password)
    new_user = User(
        login=user.login,
        password=hashed_password,
        role_id=user.role_id,
        department_id=user.department_id,
        access_id=user.access_id,
        full_name=user.full_name
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "Пользователь успешно зарегистрирован"}

class UserLogin(BaseModel):
    login: str
    password: str

def generate_auth_key() -> str:
    """Генерация случайного ключа аутентификации."""
    return secrets.token_hex(16)

@router.post("/login")
@limiter.limit("5/minute")  # ✅ Уже есть - строгий лимит для входа
async def login(request: Request, user_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.login == user_data.login).first()
    if not user or not user.check_password(user_data.password):
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")
    
    # Генерация JWT токена
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "login": user.login,
            "role_id": user.role_id,
            "department_id": user.department_id,
            "access_id": user.access_id,
        }
    )

    # Для обратной совместимости можно оставить auth_key (если используется где-то ещё)
    auth_key = generate_auth_key()
    user.auth_key = auth_key
    db.commit()

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "login": user.login,
            "role_id": user.role_id,
            "department_id": user.department_id,
            "access_id": user.access_id,
            "full_name": user.full_name,
        },
        "auth_key": auth_key,
        # Дублируем некоторые поля для обратной совместимости фронтенда
        "id": user.id,
        "role_id": user.role_id,
        "department_id": user.department_id,
    }

@router.get("/user/{id}")
@limiter.limit("60/minute")  # ✅ Умеренный лимит для получения информации о пользователе
async def get_user(request: Request, id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # Получаем название отдела
    department = db.query(Department).filter(Department.id == user.department_id).first()
    department_name = department.department_name if department else "Неизвестный отдел"

    # Получаем название доступа
    access = db.query(Access).filter(Access.id == user.access_id).first()
    access_name = access.access_name if access else "Неизвестный доступ"

    return {
        "login": user.login,
        "role_id": user.role_id,
        "department_name": department_name,
        "access_name": access_name,
        "full_name": user.full_name
    }

@router.get("/me")
@limiter.limit("120/minute")  # ✅ Высокий лимит для получения собственного профиля
async def read_current_user(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    department = db.query(Department).filter(Department.id == current_user.department_id).first()
    department_name = department.department_name if department else "Неизвестный отдел"

    access = db.query(Access).filter(Access.id == current_user.access_id).first()
    access_name = access.access_name if access else "Неизвестный доступ"

    return {
        "id": current_user.id,
        "login": current_user.login,
        "role_id": current_user.role_id,
        "department_id": current_user.department_id,
        "department_name": department_name,
        "access_id": current_user.access_id,
        "access_name": access_name,
        "full_name": current_user.full_name,
    }

@router.get("/user/{user_id}/content")
@limiter.limit("100/minute")  # ✅ Высокий лимит для получения контента
async def get_user_content(
    request: Request,
    user_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Проверяем права: пользователь может получить только свой контент или админ
    if not (is_admin(current_user) or current_user.id == user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав для доступа к контенту другого пользователя")
    try:
        # Получаем пользователя по user_id
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise HTTPException(status_code=404, detail="Пользователь не найден")

        # Получаем контент из базы данных по access_level и department_id пользователя
        contents = db.query(Content).filter(
            Content.access_level == user.access_id,
            Content.department_id == user.department_id
        ).all()

        print(f"Access Level: {user.access_id}, Department ID: {user.department_id}")  # Отладочное сообщение
        print(f"Found contents: {len(contents)}")  # Количество найденного контента

        if not contents:
            raise HTTPException(status_code=404, detail="Контент не найден")

        result = []
        for content in contents:
            # Получаем название отдела
            department = db.query(Department).filter(Department.id == content.department_id).first()
            department_name = department.department_name if department else "Неизвестный отдел"
            
            # Получаем название уровня доступа
            access = db.query(Access).filter(Access.id == content.access_level).first()
            access_name = access.access_name if access else "Неизвестный уровень"
            
            result.append({
                "id": content.id,
                "title": content.title,
                "description": content.description,
                "file_path": content.file_path,
                "department_id": content.department_id,
                "department_name": department_name,
                "access_level": content.access_level,
                "access_name": access_name
            })
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении контента: {str(e)}")

@router.get("/users")
@limiter.limit("30/minute")  # ✅ Умеренный лимит для получения списка пользователей
async def get_users(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    try:
        users = db.query(User).all()  # Получаем всех пользователей из базы данных
        user_list = []
        
        for user in users:
            # Получаем название отдела
            department = db.query(Department).filter(Department.id == user.department_id).first()
            department_name = department.department_name if department else "Неизвестный отдел"

            # Получаем название доступа
            access = db.query(Access).filter(Access.id == user.access_id).first()
            access_name = access.access_name if access else "Неизвестный доступ"

            user_list.append({
                "id": user.id,
                "login": user.login,
                "role_id": user.role_id,
                "department_name": department_name,
                "access_name": access_name,
                "full_name": user.full_name
            })

        return user_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении пользователей: {str(e)}")

@router.put("/user/{user_id}")
@limiter.limit("20/minute")  # ✅ Умеренный лимит для обновления пользователей
async def update_user(
    request: Request,
    user_id: int, 
    user_data: dict, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Проверяем права: пользователь может изменять только свои данные или админ
    if not (is_admin(current_user) or current_user.id == user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав для изменения данных другого пользователя")
    try:
        # Получаем пользователя по ID
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        
        # Обновляем данные пользователя
        if "department_id" in user_data:
            user.department_id = user_data["department_id"]
        
        if "access_id" in user_data:
            user.access_id = user_data["access_id"]
            
        # Сохраняем изменения
        db.commit()
        db.refresh(user)
        
        return {"message": "Данные пользователя успешно обновлены"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при обновлении пользователя: {str(e)}")

@router.delete("/user/{user_id}")
@limiter.limit("10/minute")  # ✅ Строгий лимит для удаления пользователей
async def delete_user(
    request: Request,
    user_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    try:
        # Получаем пользователя по ID
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        
        # Удаляем пользователя
        db.delete(user)
        db.commit()
        
        return {"message": "Пользователь успешно удален"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при удалении пользователя: {str(e)}")

@router.put("/user/{user_id}/password")
@limiter.limit("5/minute")  # ✅ Строгий лимит для смены пароля
async def update_password(
    request: Request,
    user_id: int, 
    password_data: dict, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Проверяем права: пользователь может изменять только свой пароль или админ
    if not (is_admin(current_user) or current_user.id == user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав для изменения пароля другого пользователя")
    try:
        # Получаем пользователя по ID
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        
        # Хешируем новый пароль
        hashed_password = pwd_context.hash(password_data["password"])
        
        # Обновляем пароль пользователя
        user.password = hashed_password
        
        # Сохраняем изменения
        db.commit()
        
        return {"message": "Пароль пользователя успешно обновлен"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при обновлении пароля: {str(e)}")
