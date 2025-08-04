"""
Утилиты для работы с конфигурацией и переменными окружения.
Обеспечивает безопасное чтение чувствительных данных и валидацию настроек.
Включает централизованную конфигурационную систему для Yandex Cloud.
"""

import os
import logging
import re
import hashlib
from typing import Optional, Dict, Any, List, Union, Tuple
from dataclasses import dataclass, field, asdict
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

# Загружаем переменные из .env файла
load_dotenv()

logger = logging.getLogger(__name__)

class ConfigError(Exception):
    """Ошибка конфигурации"""
    pass

class ConfigValidationError(ConfigError):
    """Ошибка валидации конфигурации"""
    pass

class SecretNotFoundError(ConfigError):
    """Ошибка отсутствия секретного значения"""
    pass

@dataclass
class ModelConfig:
    """Конфигурация для конкретной модели"""
    name: str
    max_tokens: int
    temperature: float
    timeout: int
    cost_per_token: float = 0.0
    description: str = ""
    
    def __post_init__(self):
        """Валидация параметров модели"""
        # Для embedding моделей max_tokens может быть 0
        if self.max_tokens < 0:
            raise ConfigValidationError(f"max_tokens не может быть отрицательным, получено: {self.max_tokens}")
        if not 0.0 <= self.temperature <= 1.0:
            raise ConfigValidationError(f"temperature должен быть в диапазоне [0.0, 1.0], получено: {self.temperature}")
        if self.timeout <= 0:
            raise ConfigValidationError(f"timeout должен быть > 0, получено: {self.timeout}")

