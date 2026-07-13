"""
ReAct:思考与行动是相辅相成的。思考指导行动，而行动的结果又反过来修正思考
ReAct范式通过一种特殊的提示工程来引导模型(这里是仅用提示词)
"""
from pyexpat.errors import messages
import re
from LLM_Client import HelloAgentsLLM
from tools import ToolExecutor
# 仅从这里的提示词来看，我完全看不到思考-行动 -> 将行动结果再次输入给llm这种标准范式，可能是在history里面
REACT_PROMPT_TEMPLATE = """
请注意，你是一个有能力调用外部工具的智能助手。

可用工具如下:
{tools}

请严格按照以下格式进行回应:

Thought: 你的思考过程，用于分析问题、拆解任务和规划下一步行动。
Action: 你决定采取的行动，必须是以下格式之一:
- `{{tool_name}}[{{tool_input}}]`:调用一个可用工具。
- `Finish[最终答案]`:当你认为已经获得最终答案时。
- 当你收集到足够的信息，能够回答用户的最终问题时，你必须在Action:字段后使用 Finish[最终答案] 来输出最终答案。

现在，请开始解决以下问题:
Question: {question}
History: {history}
"""

class ReActAgent:
    def __init__(self,llm_client:HelloAgentsLLM,tool_executor:ToolExecutor,max_steps: int = 5):
        self.llm_client = llm_client
        self.tool_executor = tool_executor
        self.max_steps = max_steps
        self.history = []

    def run(self,question: str):

        self.history = []
        current_step = 0

        while current_step < self.max_steps:
            current_step += 1
            print(f"---------目前正在执行第{current_step}步-----------")

            tools_desc = self.tool_executor.getAvailableTools()
            history_str = "".join(self.history)
            prompt = REACT_PROMPT_TEMPLATE.format(
                tools = tools_desc,
                question = question,
                history = history_str
            )

            # 调用llm
            messages = [{"role":"user","content":prompt}]
            response_text = self.llm_client.think(messages = messages)
            if not response_text:
                print("错误:LLM未能返回有效响应。")
                break

    def _parse_output(self, text: str):
        """解析LLM的输出，提取Thought和Action。
        """
        # Thought: 匹配到 Action: 或文本末尾
        thought_match = re.search(r"Thought:\s*(.*?)(?=\nAction:|$)", text, re.DOTALL)
        # Action: 匹配到文本末尾
        action_match = re.search(r"Action:\s*(.*?)$", text, re.DOTALL)
        thought = thought_match.group(1).strip() if thought_match else None
        action = action_match.group(1).strip() if action_match else None
        return thought, action

    def _parse_action(self, action_text: str):
        """解析Action字符串，提取工具名称和输入。
        """
        match = re.match(r"(\w+)\[(.*)\]", action_text, re.DOTALL)
        if match:
            return match.group(1), match.group(2)
        return None, None



