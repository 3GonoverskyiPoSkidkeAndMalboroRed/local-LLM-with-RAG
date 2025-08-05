from langchain_community.document_loaders import (
    DirectoryLoader,
    PyPDFLoader,
    TextLoader,
    Docx2txtLoader
)
import os
from typing import List, Tuple
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from yandex_embeddings import create_embeddings
from config_utils import get_env_bool
from langchain.text_splitter import RecursiveCharacterTextSplitter
import time
import concurrent.futures
import threading

# Изменяем директорию для хранения данных на files/storage
PERSIST_DIRECTORY = "files/storage"
# Улучшенные параметры для лучшего качества RAG
TEXT_SPLITTER = RecursiveCharacterTextSplitter(
    chunk_size=1500,  # Увеличиваем размер чанка для лучшего контекста
    chunk_overlap=200,  # Оптимизируем перекрытие
    length_function=len,
    separators=["\n\n", "\n", ". ", " ", ""]  # Более точные разделители
)
# Получение URL для Ollama из переменной окружения или использование значения по умолчанию
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

def get_embedding_function(model_name: str):
    """
    Получение функции эмбеддингов только через Yandex Cloud.
    Ollama fallback отключен для полного использования Yandex API.
    
    Args:
        model_name: Название модели эмбеддингов
        
    Returns:
        Экземпляр YandexEmbeddings
    """
    print(f"Используем YandexEmbeddings с моделью {model_name}")
    from yandex_embeddings import create_yandex_embeddings
    return create_yandex_embeddings(model=model_name)

