import streamlit as st
import chromadb
import google.generativeai  as genai
import time

__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

class AI():
    def __init__(self):
        db = chromadb.PersistentClient()
        self.collection = db.get_or_create_collection("genai")

    def query(self, prompt, res_limit = 15):
        res_db = self.collection.query(query_texts=[prompt], n_results=138)["documents"][0][0:res_limit]
        context = '\n -------------- \n '.join(res_db)
        
        return context
    
    def stream_data(self, data):
        for word in data.split(" "):
            yield word + " "
            time.sleep(0.02)

    def answer(self, message, API_KEY = ''):
        prompt = message[-1]['content']
        context = self.query(prompt)

        comp_prompt = "Give the most accurate answer using only the folling information: \n"+context

        if API_KEY != '':
            genai.configure(api_key = API_KEY)
            model_system = genai.GenerativeModel('gemini-1.5-flash-latest', system_instruction=comp_prompt)
            bot_response = model_system.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(temperature=0.3)
            )

            return self.stream_data(bot_response.text)
        else:
            return 'API Key invalid'
        
    
ai = AI()
st.set_page_config(
        page_title="Tax Systems AI",
        page_icon="🌍",
    )

st.sidebar.title("🌍 Tax Systems AI")


app = st.session_state

if "messages" not in app:
    app["messages"] = [{"role":"assistant", "content":"Hello! I'm your tax chatbot.\n I'm trained with the summaries of tax jurisdictions from 137 countries in the World! Please send your questions."}]

if 'history' not in app:
    app['history'] = []

if 'full_response' not in app:
    app['full_response'] = '' 

if 'api_key' not in app:
    app['api_key'] = ''

api_key = st.sidebar.text_input("Input your Google GenAI API Key", type="password")
if st.sidebar.button("Submit"):
    st.session_state.api_key = api_key
    # Clear the input field by setting the widget value to an empty string


for msg in app["messages"]:
    if msg["role"] == "user":
        st.chat_message(msg["role"], avatar="😎").write(msg["content"])
    elif msg["role"] == "assistant":
        st.chat_message(msg["role"], avatar="🧠").write(msg["content"])


prompt = st.chat_input()
    
if prompt:
    app["messages"].append({"role":"user", "content":prompt})
    st.chat_message("user", avatar="😎").write(prompt)

    app["full_response"] = ""
    answer = ai.answer(app["messages"], app["api_key"]) 
    st.chat_message("assistant", avatar="🧠").write_stream(answer)
    app["full_response"] = ' '.join(answer)
    app["messages"].append({"role":"assistant", "content":app["full_response"]})

    ### Show sidebar history
    app['history'].append("😎: "+prompt)
    app['history'].append("🧠: "+app["full_response"])
    st.sidebar.markdown("<br />".join(app['history'])+"<br /><br />", unsafe_allow_html=True)

