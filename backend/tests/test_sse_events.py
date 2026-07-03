"""
AI 圆桌讨论 — GET /api/sessions/{id}/events SSE 事件流测试

测试 SSE 连接建立、心跳保活、多连接隔离。
SSE 端点返回 text/event-stream 流式响应，使用 Flask test_client
的 buffered=False 模式获取底层迭代器，通过线程异步读取。
"""
import json
import queue
import threading
import time

import pytest


def _create_session(client):
    """辅助函数：通过 POST 创建一个会话，返回 session_id。"""
    resp = client.post('/api/sessions', json={
        'topic': 'SSE 测试话题',
        'expert_count': 2,
    })
    assert resp.status_code == 201
    return resp.get_json()['id']


def _read_stream_into_queue(resp, event_queue, stop_event=None):
    """
    将 SSE 响应流的内容放入队列，供主线程消费。

    参数:
        resp: Flask test_client 的流式响应 (buffered=False)
        event_queue: queue.Queue，存放原始 SSE 块
        stop_event: threading.Event，设置后停止读取
    """
    try:
        for chunk in resp.response:
            if stop_event and stop_event.is_set():
                break
            if chunk:
                event_queue.put(chunk)
    except Exception:
        pass


def _parse_sse_events(raw_chunks):
    """
    将原始 SSE 字节块解析为事件列表。

    返回:
        list[dict]: [{'event': 'session.status', 'data': {...}}, ...]
    """
    text = b''.join(raw_chunks).decode('utf-8')
    events = []
    current_event = None
    current_data = []

    for line in text.splitlines():
        if line.startswith('event: '):
            # 保存上一条事件
            if current_event is not None and current_data:
                events.append({
                    'event': current_event,
                    'data': ''.join(current_data),
                })
            current_event = line[7:].strip()
            current_data = []
        elif line.startswith('data: '):
            current_data.append(line[6:])
        elif line.strip() == '':
            # 空行表示事件结束
            if current_event is not None and current_data:
                events.append({
                    'event': current_event,
                    'data': ''.join(current_data),
                })
                current_event = None
                current_data = []

    # flush 最后一条
    if current_event is not None and current_data:
        events.append({
            'event': current_event,
            'data': ''.join(current_data),
        })

    # 解析 JSON data
    for ev in events:
        try:
            ev['data'] = json.loads(ev['data'])
        except (json.JSONDecodeError, TypeError):
            pass

    return events


