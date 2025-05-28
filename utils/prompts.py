from typing import List

from utils.profiles import Profile
from utils.store import Memory
from utils.tools import ToolManager

HISTORY_MAX_LEN = 20


def truncate_history(history: List[str], max_len: int = HISTORY_MAX_LEN) -> List[str]:
    """
    截断历史记录
    """
    if len(history) > max_len:
        return history[-max_len:]
    return history


def pipeline_routing(memory: Memory) -> str:
    """
    Pipeline路由阶段的prompt
    """
    prompt = (
        "你需要根据用户的聊天记录，判断与用户的聊天处于哪个阶段，决定经理人下一步的行动。",
        "可用的阶段有下列几种：",
        "1. 需求分析：此阶段的用户表达的需求较为模糊，需要经理人进一步追问。",
        "2. 产品推荐：此阶段的用户已经表达了明确的需求，需要经理人为用户推荐产品。",
        "3. 产品解释：此阶段经理人已经向用户推荐了具体的产品，且用户对其中具体的产品有疑问，需要经理人解释产品。",
        # "如果用户刚刚开始与经理人对话，你应该分类为阶段1。", #这个可用程序直接判断
        "你的回复应该为下面的json格式：",
        '{"thought":"<你对问题的思考>","stage":"<阶段的数字编号，取值为1~4>"}',
        "下面是用户的对话历史：",
        # f"{'\n'.join(truncate_history(memory.history))}",
        "\n".join(truncate_history(memory.history)),
    )
    return "\n".join(prompt)


def react_prompt(
    tools: ToolManager, tool_result: str = None, force_final: bool = False
) -> str:
    """
    ReAct prompt模板
    force_final: bool 取True时强制模型进行总结，不使用工具，用于限制工具调用最大次数
    """
    prompt = ["你需要根据用户的历史记录，工具来为完成任务：", f"{tools.introduce()}"]

    if force_final:
        prompt = []
    if tool_result:
        prompt.extend(
            ["这是你过去调用工具的结果供你参考，请不要重复调用工具：", f"{tool_result}"]
        )

    if force_final:
        prompt.extend(
            [
                "你的回复应该为下面的json格式：",
                '{"thought":"<你的想法>","answer":"<你的回复>"}',
            ]
        )
        return "\n".join(prompt)

    prompt.extend(
        [
            "如果需要使用工具，你的回复应该为下面的json格式：",
            '{"thought":"<你的想法>","tool":"<你要使用的工具的名字>","params":{"<你要使用的工具参数名称>":"<参数值>"}',
            "如果不需要使用工具，你的回复应该为下面的json格式：",
            '{"thought":"<你的想法>","answer":"<你的回复>"}',
        ]
    )
    return "\n".join(prompt)


def requirement_analysis(
    memory: Memory,
    profile: Profile,
) -> str:
    """
    需求分析阶段的prompt
    """
    prompt = (
        f"你是{profile.name}，{profile.title}，来自{profile.company},公司理念是{profile.slogan}。",
        f"用户的姓名是{memory.name}，性别{memory.gender}，年龄是{memory.age}岁，请正确地称呼用户。"
        "首次见面请先向用户问好，然后询问用户的需求，如果用户的需求有表述不清或较为笼统之处，请向用户追问。",
        "用户至少应当让你了解：保险为谁而投，希望保障的内容，如果用户投保的险种有特别的事项，你应该向用户追问。",
        "如果用户的需求表述已经较为清晰，请询问用户是否需要具体的产品推荐。",
        "下面是用户的对话历史：",
        "-------------------------------------",
        # f"{'\n'.join(truncate_history(memory.history))}",
        "\n".join(truncate_history(memory.history)),
        "-------------------------------------",
        "你应该以经理人的身份回答用户的最后一句话，请直接回答",
    )
    return "\n".join(prompt)


def product_recommendation(
    memory: Memory,
    profile: Profile,
    tools: ToolManager,
    tool_result: str = None,
    force_final: bool = False,
) -> str:
    """
    产品推荐阶段的prompt
    """
    prompt = (
        f"你是{profile.name}，{profile.title}，来自{profile.company},公司理念是{profile.slogan}。",
        f"用户的姓名是{memory.name}，性别{memory.gender}，年龄是{memory.age}岁，请正确地称呼用户。",
        "你需要根据用户的历史记录，分析用户的需求，为用户推荐产品，你并不了解任何产品的具体信息，只有工具告知你的产品才是真实存在的，请不要编造产品。",
        "下面是用户的对话历史：",
        # f"{'\n'.join(truncate_history(memory.history))}",
        "\n".join(truncate_history(memory.history)),
        react_prompt(tools, tool_result, force_final=force_final),
    )
    return "\n".join(prompt)