def vec_search(embedding_model, query, db, n_top_cos: int = 10, timeout: int = 20):
    """
    Улучшенный поиск в векторной базе Chroma с множественными стратегиями поиска.
    
    Args:
        embedding_model: Модель для создания эмбеддингов
        query (str): Текст запроса
        db: Векторная база данных
        n_top_cos (int): Количество результатов для возврата
        timeout (int): Таймаут в секундах для операции поиска
        
    Returns:
        tuple: Кортеж из трех списков - топ-фрагменты, scores, metadata
    """
    start_time = time.time()
    result = []
    error = None
    
    def enhance_query(original_query: str) -> List[str]:
        """Генерирует дополнительные варианты запроса для лучшего поиска"""
        queries = [original_query]
        
        # Добавляем ключевые слова
        words = original_query.lower().split()
        if len(words) > 1:
            # Добавляем отдельные ключевые слова
            for word in words:
                if len(word) > 3:  # Игнорируем короткие слова
                    queries.append(word)
        
        # Добавляем варианты без вопросительных слов
        question_words = ['что', 'как', 'где', 'когда', 'почему', 'какой', 'кто']
        filtered_query = ' '.join([word for word in words if word not in question_words])
        if filtered_query and filtered_query != original_query:
            queries.append(filtered_query)
        
        return queries[:2]  # Оптимизация: только 2 варианта вместо 3
    
    # Функция для выполнения поиска в отдельном потоке
    def search_task():
        nonlocal result, error
        try:
            print(f"Начало улучшенного поиска для запроса: {query[:50]}...")
            
            # Генерируем варианты запроса
            query_variants = enhance_query(query)
            print(f"Сгенерировано {len(query_variants)} вариантов запроса")
            
            all_results = []
            seen_content = set()
            
            for i, q in enumerate(query_variants):
                print(f"Поиск по варианту {i+1}: {q[:30]}...")
                
                # Кодируем запрос в вектор
                try:
                    # Проверяем, что запрос не пустой
                    if not q or not q.strip():
                        print(f"Пропускаем пустой запрос: '{q}'")
                        continue
                        
                    # Используем embed_query для поисковых запросов (более подходящий метод)
                    if hasattr(embedding_model, 'embed_query'):
                        query_emb = embedding_model.embed_query(q)
                    else:
                        # Fallback для совместимости
                        query_emb = embedding_model.embed_documents([q])[0]
                except Exception as embed_error:
                    print(f"Ошибка создания эмбеддинга для запроса '{q}': {embed_error}")
                    continue
                
                # Оптимизированный поиск - используем similarity_search_with_score для получения scores
                try:
                    # Проверяем, что db имеет правильный тип
                    if hasattr(db, 'similarity_search_with_score'):
                        search_result = db.similarity_search_with_score(query_emb, k=n_top_cos)
                    elif hasattr(db, 'similarity_search_by_vector'):
                        search_result = db.similarity_search_by_vector(query_emb, k=n_top_cos)
                        # Преобразуем в формат с scores
                        search_result = [(doc, 0.8) for doc in search_result]  # Фиктивный score
                    elif hasattr(db, 'similarity_search'):
                        search_result = db.similarity_search(q, k=n_top_cos)
                        # Преобразуем в формат с scores
                        search_result = [(doc, 0.8) for doc in search_result]  # Фиктивный score
                    else:
                        print(f"Неподдерживаемый тип базы данных: {type(db)}")
                        continue
                        
                    for doc, score in search_result:
                        content = doc.page_content if hasattr(doc, 'page_content') else str(doc)
                        # Избегаем дубликатов по содержимому
                        content_hash = hash(content[:100])  # Используем первые 100 символов для хеша
                        if content_hash not in seen_content:
                            seen_content.add(content_hash)
                            all_results.append((doc, score))
                except Exception as method_error:
                    print(f"Ошибка в поиске: {method_error}")
                    continue
            
            # Сортируем результаты по score и берем топ
            all_results.sort(key=lambda x: x[1], reverse=True)  # Сортируем по score
            if len(all_results) > n_top_cos:
                all_results = all_results[:n_top_cos]
            
            print(f"Найдено {len(all_results)} уникальных результатов")
            
            # Извлечение фрагментов, scores и метаданных
            top_chunks = []
            top_scores = []
            top_metadata = []
            
            for doc, score in all_results:
                chunk_content = ""
                metadata = {}
                
                if hasattr(doc, 'page_content') and doc.page_content.strip():
                    chunk_content = doc.page_content
                    top_chunks.append(chunk_content)
                elif hasattr(doc, 'metadata') and 'chunk' in doc.metadata:
                    chunk_content = doc.metadata.get('chunk')
                    if chunk_content and chunk_content.strip():
                        top_chunks.append(chunk_content)
                
                if hasattr(doc, 'metadata') and doc.metadata:
                    metadata = doc.metadata
                
                top_scores.append(score)
                top_metadata.append(metadata)
            
            # Фильтруем слишком короткие чанки
            filtered_chunks = []
            filtered_scores = []
            filtered_metadata = []
            
            for chunk, score, meta in zip(top_chunks, top_scores, top_metadata):
                if len(chunk.strip()) > 50:
                    filtered_chunks.append(chunk)
                    filtered_scores.append(score)
                    filtered_metadata.append(meta)
            
            print(f"Отфильтровано {len(filtered_chunks)} содержательных фрагментов")
            
            result = [filtered_chunks, filtered_scores, filtered_metadata]
        except Exception as e:
            import traceback
            print(f"Ошибка в vec_search: {e}")
            print(traceback.format_exc())
            error = e
    
    # Запускаем поиск в отдельном потоке с таймаутом
    search_thread = threading.Thread(target=search_task)
    search_thread.daemon = True
    search_thread.start()
    search_thread.join(timeout)
    
    if search_thread.is_alive():
        # Если поток все еще выполняется после таймаута
        print(f"Превышен таймаут ({timeout} сек) при выполнении векторного поиска")
        return [], [], []
    
    if error:
        print(f"Произошла ошибка при векторном поиске: {error}")
        return [], [], []
    
    if not result:
        print("Векторный поиск не вернул результатов")
        return [], [], []
    
    print(f"Улучшенный векторный поиск успешно завершен за {time.time() - start_time:.2f} секунд")
    return result[0], result[1], result[2] if len(result) > 2 else []

