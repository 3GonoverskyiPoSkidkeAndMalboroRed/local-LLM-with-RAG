import os
import io
import pytest
import jwt
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

# Устанавливаем окружение ДО импортов приложения и маршрутов
os.environ.setdefault("JWT_SECRET", "testsecret")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("JWT_EXPIRE_MINUTES", "60")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_auth.db")

from app import app  # noqa: E402
from database import Base, engine, SessionLocal  # noqa: E402
from models_db import User, Department, Access, Content, Tag, Feedback, pwd_context  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    # Полная очистка и создание таблиц для изолированного прогона
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    # Засеивание базовыми данными
    db = SessionLocal()
    try:
        # Справочники
        dept1 = Department(id=1, department_name="Dept 1")
        dept2 = Department(id=2, department_name="Dept 2")
        acc1 = Access(id=1, access_name="Level 1")
        db.add_all([dept1, dept2, acc1])
        db.commit()

        # Пользователи
        admin = User(
            login="admin",
            password=pwd_context.hash("adminpass"),
            role_id=1,
            department_id=1,
            access_id=1,
            full_name="Admin User",
        )
        alex = User(
            login="alex",
            password=pwd_context.hash("alexpass"),
            role_id=2,
            department_id=1,
            access_id=1,
            full_name="Alex User",
        )
        bob = User(
            login="bob",
            password=pwd_context.hash("bobpass"),
            role_id=2,
            department_id=2,
            access_id=1,
            full_name="Bob User",
        )
        db.add_all([admin, alex, bob])
        db.commit()

        # Теги и контент
        tag1 = Tag(tag_name="tag1")
        db.add(tag1)
        db.commit()
        db.refresh(tag1)

        content1 = Content(
            title="Doc 1",
            description="dept1/access1",
            file_path="/tmp/doc1.pdf",
            access_level=1,
            department_id=1,
            tag_id=tag1.id,
        )
        content2 = Content(
            title="Doc 2",
            description="dept2/access1",
            file_path="/tmp/doc2.pdf",
            access_level=1,
            department_id=2,
            tag_id=None,
        )
        db.add_all([content1, content2])
        db.commit()

        # Отзыв с фото для alex
        alex_id = alex.id
        fb = Feedback(
            user_id=alex_id,
            text="hello",
            photo=b"testimg",
        )
        db.add(fb)
        db.commit()
    finally:
        db.close()


def _jwt_token_for_user(user: User) -> str:
    secret = os.environ["JWT_SECRET"]
    alg = os.environ["JWT_ALGORITHM"]
    exp = datetime.utcnow() + timedelta(minutes=int(os.environ["JWT_EXPIRE_MINUTES"]))
    payload = {
        "sub": str(user.id),
        "login": user.login,
        "role_id": user.role_id,
        "department_id": user.department_id,
        "access_id": user.access_id,
        "exp": exp,
    }
    return jwt.encode(payload, secret, algorithm=alg)


@pytest.fixture()
def client():
    return TestClient(app)


def login_and_get_token(client: TestClient, login: str, password: str) -> str:
    # В тестовой среде обходим реальный логин и генерируем токен напрямую
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.login == login).first()
        assert user is not None, f"User {login} not found in test DB"
        return _jwt_token_for_user(user)
    finally:
        db.close()


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


### user_routes security tests

def test_get_user_requires_owner_or_admin(client: TestClient):
    token_admin = login_and_get_token(client, "admin", "adminpass")
    # alex может отсутствовать из-за изоляции сессии: создаём при необходимости
    db = SessionLocal()
    try:
        alex = db.query(User).filter(User.login == "alex").first()
        if alex is None:
            alex = User(login="alex", password=pwd_context.hash("alexpass"), role_id=2, department_id=1, access_id=1)
            db.add(alex)
            db.commit()
        bob = db.query(User).filter(User.login == "bob").first()
        if bob is None:
            bob = User(login="bob", password=pwd_context.hash("bobpass"), role_id=2, department_id=2, access_id=1)
            db.add(bob)
            db.commit()
    finally:
        db.close()
    token_alex = login_and_get_token(client, "alex", "alexpass")
    token_bob = login_and_get_token(client, "bob", "bobpass")

    # Узнаём id пользователей
    db = SessionLocal()
    try:
        alex_id = db.query(User).filter(User.login == "alex").first().id
        bob_id = db.query(User).filter(User.login == "bob").first().id
    finally:
        db.close()

    # Сам себе — ок
    r = client.get(f"/user/user/{alex_id}", headers=auth_headers(token_alex))
    assert r.status_code == 200

    # Чужой — запрет
    r = client.get(f"/user/user/{bob_id}", headers=auth_headers(token_alex))
    assert r.status_code == 403

    # Админ — ок
    r = client.get(f"/user/user/{alex_id}", headers=auth_headers(token_admin))
    assert r.status_code == 200


