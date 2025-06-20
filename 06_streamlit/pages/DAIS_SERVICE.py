# ==============================================================================
# 1. 필수 라이브러리 임포트 및 환경 설정
# ==============================================================================
import os, re, torch, numpy as np
import wikipediaapi
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from sentence_transformers import SentenceTransformer
from peft import PeftModel

# LangChain
from langchain_community.vectorstores.faiss import FAISS
from langchain_core.runnables import RunnableSequence
from langchain_core.prompts import PromptTemplate
from langchain_huggingface import HuggingFacePipeline
from huggingface_hub import login
import streamlit as st

# 로그인 (한 번만)
HF_TOKEN = os.getenv("HF_TOKEN")
login(token=HF_TOKEN)

# ==============================================================================
# 2. 모델 병합 & Hub 푸시 (한 번만 수행)
# ==============================================================================
BASE    = "Qwen/Qwen3-8B"
ADAPTER = "SIQRIT/DAIS-Qwen3-8B-qdora"

base       = AutoModelForCausalLM.from_pretrained(BASE, trust_remote_code=True)
tokenizer  = AutoTokenizer.from_pretrained(BASE, trust_remote_code=True)
peft_model = PeftModel.from_pretrained(base, ADAPTER, trust_remote_code=True)
merged     = peft_model.merge_and_unload()

specials = [
    "[DAIS_INSTRUCTION]", "[DAIS_STYLE]", "[DAIS_RULE]",
    "[DAIS_EXAMPLE]", "[HISTORY]", "[INPUT]", "[OUTPUT]", "[CONTEXT]"
]

tokenizer.add_special_tokens({"additional_special_tokens": specials})
merged.resize_token_embeddings(len(tokenizer))

# ==============================================================================
# 3. RAG용 리소스 로드
# ==============================================================================
merged.eval()

generator = pipeline(
    "text-generation",
    model=merged,
    tokenizer=tokenizer,
    device_map="auto",
    torch_dtype=torch.bfloat16,
    trust_remote_code=True
)

hf_pipeline = HuggingFacePipeline(pipeline=generator)

# ==============================================================================
# 4. 벡터 DB & 위키 API 초기화
# ==============================================================================
EMBED_MODEL = "nlpai-lab/KURE-v1"
DB_PATH     = "./vectordb/"
st_model    = SentenceTransformer(EMBED_MODEL)

class KUREEmbeddings:
    def __init__(self, m): self.m = m
    def __call__(self, texts):
        return self.m.encode([texts], normalize_embeddings=True)[0] if isinstance(texts, str) else self.m.encode(texts, normalize_embeddings=True)

# FAISS DB 로드 시 파일이 없으면 에러 메시지 출력 후 중단
try:
    faiss_store = FAISS.load_local(
        folder_path=DB_PATH,
        embeddings=KUREEmbeddings(st_model),
        allow_dangerous_deserialization=True
    )
except Exception as e:
    st.error(f"Vector DB 로드 실패: {e}")
    st.stop()

# Wikipedia API 초기화
wiki = wikipediaapi.Wikipedia(user_agent="DAIS-ScienceBot/1.0", language="ko")

# ==============================================================================
# 5. DAIS SFT 프롬프트 템플릿 정의
# ==============================================================================
PROMPT_TEMPLATE = """
[DAIS_INSTRUCTION]
너는 과학 AI 인플루언서 DAIS야.
{input}의 요청에 대해 {output}의 맥락을 **참고**해서 새로운 답변을 **요약해서** 생성해야해.
새로운 답변을 생성할때는 **128 tokens 이내**로 [DAIS_SYTLE]과 [DAIS_RULE]을 반드시 지켜야해.

[DAIS_STYLE]
1. 핵심만 쉽게 설명.
2. 반드시 반말.
3. 쾌활·위트·유머러스.

[DAIS_RULE]
1. 절대 한국어 이외 언어 사용 금지.
2. CoT 적용하여 **간단히** 표현.
3. 중복 표현 금지.
4. 맥락 기반 응답.
5. 반드시 **문장으로 끝낼 것**.

[DAIS_EXAMPLE]
Q: 블랙홀이 뭐야?
A: 블랙홀은 중력이 워낙 세서 빛조차 못 빠져나가는 우주의 구멍이야. 주변 물질을 빨아들이면서 커지기도 해! — DAIS

[HISTORY]
{history}

[INPUT]
{input}

[OUTPUT]
{output}

[CONTEXT]
"""
AGENT_PROMPT = PromptTemplate(input_variables=["history","input","output"], template=PROMPT_TEMPLATE)

# ==============================================================================
# 6. Tool 함수 정의: rag_db, rag_wiki
# ==============================================================================
def tool_rag_db(query: str):
    docs = faiss_store.similarity_search_with_score(query, k=1)
    return {"doc": docs[0][0], "score": docs[0][1]} if docs else {"doc": None, "score": 0.0}

def tool_rag_wiki(query: str):
    page = wiki.page(query)
    summary = page.summary[:1000] if page.exists() else "위키피디아에 관련 정보가 없습니다."
    return {"doc": summary, "score": None}

# ==============================================================================
# 7. RunnableSequence 정의
# ==============================================================================
def step_back(inputs: dict):
    print(f"사용자 질문: '{inputs['input']}'")
    return inputs

def run_rag_db(inputs: dict):
    out = tool_rag_db(inputs['input'])
    print(f"DB cosine similarity = {out['score']:.4f}")
    return {**inputs, **out}

