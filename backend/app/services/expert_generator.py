"""
AI 圆桌讨论 — 专家生成器

负责调用 DeepSeek API 生成虚拟专家列表（姓名、头衔、立场等）。
当前为占位实现，后续集成 LLM 调用。
"""
from flask import current_app


def generate_experts(topic, count=4):
    """
    根据讨论话题生成指定数量的虚拟专家。

    参数:
        topic (str): 讨论话题
        count (int): 专家人数（含主持人时为 count+1）

    返回:
        list[dict]: 专家数据列表
            [{'name': str, 'title': str, 'stance': str,
              'color': str, 'avatar_emoji': str, 'sort_order': int}]
    """
    api_key = current_app.config.get('DEEPSEEK_API_KEY', '')

    if not api_key:
        # 无 API Key 时返回占位数据
        return _fallback_experts(topic, count)

    # TODO: 调用 DeepSeek API 生成专家
    # prompt = f"为圆桌讨论话题「{topic}」生成 {count} 位虚拟专家..."
    # response = call_deepseek_api(prompt, api_key)
    # return parse_experts_from_response(response)

    return _fallback_experts(topic, count)


def _fallback_experts(topic, count):
    """当 API 不可用时返回固定占位数据。"""
    import random

    pool = [
        {'name': '张思远', 'title': 'AI 伦理研究员 · 清华大学',
         'stance': '持审慎乐观态度，认为 AI 会重塑而非取代',
         'color': '#6366f1', 'avatar_emoji': '🧑‍🔬'},
        {'name': '李敏', 'title': '算法工程师 · 字节跳动',
         'stance': 'AI 将大规模创造新岗位',
         'color': '#10b981', 'avatar_emoji': '👩‍💻'},
        {'name': '王建国', 'title': '劳动经济学教授 · 北京大学',
         'stance': '结构性失业风险真实存在',
         'color': '#f59e0b', 'avatar_emoji': '👨‍🏫'},
        {'name': '陈思睿', 'title': 'AI 政策研究顾问',
         'stance': '需要全球协同治理框架',
         'color': '#ef4444', 'avatar_emoji': '👩‍🎓'},
        {'name': '赵明宇', 'title': '机器人学专家 · 中科院',
         'stance': '人机协作是未来主旋律',
         'color': '#8b5cf6', 'avatar_emoji': '👨‍🚀'},
        {'name': '林小婉', 'title': '未来学家 · 腾讯研究院',
         'stance': 'AI 将催生全新文明形态',
         'color': '#ec4899', 'avatar_emoji': '🧙‍♀️'},
        {'name': '周浩然', 'title': '社会学家 · 复旦大学',
         'stance': '技术中性，关键在于制度设计',
         'color': '#14b8a6', 'avatar_emoji': '👨‍🎓'},
        {'name': '吴晓峰', 'title': 'AI 安全研究员 · 微软亚洲研究院',
         'stance': '对齐问题比替代问题更紧迫',
         'color': '#f97316', 'avatar_emoji': '🧑‍💻'},
        {'name': '孙雅文', 'title': '教育科技创业者',
         'stance': '教育体系必须率先变革',
         'color': '#06b6d4', 'avatar_emoji': '👩‍🏫'},
        {'name': '黄磊', 'title': '科技记者 · 36氪',
         'stance': '公众认知与技术发展存在鸿沟',
         'color': '#a855f7', 'avatar_emoji': '📝'},
    ]

    # 打乱后取前 count 位，赋予 sort_order
    selected = random.sample(pool, min(count, len(pool)))
    for i, expert in enumerate(selected):
        expert['sort_order'] = i + 1

    return selected