def product_explanation_react(
    memory: Memory,
    profile: Profile,
    tools: ToolManager,
    tool_result: str = None,
    force_final: bool = False,
) -> str:
    """
    产品解释阶段的第1个prompt，用于ReAct Agent
    """
    prompt = (
        f"你是{profile.name}，{profile.title}，来自{profile.company},公司理念是{profile.slogan}。",
        f"用户的姓名是{memory.name}，性别{memory.gender}，年龄是{memory.age}岁，请正确地称呼用户。",
        "你需要根据用户的历史记录，分析用户的需求，为用户解释产品，你并不了解任何产品的具体信息，需要通过工具获取产品的具体信息。",
        "你可以获取的产品信息如下：",
        # f"{'\n'.join([product.short_str() for product in memory.recommended_products.values()])}"
        "\n".join(
            [product.short_str() for product in memory.recommended_products.values()]
        ),
        "下面是用户的对话历史：",
        # f"{'\n'.join(truncate_history(memory.history))}",
        "\n".join(truncate_history(memory.history)),
        react_prompt(tools, tool_result, force_final=force_final),
    )
    return "\n".join(prompt)


def product_explanation_plain(memory: Memory, profile: Profile, bg_info: str) -> str:
    """
    产品解释阶段的第2个prompt，用于Plain Agent
    """
    prompt = (
        f"你是{profile.name}，{profile.title}，来自{profile.company},公司理念是{profile.slogan}。",
        f"用户的姓名是{memory.name}，性别{memory.gender}，年龄是{memory.age}岁，请正确地称呼用户。",
        "你需要根据下面的资料是用户询问的产品的相关信息，请据此回答用户对保险产品的疑问，请注意这不是用户告诉你的信息，回答应该是一段话。",
        f"{bg_info}",
        "下面是用户的对话历史：",
        # f"{'\n'.join(truncate_history(memory.history,max_len=4))}",
        "\n".join(truncate_history(memory.history, max_len=4)),
    )
    return "\n".join(prompt)


def purchase_summary(memory: Memory, profile: Profile) -> str:
    """
    购买意向达成阶段的prompt, 用于生成总结存储
    """
    prompt = (
        "用户刚刚决定购买保险产品，你需要根据用户的聊天记录，总结用户的购买意向信息,并判断用户给出的信息是否完整。",
        f"用户的姓名是{memory.name}，性别{memory.gender}，年龄是{memory.age}岁, 电话是{memory.tel}"
        "用户可能购买的产品有：",
        # f"{'\n'.join([product.short_str() for product in memory.recommended_products.values()])}",
        "\n".join(
            [product.short_str() for product in memory.recommended_products.values()]
        ),
        "你的回复应该为下面的json格式，不要包含其他内容：",
        "{'thought':'<你的想法>','product_id':'<用户希望购买的产品id>','for_self':'<用户是否为自己购买，取值为True或False>','relation':'<被保险人与用户的关系>','name':'<被保险人的姓名>','age':'<被保险人的年龄>','gender':'<被保险人的性别，取值为男或女>','notes':'<其他备注>','is_complete':'<用户给出的信息是否完整，取值为True或False>'}",
        "下面是用户的对话历史：",
        # f"{'\n'.join(memory.history)}",
        "\n".join(memory.history),
    )
    return "\n".join(prompt)


def purchase_completion(memory: Memory, profile: Profile) -> str:
    """
    购买意向达成阶段的prompt, 用于通知用户购买意向达成
    """
    prompt = (
        f"你是{profile.name}，{profile.title}，来自{profile.company},公司理念是{profile.slogan}。",
        f"用户的姓名是{memory.name}，性别{memory.gender}，年龄是{memory.age}岁，请正确地称呼用户。",
        f"用户希望购买的产品是{memory.purchased_product.name}。",
        "你需要告诉客户购买意向已经达成，公司会尽快与客户联系完成核保事宜。",
        "下面是用户的对话历史：",
        "-------------------------------------",
        # f"{'\n'.join(truncate_history(memory.history))}",
        "\n".join(truncate_history(memory.history)),
        "-------------------------------------",
        "你应该以经理人的身份回答用户的最后一句话，请直接回答",
    )
    return "\n".join(prompt)


def information_fill(memory: Memory, profile: Profile, bg_info: str) -> str:
    """
    信息填写阶段的prompt
    """
    prompt = (
        f"你是{profile.name}，{profile.title}，来自{profile.company},公司理念是{profile.slogan}。",
        f"用户的姓名是{memory.name}，性别{memory.gender}，年龄是{memory.age}岁，电话是{memory.tel}，请正确地称呼用户。",
        "用户刚刚决定购买保险产品, 但是用户没有提供完整的信息, 请根据下面的资料, 询问其中空缺的信息。",
        f"{bg_info}",
        "下面是用户的对话历史：",
        # f"{'\n'.join(truncate_history(memory.history,max_len=4))}",
        "\n".join(truncate_history(memory.history, max_len=4)),
    )
    return "\n".join(prompt)


prompt_template = [requirement_analysis, product_recommendation]