def choose_output(inputs: dict):
    if inputs['score'] < 0.6:
        wiki_out = tool_rag_wiki(inputs['input'])
        inputs_emb = st_model.encode([inputs['input']], normalize_embeddings=True)[0]
        ctx_emb    = st_model.encode([wiki_out['doc']], normalize_embeddings=True)[0]
        wiki_score = float(np.dot(inputs_emb, ctx_emb))
        return {**inputs, 'output': wiki_out['doc'], 'wiki_score': wiki_score}
    return {**inputs, 'output': inputs['doc'].page_content, 'wiki_score': None}

def run_llm(inputs: dict):
    prompt = AGENT_PROMPT.format(history=inputs['history'], input=inputs['input'], output=inputs['output'])
    tok = tokenizer(prompt, return_tensors='pt', truncation=True, max_length=2048).to(merged.device)
    out_ids = merged.generate(
        **tok,
        max_new_tokens=512,
        do_sample=True,
        temperature=0.95,
        top_p=0.05,
        repetition_penalty=1.2,
        no_repeat_ngram_size=3,
        eos_token_id=tokenizer.eos_token_id,
        pad_token_id=tokenizer.eos_token_id
    )
    gen = out_ids[0, tok['input_ids'].shape[1]:]
    return {**inputs, 'output': tokenizer.decode(gen, skip_special_tokens=True)}

def cleanup(inputs: dict) -> dict:
    text = inputs['output']
    text = re.sub(r'다음은.*?의 설명입니다', '', text)
    text = text.replace('다이스', '')
    text = re.sub(r'(</?think>)', '', text)
    text = text.replace(inputs['input'], '')
    for token in specials:
        text = text.replace(token, '')
    text = re.sub(r"[^가-힣0-9\.\?\!\,\s]", '', text)
    sentences = re.split(r'(?<=[.!?])\s+', text.strip()) if text else []
    text = ' '.join(sentences[:5])
    if not text.endswith(('.', '!', '?')):
        text += '.'
    return {'response': text.strip() + ' — DAIS'}

agent_chain = RunnableSequence(step_back, run_rag_db, choose_output, run_llm, cleanup)

# ==============================================================================
# 8. Streamlit UI 구현 (스타일 포함)
# ==============================================================================

st.set_page_config(layout="wide", page_title="DAIS RAG Chat")

# ===== 스타일 적용 =====
st.markdown("""
<style>
    .stApp {
        background-color: #00102D !important;
    }
    .dais-chat-container {
        background: #A2ABFF !important;
        border: 2px solid #FFA500 !important;
        border-radius: 16px;
        padding: 24px 32px;
        margin-bottom: 18px;
        color: black !important;
        font-size: 20px;
        text-align: left;
    }
    .dais-user {
        font-weight: bold;
        color: #222 !important;
        margin-bottom: 6px;
    }
    .dais-bot {
        font-weight: bold;
        color: #222 !important;
        margin-bottom: 6px;
    }
    .dais-input-box input {
        background: #BF94E4 !important;
        color: black !important;
        border-radius: 8px !important;
        border: 2px solid #FFA500 !important;
        font-size: 18px !important;
    }
    .dais-send-btn button {
        background: #FFA500 !important;
        color: black !important;
        border: 2px solid #FFA500 !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        font-size: 18px !important;
    }
    .dais-send-btn button:hover {
        background: #ffbe4d !important;
        color: black !important;
    }
</style>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    st.title("DAIS")
    st.markdown("과학 AI 인플루언서와 대화해보세요.")

with col2:
    if 'history' not in st.session_state:
        st.session_state.history = []
    st.header("Chat with DAIS")

    # 대화 출력
    for msg, role in st.session_state.history:
        if role == 'user':
            st.markdown(
                f"<div class='dais-chat-container'><span class='dais-user'>햄:</span> {msg}</div>",
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"<div class='dais-chat-container'><span class='dais-bot'>DAIS:</span> {msg}</div>",
                unsafe_allow_html=True
            )

    # 입력창 & 버튼 커스텀
    input_col1, input_col2 = st.columns([5, 1])
    with input_col1:
        user_input = st.text_input(
            "질문을 입력하세요:",
            key='input_text',
            label_visibility="collapsed",
            placeholder="질문을 입력하세요.",
            help=None
        )
        st.markdown(
            "<style>.stTextInput input {background: #BF94E4 !important; color: black !important; border-radius: 8px !important; border: 2px solid #FFA500 !important; font-size: 18px !important;}</style>",
            unsafe_allow_html=True
        )
    with input_col2:
        send_btn = st.button("전송", key='send_btn', help="질문 보내기")
        st.markdown(
            "<style>.stButton button {background: #FFA500 !important; color: black !important; border: 2px solid #FFA500 !important; border-radius: 8px !important; font-weight: bold !important; font-size: 18px !important;}</style>",
            unsafe_allow_html=True
        )

    if send_btn and user_input:
        st.session_state.history.append((user_input, 'user'))
        hist_lines = [f"[{'USER' if r=='user' else 'DAIS'}] {m}" for m, r in st.session_state.history]
        history_text = "\n".join(hist_lines)
        inputs = {'history': history_text, 'input': user_input, 'output': ''}
        result = agent_chain.invoke(inputs)
        st.session_state.history.append((result['response'], 'dais'))
        st.session_state.input_text = ''
        st.experimental_rerun()

with col3:
    st.info("DAIS RAG Chat Powered by Streamlit")