def load_documents_into_database(model_name: str, documents_path: str, department_id: str, reload: bool = True) -> Chroma:
    """
    Загружает документы из указанной директории в векторную базу данных Chroma
    после разделения текста на части, создавая базу данных для конкретного отдела.

    Args:
        model_name (str): Название модели эмбеддинга.
        documents_path (str): Путь к директории с документами.
        department_id (str): Идентификатор отдела для создания уникальной базы данных.
        reload (bool): Нужно ли перезагружать существующие документы. По умолчанию True.

    Returns:
        Chroma: Векторная база данных с загруженными документами.
    """
    print(f"DEBUG: Начало load_documents_into_database")
    print(f"DEBUG: model_name={model_name}, documents_path={documents_path}, department_id={department_id}, reload={reload}")
    
    # ВСЕГДА создаем директорию ContentForDepartment для отдела, если она не существует
    content_department_path = f"files/ContentForDepartment/{department_id}"
    if not os.path.exists(content_department_path):
        print(f"Создаем директорию для документов отдела {department_id}: {content_department_path}")
        os.makedirs(content_department_path, exist_ok=True)
        
        # Если директория пуста, создаем пустой файл README.md
        if not os.listdir(content_department_path):
            readme_path = os.path.join(content_department_path, "README.md")
            with open(readme_path, 'w') as f:
                f.write("# Директория для документов\n\nЭта директория создана для хранения документов для RAG.")
            print(f"Создан файл README.md в {content_department_path}")
    else:
        print(f"Директория для документов отдела {department_id} уже существует: {content_department_path}")
    
    # Определяем директорию для хранения данных в зависимости от отдела
    department_directory = f"{PERSIST_DIRECTORY}/{department_id}"
    print(f"DEBUG: department_directory={department_directory}")

    # Создаем директорию для хранения данных, если она не существует
    os.makedirs(PERSIST_DIRECTORY, exist_ok=True)
    os.makedirs(department_directory, exist_ok=True)

    # Проверяем существует ли директория для хранения данных
    if os.path.exists(department_directory) and not reload:
        print(f"Загрузка существующей базы данных Chroma для отдела {department_id}...")
        db = Chroma(
            embedding_function=get_embedding_function(model_name),
            persist_directory=department_directory
        )
        return db
    
    # Если нужно перезагрузить документы или директория не существует
    print(f"Загрузка документов для отдела {department_id}...")
    
    # Автоматически формируем путь на основе ID отдела
    print(f"DEBUG: Исходный documents_path: {documents_path}")
    if not documents_path.startswith('files/'):
        # Если передан просто ID отдела или название, формируем полный путь
        if documents_path.isdigit():
            # Если передан только ID отдела, используем стандартную структуру
            documents_path = f"files/ContentForDepartment/{documents_path}"
            print(f"DEBUG: Сформирован путь для отдела: {documents_path}")
        else:
            # Если передан путь, добавляем префикс
            documents_path = f"files/{documents_path}"
            print(f"DEBUG: Добавлен префикс к пути: {documents_path}")
    else:
        print(f"DEBUG: Путь уже содержит files/: {documents_path}")
    
    # Проверяем существование пути к документам
    if not os.path.exists(documents_path):
        print(f"Путь к документам не существует: {documents_path}")
        print(f"Текущая директория: {os.getcwd()}")
        print(f"Содержимое директории /app/files/: {os.listdir('/app/files/') if os.path.exists('/app/files/') else 'директория не существует'}")
        
        # Создаем директорию, если она не существует
        try:
            os.makedirs(documents_path, exist_ok=True)
            print(f"Создана директория: {documents_path}")
            
            # Если директория пуста, создаем пустой файл README.md
            readme_path = os.path.join(documents_path, "README.md")
            if not os.listdir(documents_path):
                with open(readme_path, 'w') as f:
                    f.write("# Директория для документов\n\nЭта директория создана для хранения документов для RAG.")
                print(f"Создан файл README.md в {documents_path}")
        except Exception as e:
            print(f"Ошибка при создании директории: {e}")
            raise FileNotFoundError(f"Не удалось создать директорию: {documents_path}. Ошибка: {e}")
    
    try:
        print(f"DEBUG: Загружаем документы из: {documents_path}")
        raw_documents = load_documents(documents_path)
        print(f"DEBUG: Загружено {len(raw_documents)} документов")
        for i, doc in enumerate(raw_documents[:3]):  # Показываем первые 3 документа
            source = doc.metadata.get('source', 'unknown') if hasattr(doc, 'metadata') else 'unknown'
            print(f"DEBUG: Документ {i+1}: {source}")
    except Exception as e:
        print(f"Ошибка при загрузке документов: {e}")
        # Если нет документов, создаем пустую базу
        return Chroma.from_documents(
            documents=[],
            embedding=get_embedding_function(model_name),
            persist_directory=department_directory
        )
    
    # Если директория для хранения существует, получаем список уже загруженных файлов
    loaded_files = set()
    if os.path.exists(department_directory):
        try:
            db = Chroma(
                embedding_function=get_embedding_function(model_name),
                persist_directory=department_directory
            )
            # Получаем список файлов, которые уже есть в базе
            all_docs = db.get()
            if all_docs and all_docs.get('metadatas'):
                for metadata in all_docs['metadatas']:
                    if metadata and 'source' in metadata:
                        loaded_files.add(metadata['source'])
            print(f"Уже загружено {len(loaded_files)} файлов")
        except Exception as e:
            print(f"Ошибка при попытке получить список загруженных файлов: {e}")
            # Если произошла ошибка, считаем что нет загруженных файлов
            loaded_files = set()
    
    # Фильтруем только новые документы
    new_documents = []
    for doc in raw_documents:
        if hasattr(doc, 'metadata') and 'source' in doc.metadata:
            if doc.metadata['source'] not in loaded_files:
                new_documents.append(doc)
        else:
            # Если у документа нет метаданных о источнике, добавляем его
            new_documents.append(doc)
    
    print(f"Найдено {len(new_documents)} новых документов из {len(raw_documents)} всего")
    
    if not new_documents:
        print("Нет новых документов для загрузки")
        # Возвращаем существующую базу данных
        if os.path.exists(department_directory):
            return Chroma(
                embedding_function=get_embedding_function(model_name),
                persist_directory=department_directory
            )
        # Если директории нет, но и новых документов нет - создаем пустую базу
        return Chroma.from_documents(
            documents=[],
            embedding=get_embedding_function(model_name),
            persist_directory=department_directory
        )
    
    # Разбиваем новые документы на чанки
    documents = TEXT_SPLITTER.split_documents(new_documents)
    print(f"Разбито на {len(documents)} чанков")
    
    # Фильтруем пустые чанки
    filtered_documents = []
    for doc in documents:
        if hasattr(doc, 'page_content') and doc.page_content and doc.page_content.strip():
            filtered_documents.append(doc)
    
    print(f"После фильтрации пустых чанков осталось {len(filtered_documents)} документов")
    documents = filtered_documents
    
    # Создаем встраивания и загружаем в Chroma
    print("Создание встраиваний и загрузка документов в Chroma...")
    
    # Если директория существует, добавляем к существующей базе
    if os.path.exists(department_directory):
        db = Chroma(
            embedding_function=get_embedding_function(model_name),
            persist_directory=department_directory
        )
        db.add_documents(documents)
        return db
    else:
        # Иначе создаем новую базу
        return Chroma.from_documents(
            documents=documents,
            embedding=get_embedding_function(model_name),
            persist_directory=department_directory
        )