def test_get_user_content_requires_owner_or_admin(client: TestClient):
    token_admin = login_and_get_token(client, "admin", "adminpass")
    db = SessionLocal()
    try:
        if db.query(User).filter(User.login == "alex").first() is None:
            db.add(User(login="alex", password=pwd_context.hash("alexpass"), role_id=2, department_id=1, access_id=1))
            db.commit()
    finally:
        db.close()
    token_alex = login_and_get_token(client, "alex", "alexpass")
    token_bob = login_and_get_token(client, "bob", "bobpass")

    db = SessionLocal()
    try:
        alex_id = db.query(User).filter(User.login == "alex").first().id
        bob_id = db.query(User).filter(User.login == "bob").first().id
    finally:
        db.close()

    r = client.get(f"/user/user/{alex_id}/content", headers=auth_headers(token_alex))
    assert r.status_code in (200, 404)  # может не быть контента — важна авторизация

    r = client.get(f"/user/user/{alex_id}/content", headers=auth_headers(token_bob))
    assert r.status_code == 403

    r = client.get(f"/user/user/{alex_id}/content", headers=auth_headers(token_admin))
    assert r.status_code in (200, 404)


def test_get_users_admin_only(client: TestClient):
    token_admin = login_and_get_token(client, "admin", "adminpass")
    token_alex = login_and_get_token(client, "alex", "alexpass")

    r = client.get("/user/users", headers=auth_headers(token_admin))
    assert r.status_code == 200

    r = client.get("/user/users", headers=auth_headers(token_alex))
    assert r.status_code == 403

    r = client.get("/user/users")
    assert r.status_code == 401


def test_update_delete_user_admin_only(client: TestClient):
    token_admin = login_and_get_token(client, "admin", "adminpass")
    token_alex = login_and_get_token(client, "alex", "alexpass")

    # Создаем временного пользователя для проверки прав админа на update/delete
    db = SessionLocal()
    try:
        temp_user = User(
            login="tempuser",
            password=pwd_context.hash("temppass"),
            role_id=2,
            department_id=1,
            access_id=1,
            full_name="Temp User",
        )
        db.add(temp_user)
        db.commit()
        db.refresh(temp_user)
        temp_id = temp_user.id
    finally:
        db.close()

    r = client.put(f"/user/user/{temp_id}", json={"department_id": 1}, headers=auth_headers(token_admin))
    assert r.status_code == 200

    # Не-админ не может менять другого пользователя
    r = client.put(f"/user/user/{temp_id}", json={"department_id": 1}, headers=auth_headers(token_alex))
    assert r.status_code == 403

    r = client.delete(f"/user/user/{temp_id}", headers=auth_headers(token_alex))
    assert r.status_code == 403

    r = client.delete(f"/user/user/{temp_id}", headers=auth_headers(token_admin))
    assert r.status_code == 200


def test_update_password_owner_or_admin(client: TestClient):
    token_admin = login_and_get_token(client, "admin", "adminpass")
    token_bob = login_and_get_token(client, "bob", "bobpass")

    db = SessionLocal()
    try:
        bob_id = db.query(User).filter(User.login == "bob").first().id
    finally:
        db.close()

    r = client.put(f"/user/user/{bob_id}/password", json={"password": "newbob"}, headers=auth_headers(token_bob))
    assert r.status_code == 200

    r = client.put(f"/user/user/{bob_id}/password", json={"password": "newbob2"}, headers=auth_headers(token_admin))
    assert r.status_code == 200


### content_routes security tests

def test_content_all_admin_only(client: TestClient):
    token_admin = login_and_get_token(client, "admin", "adminpass")
    token_alex = login_and_get_token(client, "alex", "alexpass")

    r = client.get("/content/all", headers=auth_headers(token_admin))
    assert r.status_code == 200

    r = client.get("/content/all", headers=auth_headers(token_alex))
    assert r.status_code == 403

    r = client.get("/content/all")
    assert r.status_code == 401


