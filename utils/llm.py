import requests
import torch
import utils.CONFIG as CONFIG
from transformers import (
    AutoModel,
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
)

# from peft import PeftModel,PeftConfig


class LLM:
    def __init__(self):
        pass

    def chat(self, prompt: str) -> str:
        pass


class Doubao(LLM):
    url = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"

    def __init__(self, model: str, api_secret: str):
        super().__init__()
        self.model = model
        self.api_secret = api_secret

    def chat(self, prompt: str) -> str:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_secret}",
        }
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": ""},
                {"role": "user", "content": prompt},
            ],
        }
        response = requests.post(self.url, headers=headers, json=data)
        return response.json()["choices"][0]["message"]["content"]


class vLLM(LLM):

    def __init__(self, url, model, api_secret):
        super().__init__()
        self.model = model
        self.api_secret = api_secret
        self.url = url

    def chat(self, prompt: str) -> str:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_secret}",
        }
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
        }
        response = requests.post(
            f"{self.url}/v1/chat/completions", headers=headers, json=data
        )
        # print(response)
        return response.json()["choices"][0]["message"]["content"]


class ChatGLM(LLM):
    def __init__(self, model_path="THUDM/chatglm3-6b", lora_adapter_path=None):
        self.model_path = model_path
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_path, trust_remote_code=True
        )
        self.model = AutoModel.from_pretrained(
            self.model_path, trust_remote_code=True, device="cuda"
        ).cuda()  # .quantize(8).cuda()
        self.model = self.model.eval()
        if lora_adapter_path:
            self.lora_config = PeftConfig.from_pretrained(lora_adapter_path)
            self.model.add_adapter(self.lora_config, "adapter")
            self.model.enable_adapters()

    def chat(self, prompt: str) -> str:
        response, history = self.model.chat(self.tokenizer, prompt, history=[])
        return response


class ChatGLM4(LLM):
    def __init__(self, model_path="THUDM/glm-4-9b-chat"):
        self.model_path = model_path
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_path, trust_remote_code=True
        )

        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_path,
            low_cpu_mem_usage=True,
            trust_remote_code=True,
            # device_map="auto",
            load_in_4bit=True,
        ).eval()

    def chat(self, prompt: str) -> str:
        inputs = self.tokenizer.apply_chat_template(
            [{"role": "user", "content": prompt}],
            add_generation_prompt=True,
            tokenize=True,
            return_tensors="pt",
            return_dict=True,
        )

        inputs = inputs.to("cuda")
        gen_kwargs = {"max_length": 4000, "do_sample": True, "top_k": 1}
        with torch.no_grad():
            outputs = self.model.generate(**inputs, **gen_kwargs)
            outputs = outputs[:, inputs["input_ids"].shape[1] :]
            return self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return response


doubao_llm = Doubao(model=CONFIG.DOUBAO_MODEL, api_secret=CONFIG.DOUBAO_API_SECRET)
# vllm_247=vLLM(url=CONFIG.VLLM_URL,model=CONFIG.VLLM_MODEL,api_secret=CONFIG.VLLM_API_SECRET)