@dataclass
class YandexCloudConfig:
    """
    Централизованная конфигурация для Yandex Cloud интеграции
    """
    # Основные параметры аутентификации
    api_key: str
    folder_id: str
    
    # Модели по умолчанию
    default_llm_model: str = "yandexgpt"
    default_embedding_model: str = "text-search-doc"
    
    # Сетевые настройки
    base_url: str = "https://llm.api.cloud.yandex.net"
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    
    # Лимиты и квоты
    max_tokens_per_request: int = 2000
    max_requests_per_minute: int = 60
    max_concurrent_requests: int = 10
    
    # Настройки кэширования
    enable_caching: bool = True
    cache_dir: str = "files/cache"
    cache_ttl_hours: int = 24
    
    # Настройки мониторинга
    enable_metrics: bool = True
    metrics_file: str = "files/yandex_metrics.json"
    enable_performance_monitoring: bool = True
    
    # Настройки fallback
    enable_fallback: bool = True
    fallback_provider: str = "ollama"
    fallback_timeout: int = 60
    
    # Конфигурации моделей
    llm_models: Dict[str, ModelConfig] = field(default_factory=dict)
    embedding_models: Dict[str, ModelConfig] = field(default_factory=dict)
    
    def __post_init__(self):
        """Инициализация и валидация конфигурации"""
        self._validate_basic_config()
        self._setup_default_models()
        self._validate_paths()
    
    def _validate_basic_config(self):
        """Валидация базовых параметров"""
        if not self.api_key:
            raise ConfigValidationError("YANDEX_API_KEY не может быть пустым")
        
        if len(self.api_key) < 10:
            raise ConfigValidationError("YANDEX_API_KEY слишком короткий")
        
        if not self.folder_id:
            raise ConfigValidationError("YANDEX_FOLDER_ID не может быть пустым")
        
        if not re.match(r'^[a-zA-Z0-9_-]+$', self.folder_id):
            raise ConfigValidationError("YANDEX_FOLDER_ID содержит недопустимые символы")
        
        if not self.base_url.startswith(('http://', 'https://')):
            raise ConfigValidationError("base_url должен начинаться с http:// или https://")
        
        if self.timeout <= 0:
            raise ConfigValidationError("timeout должен быть положительным")
        
        if self.max_retries < 0:
            raise ConfigValidationError("max_retries не может быть отрицательным")
        
        if self.max_tokens_per_request <= 0:
            raise ConfigValidationError("max_tokens_per_request должен быть положительным")
    
    def _setup_default_models(self):
        """Настройка конфигураций моделей по умолчанию"""
        if not self.llm_models:
            self.llm_models = {
                "yandexgpt": ModelConfig(
                    name="yandexgpt",
                    max_tokens=2000,
                    temperature=0.1,
                    timeout=30,
                    cost_per_token=0.002,
                    description="Основная модель YandexGPT для генерации текста"
                ),
                "yandexgpt-lite": ModelConfig(
                    name="yandexgpt-lite",
                    max_tokens=1000,
                    temperature=0.1,
                    timeout=20,
                    cost_per_token=0.001,
                    description="Облегченная версия YandexGPT для быстрых запросов"
                )
            }
        
        if not self.embedding_models:
            self.embedding_models = {
                "text-search-doc": ModelConfig(
                    name="text-search-doc",
                    max_tokens=0,  # Эмбеддинги не используют токены генерации
                    temperature=0.0,
                    timeout=15,
                    cost_per_token=0.0001,
                    description="Модель для создания эмбеддингов документов"
                ),
                "text-search-query": ModelConfig(
                    name="text-search-query",
                    max_tokens=0,
                    temperature=0.0,
                    timeout=15,
                    cost_per_token=0.0001,
                    description="Модель для создания эмбеддингов поисковых запросов"
                )
            }
    
    def _validate_paths(self):
        """Валидация и создание необходимых директорий"""
        try:
            # Создаем директорию для кэша
            cache_path = Path(self.cache_dir)
            cache_path.mkdir(parents=True, exist_ok=True)
            
            # Создаем директорию для метрик
            metrics_path = Path(self.metrics_file).parent
            metrics_path.mkdir(parents=True, exist_ok=True)
            
        except Exception as e:
            logger.warning(f"Не удалось создать директории: {e}")
    
    def get_model_config(self, model_name: str, model_type: str = "llm") -> ModelConfig:
        """
        Получение конфигурации модели
        
        Args:
            model_name: Название модели
            model_type: Тип модели ("llm" или "embedding")
            
        Returns:
            Конфигурация модели
            
        Raises:
            ConfigError: Если модель не найдена
        """
        models_dict = self.llm_models if model_type == "llm" else self.embedding_models
        
        if model_name not in models_dict:
            available_models = list(models_dict.keys())
            raise ConfigError(
                f"Модель '{model_name}' типа '{model_type}' не найдена. "
                f"Доступные модели: {available_models}"
            )
        
        return models_dict[model_name]
    
    def get_available_models(self, model_type: str = None) -> Dict[str, List[str]]:
        """
        Получение списка доступных моделей
        
        Args:
            model_type: Тип моделей ("llm", "embedding" или None для всех)
            
        Returns:
            Словарь с доступными моделями
        """
        result = {}
        
        if model_type is None or model_type == "llm":
            result["llm_models"] = list(self.llm_models.keys())
        
        if model_type is None or model_type == "embedding":
            result["embedding_models"] = list(self.embedding_models.keys())
        
        return result
    
    def estimate_cost(self, model_name: str, tokens_used: int, model_type: str = "llm") -> float:
        """
        Оценка стоимости использования модели
        
        Args:
            model_name: Название модели
            tokens_used: Количество использованных токенов
            model_type: Тип модели
            
        Returns:
            Оценочная стоимость в рублях
        """
        try:
            model_config = self.get_model_config(model_name, model_type)
            return tokens_used * model_config.cost_per_token
        except ConfigError:
            return 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертация в словарь (без чувствительных данных)"""
        data = asdict(self)
        
        # Маскируем чувствительные данные
        if data.get("api_key"):
            data["api_key"] = f"{data['api_key'][:8]}***"
        
        return data
    
    @classmethod
    def from_env(cls) -> 'YandexCloudConfig':
        """
        Создание конфигурации из переменных окружения
        
        Returns:
            Экземпляр YandexCloudConfig
            
        Raises:
            ConfigError: При ошибке конфигурации
        """
        try:
            # Обязательные параметры
            api_key = get_env_var("YANDEX_API_KEY", required=True, sensitive=True)
            folder_id = get_env_var("YANDEX_FOLDER_ID", required=True)
            
            # Опциональные параметры с значениями по умолчанию
            config = cls(
                api_key=api_key,
                folder_id=folder_id,
                default_llm_model=get_env_var("YANDEX_LLM_MODEL", "yandexgpt"),
                default_embedding_model=get_env_var("YANDEX_EMBEDDING_MODEL", "text-search-doc"),
                base_url=get_env_var("YANDEX_BASE_URL", "https://llm.api.cloud.yandex.net"),
                timeout=get_env_int("YANDEX_TIMEOUT", 30, min_value=5, max_value=300),
                max_retries=get_env_int("YANDEX_MAX_RETRIES", 3, min_value=0, max_value=10),
                retry_delay=get_env_float("YANDEX_RETRY_DELAY", 1.0, min_value=0.1, max_value=10.0),
                max_tokens_per_request=get_env_int("YANDEX_MAX_TOKENS", 2000, min_value=1, max_value=8000),
                max_requests_per_minute=get_env_int("YANDEX_MAX_REQUESTS_PER_MINUTE", 60, min_value=1),
                max_concurrent_requests=get_env_int("YANDEX_MAX_CONCURRENT", 10, min_value=1),
                enable_caching=get_env_bool("YANDEX_ENABLE_CACHING", True),
                cache_dir=get_env_var("YANDEX_CACHE_DIR", "files/cache"),
                cache_ttl_hours=get_env_int("YANDEX_CACHE_TTL_HOURS", 24, min_value=1),
                enable_metrics=get_env_bool("YANDEX_ENABLE_METRICS", True),
                metrics_file=get_env_var("YANDEX_METRICS_FILE", "files/yandex_metrics.json"),
                enable_performance_monitoring=get_env_bool("YANDEX_ENABLE_PERFORMANCE_MONITORING", True),
                enable_fallback=get_env_bool("YANDEX_FALLBACK_TO_OLLAMA", True),
                fallback_provider=get_env_var("YANDEX_FALLBACK_PROVIDER", "ollama"),
                fallback_timeout=get_env_int("YANDEX_FALLBACK_TIMEOUT", 60, min_value=5)
            )
            
            logger.info("YandexCloudConfig успешно создан из переменных окружения")
            return config
            
        except Exception as e:
            raise ConfigError(f"Ошибка создания конфигурации из переменных окружения: {e}")

@dataclass
class OllamaConfig:
    """Конфигурация для Ollama (fallback провайдер)"""
    host: str = "http://localhost:11434"
    timeout: int = 60
    max_retries: int = 3
    default_llm_model: str = "gemma3"
    default_embedding_model: str = "nomic-embed-text"
    
    def __post_init__(self):
        """Валидация конфигурации Ollama"""
        if not self.host.startswith(('http://', 'https://')):
            raise ConfigValidationError("Ollama host должен начинаться с http:// или https://")
    
    @classmethod
    def from_env(cls) -> 'OllamaConfig':
        """Создание конфигурации Ollama из переменных окружения"""
        return cls(
            host=get_env_var("OLLAMA_HOST", "http://localhost:11434"),
            timeout=get_env_int("OLLAMA_TIMEOUT", 60, min_value=5),
            max_retries=get_env_int("OLLAMA_MAX_RETRIES", 3, min_value=0),
            default_llm_model=get_env_var("OLLAMA_LLM_MODEL", "gemma3"),
            default_embedding_model=get_env_var("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
        )

@dataclass
class DatabaseConfig:
    """Конфигурация базы данных"""
    url: str
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600
    
    def __post_init__(self):
        """Валидация конфигурации базы данных"""
        if not self.url:
            raise ConfigValidationError("DATABASE_URL не может быть пустым")
    
    @classmethod
    def from_env(cls) -> 'DatabaseConfig':
        """Создание конфигурации БД из переменных окружения"""
        return cls(
            url=get_env_var("DATABASE_URL", "mysql+mysqlconnector://root:123123@localhost:3306/db_test"),
            pool_size=get_env_int("DB_POOL_SIZE", 10, min_value=1),
            max_overflow=get_env_int("DB_MAX_OVERFLOW", 20, min_value=0),
            pool_timeout=get_env_int("DB_POOL_TIMEOUT", 30, min_value=1),
            pool_recycle=get_env_int("DB_POOL_RECYCLE", 3600, min_value=60)
        )

@dataclass
class AppConfig:
    """Общая конфигурация приложения"""
    yandex_cloud: YandexCloudConfig
    ollama: OllamaConfig
    database: DatabaseConfig
    
    # Общие настройки приложения
    debug: bool = False
    log_level: str = "INFO"
    environment: str = "development"
    
    # Настройки безопасности
    secret_key: str = ""
    allowed_hosts: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Валидация общей конфигурации"""
        if self.environment not in ["development", "testing", "staging", "production"]:
            raise ConfigValidationError(f"Неподдерживаемая среда: {self.environment}")
        
        if self.log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            raise ConfigValidationError(f"Неподдерживаемый уровень логирования: {self.log_level}")
    
    @classmethod
    def from_env(cls) -> 'AppConfig':
        """Создание полной конфигурации приложения из переменных окружения"""
        return cls(
            yandex_cloud=YandexCloudConfig.from_env(),
            ollama=OllamaConfig.from_env(),
            database=DatabaseConfig.from_env(),
            debug=get_env_bool("DEBUG", False),
            log_level=get_env_var("LOG_LEVEL", "INFO").upper(),
            environment=get_env_var("ENVIRONMENT", "development").lower(),
            secret_key=get_env_var("SECRET_KEY", "", sensitive=True),
            allowed_hosts=get_env_var("ALLOWED_HOSTS", "").split(",") if get_env_var("ALLOWED_HOSTS") else []
        )

