from operator import itemgetter

from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.memory import ConversationBufferMemory
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_core.messages import get_buffer_string
from langchain_core.prompts import format_document
from langchain.prompts.prompt import PromptTemplate


condense_question = """Учитывая следующий разговор и последующий вопрос, переформулируйте последующий вопрос так, чтобы он стал самостоятельным вопросом.

Chat History:
{chat_history}

Follow Up Input: {question}
Standalone question:"""
CONDENSE_QUESTION_PROMPT = PromptTemplate.from_template(condense_question)

answer = """
### Instruction:
Ты полезный рабочий ассисент, который отвечает на вопросы на основе предоставленных документов кратким и понятным образом, цитируя эти документы(отображая их в виде ссылок).
Если вопрос не имеет отношения к предоставленным документам, просто ответьте в свободной форме(беря в контекст только запрос пользователя).

## Research:
{context}

## Question:
{question}
"""
ANSWER_PROMPT = ChatPromptTemplate.from_template(answer)

DEFAULT_DOCUMENT_PROMPT = PromptTemplate.from_template(
    template="Source Document: {source}, Page {page}:\n{page_content}"
)


def _combine_documents(
    docs, document_prompt=DEFAULT_DOCUMENT_PROMPT, document_separator="\n\n"
):
    doc_strings = [format_document(doc, document_prompt) for doc in docs]
    return document_separator.join(doc_strings)


def getStreamingChain(question: str, memory, llm, db):
    retriever = db.as_retriever(search_kwargs={"k": 10})
    loaded_memory = RunnablePassthrough.assign(
        chat_history=RunnableLambda(
            lambda x: "\n".join(
                [f"{item['role']}: {item['content']}" for item in x["memory"]]
            )
        ),
    )

    standalone_question = {
        "standalone_question": {
            "question": lambda x: x["question"],
            "chat_history": lambda x: x["chat_history"],
        }
        | CONDENSE_QUESTION_PROMPT
        | llm
        | (lambda x: x.content if hasattr(x, "content") else x)
    }

    retrieved_documents = {
        "docs": itemgetter("standalone_question") | retriever,
        "question": lambda x: x["standalone_question"],
    }

    final_inputs = {
        "context": lambda x: _combine_documents(x["docs"]),
        "question": itemgetter("question"),
    }

    answer = final_inputs | ANSWER_PROMPT | llm

    final_chain = loaded_memory | standalone_question | retrieved_documents | answer

    return final_chain.stream({"question": question, "memory": memory})


def getChatChain(llm, db):
    retriever = db.as_retriever(search_kwargs={"k": 10})

    def chat(question: str):
        # Инициализация памяти для каждого запроса
        memory = ConversationBufferMemory(return_messages=True, output_key="answer", input_key="question")
        
        loaded_memory = RunnablePassthrough.assign(
            chat_history=RunnableLambda(memory.load_memory_variables)
            | itemgetter("history"),
        )

        standalone_question = {
            "standalone_question": {
                "question": lambda x: x["question"],
                "chat_history": lambda x: get_buffer_string(x["chat_history"]),
            }
            | CONDENSE_QUESTION_PROMPT
            | llm
            | (lambda x: x.content if hasattr(x, "content") else x)
        }

        # Теперь мы извлекаем документы
        retrieved_documents = {
            "docs": itemgetter("standalone_question") | retriever,
            "question": lambda x: x["standalone_question"],
        }

        # Теперь мы строим входные данные для финального запроса
        final_inputs = {
            "context": lambda x: _combine_documents(x["docs"]),
            "question": itemgetter("question"),
        }

        # И, наконец, мы делаем часть, которая возвращает ответы
        answer = {
            "answer": final_inputs
            | ANSWER_PROMPT
            | llm.with_config(callbacks=[StreamingStdOutCallbackHandler()]),
            "docs": itemgetter("docs"),
        }

        final_chain = loaded_memory | standalone_question | retrieved_documents | answer

        try:
            print(f"getChatChain: обработка вопроса: {question}")
            inputs = {"question": question}
            result = final_chain.invoke(inputs)
            
            if "answer" not in result:
                print("getChatChain: ключ 'answer' отсутствует в результате")
                return "Не удалось получить ответ от модели"
                
            answer_content = result["answer"].content if hasattr(result["answer"], "content") else result["answer"]
            memory.save_context(inputs, {"answer": answer_content})
            
            print(f"getChatChain: успешный ответ: {answer_content[:100]}...")
            return answer_content
        except Exception as e:
            import traceback
            print(f"getChatChain: ошибка при обработке вопроса: {str(e)}")
            print(traceback.format_exc())
            return f"Произошла ошибка при обработке запроса: {str(e)}"

    return chat
