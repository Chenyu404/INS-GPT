from typing import List

from agent import (
    closing_agent,
    explain_agent,
    info_fill_agent,
    recomend_agent,
    requirememet_analysis_agent,
    summary_agent,
)
from logger_config import logger
from pipeline_router import pipeline_router
from utils.store import Memory, Order


def generate(memory: Memory, orders: List[Order]):
    """
    生成对话
    """
    stage = pipeline_router.route(memory)
    memory.stage = stage
    if stage == 1:
        logger.info("Pipeline：进入阶段1：需求分析")
        ans = requirememet_analysis_agent.chat(memory)
    elif stage == 2:
        logger.info("Pipeline：进入阶段2：产品推荐")
        ans = recomend_agent.chat(memory)
    elif stage == 3:
        logger.info("Pipeline：进入阶段3：产品解释")
        ans = explain_agent.chat(memory)

    if len(memory.history) % 10 == 0 and len(memory.history) != 0:
        summary(memory, orders)

    return ans


def summary(memory: Memory, orders: List[Order]):
    summary: dict = summary_agent.chat(memory, None)
    logger.info(f"Pipeline：意向总结-response：{summary}")
    product_id = summary["product_id"]
    if isinstance(product_id, str):
        product_id = int(product_id)
    product = memory.recommended_products[product_id]
    memory.purchased_product = product

    for_self = summary["for_self"] == "True"
    if for_self:
        relation = "本人"
        name = memory.name
        age = memory.age
        gender = memory.gender
    else:
        relation = summary["relation"]
        name = summary["name"]
        age = summary["age"]
        if isinstance(age, str):
            if age.isdigit():
                age = int(age)
        gender = summary["gender"]
    notes = summary["notes"]

    new_order = Order(
        tel=memory.tel,
        product=product,
        for_self=for_self,
        relation=relation,
        name=name,
        age=age,
        gender=gender,
        notes=notes,
    )
    orders.append(new_order)
