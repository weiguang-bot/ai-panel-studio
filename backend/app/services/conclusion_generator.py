"""
AI 圆桌讨论 — 结论生成器

负责为已完成的讨论生成共识与分歧摘要。
当前为占位实现（返回固定模板数据），后续集成 DeepSeek API 调用。
"""
import uuid


def generate_conclusion(session_id):
    """
    根据讨论会话生成共识与分歧摘要。

    参数:
        session_id (str): 会话 UUID

    返回:
        dict: {
            'consensus': [{'id': str, 'summary': str, 'degree': str, 'order_index': int}],
            'divergences': [{'id': str, 'description': str, 'involved_expert_ids': list,
                             'severity': str, 'order_index': int}],
            'session_status': 'concluded',
        }
    """
    # TODO: 替换为真实的 AI 调用（基于 transcripts 生成 consensus/divergences）
    # api_key = current_app.config.get('DEEPSEEK_API_KEY', '')
    # if api_key:
    #     return _call_deepseek_api(session_id, api_key)

    return _fallback_conclusion()


def _fallback_conclusion():
    """当 API 不可用时返回固定占位数据。"""
    consensus = [
        {
            'id': str(uuid.uuid4()),
            'summary': 'AI 将深度改变工作方式，人类需持续学习以适应变革',
            'degree': 'strong',
            'order_index': 1,
        },
        {
            'id': str(uuid.uuid4()),
            'summary': '法律法规和伦理准则应同步跟进技术发展',
            'degree': 'moderate',
            'order_index': 2,
        },
    ]

    divergences = [
        {
            'id': str(uuid.uuid4()),
            'description': 'AI 对白领 vs 蓝领岗位的影响程度与时间线存在分歧',
            'involved_expert_ids': [],
            'severity': 'high',
            'order_index': 1,
        },
    ]

    return {
        'consensus': consensus,
        'divergences': divergences,
        'session_status': 'concluded',
    }
