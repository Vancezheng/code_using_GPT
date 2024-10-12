import streamlit as st
import work.work as work
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union


def doc_code(code_str,chat)->str:
    """
    Takes a code string and a chat input, splits the code into lines based on a
    file type, runs future code documentation on each line, and returns the combined
    results as a string.

    Args:
        code_str (str): Passed as input to the function, representing a string
            containing code.
        chat (str): Passed to the `work.doc_futures_run` method, which implies it
            is used for documentation or running code in a chat environment.

    Returns:
        str: A string containing the results of executing code snippets from the
        input `code_str`, processed according to the file type specified in `st.session_state.file_type`.

    """
    spliter = work.get_file_type(st.session_state.file_type)
    code_split_ = work.code_splite(code_str,spliter)
    result = ""
    results = work.doc_futures_run(code_split_,chat)
    for i in results:
        result += i
    return result

def code_with_comment(code_str,chat)->str:
    """
    Takes a code string and chat input, splits the code into lines based on its
    type, adds comments for future runs, and returns the modified code with comments.

    Args:
        code_str (str): A string containing the code to be processed, likely a
            string representation of a code snippet or a file.
        chat (str): Used to pass a string containing chat messages or other
            information to be used in conjunction with the code splitting and
            commenting process.

    Returns:
        str: A string containing the commented code split into lines from the input
        code string.

    """
    spliter = work.get_file_type(st.session_state.file_type)
    code_split_ = work.code_splite(code_str,spliter)
    result = ""
    results = work.comment_future_run(code_split_,chat)
    for i in results:
        result += i
    return result

def qa_with_code(question:str,code_str,chat)->str:
    """
    Processes user input by splitting code into segments based on file type,
    generates embeddings, and then uses a code-chain model to answer a question
    related to the code, returning the result.

    Args:
        question (str): Passed to the `work.qa_with_code_chain` function, where
            it is used as a query to retrieve an answer from a knowledge base.
        code_str (str): Expected to be a string containing code that needs to be
            processed, split, and used in the QA process.
        chat (str): Used as input for the `work.qa_with_code_chain` function, which
            implies it is a string representing a chat or conversation.

    Returns:
        str: The result of the question answering process with the given code and
        question.

    """
    spliter = work.get_file_type(st.session_state.file_type)
    code_split_ = work.code_splite(code_str,spliter)
    db = work.get_code_embd_save(code_split_)
    result = work.qa_with_code_chain(db = db,question=question,chat = chat)
    return result



st.title(":blue[Analyzing code using GPT 🤖]")


if 'code' not in st.session_state:
    st.session_state.code = ""
if 'doc_result' not in st.session_state:
    st.session_state.doc_result = ""
if 'comment_result' not in st.session_state:
    st.session_state.comment_result = ""
if 'file_type' not in st.session_state:
    st.session_state.file_type = ""

with st.sidebar:
    st.title(":blue[ChatGPT 🤖]")
    openai_api_key = st.text_input("OpenAI API Key", key="chatbot_api_key", type="password")
    model_name = st.selectbox(
    '选择Openai模型',
    ('gpt-3.5-turbo', 'gpt-3.5-turbo-16k', 'gpt-3.5-turbo-0613','gpt-3.5-turbo-16k-0613','gpt-4','gpt-4-0613','gpt-4-32k','gpt-4-32k-0613'))
    temperature = st.slider('设置模型温度值', 0.0, 2.0, 0.5)   

if not openai_api_key:
    st.error("请输入OpenAI API Key")
    st.stop()
else:
    st.session_state.chat = work.load_env(openai_api_key=openai_api_key,model_name=model_name,temperature=temperature)




uploaded_file = st.file_uploader(label=":blue[上传代码文件]",type=[
    'cpp', 'cc', 'cxx', 'hpp', 'h', 'hxx', 
    'go', 'java', 'js', 'php', 'proto', 'py', 
    'rst', 'rb', 'rs', 'scala', 'swift', 'md', 
    'markdown', 'tex', 'html', 'sol'], help=":blue[仅支持所有主流代码文件]",key = "up_file")

if uploaded_file is not None:
    with st.sidebar:
        st.title(f"{uploaded_file.name}文件源码:")
        code_str = uploaded_file.getvalue().decode("utf-8")
        st.session_state.file_type = uploaded_file.name
        st.session_state.code = code_str
        st.code(code_str,language="python")
    col1, col2 = st.columns(spec= [0.5,0.5], gap = "large")
    with col1:
        comment_bt = st.button("插入注释")
    if comment_bt:
        with st.spinner("正在插入注释..."):
            result = code_with_comment(st.session_state.code,st.session_state.chat)
        st.session_state.comment_result = result
        st.success("注释插入完成")
    with col2:
        doc_code_bt = st.button("生成文档")
    if doc_code_bt:
        with st.spinner("正在生成文档..."):
            result = doc_code(st.session_state.code,st.session_state.chat)
        st.session_state.doc_result = result
        st.success("文档生成完成")
if st.session_state.comment_result != "":
    with st.expander("注释结果"):
        st.code(st.session_state.comment_result,language="python")
        st.download_button(
            label="下载注释后文件",
            data=st.session_state.comment_result,
            file_name='llmadd.py',)
if st.session_state.doc_result != "":
    with st.expander("文档内容"):
        st.markdown(st.session_state.doc_result)
        st.download_button(
            label="下载文档",
            data=st.session_state.doc_result,
            file_name='doc.md',)

# chat 
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "ai", "avatar":"🤖", "content": "我是强大的人工智能助手,请上传你的代码文件，我将帮助你更好了解代码！"}]
for msg in st.session_state.messages:
    st.chat_message(name=msg["role"],avatar=msg["avatar"]).markdown(msg["content"])

if st.session_state.code == "":
    st.error("请上传代码文件")
    st.stop()
prompt = st.chat_input(placeholder="咨询与代码文件有关问题",max_chars = 4000,key="prompt")
if prompt:

    st.session_state.messages.append({"role": "human", "avatar":"🧑", "content": prompt})

    st.chat_message(name="human",avatar="🧑").markdown(prompt)

    with st.chat_message(name="ai",avatar="🤖"):
        with st.spinner("正在生成答案..."):
            response = qa_with_code(prompt,st.session_state.code,st.session_state.chat)

        st.session_state.messages.append({"role": "ai", "avatar":"🤖", "content": response})

        st.markdown(response)

