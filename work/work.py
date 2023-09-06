import os
from dotenv import load_dotenv
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union
import concurrent.futures
from langchain.chains.base import Chain
from langchain.prompts import PromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts.chat import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.text_splitter import (
    RecursiveCharacterTextSplitter,
    Language,
)
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from template.template import(
    code_with_comment_chain_systemtemplate,
    doc_code_chain_systemtemplate,
    qa_with_code_chain_systemtemplate
    )

load_dotenv()

os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

CHUNK_SIZE = 3000

chat = ChatOpenAI(model="gpt-3.5-turbo-16k",temperature=0.5,streaming=True)


def get_code_embd_save(code_split:List[str])->Chroma:
    embeddings = OpenAIEmbeddings()
    db = Chroma.from_texts(texts=code_split,embedding=embeddings)   
    return db


def qa_with_code_chain(db:Chroma,question:str)->str:
    retrievers_re = ""
    retrievers = db.as_retriever(search_kwargs={'k': 4,})
    doc_re = retrievers.get_relevant_documents(question)
    for i in doc_re:
        retrievers_re += i.page_content   
    human_prompt = """
    根据下面代码内容回答问题：
    --------------------
    {retrievers_re}
    --------------------
    问题：{question}
    """
    human_message_prompt = HumanMessagePromptTemplate(
        prompt=PromptTemplate(
            template=human_prompt,
            input_variables=["question"],
            partial_variables={"retrievers_re": retrievers_re}
        )
    )
    chat_prompt_template = ChatPromptTemplate.from_messages([
        ("system", qa_with_code_chain_systemtemplate),
        human_message_prompt
    ])
    chain = LLMChain(llm=chat, prompt=chat_prompt_template)
    answer = chain.run(question)
    return answer

def code_splite(code:str)->List[str]:
    python_splitter = RecursiveCharacterTextSplitter.from_language(
        language=Language.PYTHON,chunk_size=CHUNK_SIZE, chunk_overlap=0
    )
    splite_code = python_splitter.split_text(text=code)

    return splite_code

def code_with_comment_chain(code:str)->str:
    chat_prompt_template = ChatPromptTemplate.from_messages([
        ("system", code_with_comment_chain_systemtemplate),
        ("human","{text}")
    ])
    chain = LLMChain(llm=chat, prompt=chat_prompt_template)
    result = chain.run(code)
    return result

def code_doc_chain(code: str) -> str:
    chat_prompt_template = ChatPromptTemplate.from_messages([
        ("system", doc_code_chain_systemtemplate),
        ("human", "{text}")
    ])
    chain = LLMChain(llm=chat, prompt=chat_prompt_template)
    result = chain.run(code)
    return  result

def doc_futures_run(code_list:List[str])->List[str]:

    results = []

    with concurrent.futures.ThreadPoolExecutor() as executor:

        futures = [executor.submit(code_doc_chain, _i) for _i in code_list]
        
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            results.append(result)
    return results

def comment_future_run(code_list:List[str])->List[str]:
    results = []

    with concurrent.futures.ThreadPoolExecutor() as executor:

        futures = [executor.submit(code_with_comment_chain, _i) for _i in code_list]
        
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            results.append(result)
    return results




    