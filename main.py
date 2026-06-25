# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 sudo1123
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import requests
import json
from ddgs import DDGS

__version__ = "0.1.0-alpha"

with open ("keys.json","r",encoding="utf-8") as K:
    global_keys_file=json.load(K)

with open ("prompts.json", "r", encoding="utf-8") as P:
    global_prompts_file=json.load(P)

class Config:
    '''本类被用于处理所有与配置文件相关的实例

    包含的attribute:
        self.prompt_file : 从全局变量global_prompts_file中加载的prompts.json的内容,即对deepseek的提示词
        self.keys_file :从全局变量global_keys_file中加载的keys.json的内容,即deepseek的API密钥


    '''
    def __init__(self):
        self.prompt_file=global_prompts_file
        self.keys_file=global_keys_file

    def get_prompt(self,role=str,prompt_name=str): #获取对应的prompt
        try:
            prompt=self.prompt_file["prompts"][role][prompt_name] # 获取json保存的对应角色的prompt
        except KeyError:                               # 找不到任意一个键
            raise ValueError(f"{prompt_name} is missing in prompts.json") from None
        if not isinstance(prompt, str):                # api数据类型有误
            raise TypeError(f"{prompt_name} in prompts.json must be a string") 
        return prompt
    
    def get_ds_api_key(self): #获取ds密钥
        try:
            ds_api_key=self.keys_file["keys"]["ds_api_key"] # 获取json保存的deepseek chat api的密钥
        except KeyError:                               # 找不到任意一个键
            raise ValueError("ds_api_key is missing in keys.json") from None
        if not isinstance(ds_api_key, str):                # api数据类型有误
            raise AttributeError("ds_api_key in keys.json must be a string") 
        return ds_api_key
    def get_jina_api_key(self): #获取jina密钥
        try:
            jina_api_key=self.keys_file["keys"]["jina_api_key"] # 获取json保存的jina api的密钥
        except KeyError:                               # 找不到任意一个键
            raise ValueError("jina_api_key is missing in keys.json") from None
        if not isinstance(jina_api_key, str):                # api数据类型有误
            raise AttributeError("jina_api_key in keys.json must be a string") 
        return jina_api_key
    
class User_Input:
    '''本类被用于处理所有与用户输入相关的实例

    包含的attribute:
        self.keyword:获取到的用户想查询的关键词


    '''
    def __init__(self):
        self.keyword=None

    def get_keyword(self):#获取用户输入的关键词的方法（目前暂时先硬编码固定关键词）
        self.keyword="2026年6月16日"

config_instance=Config() #创建Config类实例
user_input_instance=User_Input()  #创建User_Input类实例



# == deepseek api 通讯器 ==
def llm_communicator(user_prompt_content: str, json_output:bool):
    DS_API_URL = "https://api.deepseek.com/v1/chat/completions" #deepseek 官方api URL
    ds_api_key=config_instance.get_ds_api_key()
    headers = {
        "Authorization": f"Bearer {ds_api_key}",
        "Content-Type": "application/json"
    }
    if json_output:
        data = {
            "model": "deepseek-chat", 
            "messages": [
                {"role": "system", "content": config_instance.get_prompt("system","system").format(keyword=user_input_instance.keyword)},
                {"role": "user", "content": user_prompt_content}
            ],
            "stream": False,  # 非流式输出
            "response_format":{"type": "json_object"} #强制使大模型回复json格式数据
        }
    else:
        data = {
            "model": "deepseek-chat", 
            "messages": [
                {"role": "system", "content": config_instance.get_prompt("system","system")},
                {"role": "user", "content": user_prompt_content}
            ],
            "stream": False,  # 非流式输出
        }

    print("正在向 DeepSeek 发送请求，请稍候...") 

    # 发送请求并获取回复

    try:
        response = requests.post(DS_API_URL, headers=headers, json=data, timeout=30)
    except requests.exceptions.Timeout:
        print("请求超时，请检查网络连接或稍后重试。")
        raise TimeoutError("请求超时")
    except requests.exceptions.RequestException as e:
        print(f"网络请求发生错误: {e}")
        raise RuntimeError(f"网络请求失败: {e}")

    if response.status_code == 200:
        result = response.json()
        return result["choices"][0]["message"]["content"]
    else:
        print(f"请求失败：{response.status_code} - {response.text}")
        raise RuntimeError(f"网络请求失败")