def get_env_var(
    name: str, 
    default: Optional[str] = None, 
    required: bool = False,
    sensitive: bool = False
) -> Optional[str]:
    """
    Безопасное получение переменной окружения
    
    Args:
        name: Имя переменной
        default: Значение по умолчанию
        required: Обязательная ли переменная
        sensitive: Чувствительные данные (не логируются)
        
    Returns:
        Значение переменной или None
        
    Raises:
        ConfigError: Если обязательная переменная отсутствует
    """
    value = os.getenv(name, default)
    
    if required and value is None:
        raise ConfigError(f"Обязательная переменная окружения {name} не установлена")
    
    if value is not None and not sensitive:
        logger.debug(f"Загружена переменная {name}={value}")
    elif value is not None and sensitive:
        logger.debug(f"Загружена чувствительная переменная {name}=***")
    
    return value

def get_secret_var(
    name: str,
    default: Optional[str] = None,
    required: bool = True,
    min_length: int = 8
) -> str:
    """
    Безопасное получение секретной переменной окружения с дополнительной валидацией
    
    Args:
        name: Имя переменной
        default: Значение по умолчанию
        required: Обязательная ли переменная
        min_length: Минимальная длина секрета
        
    Returns:
        Значение секретной переменной
        
    Raises:
        SecretNotFoundError: Если секрет не найден
        ConfigValidationError: Если секрет не прошел валидацию
    """
    value = os.getenv(name, default)
    
    if required and not value:
        raise SecretNotFoundError(f"Секретная переменная {name} не установлена")
    
    if value and len(value) < min_length:
        raise ConfigValidationError(
            f"Секретная переменная {name} слишком короткая (минимум {min_length} символов)"
        )
    
    # Проверяем на простые пароли
    if value and value.lower() in ['password', '123456', 'admin', 'secret']:
        raise ConfigValidationError(f"Секретная переменная {name} содержит небезопасное значение")
    
    logger.debug(f"Загружена секретная переменная {name} (длина: {len(value) if value else 0})")
    return value

