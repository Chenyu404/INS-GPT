import atexit
import json
import os
import os.path
import pathlib
from typing import List
import jieba
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import io
import base64
from collections import Counter
import re
import uvicorn
from fastapi import FastAPI, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pipeline import generate
from utils.chroma import DATA_PATH
from utils.store import Memory, Order

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

script_home = pathlib.Path(os.path.abspath(__file__)).parent
# 配置模板路径
templates = Jinja2Templates(directory=script_home / "frontend" / "templates")
# 挂载静态文件目录
app.mount(
    "/static", StaticFiles(directory=script_home / "frontend" / "static"), name="static"
)
app.mount(
    "/font", StaticFiles(directory=script_home / "frontend" / "font"), name="font"
)


@app.get("/")  # 返回登录页面
async def get_login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/index")
async def get_chat_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/Files")
async def get_Files_page(request: Request):
    return templates.TemplateResponse("Files.html", {"request": request})

@app.get("/getUser")
async def get_user_page(request: Request):
    return templates.TemplateResponse("getUser.html", {"request": request})

@app.get("/recommend")
async def get_user_page(request: Request):
    return templates.TemplateResponse("recommend.html", {"request": request})

@app.get("/getBuy")
async def get_buy_page(request: Request):
    return templates.TemplateResponse("getBuy.html", {"request": request})


@app.get("/manager")
async def get_manager_page(request: Request):
    return templates.TemplateResponse("manager.html", {"request": request})


@app.put("/addUser")  # 添加用户
async def addUser(request: Request):
    data = await request.json()
    new_memory = Memory(**data)
    memories[new_memory.tel] = new_memory
    return Response(
        content=json.dumps({"msg": "success"}, ensure_ascii=False), status_code=201
    )


@app.post("/chat")  # 聊天
async def chat(request: Request):
    data = await request.json()
    memory = memories[data["tel"]]
    memory.history.append(f"用户：{data['msg']}")
    output = generate(memory, orders)
    memory.history.append(f"经理人：{output}")
    response = Response(
        content=json.dumps(
            {"msg": output, "pdffile": memory.user_pdf, "stage": memory.stage},
            ensure_ascii=False,
        ),
        status_code=200,
    )
    return response


# @app.get("/getMemory")#获取用户信息
# async def getMemory(request: Request):
#     data = await request.json()
#     tel = data["tel"]
#     if tel in memories.keys():
#         memory = memories[tel]
#         response = Response(content=json.dumps(memory.to_dict(), ensure_ascii=False), status_code=200)
#     else:
#         response = Response(content=json.dumps({"msg": "没有找到用户"}, ensure_ascii=False), status_code=404)
#     return response


@app.get("/getMemory")  # 获取用户信息
async def getMemory(tel: str = Query(..., description="用户的手机号")):
    # data = await request.json()
    # tel = data["tel"]
    if tel in memories.keys():
        memory = memories[tel]
        response = Response(
            content=json.dumps(memory.to_dict(), ensure_ascii=False), status_code=200
        )
    else:
        response = Response(
            content=json.dumps({"msg": "没有找到用户"}, ensure_ascii=False),
            status_code=404,
        )
    return response


@app.get("/getOrders")  # 获取订单信息
async def getOrderInfo(request: Request):
    response = Response(
        content=json.dumps([order.to_dict() for order in orders], ensure_ascii=False),
        status_code=200,
    )
    return response


@app.post("/pdfPreview/{file}")  # pdf预览
async def pdfPreview(file: str, request: Request):
    return FileResponse(
        os.path.join(f"{DATA_PATH}/pdf/", f"{file}.pdf"),
        media_type="application/pdf",
        filename=f"{file}.pdf",
    )
#实现词云图
STOP_WORDS = set([
    '的', '了', '和', '是', '在', '有', '与', '及', '等', '因', '由', '于',
    '也', '又', '都', '而', '要', '这', '那', '你', '我', '他', '她', '它'
])
@app.post("/generate_wordcloud")
async def generate_wordcloud(request: Request):
    data = await request.json()
    text = data.get("text", "").strip()
    if not text:
        return {"error": "输入文本为空"}
    
    try:
        # 改进分词处理
        words = jieba.lcut(text)
        filtered_words = [w for w in words if len(w) > 1 and w not in STOP_WORDS]
        if not filtered_words:
            return {"error": "没有有效词汇可生成词云"}
        
        # 生成词云
        wc = WordCloud(
            font_path="/home/student/wsc/INS-GPT_test/INS-GPT/frontend/font/STHUPO.TTF",
            width=800,
            height=600,
            background_color='white',
            max_words=100,
            colormap='viridis',
            margin=10
        ).generate_from_frequencies(dict(Counter(filtered_words)))
        # 转换图片格式
        buf = io.BytesIO()
        plt.figure(figsize=(10, 8), dpi=100)
        plt.imshow(wc, interpolation='bicubic')  # 改进插值算法
        plt.axis('off')
        # # 显式保存为PNG格式
        plt.savefig(
            buf, 
            format='png',
            bbox_inches='tight',  # 去除空白边距
            pad_inches=0.1,       # 保留少量边距防止截断
            dpi=100
        )
        plt.close()  # 关闭绘图释放内存
        img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        print(img_base64)
        return {"imageUrl": f"data:image/png;base64,{img_base64}"}
    
    except Exception as e:
        print(f"词云生成错误: {str(e)}")
        return {"error": f"生成失败: {str(e)}"}




if __name__ == "__main__":
    # 读取数据
    script_home = pathlib.Path(os.path.abspath(__file__)).parent
    if os.path.exists(script_home / "storage" / "memories.json"):
        with open(
            script_home / "storage" / "memories.json", "r", encoding="utf-8"
        ) as f:
            memories = json.load(f)
            memories = {
                tel: Memory.from_dict(memory) for tel, memory in memories.items()
            }
    else:
        memories = {}

    if os.path.exists(script_home / "storage" / "orders.json"):
        with open(script_home / "storage" / "orders.json", "r", encoding="utf-8") as f:
            orders = json.load(f)
            orders = [Order.from_dict(order) for order in orders]
    else:
        orders: List[Order] = []

    # print(orders)
    # 保存数据
    def save_data():
        memories_serializable = {
            tel: memory.to_dict() for tel, memory in memories.items()
        }
        orders_serializable = [order.to_dict() for order in orders]
        with open(
            script_home / "storage" / "memories.json", "w", encoding="utf-8"
        ) as f:
            json.dump(memories_serializable, f, ensure_ascii=False)
        with open(script_home / "storage" / "orders.json", "w", encoding="utf-8") as f:
            json.dump(orders_serializable, f, ensure_ascii=False)

    # 注册退出时保存数据的函数
    atexit.register(save_data)

    # 启动服务
    uvicorn.run(app, host="0.0.0.0", port=8000)
