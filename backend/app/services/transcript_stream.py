"""
AI 圆桌讨论 — 发言流服务

负责管理 SSE (Server-Sent Events) 连接、推送发言及心跳。
"""
import json
import time


def event_generator(session_id, current_status='generating',
                    previous_status='pending', last_event_id=None,
                    topic=None, experts=None):
    """
    SSE 事件生成器。

    参数:
        session_id (str): 会话 ID
        current_status (str): 当前会话状态
        previous_status (str): 先前会话状态
        last_event_id (str, optional): 断线重连时传入的最后事件 ID
        topic (str, optional): 讨论话题，提供后将自动启动讨论引擎
        experts (list, optional): 专家列表，与 topic 配合使用

    生成的 SSE 事件:
        1. session.status — 连接建立后立即发送
        2. transcript.new  — 讨论引擎生成的发言（如提供 topic + experts）
        3. session.status — 讨论结束状态（concluded）
        4. heartbeat      — 每 30 秒发送一次
    """
    event_id = 0

    # ── 1. 立即发送 session.status ──────────────────────
    event_id += 1
    yield _format_sse('session.status', {
        'session_id': session_id,
        'status': current_status,
        'previous_status': previous_status,
    }, event_id)

    # ── 2. 讨论引擎发言（如提供了 topic 和 experts） ────
    if topic and experts:
        from app.services.discussion_engine import speech_event_generator
        gen = speech_event_generator(
            session_id, topic, experts, event_id_start=event_id,
        )
        chunk_count = 0
        for sse_chunk in gen:
            chunk_count += 1
            yield sse_chunk
        event_id += chunk_count  # 同步 event_id

    # ── 3. 心跳循环（每 30 秒） ─────────────────────────
    try:
        while True:
            time.sleep(30)
            event_id += 1
            yield _format_sse('heartbeat', {
                'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            }, event_id)
    except GeneratorExit:
        pass


def _format_sse(event, data, event_id=None):
    """
    格式化为 SSE 协议文本。

    SSE 协议格式:
        id: <sequence_number>
        event: <event_type>
        data: <json_payload>

    每块以空行结束。
    """
    lines = []
    if event_id is not None:
        lines.append(f'id: {event_id}')
    lines.append(f'event: {event}')
    lines.append(f'data: {json.dumps(data, ensure_ascii=False)}')
    lines.append('')  # 空行表示事件结束
    return '\n'.join(lines) + '\n'