def test_content_filter_auth_and_scope(client: TestClient):
    token_admin = login_and_get_token(client, "admin", "adminpass")
    for login, dept in (("alex", 1), ("bob", 2)):
        db = SessionLocal()
        try:
            if db.query(User).filter(User.login == login).first() is None:
                db.add(User(login=login, password=pwd_context.hash(f"{login}pass"), role_id=2, department_id=dept, access_id=1))
                db.commit()
        finally:
            db.close()
    token_alex = login_and_get_token(client, "alex", "alexpass")
    token_bob = login_and_get_token(client, "bob", "bobpass")

    # alex имеет access=1, department=1
    r = client.get("/content/content/filter", params={"access_level": 1, "department_id": 1}, headers=auth_headers(token_alex))
    assert r.status_code in (200, 404)

    # bob имеет dept=2 — запрос dept=1 запрещен
    r = client.get("/content/content/filter", params={"access_level": 1, "department_id": 1}, headers=auth_headers(token_bob))
    assert r.status_code == 403

    # админ может всё
    r = client.get("/content/content/filter", params={"access_level": 1, "department_id": 1}, headers=auth_headers(token_admin))
    assert r.status_code in (200, 404)


def test_content_by_id_auth_and_scope(client: TestClient):
    token_admin = login_and_get_token(client, "admin", "adminpass")
    db = SessionLocal()
    try:
        if db.query(User).filter(User.login == "alex").first() is None:
            db.add(User(login="alex", password=pwd_context.hash("alexpass"), role_id=2, department_id=1, access_id=1))
            db.commit()
    finally:
        db.close()
    token_alex = login_and_get_token(client, "alex", "alexpass")
    token_bob = login_and_get_token(client, "bob", "bobpass")

    db = SessionLocal()
    try:
        content_dept1 = db.query(Content).filter(Content.department_id == 1).first()
        content_dept2 = db.query(Content).filter(Content.department_id == 2).first()
    finally:
        db.close()

    r = client.get(f"/content/content/{content_dept1.id}", headers=auth_headers(token_alex))
    assert r.status_code == 200

    r = client.get(f"/content/content/{content_dept2.id}", headers=auth_headers(token_alex))
    assert r.status_code == 403

    r = client.get(f"/content/content/{content_dept2.id}", headers=auth_headers(token_admin))
    assert r.status_code == 200


def test_update_content_admin_only(client: TestClient):
    token_admin = login_and_get_token(client, "admin", "adminpass")
    token_alex = login_and_get_token(client, "alex", "alexpass")

    db = SessionLocal()
    try:
        any_content = db.query(Content).first()
    finally:
        db.close()

    r = client.put(f"/content/{any_content.id}", json={"title": "new"}, headers=auth_headers(token_admin))
    assert r.status_code == 200

    r = client.put(f"/content/{any_content.id}", json={"title": "new2"}, headers=auth_headers(token_alex))
    assert r.status_code == 403


def test_user_content_by_tags_and_search_require_owner_or_admin(client: TestClient):
    token_admin = login_and_get_token(client, "admin", "adminpass")
    for login, dept in (("alex", 1), ("bob", 2)):
        db = SessionLocal()
        try:
            if db.query(User).filter(User.login == login).first() is None:
                db.add(User(login=login, password=pwd_context.hash(f"{login}pass"), role_id=2, department_id=dept, access_id=1))
                db.commit()
        finally:
            db.close()
    token_alex = login_and_get_token(client, "alex", "alexpass")
    token_bob = login_and_get_token(client, "bob", "bobpass")

    db = SessionLocal()
    try:
        alex_id = db.query(User).filter(User.login == "alex").first().id
        tag_id = db.query(Tag).first().id
    finally:
        db.close()

    # by-tags
    r = client.get(f"/content/user/{alex_id}/content/by-tags/{tag_id}", headers=auth_headers(token_alex))
    assert r.status_code in (200, 404)

    r = client.get(f"/content/user/{alex_id}/content/by-tags/{tag_id}", headers=auth_headers(token_bob))
    assert r.status_code == 403

    r = client.get(f"/content/user/{alex_id}/content/by-tags/{tag_id}", headers=auth_headers(token_admin))
    assert r.status_code in (200, 404)

    # search-documents
    r = client.get("/content/search-documents", params={"user_id": alex_id, "search_query": "Doc"}, headers=auth_headers(token_alex))
    assert r.status_code == 200

    r = client.get("/content/search-documents", params={"user_id": alex_id}, headers=auth_headers(token_bob))
    assert r.status_code == 403

    r = client.get("/content/search-documents", params={"user_id": alex_id}, headers=auth_headers(token_admin))
    assert r.status_code == 200