def jina_communicator(target_url: str):
    JINA_API_URL = "https://r.jina.ai/" #jina 官方api URL
    final_url=JINA_API_URL+target_url
    jina_api_key=config_instance.get_jina_api_key()
    headers = {
    "Authorization": f"Bearer {config_instance.get_jina_api_key()}",
    "Accept": "application/json"
}

    print("正在向 jina api 发送请求，请稍候...") 

    # 发送请求并获取回复

    try:
        response = requests.get(final_url, headers=headers, timeout=30)
    except requests.exceptions.Timeout:
        print("请求超时，请检查网络连接或稍后重试。")
        raise TimeoutError("请求超时")
    except requests.exceptions.RequestException as e:
        print(f"网络请求发生错误: {e}")
        raise RuntimeError(f"网络请求失败: {e}")

    if response.status_code == 200:
        result = response.json()
        return result["data"]["content"]
    else:
        print(f"请求失败：{response.status_code} - {response.text}")
        raise RuntimeError(f"网络请求失败")



def format_search_result(search_result):
       return json.dumps(search_result, ensure_ascii=False, indent=2)

def analyze_search_result(results_text):
    template_prompt=config_instance.get_prompt("user","search_analyzer") #从提示词模板文件中导入search_analyzer模板
    prompt=template_prompt.format(keyword=user_input_instance.keyword,results_text=results_text)#格式化拼接生成实际提示词
    response=llm_communicator(prompt,json_output=True)
    return response

def duck_search(keyword,max_results): #调用ddgs库进行搜索并输出映射后的字典列表
    try:
        raw_response=DDGS().text(keyword, region="cn-zh", max_results=max_results, time="d") #目前三个配置项硬编码为中文，（配置项），最新一天的消息，未来加入可配置项
    
    except Exception as e:
        print(f"ddgs搜索服务出现问题: {e}")

    '''映射ddgs回传的字典列表里的每个字典中的键名为符合prompt中使用的键名
    '''    
    # 映射后的新字典
    mapped_results = []

    # 遍历原始列表中的每一个字典
    for item in raw_response:
        new_item = {
            "title": item["title"],      # 键名不变，值照搬
            "link": item["href"],        # 键名从 href 变成 link
            "snippet": item["body"]      # 键名从 body 变成 snippet
        }
        mapped_results.append(new_item)  # 把新字典装进新列表
    return mapped_results

def screening_result(ds_result):  #筛选ds返回的评估后的结果，筛去无关结果
    if not isinstance(ds_result, list):
        print(f"错误: 期望传入列表，但实际传入类型为 {type(ds_result)}")

    max_fulltext_fetch=3          #最大抓取数量（将可由用户自定义，目前硬编码3）
    urls_to_fetch=[]              #确认保留的url
    for result in ds_result:
        if result["keep"] is True and not result["url"].endswith(".pdf"): #提取所有确认保留并且不是pdf文档的url
            urls_to_fetch.append(str(result["url"]))
    target_urls = urls_to_fetch[:max_fulltext_fetch] # 要传给 Jina 的 URL 列表（只取max_fulltext_fetch规定的数量）
    return target_urls 

def jina_fetch(target_urls):  #调用jina api 抓取全文
    fetched_texts=[]
    for url in target_urls:
        fetched_text=jina_communicator(url)
        fetched_texts.append(fetched_text)
    return fetched_texts

def generate_report(fetched_texts):
    template_prompt=config_instance.get_prompt("user","deep_summarizer") #从提示词模板文件中导入deep_summarizer模板
    prompt=template_prompt.format(keyword=user_input_instance.keyword,full_texts=fetched_texts)#格式化拼接生成实际提示词
    response=llm_communicator(prompt,json_output=False)
    return response

    

def main():
    user_input_instance.get_keyword()
    search_result=duck_search(user_input_instance.keyword,10)   #搜索网页(目前硬编码10条结果)
    str_search_result=format_search_result(search_result)
    analyze_result=json.loads(analyze_search_result(str_search_result)) #获取ds返回的JSON数组并解析为Python 列表
    target_urls=screening_result(analyze_result)
    fetched_texts=jina_fetch(target_urls)
    final_report=generate_report(fetched_texts)
    print(final_report)

if __name__ == "__main__":
    main()   