"""
AI 圆桌讨论 — 讨论引擎

负责根据话题和专家列表生成发言序列。
当前为预设发言池（MVP 阶段），后续接入 LLM 生成。
"""
import json
import os
import random
import time

from app.models import Session


HOST_OPENINGS = [
    '各位专家好，欢迎来到今天的 AI 圆桌讨论！我们今天聚焦的话题是：{topic}。请大家畅所欲言。',
    '大家好！今天的讨论话题非常有意义：{topic}。首先请各位专家谈谈初步看法。',
]

HOST_INTERJECTIONS = [
    '非常精彩的观点！关于这个话题，其他专家有什么不同的看法？',
    '感谢各位的深入分享。我想把话题引向另一个角度——从社会层面来看，我们该如何看待这个问题？',
    '好的，让我们进入下一个议题。各位专家对此还有什么补充？',
    '这个角度很有意思！能不能再深入谈谈您的看法？',
]

HOST_CLOSING = [
    '非常感谢各位专家的精彩讨论！今天的圆桌交流让我们看到了{topic}的多维视角。期待下次再会！',
]

ROUND_SUMMARIES = [
    '一轮下来，各位的观点都非常鲜明。让我们进入第二轮深入讨论。',
    '非常富有启发性的讨论！让我们进入最后一个环节——请每位专家用一句话总结您的核心观点。',
]


# ─── 专家观点模板 ────────────────────────────────────────

SPEECH_POOL = {
    # 正面 / 乐观 / 机遇
    'positive': [
        '我认为{topic}带来了前所未有的发展机遇，我们应该积极拥抱这一变革。',
        '从技术发展的历史来看，{topic}终将创造出更多我们目前还无法想象的价值。',
        '我在实际工作中深切感受到，{topic}正在极大地提升效率、降低成本。',
        '机遇远大于挑战，关键是我们要主动适应、积极布局。',
        '与其担忧{topic}的负面影响，不如思考如何最大化其正面价值。',
    ],
    # 审慎 / 风险
    'cautious': [
        '虽然{topic}前景广阔，但我们不能忽视其中存在的风险和挑战。',
        '我们需要在推进{topic}的同时，建立完善的监管和保障机制。',
        '变革的过程往往充满阵痛，我们需要为可能的负面影响做好准备。',
        '技术本身是中性的，关键在于我们如何引导和应用它。',
        '我认为我们更应该关注{topic}对社会公平和就业结构带来的深远影响。',
    ],
    # 政策 / 治理
    'policy': [
        '各国政府需要加快制定相关法律法规，为{topic}的健康发展提供制度保障。',
        '全球协同治理是关键——{topic}不分国界，需要国际社会共同努力。',
        '我们需要平衡创新与安全，既不能过度监管扼杀创新，也不能放任不管。',
        '在{topic}的发展过程中，必须确保公众利益优先。',
    ],
    # 教育 / 人才
    'education': [
        '教育体系需要率先变革，为{topic}时代培养具备新技能的人才。',
        '我们应该在基础教育阶段就开始培养{topic}相关的能力和素养。',
        '终身学习将成为新常态，每个人都需不断更新自己的知识结构。',
        '掌握{topic}相关技能的人才将在未来市场中占据优势。',
    ],
    # 人机协作
    'collaboration': [
        '人机协作是未来的主旋律——机器做机器擅长的事，人类做人类擅长的事。',
        'AI 不是替代人类，而是扩展人类的能力边界。',
        '真正的突破在于人机融合——不是谁替代谁，而是产生 1+1>2 的协同效应。',
        '{topic}将把人类从重复性工作中解放出来，让我们专注于创造性和战略性的工作。',
    ],
    # 安全 / 伦理
    'ethics': [
        '在推进{topic}的同时，我们必须重视安全和伦理问题。',
        '{topic}的对齐问题比替代问题更紧迫——如何确保其目标与人类价值观一致。',
        '我们需要更严格的测试和验证机制，确保{topic}的可靠性。',
        '技术透明度是建立公众信任的基础，{topic}的发展需要更开放的沟通。',
        '算法偏见和数据隐私是当前最棘手的问题，需要全行业共同努力解决。',
    ],
}