class TestSSEEvents:
    """GET /api/sessions/{id}/events — SSE 事件流"""

    # ─── 连接建立 ─────────────────────────────────────────

    def test_sse_connection_success(self, client):
        """
        创建会话后连接 /events 端点，验证：
        - 返回 200
        - Content-Type 为 text/event-stream
        - 包含必要的 SSE 头（Cache-Control: no-cache）
        """
        session_id = _create_session(client)

        resp = client.get(f'/api/sessions/{session_id}/events')

        assert resp.status_code == 200
        assert resp.mimetype == 'text/event-stream', \
            f'Content-Type 应为 text/event-stream，实际为 {resp.mimetype}'
        assert resp.cache_control.no_cache is True, \
            'SSE 响应应包含 Cache-Control: no-cache'

    def test_sse_connection_streaming(self, client):
        """
        验证 SSE 响应为流式（非缓冲），
        能在不关闭连接的情况下收到初始事件。
        """
        session_id = _create_session(client)

        resp = client.get(f'/api/sessions/{session_id}/events', buffered=False)
        assert resp.status_code == 200
        assert resp.is_streamed, 'SSE 响应应为流式响应'

        # 读取第一个事件（session.status，应立即可用）
        event_queue = queue.Queue()
        reader = threading.Thread(
            target=_read_stream_into_queue,
            args=(resp, event_queue),
            daemon=True,
        )
        reader.start()

        try:
            chunk = event_queue.get(timeout=3)
            assert chunk, '应收到初始 SSE 事件'
        except queue.Empty:
            pytest.fail('3 秒内未收到任何 SSE 事件，流式响应未生效')

    # ─── 会话不存在 ──────────────────────────────────────

    def test_sse_session_not_found(self, client):
        """
        连接不存在的会话 ID，验证：
        - 返回 404
        - 错误码为 SESSION_NOT_FOUND
        """
        resp = client.get('/api/sessions/non-existent-id/events')

        assert resp.status_code == 404
        data = resp.get_json()
        assert data['error']['code'] == 'SESSION_NOT_FOUND'

    def test_sse_session_not_found_uuid_format(self, client):
        """
        使用 UUID 格式但不存在于数据库的 ID，验证返回 404。
        """
        resp = client.get(
            '/api/sessions/00000000-0000-0000-0000-000000000000/events'
        )
        assert resp.status_code == 404

    # ─── 初始事件 ─────────────────────────────────────────

    def test_sse_initial_status_event(self, client):
        """
        连接成功后，验证收到的第一个事件为 session.status，
        包含正确的 session_id、status 和 previous_status。
        """
        session_id = _create_session(client)

        resp = client.get(f'/api/sessions/{session_id}/events', buffered=False)
        event_queue = queue.Queue()
        reader = threading.Thread(
            target=_read_stream_into_queue,
            args=(resp, event_queue),
            daemon=True,
        )
        reader.start()

        # 收集事件，3 秒超时
        chunks = []
        deadline = time.time() + 3
        while time.time() < deadline:
            try:
                chunks.append(event_queue.get(timeout=0.5))
            except queue.Empty:
                break

        assert len(chunks) > 0, '应收到至少一个 SSE 事件'

        events = _parse_sse_events(chunks)
        assert len(events) >= 1, '应能解析出至少一个事件'

        first = events[0]
        assert first['event'] == 'session.status', \
            f'第一个事件应为 session.status，实际为 {first["event"]}'
        assert first['data']['session_id'] == session_id
        assert 'status' in first['data']
        assert 'previous_status' in first['data']

    # ─── 心跳 ─────────────────────────────────────────────

    def test_sse_heartbeat(self, client):
        """
        连接后，验证在 30 秒内收到 heartbeat 事件。
        注意：该测试依赖 stream_events 中 30 秒的心跳间隔，
        实际执行约需 30 秒。
        """
        session_id = _create_session(client)

        resp = client.get(f'/api/sessions/{session_id}/events', buffered=False)
        assert resp.status_code == 200

        event_queue = queue.Queue()
        stop_event = threading.Event()
        reader = threading.Thread(
            target=_read_stream_into_queue,
            args=(resp, event_queue, stop_event),
            daemon=True,
        )
        reader.start()

        # 在 35 秒内等待 heartbeat 事件
        max_wait = 35
        deadline = time.time() + max_wait
        found_heartbeat = False

        while time.time() < deadline and not found_heartbeat:
            try:
                chunk = event_queue.get(timeout=min(5, deadline - time.time()))
                parsed = _parse_sse_events([chunk])
                for ev in parsed:
                    if ev['event'] == 'heartbeat':
                        found_heartbeat = True
                        # 验证 heartbeat 数据结构
                        assert 'timestamp' in ev['data'], \
                            'heartbeat 事件应包含 timestamp'
                        break
            except queue.Empty:
                continue
        stop_event.set()

        assert found_heartbeat, (
            f'应在 {max_wait} 秒内收到 heartbeat 事件 '
            f'（服务端心跳间隔为 30 秒）'
        )

    # ─── 多连接 ───────────────────────────────────────────

    def test_sse_multiple_connections(self, client):
        """
        同一会话创建多个 SSE 连接，验证：
        - 每个连接都能正常建立
        - 每个连接都能独立接收事件
        """
        session_id = _create_session(client)
        n_connections = 3

        results = []  # [(queue, thread, resp, stop_event), ...]

        for i in range(n_connections):
            resp = client.get(
                f'/api/sessions/{session_id}/events', buffered=False
            )
            assert resp.status_code == 200, f'连接 {i} 建立失败'

            q = queue.Queue()
            stop = threading.Event()
            t = threading.Thread(
                target=_read_stream_into_queue,
                args=(resp, q, stop),
                daemon=True,
            )
            t.start()
            results.append((q, t, resp, stop))

        # 等待每个连接收到初始 session.status 事件
        for i, (q, t, resp, stop) in enumerate(results):
            try:
                chunk = q.get(timeout=5)
                assert chunk, f'连接 {i} 未收到任何事件'
                parsed = _parse_sse_events([chunk])
                assert len(parsed) >= 1, f'连接 {i} 的事件无法解析'
                assert parsed[0]['event'] == 'session.status', \
                    f'连接 {i} 的第一个事件应为 session.status'
            except queue.Empty:
                pytest.fail(f'连接 {i} 在 5 秒内未收到初始事件')
            finally:
                stop.set()

    def test_sse_connections_independent(self, client):
        """
        验证不同会话的 SSE 连接相互隔离：
        会话 A 的连接不会收到会话 B 的事件。
        """
        sid_a = _create_session(client)
        sid_b = _create_session(client)

        resp_a = client.get(f'/api/sessions/{sid_a}/events', buffered=False)
        resp_b = client.get(f'/api/sessions/{sid_b}/events', buffered=False)

        q_a = queue.Queue()
        q_b = queue.Queue()
        stop_a = threading.Event()
        stop_b = threading.Event()

        ta = threading.Thread(
            target=_read_stream_into_queue, args=(resp_a, q_a, stop_a),
            daemon=True,
        )
        tb = threading.Thread(
            target=_read_stream_into_queue, args=(resp_b, q_b, stop_b),
            daemon=True,
        )
        ta.start()
        tb.start()

        try:
            # 读取两个连接的第一个事件
            chunk_a = q_a.get(timeout=5)
            chunk_b = q_b.get(timeout=5)

            events_a = _parse_sse_events([chunk_a])
            events_b = _parse_sse_events([chunk_b])

            # 两个事件的 session_id 应不同
            for ev in events_a:
                if ev['event'] == 'session.status':
                    assert ev['data']['session_id'] == sid_a, \
                        '连接 A 的事件 session_id 应匹配 sid_a'

            for ev in events_b:
                if ev['event'] == 'session.status':
                    assert ev['data']['session_id'] == sid_b, \
                        '连接 B 的事件 session_id 应匹配 sid_b'

        except queue.Empty:
            pytest.fail('某个连接在 5 秒内未收到事件')
        finally:
            stop_a.set()
            stop_b.set()

    # ─── SSE 协议格式 ─────────────────────────────────────

    def test_sse_event_format(self, client):
        """
        验证 SSE 事件的格式符合协议规范：
        - 事件以 'event:' 行开头
        - 数据以 'data:' 行开头
        - 事件以空行结束
        - data 为合法 JSON
        """
        session_id = _create_session(client)

        resp = client.get(f'/api/sessions/{session_id}/events', buffered=False)
        event_queue = queue.Queue()
        reader = threading.Thread(
            target=_read_stream_into_queue, args=(resp, event_queue),
            daemon=True,
        )
        reader.start()

        # 收集原始字节
        raw_chunks = []
        deadline = time.time() + 3
        while time.time() < deadline:
            try:
                raw_chunks.append(event_queue.get(timeout=0.5))
            except queue.Empty:
                break

        assert len(raw_chunks) > 0, '应收到 SSE 数据'

        full_text = b''.join(raw_chunks).decode('utf-8')

        # 基础格式校验
        assert 'event:' in full_text, 'SSE 应包含 event 行'
        assert 'data:' in full_text, 'SSE 应包含 data 行'

        # 解析后验证
        events = _parse_sse_events(raw_chunks)
        assert len(events) >= 1, '应能解析出至少一个事件'

        for ev in events:
            assert isinstance(ev['event'], str) and ev['event'], \
                'event 字段应为非空字符串'
            assert isinstance(ev['data'], dict), \
                'data 字段应为合法 JSON 对象'
