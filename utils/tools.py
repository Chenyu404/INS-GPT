import json
from collections.abc import Callable
from typing import List

from utils.chroma import DATA_PATH, ChromaDB
from utils.store import Memory, Product


class Parameter:
    def __init__(
        self,
        name: str,
        description: str,
    ):
        """
        name: 参数的名字
        description: 参数的描述
        required: 参数是否必须
        """
        self.name = name  # 参数名
        self.description = description  # 参数描述

    def __str__(self):
        return json.dumps(
            {self.name: self.description},
            ensure_ascii=False,
        )


class Tool:
    def __init__(
        self,
        name: str,
        description: str,
        params: List[Parameter],
        function: Callable[..., str],
    ):
        """
        name: 工具的名字
        description: 工具的描述
        params: 工具的参数，一个字典，key是参数名，value是参数的描述
        function: 工具的功能，一个函数，接受的参数是params中的参数，参数均需为kwarg，返回值是一个字符串
        """
        self.name = name
        self.description = description
        self.params = params
        self.function = function

    def introduce(self):
        # chatglm不理解这个。
        # return f"{self.name}: {self.description} with params: {[str(param) for param in self.params]}"
        # return f"工具名：{self.name}，参数：{[str(param) for param in self.params]}, 功能：{self.description} "
        param = {}
        for i in self.params:
            param = param | {i.name: i.description}
        return f"工具名：{self.name}，参数：{json.dumps(param, ensure_ascii=False)}, 功能：{self.description} "

    def run(self, param: dict, additional_args: dict = None):
        """
        param_str: 一个json字符串，包含了工具所需的参数
        additional_args: 一个字典，包含了额外的参数(这部分参数对llm不可见，用于传递来自pipeline的参数)
        """
        args = param
        assert set(args.keys()) == set([param.name for param in self.params])
        if additional_args:
            args.update(additional_args)
        return self.function(**args)


class ToolManager:
    def __init__(self):
        self.tools = []

    def register_tool(self, tool: Tool):
        """
        注册一个工具
        """
        self.tools.append(tool)

    def get_tool(self, name: str):
        """
        根据名字获取一个工具
        """
        for tool in self.tools:
            if tool.name == name:
                return tool
        return None

    def list_tools(self):
        """
        列出所有的工具
        """
        return [tool.name for tool in self.tools]

    def introduce(self):
        """
        介绍所有的工具
        """
        return "\n".join([tool.introduce() for tool in self.tools])

    def run_tool(self, name: str, param: dict, additional_args: dict = None):
        """
        运行一个工具
        """
        tool = self.get_tool(name)
        if tool:
            return tool.run(param, additional_args)
        else:
            return None


db = ChromaDB(f"{DATA_PATH}/json", f"{DATA_PATH}/markdown")  # chroma


def get_recommendation(*, requirement: str, memory: Memory) -> str:
    recommend_result = db.query_doc(requirement)
    product_id_list = recommend_result["ids"][0]
    product_list = recommend_result["metadatas"][0]
    memory.recommended_products.clear()
    for i, prod in zip(product_id_list, product_list):
        memory.recommended_products[i] = Product(
            id=i,
            name=prod["product"],
            document=prod["filename"],  # dynamic load.
            description=prod["introduction"],
        )
    result_str = (
        f"这是我们为客户推荐的产品列表，请从中选择若干产品向客户推荐",
        "\n".join(
            [product.long_str() for product in memory.recommended_products.values()]
        ),
        "请注意你只能从上面的列表中选择推荐的产品，不得编造任何其他产品,这点非常重要，谢谢！",
    )
    return "\n".join(result_str)


recommend_product = Tool(
    name="recommend_product",
    description="根据总结出的用户需求文本，为用户推荐保险产品",
    params=[
        Parameter(
            name="requirement", description="用户需求的总结，需要模仿保险责任的写作风格"
        ),
    ],
    function=get_recommendation,
)
tools_recommend_stage = ToolManager()
tools_recommend_stage.register_tool(recommend_product)


def get_product_info(*, product_ids: str, query: str, memory: Memory) -> str:
    """
    根据产品的id，返回产品的详细信息文段
    product_ids: 产品id的列表,用字符串表示
    query: 要查询的产品信息
    """
    try:
        # def to_str(x):
        #     if isinstance(x,int): #如果传入的是整数，转换为字符串
        #         product_id=str(x)
        if not isinstance(product_ids, str):
            product_ids = str(product_ids)
        product_ids: List[int] = eval(product_ids)
        product_ids = list(map(int, product_ids))
        query_result = db.query_para(query, product_ids)["metadatas"][0]
        result = ""
        for res in query_result:
            # 每个产品只返回一个段落
            if len(product_ids) == 0:
                break
            curr_product_id = int(res["product_id"])
            try:
                product_ids.remove(curr_product_id)
                result += f"{res['product']}:{res['paragraph']}\n"  # 上一步没抛出异常说明product_ids里还有这个段落的product_id
            except ValueError:
                pass
        return result
    except Exception as e:
        # import pdb; pdb.set_trace()
        print(e)
        return ""


get_product_info = Tool(
    name="get_product_info",
    description="根据产品id列表和问题，返回这些产品的相关信息",
    params=[
        Parameter(name="product_ids", description="产品id的列表"),
        Parameter(name="query", description=f"需要搜索的信息"),
    ],
    function=get_product_info,
)

tools_explain_stage = ToolManager()
tools_explain_stage.register_tool(get_product_info)


test_memory = Memory(
    tel="1",
    name="张三",
    age=25,
    gender="男",
    history=[
        "你好",
        "我想买保险",
        # "我想买一份保险给我报销门诊住院的费用"
    ],
    recommended_products={},
)

if __name__ == "__main__":
    # print(tools_recommend_stage.get_tool("recommend_product").run({"requirement":"我想买一份保险给我报销门诊住院的费用"},additional_args={"memory":test_memory}))
    # print(tools_explain_stage.get_tool("get_product_info").run({"query":"被保险人身故","product_ids":"[0,1,22]"},additional_args={"memory":test_memory}))
    print(
        tools_explain_stage.get_tool("get_product_info").run(
            {"query": "保险金额度", "product_ids": '["1511","318"]'},
            additional_args={"memory": test_memory},
        )
    )
