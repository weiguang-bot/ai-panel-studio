"""
AI 圆桌讨论 — 结论生成器

负责为已完成的讨论生成共识与分歧摘要。
优先调用 DeepSeek API，不可用时回退到预设模板。
"""
import uuid
from flask import current_app


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
    # ── 1. 尝试 DeepSeek API ────────────────────────────
    api_result = _api_generate_conclusion(session_id)
    if api_result is not None:
        return api_result

    # ── 2. API 不可用，回退到预设模板 ────────────────────
    return _fallback_conclusion()


def _api_generate_conclusion(session_id):
    """
    调用 DeepSeek API 根据发言记录生成共识分歧摘要。

    返回:
        dict | None: API 成功时返回结论数据，失败时返回 None
    """
    from app.services.deepseek_client import call_deepseek_json
    from app.models import Transcript, Expert

    # 获取发言记录（返回 (items, next_cursor) 元组）
    transcripts, _ = Transcript.list_by_session(session_id, limit=200)

    if not transcripts:
        return None

    # 获取专家列表
    experts = Expert.list_by_session(session_id)
    expert_map = {e['id']: e['name'] for e in experts}

    # 构建发言文本
    transcript_lines = []
    for t in transcripts:
        speaker = t['speaker_name']
        content = t['content']
        transcript_lines.append(f'{speaker}: {content}')
    transcript_text = '\n'.join(transcript_lines)

    system_prompt = (
        '你是一位圆桌讨论分析师。请根据发言记录，'
        '总结出专家们达成的共识要点和存在的分歧要点。'
        '要求：客观中立，基于发言内容，不要添加发言中没有的观点。'
    )

    user_prompt = (
        f'## 发言记录\n{transcript_text}\n\n'
        '## 要求\n'
        '1. 共识要点（2-3 条）：专家们达成一致的看法\n'
        '2. 分歧要点（0-2 条）：专家们存在不同意见的地方\n\n'
        '## 输出格式（JSON）\n'
        '{\n'
        '  "consensus": [\n'
        '    {"summary": "共识描述", "degree": "strong|moderate|weak", "order_index": 1},\n'
        '    ...\n'
        '  ],\n'
        '  "divergences": [\n'
        '    {"description": "分歧描述", "involved_expert_ids": ["e001"], "severity": "high|medium|low", "order_index": 1},\n'
        '    ...\n'
        '  ]\n'
        '}\n'
        'degree: strong=高度共识, moderate=一般共识, weak=弱共识\n'
        'severity: high=严重分歧, medium=一般分歧, low=轻微分歧\n'
        'involved_expert_ids: 参与该分歧的专家 ID 列表（发言记录中提取）'
    )

    result = call_deepseek_json(
        messages=[{'role': 'user', 'content': user_prompt}],
        system_message=system_prompt,
        temperature=0.5,
        max_tokens=2000,
    )

    if not isinstance(result, dict) or 'consensus' not in result:
        return None

    # 映射到标准响应格式
    consensus = []
    for i, c in enumerate(result.get('consensus', [])):
        consensus.append({
            'id': str(uuid.uuid4()),
            'summary': c.get('summary', ''),
            'degree': c.get('degree', 'moderate'),
            'order_index': c.get('order_index', i + 1),
        })

    divergences = []
    for i, d in enumerate(result.get('divergences', [])):
        divergences.append({
            'id': str(uuid.uuid4()),
            'description': d.get('description', ''),
            'involved_expert_ids': d.get('involved_expert_ids', []),
            'severity': d.get('severity', 'medium'),
            'order_index': d.get('order_index', i + 1),
        })

    if not consensus:
        return None

    return {
        'consensus': consensus,
        'divergences': divergences,
        'session_status': 'concluded',
    }


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
