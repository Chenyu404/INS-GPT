import json
from collections.abc import Callable

from logger_config import logger
from utils.llm import LLM, doubao_llm
from utils.prompts import pipeline_routing
from utils.store import Memory


class PipelineRouter:
    def __init__(self, llm: LLM, prompt_template: Callable[[Memory], str]):
        self.llm = llm
        self.prompt_template = prompt_template

    def route(self, memory: Memory) -> int:
        if len(memory.history) == 1:  # 如果用户刚刚开始与经理人对话，你应该分类为阶段1
            logger.info("PipelineRouter: 对话刚开始，直接分入流程1：需求分析")
            return 1
        for _ in range(5):  # 最多重试5次
            try:

                response = self.llm.chat(self.prompt_template(memory=memory))
                logger.info(f"PipelineRouter: response: {response}")
                response: dict = json.loads(response)
                if response.get("stage", None):
                    stage = response["stage"]
                    if isinstance(stage, str):
                        stage = int(stage)  # 若stage为str,转换为int
                    if stage in [1, 2, 3]:
                        if memory.recommended_products is None and stage in [
                            3,
                        ]:
                            logger.info(
                                "PipelineRouter: 未推荐产品，无法进入阶段3或4，重新选择阶段"
                            )
                            stage = 2
                        logger.info(f"PipelineRouter: 分入流程{stage}")
                        return stage
                    else:
                        continue
            except Exception:
                continue
        # fallback 最终尝试
        if memory.recommended_products is None:
            return 2
        else:
            return 3


pipeline_router = PipelineRouter(llm=doubao_llm, prompt_template=pipeline_routing)
