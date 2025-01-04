from huggingface_hub import InferenceClient
import streamlit as st
# --- Initialize the Inference Client with the API key ----#
client = InferenceClient(token=st.secrets.api_keys.huggingfacehub_api_token)

# set LLM model
model_option = {"qwen2.5-72b": "Qwen/Qwen2.5-72B-Instruct",
                "llama3.3-70b": "meta-llama/Llama-3.3-70B-Instruct",
                "llama3.1-70b": "meta-llama/Meta-Llama-3.1-70B-Instruct",
                }