def _classify_stance(stance):
    """
    根据专家立场文本，分配发言类型标签。
    返回 list[str]: 匹配的发言池类型。
    """
    stance_lower = stance.lower() if stance else ''
    tags = []

    # 关键词匹配
    positive_words = ['乐观', '机遇', '创造', '积极', '发展', '赋能', '效率', '突破', '重塑', '深远']
    cautious_words = ['风险', '审慎', '担忧', '挑战', '阵痛', '分配', '不平等', '结构性']
    policy_words = ['治理', '监管', '框架', '制度', '国际', '协同', '法律', '政策', '全球']
    education_words = ['教育', '学习', '培养', '人才', '培训', '课程', '素养']
    collaboration_words = ['协作', '协作', '融合', '协同', '共生', '人机']
    ethics_words = ['安全', '伦理', '对齐', '偏见', '隐私', '可靠', '透明', '对齐']

    keyword_maps = [
        (positive_words, 'positive'),
        (cautious_words, 'cautious'),
        (policy_words, 'policy'),
        (education_words, 'education'),
        (collaboration_words, 'collaboration'),
        (ethics_words, 'ethics'),
    ]

    for keywords, tag in keyword_maps:
        for kw in keywords:
            if kw in stance_lower:
                if tag not in tags:
                    tags.append(tag)
                break

    # 兜底：如果没匹配到任何标签，随机分配 2 个
    if not tags:
        tags = random.sample(
            ['positive', 'cautious', 'policy', 'education', 'collaboration', 'ethics'],
            k=2,
        )

    return tags


def build_speeches_for_topic(topic, experts):
    """
    根据话题和专家列表构建完整发言序列。

    优先调用 DeepSeek API 生成动态发言，
    API 不可用时回退到预设发言池。

    参数:
        topic (str): 讨论话题
        experts (list[dict]): 专家列表（包含 id, name, stance, avatar_emoji, color 等）

    返回:
        list[dict]: 发言序列，每个元素包含 speaker_id, speaker_type,
                    speaker_name, avatar_emoji, content
    """
    if not experts:
        return []

    # ── 1. 尝试 DeepSeek API ────────────────────────────
    api_result = _api_generate_speeches(topic, experts)
    if api_result is not None:
        return api_result

    # ── 2. API 不可用，回退到预设发言池 ──────────────────
    return _fallback_speeches(topic, experts)