def test_admin_only_file_ops_and_departments_listing(client: TestClient):
    token_admin = login_and_get_token(client, "admin", "adminpass")
    db = SessionLocal()
    try:
        if db.query(User).filter(User.login == "alex").first() is None:
            db.add(User(login="alex", password=pwd_context.hash("alexpass"), role_id=2, department_id=1, access_id=1))
            db.commit()
    finally:
        db.close()
    token_alex = login_and_get_token(client, "alex", "alexpass")

    # list-files
    r = client.get("/content/list-files/1", headers=auth_headers(token_admin))
    assert r.status_code == 200
    r = client.get("/content/list-files/1", headers=auth_headers(token_alex))
    assert r.status_code == 403

    # delete single file (директории может не существовать -> 404, важна авторизация)
    r = client.delete("/content/delete-file/1/nonexistent.txt", headers=auth_headers(token_alex))
    assert r.status_code == 403
    r = client.delete("/content/delete-file/1/nonexistent.txt", headers=auth_headers(token_admin))
    assert r.status_code in (200, 404)

    # delete all files
    r = client.delete("/content/delete-all-files/1", headers=auth_headers(token_alex))
    assert r.status_code == 403
    r = client.delete("/content/delete-all-files/1", headers=auth_headers(token_admin))
    assert r.status_code in (200, 404)

    # list-all-departments
    r = client.get("/content/list-all-departments", headers=auth_headers(token_alex))
    assert r.status_code == 403
    r = client.get("/content/list-all-departments", headers=auth_headers(token_admin))
    assert r.status_code == 200


### feedback_routes security tests

def test_feedback_create_requires_token_and_self_or_admin(client: TestClient):
    token_admin = login_and_get_token(client, "admin", "adminpass")
    for login, dept in (("alex", 1), ("bob", 2)):
        db = SessionLocal()
        try:
            if db.query(User).filter(User.login == login).first() is None:
                db.add(User(login=login, password=pwd_context.hash(f"{login}pass"), role_id=2, department_id=dept, access_id=1))
                db.commit()
        finally:
            db.close()
    token_alex = login_and_get_token(client, "alex", "alexpass")
    token_bob = login_and_get_token(client, "bob", "bobpass")

    db = SessionLocal()
    try:
        alex_id = db.query(User).filter(User.login == "alex").first().id
        bob_id = db.query(User).filter(User.login == "bob").first().id
    finally:
        db.close()

    # alex от своего имени — ок
    r = client.post(
        "/feedback/create",
        headers=auth_headers(token_alex),
        data={"user_id": str(alex_id), "text": "hi"},
    )
    assert r.status_code == 200

    # bob за alex — запрещено
    r = client.post(
        "/feedback/create",
        headers=auth_headers(token_bob),
        data={"user_id": str(alex_id), "text": "no"},
    )
    assert r.status_code == 403

    # admin за alex — ок
    r = client.post(
        "/feedback/create",
        headers=auth_headers(token_admin),
        data={"user_id": str(alex_id), "text": "admin"},
    )
    assert r.status_code == 200


def test_feedback_list_admin_only(client: TestClient):
    token_admin = login_and_get_token(client, "admin", "adminpass")
    db = SessionLocal()
    try:
        if db.query(User).filter(User.login == "alex").first() is None:
            db.add(User(login="alex", password=pwd_context.hash("alexpass"), role_id=2, department_id=1, access_id=1))
            db.commit()
    finally:
        db.close()
    token_alex = login_and_get_token(client, "alex", "alexpass")

    r = client.get("/feedback/list", headers=auth_headers(token_admin))
    assert r.status_code == 200

    r = client.get("/feedback/list", headers=auth_headers(token_alex))
    assert r.status_code == 403


def test_feedback_photo_and_detail_author_or_admin(client: TestClient):
    token_admin = login_and_get_token(client, "admin", "adminpass")
    token_alex = login_and_get_token(client, "alex", "alexpass")
    token_bob = login_and_get_token(client, "bob", "bobpass")

    db = SessionLocal()
    try:
        fb = db.query(Feedback).filter(Feedback.photo != None).first()  # noqa: E711
    finally:
        db.close()

    # автор — ок
    r = client.get(f"/feedback/photo/{fb.id}", headers=auth_headers(token_alex))
    assert r.status_code in (200, 404)

    r = client.get(f"/feedback/detail/{fb.id}", headers=auth_headers(token_alex))
    assert r.status_code == 200

    # чужой — запрещено
    r = client.get(f"/feedback/photo/{fb.id}", headers=auth_headers(token_bob))
    assert r.status_code == 403
    r = client.get(f"/feedback/detail/{fb.id}", headers=auth_headers(token_bob))
    assert r.status_code == 403

    # админ — ок
    r = client.get(f"/feedback/photo/{fb.id}", headers=auth_headers(token_admin))
    assert r.status_code in (200, 404)
    r = client.get(f"/feedback/detail/{fb.id}", headers=auth_headers(token_admin))
    assert r.status_code == 200


