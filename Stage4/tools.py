"""
模型是根据工具的描述来判断使用哪些工具
"""
import os
from dotenv import load_dotenv
from serpapi import SerpApiClient
from typing import Dict,Any

load_dotenv()

def search(query:str) -> str:
    print(f"正在执行 [SerpApi] 网页搜索: {query}")
    try:
        api_key = os.getenv("SERPAPI_API_KEY")
        if not api_key:
            return "没有配置SerpApi"
        params = {
            "engine": "google",
            "q": query,
            "api_key": api_key,
            "gl": "cn", # 国家代码
            "hl": "zh-cn" # 语言代码
        }

        client = SerpApiClient(params)
        results = client.get_dict()

        # 智能解析:优先寻找最直接的答案
        if "answer_box_list" in results:
            return "\n".join(results["answer_box_list"])
        if "answer_box" in results and "answer" in results["answer_box"]:
            return results["answer_box"]["answer"]
        if "knowledge_graph" in results and "description" in results["knowledge_graph"]:
            return results["knowledge_graph"]["description"]
        if "organic_results" in results and results["organic_results"]:
            # 如果没有直接答案，则返回前三个有机结果的摘要
            snippets = [
                f"[{i + 1}] {res.get('title', '')}\n{res.get('snippet', '')}"
                for i, res in enumerate(results["organic_results"][:3])
            ]
            return "\n\n".join(snippets)

        return f"对不起，没有找到关于 '{query}' 的信息。"


    except Exception as e:
        return f"搜索时发生错误: {e}"


class ToolExecutor:
    """负责注册工具，调度工具"""
    def __init__(self):
        self.tools:Dict[str,Dict[str,Any]] = {}

    def registerTool(self,name:str,description:str,func:callable):

        if name in self.tools:
            print(f"工具{name}是存在的，将会被覆盖")
        self.tools[name] = {"description":description,"func":func}
        print(f"工具{name}已经注册完成")

    def getTool(self,name:str) -> callable:

        return self.tools.get(name,{}).get("func")

    def getAvailableTools(self) -> str:
        return "\n".join(
            [ f"-{name}-:{info['description']}" for name,info in self.tools.items()]
        )

if __name__ == "__main__":
    toolExecutor = ToolExecutor()

    search_description = "一个网页搜索引擎。当你需要回答关于时事、事实以及在你的知识库中找不到的信息时，应使用此工具"
    toolExecutor.registerTool("Search",search_description,search)

    print("\n--可用工具--")
    print(toolExecutor.getAvailableTools())

    print("-----尝试通过工具调度器来调动工具search-----")
    tool_function = toolExecutor.getTool("Search")      # 这里实际上是通过工具调动器来获取函数search的功能
    if tool_function:
        print(tool_function("======潘嘎之交是什么梗？====="))
    else:
        print("=====我chovy,找工具你给我找好的啊=====")
