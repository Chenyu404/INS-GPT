from copy import deepcopy
from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional


@dataclass
class Product:
    id: int  # 产品的id
    name: str  # 产品的名字
    description: str  # 产品的描述
    # 下面的字段可以调整或补充
    document: str  # 完整的保险产品文件/条款 （感觉最好把文档拆开，这样利于解释阶段准确找到对应的字段）
    # link: str # (有时间再看)产品的链接
    # 如有其他字段可继续补充

    def short_str(self):
        """
        简短的字符串表示，用于提示模型有哪些产品被推荐了
        """
        return f"id:{self.id}, name:{self.name}"

    def long_str(self):
        """
        完整的字符串表示，用于在产品推荐阶段告知模型产品的信息
        """
        return f"id:{self.id}, name:{self.name}, description:{self.description}"

    def __str__(self):
        return self.__dict__.__str__()

    @classmethod
    def from_dict(cls, data: Dict):
        """
        从字典中加载产品信息
        """
        return cls(**data)

    @classmethod
    def get_fields(cls):
        """
        返回产品的字段信息，用于在产品解释阶段告知模型可获取哪些产品信息
        """
        # 补充了字段以后记得在这里添加
        fields = {
            "name": "产品的名字",
            "document": "完整的保险产品文件/条款",
            "description": "产品的描述",
        }
        return fields


@dataclass
class Memory:
    tel: str  # 用户的id(电话号码)
    name: str  # 用户的昵称
    age: int  # 用户的年龄
    gender: Literal["男", "女"]  # 用户的性别
    history: List[str] = field(default_factory=list)  # 用户的对话历史
    recommended_products: Dict[int, Product] = field(
        default_factory=dict
    )  # 推荐给用户的产品字典，键为产品的id，值为产品
    purchased_product: Optional[Product] = None  # 用户购买的产品
    user_pdf: Optional[str] = None  # for pdf showing.
    stage: Optional[int] = None

    @classmethod
    def from_dict(cls, data: Dict):
        """
        从字典中加载Memory信息
        """
        data["recommended_products"] = {
            int(k): Product.from_dict(v)
            for k, v in data["recommended_products"].items()
        }
        if data["purchased_product"]:
            data["purchased_product"] = Product.from_dict(data["purchased_product"])
        return cls(**data)

    def to_dict(self):
        """
        将Memory信息转换为字典
        """
        data = deepcopy(self.__dict__)
        data["recommended_products"] = {
            str(k): v.__dict__ for k, v in data["recommended_products"].items()
        }
        if data["purchased_product"]:
            data["purchased_product"] = data["purchased_product"].__dict__
        return data


@dataclass
class Order:
    tel: str
    product: Product
    for_self: bool
    name: str
    age: int
    gender: Literal["男", "女"]
    relation: Optional[str] = "本人"
    notes: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict):
        """
        从字典中加载Order信息
        """
        if data.get("product", None):
            data["product"] = Product.from_dict(data["product"])
        return cls(**data)

    def to_dict(self):
        """
        将Order信息转换为字典
        """
        data = deepcopy(self.__dict__)
        if data["product"]:
            data["product"] = data["product"].__dict__
        return data


# test_memory = Memory(
#     tel="1",
#     name="张三",
#     age=25,
#     gender="男",
#     history=["你好", "我想买保险",
#              #"我想买一份保险给我报销门诊住院的费用"
#              ],
#     recommended_products=[],
#     purchased_product=None
# )
