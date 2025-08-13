# README

<p align="center">
    <img src="images/image.png" alt="Скриншот веб-интерфейса Streamlit" width="600">
</p>


Thank you very much to [amscotti](https://github.com/amscotti) whose repository I used as a basis. Thanks to him, I was able to implement this code



## Требования

- [Python] версия 3.13 или выше.


## Установка
1. Клонируемся через------------------>`git clone`
2. В терминале------------------------>`python -m venv .venv`
3. Устанавливаем зависимости---------->`pip install requirements.txt`



## Запуск
1. Запускаем СЕРВЕР------------------->`uvicorn app:app --host 0.0.0.0 --port 8000` 
2. Запускаем ИНТЕРФЕЙС ПОЛЬЗОВАТЕЛЯ--->`streamlit run main_page.py`


## Используемые технологии
- [Langchain](https://github.com/langchain/langchain): Библиотека Python для работы с большими языковыми моделями.

- [Chroma](https://docs.trychroma.com/): Векторная база данных для хранения и извлечения встраиваний.
- [PyPDF](https://pypi.org/project/PyPDF2/): Библиотека Python для чтения и манипуляции PDF файлами.
- [Streamlit](https://streamlit.io/): Веб-фреймворк для создания интерактивных приложений для проектов в области машинного обучения и науки о данных.
- [UV](https://astral.sh/uv): Быстрый и эффективный установщик и резольвер пакетов Python.