def load_documents(path: str) -> List[Document]:
    """
    Loads documents from the specified directory path.

    This function supports loading of PDF, Markdown, and HTML documents by utilizing
    different loaders for each file type. It checks if the provided path exists and
    raises a FileNotFoundError if it does not. It then iterates over the supported
    file types and uses the corresponding loader to load the documents into a list.

    Args:
        path (str): The path to the directory containing documents to load.

    Returns:
        List[Document]: A list of loaded documents.

    Raises:
        FileNotFoundError: If the specified path does not exist.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"The specified path does not exist: {path}")

    # Проверяем, есть ли файлы в директории
    files = os.listdir(path)
    if not files:
        print(f"Директория {path} пуста")
        return []

    loaders = {
        ".pdf": DirectoryLoader(
            path,
            glob="**/*.pdf",
            loader_cls=PyPDFLoader,
            show_progress=True,
            use_multithreading=True,
        ),
        ".md": DirectoryLoader(
            path,
            glob="**/*.md",
            loader_cls=TextLoader,
            show_progress=True,
        ),
        ".txt": DirectoryLoader(
            path,
            glob="**/*.txt",
            loader_cls=TextLoader,
            show_progress=True,
        ),
        ".docx": DirectoryLoader(
            path,
            glob="**/*.docx",
            loader_cls=Docx2txtLoader,
            show_progress=True,
        ),
    }

    docs = []
    for file_type, loader in loaders.items():
        print(f"Loading {file_type} files")
        try:
            docs.extend(loader.load())
        except Exception as e:
            print(f"Ошибка при загрузке файлов типа {file_type}: {e}")
    
    return docs

def rerank_results(query: str, results: List[Document], top_k: int = 5) -> List[Tuple[Document, float]]:
    """
    Повторно ранжирует результаты на основе дополнительного анализа.

    Args:
        query (str): Исходный текст запроса.
        results (List[Document]): Список документов, полученных из векторного поиска.
        top_k (int): Количество топовых результатов для возврата.

    Returns:
        List[Tuple[Document, float]]: Список кортежей, содержащих документ и его новый ранг.
    """
    # Пример: Используем простую метрику на основе длины совпадения с запросом
    ranked_results = []
    for doc in results:
        # Пример метрики: количество совпадений слов из запроса в документе
        score = sum(1 for word in query.split() if word in doc.page_content)
        ranked_results.append((doc, score))
    
    # Сортируем результаты по убыванию ранга
    ranked_results.sort(key=lambda x: x[1], reverse=True)
    
    # Возвращаем топовые результаты
    return ranked_results[:top_k]

# Пример использования
# results = vec_search(embedding_model, query, db, n_top_cos=10)
# reranked_results = rerank_results(query, results)
