from typing import Any, Callable, Dict

import requests

BASE_URL = "http://127.0.0.1:8000"


def getMemory(tel: str) -> dict:
    response = requests.get(f"{BASE_URL}/getMemory", json={"tel": tel})
    userExists = response.status_code == 200
    return userExists, response.json()


def getOrders() -> list:
    response = requests.get(f"{BASE_URL}/getOrders")
    return response.json()


def addUser(tel: str, name: str, age: int, gender: str) -> dict:
    response = requests.put(
        f"{BASE_URL}/addUser",
        json={"tel": tel, "name": name, "age": age, "gender": gender},
    )
    return response.json()


def chat(tel: str, msg: str) -> dict:
    response = requests.post(f"{BASE_URL}/chat", json={"tel": tel, "msg": msg})
    return response.json()["msg"]


def cliChooser(question: str, options: Dict[str, str]) -> str:
    print(question)
    for k, v in options.items():
        print(f"{k}: {v}")
    while True:
        response = input("> ")
        if response in options:
            return response
        else:
            print("无效的输入！")


def cliField(
    question: str,
    validator: Callable[[str], bool] = None,
    processor: Callable[[str], Any] = None,
) -> Any:
    print(question)
    while True:
        response = input("> ")
        if validator and not validator(response):
            print("无效的输入！")
            continue
        try:
            if processor:
                response = processor(response)
        except Exception:
            print("无效的输入！")
            continue
        return response


print("🤖 欢迎使用INS-GPT")
print("-------------------")
tel = cliField(
    "请输入手机号", lambda x: x.isdigit()
)  # lambda x: re.match(r"^1(3\d|4[5-9]|5[0-35-9]|6[2567]|7[0-8]|8\d|9[0-35-9])\d{8}$",x)
userExists, _ = getMemory(tel)
if not userExists:
    name = cliField("请输入姓名", lambda x: len(x) > 0)
    gender = cliChooser("请选择性别", {"1": "男", "2": "女"})
    age = cliField("请输入年龄", lambda x: x.isdigit(), lambda x: int(x))
    addUser(tel, name, age, gender)

print("欢迎！请输入您的问题，Ctrl+C退出\n")

while True:
    msg = input("👤 ")
    response = chat(tel, msg)
    print(f"🤖 {response}")