def _api_generate_speeches(topic, experts):
    """调用 DeepSeek API 生成讨论发言。

    返回:
        list[dict] | None: 发言序列，API 失败或结果不足时返回 None
    """
    from app.services.deepseek_client import call_deepseek_json

    # 构建专家描述（附带索引，供 API 引用）
    expert_lines = []
    for i, expert in enumerate(experts):
        expert_lines.append(
            f'[{i}] {expert["name"]}（{expert.get("title", "")}）'
            f'—— 立场：{expert.get("stance", "")}'
        )
    experts_desc = '\n'.join(expert_lines)

    system_prompt = (
        '你是一位圆桌讨论主持人。请根据话题和专家阵容，'
        '生成一场3轮的小型圆桌讨论发言。'
        '要求：每轮所有专家都发言一次，主持人负责开场、串场、收尾。'
        '发言内容要贴合每位专家的立场，语言自然口语化。'
        '总发言数必须达到 16-20 条，不要少于 16 条。'
    )

    user_prompt = (
        f'## 讨论话题\n{topic}\n\n'
        f'## 专家阵容\n{experts_desc}\n\n'
        '## 要求\n'
        '生成3轮讨论，每轮每位专家发言一次：\n'
        '第1轮：主持人开场（1条）→ 每位专家依次发言（{n}条）\n'
        '第2轮：主持人引导（1条）→ 每位专家依次发言（{n}条）\n'
        '第3轮：主持人收尾引导（1条）→ 每位专家一句话总结（{n}条）→ 主持人结语（1条）\n'
        f'总计：{len(experts) * 3 + 4} 条发言\n\n'
        '## 输出格式（JSON数组）\n'
        '[\n'
        '  {"speaker_type": "host", "speaker_index": -1, "content": "..."},\n'
        '  {"speaker_type": "expert", "speaker_index": 0, "content": "..."},\n'
        '  {"speaker_type": "expert", "speaker_index": 1, "content": "..."},\n'
        '  ...\n'
        ']\n'
        'speaker_index: 主持人填 -1，专家填对应的数组索引（0, 1, 2, ...）。'
    )

    # 替换占位符
    user_prompt = user_prompt.replace('{n}', str(len(experts)))

    print(f'[DEBUG] _api_generate_speeches: topic="{topic}", experts={len(experts)}')
    result = call_deepseek_json(
        messages=[{'role': 'user', 'content': user_prompt}],
        system_message=system_prompt,
        temperature=0.8,
        max_tokens=8192,
    )

    if not isinstance(result, list):
        print(f'[DEBUG] API result is not a list: {type(result)}')
        return None

    print(f'[DEBUG] API returned {len(result)} items')

    # 将 API 返回映射到标准格式（使用 speaker_index 而非 UUID）
    speeches = []
    for item in result:
        stype = item.get('speaker_type', 'expert')
        idx = item.get('speaker_index', -1)
        content = item.get('content', '')

        if stype == 'host' or idx < 0:
            speeches.append({
                'speaker_id': None,
                'speaker_type': 'host',
                'speaker_name': '主持人',
                'avatar_emoji': '🎙️',
                'content': content,
            })
        elif 0 <= idx < len(experts):
            expert = experts[idx]
            speeches.append({
                'speaker_id': expert['id'],
                'speaker_type': 'expert',
                'speaker_name': expert['name'],
                'avatar_emoji': expert.get('avatar_emoji', '🧑‍💼'),
                'content': content,
            })
        else:
            print(f'[DEBUG] Skipping item with invalid index: speaker_index={idx}')

    # 如果结果太少，说明解析可能有问题，让调用方降级到 fallback
    min_expected = max(5, len(experts) * 2)
    if len(speeches) < min_expected:
        print(f'[DEBUG] Speeches too few ({len(speeches)} < {min_expected}), falling back')
        return None

    print(f'[DEBUG] Returning {len(speeches)} speeches')
    return speeches


def _fallback_speeches(topic, experts):
    """当 API 不可用时，使用预设发言池构建讨论。"""
    speeches = []
    n = len(experts)

    if n == 0:
        return speeches

    # 为每位专家预分配发言内容
    expert_speeches = {}
    for expert in experts:
        tags = _classify_stance(expert.get('stance', ''))
        pool = []
        for tag in tags:
            pool.extend(SPEECH_POOL.get(tag, []))
        if not pool:
            pool = SPEECH_POOL['positive']
        random.shuffle(pool)
        selected = pool[:3]
        while len(selected) < 3:
            selected.append(random.choice(SPEECH_POOL['positive']))
        expert_speeches[expert['id']] = [
            s.format(topic=topic) for s in selected
        ]

    # 第 1 轮：主持人开场 → 每位专家发言
    speeches.append({
        'speaker_id': None, 'speaker_type': 'host',
        'speaker_name': '主持人', 'avatar_emoji': '🎙️',
        'content': random.choice(HOST_OPENINGS).format(topic=topic),
    })
    for expert in experts:
        speeches.append({
            'speaker_id': expert['id'], 'speaker_type': 'expert',
            'speaker_name': expert['name'],
            'avatar_emoji': expert['avatar_emoji'],
            'content': expert_speeches[expert['id']][0],
        })

    # 第 2 轮：主持人串场 → 每位专家发言
    speeches.append({
        'speaker_id': None, 'speaker_type': 'host',
        'speaker_name': '主持人', 'avatar_emoji': '🎙️',
        'content': (random.choice(ROUND_SUMMARIES).format(topic=topic) + ' ' +
                    random.choice(HOST_INTERJECTIONS).format(topic=topic)),
    })
    for expert in experts:
        speeches.append({
            'speaker_id': expert['id'], 'speaker_type': 'expert',
            'speaker_name': expert['name'],
            'avatar_emoji': expert['avatar_emoji'],
            'content': expert_speeches[expert['id']][1],
        })

    # 第 3 轮：主持人提醒收尾 → 每位专家一句话总结
    speeches.append({
        'speaker_id': None, 'speaker_type': 'host',
        'speaker_name': '主持人', 'avatar_emoji': '🎙️',
        'content': '时间关系，我们进行最后一个环节。请每位专家用一句话总结您的核心观点。',
    })
    for expert in experts:
        speeches.append({
            'speaker_id': expert['id'], 'speaker_type': 'expert',
            'speaker_name': expert['name'],
            'avatar_emoji': expert['avatar_emoji'],
            'content': expert_speeches[expert['id']][2],
        })

    # 主持人总结
    speeches.append({
        'speaker_id': None, 'speaker_type': 'host',
        'speaker_name': '主持人', 'avatar_emoji': '🎙️',
        'content': random.choice(HOST_CLOSING).format(topic=topic),
    })

    return speeches


