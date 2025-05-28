import json
from collections.abc import Callable
from typing import Optional

from logger_config import logger
from utils.llm import LLM, doubao_llm  # ,#chatglm #vllm_247,
from utils.profiles import Profile, profile
from utils.prompts import (
    information_fill,
    product_explanation_plain,
    product_explanation_react,
    product_recommendation,
    purchase_completion,
    purchase_summary,
    requirement_analysis,
)
from utils.store import Memory
from utils.tools import (  # , tools_explain_stage_db, tools_recommend_stage
    ToolManager,
    tools_explain_stage,
    tools_recommend_stage,
)

TEST = True


class ReActAgent:
    def __init__(
        self,
        llm: LLM,
        prompt_template: Callable[[Memory, Profile, ToolManager, str], str],
        profile: Profile,
        tools: ToolManager,
        max_function_call_rounds: int = 2,
    ):
        self.llm = llm
        self.prompt_template = prompt_template
        self.profile = profile
        self.tools = tools
        self.max_function_call_rounds = max_function_call_rounds

    def chat(
        self, memory: Memory, get_tool_result: bool = False
    ) -> str:  # get_tool_result用于控制是否返回工具结果，用于MixedAgent
        # memory.history.append(f"用户: {prompt}")
        tool_result = (
            ""  # 用于存储工具的结果, 以便在下一次调用prompt_template时传递给模板
        )
        function_call_rounds = 0
        while True:  # 直到输出最终结果前一直循环调用工具
            built_prompt = self.prompt_template(
                memory=memory,
                profile=self.profile,
                tools=self.tools,
                tool_result=tool_result,
                force_final=function_call_rounds >= self.max_function_call_rounds,
            )  # 生成prompt
            logger.info(f"ReActAgent: 拼接后的prompt: {built_prompt}")
            response = self.llm.chat(prompt=built_prompt)
            response = response.strip().lstrip("```json").rstrip("```").strip()
            logger.info(f"ReActAgent: response: {response}")
            try:
                # import pdb; pdb.set_trace()
                response: dict = json.loads(response)
                if response.get("tool", None):  # 这说明模型要求使用工具
                    tool = self.tools.get_tool(response["tool"])
                    if tool:
                        tool_result += f"{tool.run(response['params'],additional_args={'memory':memory})} \n"  # 运行工具，并将结果存储进tool_result
                        function_call_rounds += 1
                    if get_tool_result:
                        return tool_result  # 如果要求返回工具结果，则只返回工具结果
                if response.get("answer", None):  # 这说明模型给出了最终回答
                    # memory.history.append(f"经理人: {response['answer']}")
                    return response["answer"]
            except Exception as e:
                logger.error(f"ReActAgent: {e}")
                # import pdb; pdb.set_trace()
                # break
                # continue
                # TODO: retry 需要有次数上限


class PlainAgent:
    def __init__(
        self,
        llm: LLM,
        prompt_template: (
            Callable[[Memory, Profile, str], str] | Callable[[Memory, Profile], str]
        ),
        profile: Profile,
        json_parse: bool = False,
    ) -> str | dict:
        self.llm = llm
        self.prompt_template = prompt_template
        self.json_parse = json_parse

    def chat(self, memory: Memory, bg_info: Optional[str] = None) -> str:
        while True:
            try:
                # import pdb; pdb.set_trace()
                if bg_info:  # 如果有背景信息，传递给模型,用于MixedAgent
                    built_prompt = self.prompt_template(
                        memory=memory, profile=profile, bg_info=bg_info
                    )
                    logger.info(f"PlainAgent: 拼接后的prompt: {built_prompt}")
                else:
                    built_prompt = self.prompt_template(memory=memory, profile=profile)
                    logger.info(f"PlainAgent: 拼接后的prompt: {built_prompt}")
                response = self.llm.chat(built_prompt)
                logger.info(f"PlainAgent: response: {response}")
                if self.json_parse:
                    response = (
                        response.strip().lstrip("```json").rstrip("```").strip()
                    )  # kill annoying suffix.
                    response: dict = json.loads(response)
                    return response
                else:
                    if response.startswith("经理人："):
                        response = response[4:]
                    return response
            except Exception as e:
                logger.error(f"PlainAgent: {e}")
                # import pdb; pdb.set_trace()
                # break
                # continue
                # TODO: retry 需要有次数上限


class MixedAgent:
    def __init__(self, react_agent: ReActAgent, plain_agent: PlainAgent):
        self.react_agent = react_agent
        self.plain_agent = plain_agent

    def chat(self, memory: Memory) -> str:
        tool_result = self.react_agent.chat(memory=memory, get_tool_result=True)
        response = self.plain_agent.chat(memory=memory, bg_info=tool_result)
        return response


# 需求分析阶段
# requirememet_analysis_agent = PlainAgent(
#     llm=doubao_llm, prompt_template=requirement_analysis, profile=profile
# )

requirememet_analysis_agent = PlainAgent(
    llm=doubao_llm, prompt_template=requirement_analysis, profile=profile
)

# 产品推荐阶段
recomend_agent = ReActAgent(
    llm=doubao_llm,
    prompt_template=product_recommendation,
    profile=profile,
    tools=tools_recommend_stage,
    max_function_call_rounds=1,
)

# 产品解释阶段
explain_agent1 = ReActAgent(
    llm=doubao_llm,
    prompt_template=product_explanation_react,
    profile=profile,
    tools=tools_explain_stage,
    max_function_call_rounds=1,
)
# explain_agent2 = PlainAgent(
#     llm=vllm_247, prompt_template=product_explanation_plain, profile=profile
# )
# explain_agent2 = PlainAgent(
#     llm=doubao_llm, prompt_template=product_explanation_plain, profile=profile
# )
explain_agent2 = PlainAgent(
    llm=doubao_llm, prompt_template=product_explanation_plain, profile=profile
)
explain_agent = MixedAgent(react_agent=explain_agent1, plain_agent=explain_agent2)

# 购买完成阶段
closing_agent = PlainAgent(
    llm=doubao_llm, prompt_template=purchase_completion, profile=profile
)
summary_agent = PlainAgent(
    llm=doubao_llm, prompt_template=purchase_summary, profile=profile, json_parse=True
)
info_fill_agent = PlainAgent(
    llm=doubao_llm, prompt_template=information_fill, profile=profile
)
