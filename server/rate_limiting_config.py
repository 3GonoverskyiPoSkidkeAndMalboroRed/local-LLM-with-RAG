"""
Конфигурация Rate Limiting для приложения
"""

# Глобальные настройки rate limiting
RATE_LIMITS = {
    # Аутентификация и регистрация
    "login": "10/minute",           # 10 попыток входа в минуту
    "register": "5/minute",         # 5 регистраций в минуту
    
    # Загрузка файлов
    "upload_content": "20/minute",  # 20 загрузок контента в минуту
    "upload_files": "10/minute",    # 10 массовых загрузок в минуту
    
    # Обратная связь
    "feedback_create": "30/minute", # 30 сообщений обратной связи в минуту
    
    # AI/ML сервисы
    "yandex_ai_generate": "60/minute",  # 60 запросов к Yandex AI в минуту
    "yandex_rag_query": "30/minute",    # 30 RAG запросов в минуту
    
    # По умолчанию для всех остальных эндпоинтов
    "default": "100/minute"         # 100 запросов в минуту
}

# Настройки для разных типов пользователей
USER_RATE_LIMITS = {
    "admin": {
        "multiplier": 2.0,  # Админы могут делать в 2 раза больше запросов
    },
    "user": {
        "multiplier": 1.0,  # Обычные пользователи
    },
    "guest": {
        "multiplier": 0.5,  # Гости могут делать в 2 раза меньше запросов
    }
}

# Настройки для защиты от DDoS
DDOS_PROTECTION = {
    "burst_limit": "200/minute",    # Максимальный всплеск запросов
    "sustained_limit": "1000/hour", # Устойчивый лимит в час
}

# Настройки для API ключей (если используются)
API_KEY_LIMITS = {
    "free": "100/hour",
    "premium": "1000/hour",
    "enterprise": "10000/hour"
}

def get_rate_limit_for_endpoint(endpoint_name: str, user_role: str = "user") -> str:
    """
    Получить rate limit для конкретного эндпоинта и роли пользователя
    """
    base_limit = RATE_LIMITS.get(endpoint_name, RATE_LIMITS["default"])
    multiplier = USER_RATE_LIMITS.get(user_role, USER_RATE_LIMITS["user"])["multiplier"]
    
    # Парсим базовый лимит (например, "10/minute")
    if "/" in base_limit:
        number, period = base_limit.split("/")
        new_number = int(float(number) * multiplier)
        return f"{new_number}/{period}"
    
    return base_limit

def get_ddos_protection_limit() -> str:
    """
    Получить лимит для защиты от DDoS
    """
    return DDOS_PROTECTION["burst_limit"]
