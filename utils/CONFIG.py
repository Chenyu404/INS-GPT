DOUBAO_MODEL="ep-20241218101052-6dzxs"
DOUBAO_API_SECRET="67f02d84-2389-4070-8e7e-217b9dc5ce5f"

VLLM_URL = "http://219.224.3.247:46747"
VLLM_MODEL = "/data1/llm/wsc/models/Qwen2_5-7B-Instruct"
VLLM_API_SECRET = "p6iYNSAvObb9fRh9OV1OrVPz5"

DATA_PATH="/home/student/wsc/INS-GPT/INS-GPT-DATA"
CHROMA_PERSISTENT_PATH="/home/student/wsc/INS-GPT/INS-GPT-DATA/chroma_persistent"

# 嵌入模型的路径
EMBEDDING_MODEL_PATH="/home/student/wsc/INS-GPT/INS-GPT-MODELS/models--BAAI--bge-base-zh-v1.5/snapshots/f03589ceff5aac7111bd60cfc7d497ca17ecac65"
# 如何获取嵌入模型？使用huggingface-cli下载
# -----------------------------------------------------------------bash---
# export HF_ENDPOINT=https://hf-mirror.com
# huggingface-cli download BAAI/bge-base-zh-v1.5 --local-dir <填入一些路径>
# ------------------------------------------------------------------------
# 然后在这里填上下载路径里面有config_sentence_transformers.json的文件夹的路径