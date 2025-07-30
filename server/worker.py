# УРЕЗАННАЯ ВЕРСИЯ БЕЗ OLLAMA - ЗАГЛУШКА
# Этот файл содержит заглушки для worker.py

import os
import sys
import time

def process_llm_query(message):
    """Заглушка для обработки запроса к LLM"""
    print("LLM functionality disabled")
    return {"error": "LLM functionality disabled"}

if __name__ == "__main__":
    print("Worker disabled - LLM functionality not available")
    # Бесконечный цикл для предотвращения завершения
    while True:
        time.sleep(60)
        print("Worker is running but LLM functionality is disabled")