def mask_sensitive_value(value: str, show_chars: int = 4) -> str:
    """
    Маскирует чувствительное значение для безопасного логирования
    
    Args:
        value: Значение для маскирования
        show_chars: Количество символов для показа в начале
        
    Returns:
        Замаскированное значение
    """
    if not value:
        return ""
    
    if len(value) <= show_chars:
        return "*" * len(value)
    
    return f"{value[:show_chars]}{'*' * (len(value) - show_chars)}"

def validate_api_key_format(api_key: str, provider: str = "yandex") -> bool:
    """
    Валидация формата API ключа
    
    Args:
        api_key: API ключ для валидации
        provider: Провайдер API (yandex, openai, etc.)
        
    Returns:
        True если формат корректный
        
    Raises:
        ConfigValidationError: Если формат некорректный
    """
    if not api_key:
        raise ConfigValidationError("API ключ не может быть пустым")
    
    if provider.lower() == "yandex":
        # Yandex Cloud API ключи обычно имеют определенный формат
        if len(api_key) < 20:
            raise ConfigValidationError("Yandex API ключ слишком короткий")
        
        # Проверяем на базовые паттерны
        if not re.match(r'^[A-Za-z0-9_-]+$', api_key):
            raise ConfigValidationError("Yandex API ключ содержит недопустимые символы")
    
    return True

def get_config_hash(config_dict: Dict[str, Any]) -> str:
    """
    Создает хеш конфигурации для отслеживания изменений
    
    Args:
        config_dict: Словарь конфигурации
        
    Returns:
        MD5 хеш конфигурации
    """
    # Удаляем чувствительные данные перед хешированием
    safe_config = {}
    sensitive_keys = ['api_key', 'secret_key', 'password', 'token']
    
    for key, value in config_dict.items():
        if any(sensitive_key in key.lower() for sensitive_key in sensitive_keys):
            safe_config[key] = "***"
        else:
            safe_config[key] = value
    
    config_str = str(sorted(safe_config.items()))
    return hashlib.md5(config_str.encode()).hexdigest()