def speech_event_generator(session_id, topic, experts, event_id_start=2):
    """
    SSE 事件生成器：按序生成发言事件（带间隔延迟）。

    每 2-3 秒生成一条 transcript.new 事件。
    全部发言推送完毕后，生成 session.status concluded 事件。

    参数:
        session_id (str): 会话 ID
        topic (str): 讨论话题
        experts (list[dict]): 专家列表
        event_id_start (int): 起始事件 ID

    生成:
        SSE 格式的 transcript.new 字符串
    """
    speeches = build_speeches_for_topic(topic, experts)
    event_id = event_id_start

    # 将数据库状态更新为 discussing
    _update_session_status(session_id, 'discussing')

    # 立即发送 session.status 事件
    event_id += 1
    yield _build_sse('session.status', {
        'session_id': session_id,
        'status': 'discussing',
        'previous_status': 'generating',
    }, event_id)

    # 逐一生成发言
    for speech in speeches:
        # 发言间隔（可通过环境变量调整，生产环境建议 2-3 秒）
        delay_min = float(os.environ.get('SPEECH_DELAY_MIN', '0.1'))
        delay_max = float(os.environ.get('SPEECH_DELAY_MAX', '0.3'))
        delay = delay_min + random.random() * (delay_max - delay_min)
        time.sleep(delay)

        event_id += 1
        yield _build_sse('transcript.new', {
            'id': f'{session_id}-t{event_id:04d}',
            'session_id': session_id,
            'speaker_type': speech['speaker_type'],
            'speaker_id': speech['speaker_id'],
            'speaker_name': speech['speaker_name'],
            'avatar_emoji': speech['avatar_emoji'],
            'content': speech['content'],
            'sequence': event_id - event_id_start,
            'created_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        }, event_id)

    # 全部发言完毕，更新数据库状态为 concluded
    _update_session_status(session_id, 'concluded')

    # 发送 session.status 事件
    event_id += 1
    yield _build_sse('session.status', {
        'session_id': session_id,
        'status': 'concluded',
        'previous_status': 'discussing',
    }, event_id)


def _update_session_status(session_id, new_status):
    """更新数据库中会话的状态（discussing / concluded）。

    在 SSE 生成器内部调用，此时请求上下文保持激活，
    current_app 可用，可直接操作数据库。
    """
    try:
        Session.update_status(session_id, new_status)
    except Exception:
        # 测试环境或无请求上下文时静默失败
        pass


def _build_sse(event, data, event_id=None):
    """构建单个 SSE 事件文本。"""
    lines = []
    if event_id is not None:
        lines.append(f'id: {event_id}')
    lines.append(f'event: {event}')
    lines.append(f'data: {json.dumps(data, ensure_ascii=False)}')
    lines.append('')
    return '\n'.join(lines) + '\n'
