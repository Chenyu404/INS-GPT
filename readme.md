# 现状
目前用模拟的数据基本实现了对话系统的后端，还需要待Chroma模块接入真实的数据、前端接入后端API进行展示。  
目前可以先启动服务端[api_server.py](./api_server.py), 然后运行简易客户端[cli_client.py](./cli_client.py)进行测试。 


# 后续工作参考
## 微调
实测247服务器的显存够跑Qwen2.5-7B模型，不过微调肯定不够，可以考虑换个更小的模型在247上微调试试效果先，或者直接一步到位租卡调7B模型。  
当然需要考虑到Chroma模块完成后Embedding模型也会占据一部分显存，所以大概可以先试试我们的服务最大能和多大的基座模型一起跑。（或者展示时暂时先把我们的服务在本地跑/或者用个Embedding的API实现嵌入功能）  
服务器上有下好的Q问2.5-7B模型，在247://data1/llm/wsc/models/Qwen2_5-7B/下，可以直接用。  
可以用247://home/student/wsc/INS-GPT/run_vllm_server.sh启动vllm服务。  
微调以后需要改动两个地方，一个是[./utils/llm.py](./utils/llm.py)中的模型路径(vLLM类实例化时那个model参数)，另一个是247://home/student/wsc/INS-GPT/run_vllm_server.sh中的模型路径。  

## 产品信息提取/Chroma 数据库
主要需要实现语义检索功能，即根据用户输入的问题，返回数据库中与之相关的数据。
工具已经实现了和模型对接的部分，模型会将它假想的需求转化为一个查询语句，然后将这个查询语句发送给数据库，数据库返回查询结果。
### 参考思路
我们将每个产品的信息存储在一个Product类中，Product类中包含了产品的ID、名称、文档、描述等信息，如果提取中的产品信息中有新的字段，可以在Product类中添加新的字段。（见[./utils/store.py#Product](./utils/store.py)）  
**！！！！！！建议最好直接把document字段拆掉，实测247上部署的Qwen2.5-7B模型最多能允许大约2000字的背景信息插入，因此每个字段不宜过长。！！！！！！**  
在数据提取构建向量数据库阶段，我们至少应该将产品编上一个int型的编号(id)，并且获取产品名称（name）字段，以及生成一个简介产品亮点,用于进行语义检索的描述字段（description）。  
（见[./utils/tools.py#get_rcomendation](./utils/tools.py)）取到模型的查询语句后，检索向量库中待检索的字段，将得到的产品信息写入Product类中，并在传入的memory对象的recommend_products列表中添加这个Product对象。  
如果Chroma的代码比较复杂，可以考虑把这部分拆分出来放在[./utils/chroma.py](./utils/chroma.py)中。  

## 前端
目前实现的API接口如下。  
如果采用基于Python的前端，[./cli_client.py](./cli_client.py)中的请求代码应该可以直接复用。  
### 添加用户
端点: `/addUser`  
功能: 添加用户, 获取用户基本信息后传给后端  
#### 请求
- 方法: `PUT`
- 类型: `application/json`
- 请求体:
```json
{
    "tel": "string", // 用户手机号,同时也是用户ID
    "name": "string", // 用户名
    "gender": "string", // 用户性别
    "age": "int", // 用户年龄
}
```
#### 响应
- 类型: `application/json`
- 响应体:
```json
{
    "msg": "string", // 信息
}
```
### 对话
端点: `/chat`  
功能: 用户与机器人对话  
#### 请求
- 方法: `POST`
- 类型: `application/json`
- 请求体:
```json
{
    "tel": "string", // 用户手机号
    "msg": "string" // 用户消息
}
```
#### 响应
- 类型: `application/json`
- 响应体:
```json
{
    "msg": "string", // 机器人消息
}
```

### 获取购买意向
端点: `/getOrders`  
功能: 获取用户购买意向  
#### 请求
- 方法: `GET`
无需请求体
#### 响应
- 类型: `application/json`
- 响应体:
```json
{
    "tel": "string", // 用户手机号
    "orders":[
        {
            "tel": "string", // 用户手机号
            "product":{
                "id": "int", // 商品ID
                "name": "string", // 商品名
                "document": "string", // 产品文档
                "description": "string", // 商品描述
                //如果天宇,听雨那边加入了新的商品元数据,这里可能添加新的字段
            },
            "for_self": "bool", // 是否为自己购买
            "name": "string", // 被保险人姓名
            "age": "int", // 被保险人年龄
            "gender": "string", // 被保险人性别
            "relationship": "string", // 用户与被保险人关系
            "notes": "string" // 备注
        }
    ]
}
```

### 获取用户信息
端点: `/getMemory`  
功能: 获取用户信息  
#### 请求
- 方法: `GET`
- 类型: `application/json`
- 请求体:
```json
{
    "tel": "string", // 用户手机号
}
```
#### 响应
- 类型: `application/json`
- 响应体:
```json
{
    "tel": "string", // 用户手机号
    "name": "string", // 用户名
    "age": "int", // 用户年龄
    "gender": "string", // 用户性别
    "history":[
        "string", // 对话历史记录条目,最新的在尾部
    ],
    "recommended_products":{
        "string":{ //key为字符串型的商品ID
            "id": "int", // 商品ID
            "name": "string", // 商品名
            "document": "string", // 产品文档
            "description": "string", // 商品描述
            //如果天宇,听雨那边加入了新的商品元数据,这里可能添加新的字段
        }
    },
    "purchased_product":{
        "id": "int", // 商品ID
        "name": "string", // 商品名
        "document": "string", // 产品文档
        "description": "string", // 商品描述
        //如果天宇,听雨那边加入了新的商品元数据,这里可能添加新的字段
    }
}
```