def load_config_from_file(file_path: str) -> Dict[str, Any]:
    """
    Загрузка конфигурации из файла
    
    Args:
        file_path: Путь к файлу конфигурации
        
    Returns:
        Словарь конфигурации
        
    Raises:
        ConfigError: При ошибке загрузки файла
    """
    try:
        path = Path(file_path)
        if not path.exists():
            raise ConfigError(f"Файл конфигурации не найден: {file_path}")
        
        if path.suffix.lower() == '.json':
            import json
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        elif path.suffix.lower() in ['.yml', '.yaml']:
            try:
                import yaml
                with open(path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
            except ImportError:
                raise ConfigError("PyYAML не установлен для загрузки YAML файлов")
        
        else:
            raise ConfigError(f"Неподдерживаемый формат файла: {path.suffix}")
    
    except Exception as e:
        raise ConfigError(f"Ошибка загрузки конфигурации из {file_path}: {e}")

def save_config_to_file(config_dict: Dict[str, Any], file_path: str, exclude_sensitive: bool = True):
    """
    Сохранение конфигурации в файл
    
    Args:
        config_dict: Словарь конфигурации
        file_path: Путь к файлу для сохранения
        exclude_sensitive: Исключить чувствительные данные
        
    Raises:
        ConfigError: При ошибке сохранения
    """
    try:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Подготавливаем данные для сохранения
        save_data = config_dict.copy()
        
        if exclude_sensitive:
            sensitive_keys = ['api_key', 'secret_key', 'password', 'token']
            for key in list(save_data.keys()):
                if any(sensitive_key in key.lower() for sensitive_key in sensitive_keys):
                    save_data[key] = "***HIDDEN***"
        
        # Добавляем метаданные
        save_data['_metadata'] = {
            'generated_at': datetime.now().isoformat(),
            'config_hash': get_config_hash(config_dict),
            'sensitive_excluded': exclude_sensitive
        }
        
        if path.suffix.lower() == '.json':
            import json
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
        
        elif path.suffix.lower() in ['.yml', '.yaml']:
            try:
                import yaml
                with open(path, 'w', encoding='utf-8') as f:
                    yaml.dump(save_data, f, default_flow_style=False, allow_unicode=True)
            except ImportError:
                raise ConfigError("PyYAML не установлен для сохранения YAML файлов")
        
        else:
            raise ConfigError(f"Неподдерживаемый формат файла: {path.suffix}")
        
        logger.info(f"Конфигурация сохранена в {file_path}")
    
    except Exception as e:
        raise ConfigError(f"Ошибка сохранения конфигурации в {file_path}: {e}")

def merge_configs(*configs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Объединение нескольких конфигураций с приоритетом последних
    
    Args:
        *configs: Словари конфигураций для объединения
        
    Returns:
        Объединенная конфигурация
    """
    result = {}
    
    for config in configs:
        if isinstance(config, dict):
            for key, value in config.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    # Рекурсивное объединение вложенных словарей
                    result[key] = merge_configs(result[key], value)
                else:
                    result[key] = value
    
    return result

def get_env_bool(name: str, default: bool = False) -> bool:
    """Получение булевой переменной окружения"""
    value = get_env_var(name, str(default).lower())
    return value.lower() in ('true', '1', 'yes', 'on')

def get_env_int(name: str, default: int = 0, min_value: int = None, max_value: int = None) -> int:
    """
    Получение целочисленной переменной окружения с валидацией
    
    Args:
        name: Имя переменной
        default: Значение по умолчанию
        min_value: Минимальное значение
        max_value: Максимальное значение
        
    Returns:
        Целочисленное значение
        
    Raises:
        ConfigError: При ошибке валидации
    """
    value_str = get_env_var(name, str(default))
    
    try:
        value = int(value_str)
    except ValueError:
        raise ConfigError(f"Переменная {name} должна быть целым числом, получено: {value_str}")
    
    if min_value is not None and value < min_value:
        raise ConfigError(f"Переменная {name} должна быть >= {min_value}, получено: {value}")
    
    if max_value is not None and value > max_value:
        raise ConfigError(f"Переменная {name} должна быть <= {max_value}, получено: {value}")
    
    return value

def get_env_float(name: str, default: float = 0.0, min_value: float = None, max_value: float = None) -> float:
    """
    Получение вещественной переменной окружения с валидацией
    
    Args:
        name: Имя переменной
        default: Значение по умолчанию
        min_value: Минимальное значение
        max_value: Максимальное значение
        
    Returns:
        Вещественное значение
        
    Raises:
        ConfigError: При ошибке валидации
    """
    value_str = get_env_var(name, str(default))
    
    try:
        value = float(value_str)
    except ValueError:
        raise ConfigError(f"Переменная {name} должна быть числом, получено: {value_str}")
    
    if min_value is not None and value < min_value:
        raise ConfigError(f"Переменная {name} должна быть >= {min_value}, получено: {value}")
    
    if max_value is not None and value > max_value:
        raise ConfigError(f"Переменная {name} должна быть <= {max_value}, получено: {value}")
    
    return value

def validate_yandex_config() -> Dict[str, Any]:
    """
    Валидация конфигурации Yandex Cloud (legacy функция для обратной совместимости)
    
    Returns:
        Словарь с валидированными настройками
        
    Raises:
        ConfigError: При ошибке валидации
    """
    try:
        # Используем новую систему конфигурации
        yandex_config = YandexCloudConfig.from_env()
        
        # Конвертируем в старый формат для обратной совместимости
        return {
            "use_yandex_cloud": True,
            "api_key": yandex_config.api_key,
            "folder_id": yandex_config.folder_id,
            "llm_model": yandex_config.default_llm_model,
            "embedding_model": yandex_config.default_embedding_model,
            "max_tokens": yandex_config.max_tokens_per_request,
            "temperature": yandex_config.llm_models[yandex_config.default_llm_model].temperature,
            "timeout": yandex_config.timeout,
            "base_url": yandex_config.base_url
        }
    except ConfigError:
        # Если Yandex Cloud не настроен, возвращаем отключенное состояние
        logger.info("Интеграция с Yandex Cloud отключена")
        return {"use_yandex_cloud": False}

def validate_all_config_new() -> AppConfig:
    """
    Валидация всей конфигурации приложения (новая версия)
    
    Returns:
        Полная конфигурация приложения
        
    Raises:
        ConfigError: При ошибке валидации любого компонента
    """
    logger.info("Начало валидации конфигурации приложения...")
    
    try:
        config = AppConfig.from_env()
        logger.info("Валидация конфигурации завершена успешно")
        return config
    except Exception as e:
        logger.error(f"Ошибка валидации конфигурации: {e}")
        raise ConfigError(f"Ошибка валидации конфигурации: {e}")

def get_runtime_config() -> Dict[str, Any]:
    """
    Получение конфигурации времени выполнения
    
    Returns:
        Словарь с конфигурацией времени выполнения
    """
    try:
        config = AppConfig.from_env()
        
        return {
            "yandex_cloud": {
                "enabled": True,
                "models": config.yandex_cloud.get_available_models(),
                "default_llm": config.yandex_cloud.default_llm_model,
                "default_embedding": config.yandex_cloud.default_embedding_model,
                "caching_enabled": config.yandex_cloud.enable_caching,
                "metrics_enabled": config.yandex_cloud.enable_metrics,
                "fallback_enabled": config.yandex_cloud.enable_fallback
            },
            "ollama": {
                "host": config.ollama.host,
                "default_llm": config.ollama.default_llm_model,
                "default_embedding": config.ollama.default_embedding_model
            },
            "application": {
                "environment": config.environment,
                "debug": config.debug,
                "log_level": config.log_level
            },
            "features": {
                "monitoring": config.yandex_cloud.enable_performance_monitoring,
                "caching": config.yandex_cloud.enable_caching,
                "fallback": config.yandex_cloud.enable_fallback
            }
        }
    except Exception as e:
        logger.warning(f"Ошибка получения полной конфигурации: {e}")
        # Возвращаем минимальную конфигурацию при ошибке
        return {
            "yandex_cloud": {"enabled": False},
            "ollama": {"host": get_env_var("OLLAMA_HOST", "http://localhost:11434")},
            "application": {
                "environment": get_env_var("ENVIRONMENT", "development"),
                "debug": get_env_bool("DEBUG", False),
                "log_level": get_env_var("LOG_LEVEL", "INFO")
            },
            "features": {"monitoring": False, "caching": False, "fallback": True}
        }

def validate_ollama_config() -> Dict[str, Any]:
    """
    Валидация конфигурации Ollama (для fallback)
    
    Returns:
        Словарь с настройками Ollama
    """
    config = {}
    
    config["host"] = get_env_var("OLLAMA_HOST", "http://localhost:11434")
    
    # Валидация URL
    if not config["host"].startswith(("http://", "https://")):
        raise ConfigError(f"OLLAMA_HOST должен начинаться с http:// или https://, получено: {config['host']}")
    
    logger.debug(f"Конфигурация Ollama: host={config['host']}")
    return config

def get_database_config() -> Dict[str, Any]:
    """Получение конфигурации базы данных"""
    config = {}
    
    config["url"] = get_env_var("DATABASE_URL", "mysql+mysqlconnector://root:123123@localhost:3306/db_test")
    
    logger.debug("Конфигурация базы данных загружена")
    return config

def validate_all_config() -> Dict[str, Any]:
    """
    Валидация всей конфигурации приложения
    
    Returns:
        Полная конфигурация приложения
        
    Raises:
        ConfigError: При ошибке валидации любого компонента
    """
    logger.info("Начало валидации конфигурации приложения...")
    
    config = {
        "yandex_cloud": validate_yandex_config(),
        "ollama": validate_ollama_config(),
        "database": get_database_config()
    }
    
    logger.info("Валидация конфигурации завершена успешно")
    return config

def print_config_summary():
    """Вывод сводки по конфигурации (без чувствительных данных)"""
    try:
        config = validate_all_config_new()
        
        print("\n" + "="*60)
        print("СВОДКА КОНФИГУРАЦИИ ПРИЛОЖЕНИЯ")
        print("="*60)
        
        # Общие настройки приложения
        print(f"🏗️  Среда: {config.environment.upper()}")
        print(f"🐛 Debug: {'ВКЛ' if config.debug else 'ВЫКЛ'}")
        print(f"📝 Уровень логирования: {config.log_level}")
        
        # Yandex Cloud
        yandex = config.yandex_cloud
        print(f"\n🟢 Yandex Cloud: ВКЛЮЧЕН")
        print(f"   📡 Base URL: {yandex.base_url}")
        print(f"   🤖 LLM модель по умолчанию: {yandex.default_llm_model}")
        print(f"   🔍 Embedding модель по умолчанию: {yandex.default_embedding_model}")
        print(f"   ⏱️  Timeout: {yandex.timeout}s")
        print(f"   🔄 Max retries: {yandex.max_retries}")
        print(f"   🎯 Max tokens: {yandex.max_tokens_per_request}")
        print(f"   🔑 API Key: {mask_sensitive_value(yandex.api_key)}")
        print(f"   📁 Folder ID: {yandex.folder_id}")
        print(f"   💾 Кэширование: {'ВКЛ' if yandex.enable_caching else 'ВЫКЛ'}")
        print(f"   📊 Метрики: {'ВКЛ' if yandex.enable_metrics else 'ВЫКЛ'}")
        print(f"   🔄 Fallback: {'ВКЛ' if yandex.enable_fallback else 'ВЫКЛ'}")
        
        # Доступные модели
        llm_models = list(yandex.llm_models.keys())
        embedding_models = list(yandex.embedding_models.keys())
        print(f"   🤖 Доступные LLM модели: {', '.join(llm_models)}")
        print(f"   🔍 Доступные Embedding модели: {', '.join(embedding_models)}")
        
        # Ollama (fallback)
        ollama = config.ollama
        print(f"\n📡 Ollama (Fallback):")
        print(f"   🌐 Host: {ollama.host}")
        print(f"   🤖 LLM модель по умолчанию: {ollama.default_llm_model}")
        print(f"   🔍 Embedding модель по умолчанию: {ollama.default_embedding_model}")
        print(f"   ⏱️  Timeout: {ollama.timeout}s")
        
        # Database
        db = config.database
        masked_db_url = mask_database_url(db.url)
        print(f"\n🗄️  База данных:")
        print(f"   🔗 URL: {masked_db_url}")
        print(f"   🏊 Pool size: {db.pool_size}")
        print(f"   ⬆️  Max overflow: {db.max_overflow}")
        print(f"   ⏱️  Pool timeout: {db.pool_timeout}s")
        
        # Пути и директории
        print(f"\n📂 Пути:")
        print(f"   💾 Кэш: {yandex.cache_dir}")
        print(f"   📊 Метрики: {yandex.metrics_file}")
        
        print("="*60 + "\n")
        
    except ConfigError as e:
        print(f"\n❌ ОШИБКА КОНФИГУРАЦИИ: {e}\n")
        raise
    except Exception as e:
        print(f"\n❌ НЕОЖИДАННАЯ ОШИБКА: {e}\n")
        raise

def mask_database_url(db_url: str) -> str:
    """Маскирует пароль в URL базы данных"""
    if not db_url or '@' not in db_url:
        return db_url
    
    try:
        parts = db_url.split('@')
        if len(parts) == 2:
            user_pass = parts[0].split('//')[-1]
            if ':' in user_pass:
                user = user_pass.split(':')[0]
                return db_url.replace(user_pass, f"{user}:***")
        return db_url
    except:
        return db_url

def print_config_validation_report():
    """Детальный отчет о валидации конфигурации"""
    print("\n" + "="*60)
    print("ОТЧЕТ О ВАЛИДАЦИИ КОНФИГУРАЦИИ")
    print("="*60)
    
    validation_results = []
    
    # Проверяем Yandex Cloud конфигурацию
    try:
        yandex_config = YandexCloudConfig.from_env()
        validation_results.append(("✅ Yandex Cloud", "Конфигурация валидна"))
        
        # Проверяем модели
        for model_name, model_config in yandex_config.llm_models.items():
            validation_results.append((f"  🤖 LLM модель {model_name}", "Конфигурация валидна"))
        
        for model_name, model_config in yandex_config.embedding_models.items():
            validation_results.append((f"  🔍 Embedding модель {model_name}", "Конфигурация валидна"))
            
    except Exception as e:
        validation_results.append(("❌ Yandex Cloud", f"Ошибка: {e}"))
    
    # Проверяем Ollama конфигурацию
    try:
        ollama_config = OllamaConfig.from_env()
        validation_results.append(("✅ Ollama", "Конфигурация валидна"))
    except Exception as e:
        validation_results.append(("❌ Ollama", f"Ошибка: {e}"))
    
    # Проверяем Database конфигурацию
    try:
        db_config = DatabaseConfig.from_env()
        validation_results.append(("✅ База данных", "Конфигурация валидна"))
    except Exception as e:
        validation_results.append(("❌ База данных", f"Ошибка: {e}"))
    
    # Выводим результаты
    for component, status in validation_results:
        print(f"{component}: {status}")
    
    # Подсчитываем статистику
    total = len(validation_results)
    passed = sum(1 for _, status in validation_results if "валидна" in status)
    
    print(f"\n📊 Статистика валидации:")
    print(f"   Всего компонентов: {total}")
    print(f"   Прошли валидацию: {passed}")
    print(f"   Не прошли валидацию: {total - passed}")
    print(f"   Успешность: {(passed/total)*100:.1f}%")
    
    print("="*60 + "\n")

# Список всех поддерживаемых переменных окружения
SUPPORTED_ENV_VARS = [
    # Yandex Cloud - основные
    "YANDEX_API_KEY",
    "YANDEX_FOLDER_ID", 
    "YANDEX_LLM_MODEL",
    "YANDEX_EMBEDDING_MODEL",
    "YANDEX_BASE_URL",
    "USE_YANDEX_CLOUD",
    
    # Yandex Cloud - параметры запросов
    "YANDEX_MAX_TOKENS",
    "YANDEX_TEMPERATURE",
    "YANDEX_TIMEOUT",
    "YANDEX_MAX_RETRIES",
    "YANDEX_RETRY_DELAY",
    "YANDEX_MAX_REQUESTS_PER_MINUTE",
    "YANDEX_MAX_CONCURRENT",
    
    # Yandex Cloud - кэширование
    "YANDEX_ENABLE_CACHING",
    "YANDEX_CACHE_DIR",
    "YANDEX_CACHE_TTL_HOURS",
    
    # Yandex Cloud - мониторинг
    "YANDEX_ENABLE_METRICS",
    "YANDEX_METRICS_FILE",
    "YANDEX_ENABLE_PERFORMANCE_MONITORING",
    
    # Yandex Cloud - fallback
    "YANDEX_FALLBACK_TO_OLLAMA",
    "YANDEX_FALLBACK_PROVIDER",
    "YANDEX_FALLBACK_TIMEOUT",
    
    # Ollama
    "OLLAMA_HOST",
    "OLLAMA_TIMEOUT",
    "OLLAMA_MAX_RETRIES",
    "OLLAMA_LLM_MODEL",
    "OLLAMA_EMBEDDING_MODEL",
    
    # Database
    "DATABASE_URL",
    "DB_POOL_SIZE",
    "DB_MAX_OVERFLOW",
    "DB_POOL_TIMEOUT",
    "DB_POOL_RECYCLE",
    
    # Application
    "DEBUG",
    "LOG_LEVEL",
    "ENVIRONMENT",
    "SECRET_KEY",
    "ALLOWED_HOSTS"
]

def check_env_completeness():
    """Проверка полноты переменных окружения"""
    missing_vars = []
    set_vars = []
    
    for var in SUPPORTED_ENV_VARS:
        if os.getenv(var) is not None:
            set_vars.append(var)
        else:
            missing_vars.append(var)
    
    print(f"\n📋 Установлено переменных: {len(set_vars)}/{len(SUPPORTED_ENV_VARS)}")
    
    if set_vars:
        print("✅ Установленные переменные:")
        for var in set_vars:
            if "KEY" in var or "PASSWORD" in var:
                print(f"   {var}=***")
            else:
                print(f"   {var}={os.getenv(var)}")
    
    if missing_vars:
        print("⚠️  Отсутствующие переменные:")
        for var in missing_vars:
            print(f"   {var}")
        print("\nСкопируйте .env.example в .env и заполните необходимые значения.")
    
    print()

if __name__ == "__main__":
    # Запуск валидации при прямом вызове модуля
    print_config_summary()
    check_env_completeness()