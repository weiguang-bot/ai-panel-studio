"""
AI 圆桌讨论 — 发言流服务

负责管理 SSE (Server-Sent Events) 连接、推送发言及心跳。
"""
import json
import time
from flask import current_app, Response


def stream_events(session_id):
    """
    为指定会话创建 SSE 事件流生成器。

    用法:
        return Response(stream_events(session_id), mimetype='text/event-stream')

    事件类型:
        event: session.status     — 状态变更
        event: transcript.new     — 新发言
        event: expert.generated   — 专家生成完成
        event: conclusion.completed — 结论生成完成
        event: heartbeat          — 保活信号（每 30 秒）
        event: session.error      — 错误
    """
    def generate():
        # TODO: 订阅 Redis/pubsub 或内存队列，实时推送
        # 当前返回一个空流，后续实现
        yield _format_sse('session.status', {
            'session_id': session_id,
            'status': 'discussing',
            'previous_status': 'generating',
        })

        # 模拟心跳
        while True:
            time.sleep(30)
            yield _format_sse('heartbeat', {
                'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            })

    return Response(generate(), mimetype='text/event-stream',
                    headers={
                        'Cache-Control': 'no-cache',
                        'Connection': 'keep-alive',
                        'X-Accel-Buffering': 'no',
                    })


def _format_sse(event, data):
    """格式化为 SSE 协议文本。"""
    return f'event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n'
