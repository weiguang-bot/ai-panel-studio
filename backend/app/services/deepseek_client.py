"""
DeepSeek API 客户端

封装对 DeepSeek Chat API 的调用，提供统一的错误处理和重试机制。
使用 OpenAI 兼容接口：POST https://api.deepseek.com/v1/chat/completions
"""
import json
import os
import time
import urllib.request
import urllib.error


DEEPSEEK_API_URL = 'https://api.deepseek.com/v1/chat/completions'
DEFAULT_MODEL = 'deepseek-chat'
MAX_RETRIES = 2
RETRY_DELAY = 2.0


def _get_api_key():
    """从环境变量获取 DeepSeek API Key。"""
    return os.environ.get('DEEPSEEK_API_KEY', '').strip()


def call_deepseek(messages, system_message=None, temperature=0.7,
                  max_tokens=2000, model=None):
    """
    调用 DeepSeek Chat API。

    参数:
        messages (list[dict]): 对话消息 [{'role': 'user', 'content': '...'}, ...]
        system_message (str, optional): System 提示词
        temperature (float): 生成温度 (0-1)
        max_tokens (int): 最大生成字数
        model (str): 模型名称，默认 deepseek-chat

    返回:
        str: API 返回的文本内容；失败时返回 None
    """
    api_key = _get_api_key()
    if not api_key:
        return None

    full_messages = []
    if system_message:
        full_messages.append({'role': 'system', 'content': system_message})
    full_messages.extend(messages)

    payload = {
        'model': model or DEFAULT_MODEL,
        'messages': full_messages,
        'temperature': temperature,
        'max_tokens': max_tokens,
    }

    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        DEEPSEEK_API_URL,
        data=data,
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        },
        method='POST',
    )

    for attempt in range(MAX_RETRIES + 1):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode('utf-8'))
                return result['choices'][0]['message']['content']
        except (urllib.error.HTTPError, urllib.error.URLError,
                json.JSONDecodeError, KeyError, OSError) as e:
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY * (attempt + 1))
                continue
            return None


def call_deepseek_json(messages, system_message=None, temperature=0.5,
                       max_tokens=3000, model=None):
    """
    调用 DeepSeek API 并解析返回的 JSON。

    返回:
        dict/list: 解析后的 JSON 对象；失败时返回 None
    """
    text = call_deepseek(
        messages=messages,
        system_message=system_message,
        temperature=temperature,
        max_tokens=max_tokens,
        model=model,
    )
    if text is None:
        return None

    # 尝试从 markdown 代码块中提取 JSON
    text = text.strip()
    if '```json' in text:
        text = text.split('```json')[1].split('```')[0].strip()
    elif '```' in text:
        text = text.split('```')[1].split('```')[0].strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None
