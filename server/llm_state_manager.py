# УРЕЗАННАЯ ВЕРСИЯ БЕЗ OLLAMA - ЗАГЛУШКА
# Этот файл содержит заглушки для LLMStateManager

class LLMStateManager:
    """Заглушка для LLMStateManager"""
    
    def __init__(self):
        pass
    
    def initialize_llm(self, *args, **kwargs):
        """Заглушка для инициализации LLM"""
        return False
    
    def is_department_initialized(self, *args, **kwargs):
        """Заглушка для проверки инициализации отдела"""
        return False
    
    def get_department_chat(self, *args, **kwargs):
        """Заглушка для получения чата отдела"""
        return None
    
    def get_initialized_departments(self, *args, **kwargs):
        """Заглушка для получения инициализированных отделов"""
        return []

# Глобальный экземпляр
_llm_state_manager = None

def get_llm_state_manager():
    """Заглушка для получения менеджера состояния"""
    global _llm_state_manager
    if _llm_state_manager is None:
        _llm_state_manager = LLMStateManager()
    return _llm_state_manager 