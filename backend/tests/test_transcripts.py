"""
AI 圆桌讨论 — GET /api/sessions/{id}/transcript 接口测试

测试发言记录的游标分页、增量拉取、排序、会话信息包含。
发言数据通过 Transcript.create() 模型直接写入临时数据库。
"""
import pytest


def _create_session(client):
    """辅助函数：创建会话并返回完整响应 JSON。"""
    resp = client.post('/api/sessions', json={
        'topic': 'Transcript 测试话题',
        'expert_count': 2,
    })
    assert resp.status_code == 201
    return resp.get_json()


def _create_session_with_transcripts(client, app, count=5):
    """
    辅助函数：创建会话并在其下插入 count 条发言记录。

    返回:
        dict: 包含 session_id, experts, transcript_ids 的字典
    """
    data = _create_session(client)
    session_id = data['id']
    experts = data.get('experts', [])
    expert_id = experts[0]['id'] if experts else None

    transcript_ids = []
    with app.app_context():
        from app.models import Transcript
        for i in range(count):
            t = Transcript.create(
                session_id=session_id,
                speaker_type='host' if i % 2 == 0 else 'expert',
                speaker_name='主持人' if i % 2 == 0 else '测试专家',
                content=f'测试发言第 {i + 1} 条',
                avatar_emoji='🎙️' if i % 2 == 0 else '🧑‍🔬',
                speaker_id=None if i % 2 == 0 else expert_id,
            )
            transcript_ids.append(t.id)

    return {
        'session_id': session_id,
        'experts': experts,
        'expert_id': expert_id,
        'transcript_ids': transcript_ids,
    }


class TestTranscript:
    """GET /api/sessions/{id}/transcript — 获取发言记录"""

    # ─── 空记录 ──────────────────────────────────────────

    def test_transcript_empty(self, client):
        """
        创建会话但无任何发言记录，验证：
        - 返回 200
        - transcripts 为空列表
        - next_cursor 为 null
        - has_more 为 false
        """
        data = _create_session(client)
        session_id = data['id']

        resp = client.get(f'/api/sessions/{session_id}/transcript')
        assert resp.status_code == 200
        body = resp.get_json()

        assert body['transcripts'] == [], '无发言时应返回空列表'
        assert body['next_cursor'] is None, '无发言时 next_cursor 应为 null'
        assert body['has_more'] is False, '无发言时 has_more 应为 false'

    # ─── 正常记录 ─────────────────────────────────────────

    def test_transcript_with_entries(self, client, app):
        """
        创建会话并插入 10 条发言，验证：
        - 返回 10 条记录
        - 每条记录包含完整字段
        """
        ctx = _create_session_with_transcripts(client, app, count=10)
        session_id = ctx['session_id']

        resp = client.get(f'/api/sessions/{session_id}/transcript')
        assert resp.status_code == 200
        body = resp.get_json()

        assert len(body['transcripts']) == 10, f'应返回 10 条，实际 {len(body["transcripts"])}'

        # 验证每条记录字段完整性
        for t in body['transcripts']:
            assert 'id' in t
            assert 'session_id' in t
            assert t['session_id'] == session_id
            assert 'speaker_type' in t
            assert t['speaker_type'] in ('host', 'expert'), \
                f'speaker_type 应为 host 或 expert，实际为 {t["speaker_type"]}'
            assert 'speaker_name' in t
            assert 'content' in t
            assert 'sequence' in t
            assert isinstance(t['sequence'], int)
            assert 'created_at' in t
            assert 'avatar_emoji' in t

    # ─── 游标分页 ─────────────────────────────────────────

    def test_transcript_pagination(self, client, app):
        """
        创建 25 条发言，使用 cursor 分页 (limit=10)，验证：
        - 第 1 页：10 条，has_more=True，next_cursor 非空
        - 第 2 页：10 条，has_more=True，next_cursor 非空
        - 第 3 页：5 条，has_more=False，next_cursor 为 None
        - 页码不重叠（各页 sequence 区间互斥）
        """
        ctx = _create_session_with_transcripts(client, app, count=25)
        session_id = ctx['session_id']

        # 第 1 页：cursor 为空
        resp = client.get(f'/api/sessions/{session_id}/transcript?limit=10')
        assert resp.status_code == 200
        page1 = resp.get_json()
        assert len(page1['transcripts']) == 10, f'第 1 页应有 10 条，实际 {len(page1["transcripts"])}'
        assert page1['has_more'] is True, '第 1 页应有更多'
        assert page1['next_cursor'] == 10, f'第 1 页 next_cursor 应为 10，实际 {page1["next_cursor"]}'

        seqs_1 = [t['sequence'] for t in page1['transcripts']]
        assert seqs_1 == list(range(1, 11)), '第 1 页 sequence 应为 1-10'

        # 第 2 页：cursor = 10
        resp = client.get(f'/api/sessions/{session_id}/transcript?limit=10&cursor=10')
        assert resp.status_code == 200
        page2 = resp.get_json()
        assert len(page2['transcripts']) == 10, f'第 2 页应有 10 条，实际 {len(page2["transcripts"])}'
        assert page2['has_more'] is True, '第 2 页应有更多'
        assert page2['next_cursor'] == 20, f'第 2 页 next_cursor 应为 20，实际 {page2["next_cursor"]}'

        seqs_2 = [t['sequence'] for t in page2['transcripts']]
        assert seqs_2 == list(range(11, 21)), '第 2 页 sequence 应为 11-20'

        # 第 3 页：cursor = 20
        resp = client.get(f'/api/sessions/{session_id}/transcript?limit=10&cursor=20')
        assert resp.status_code == 200
        page3 = resp.get_json()
        assert len(page3['transcripts']) == 5, f'第 3 页应有 5 条，实际 {len(page3["transcripts"])}'
        assert page3['has_more'] is False, '第 3 页不应有更多'
        assert page3['next_cursor'] is None, '第 3 页 next_cursor 应为 null'

        seqs_3 = [t['sequence'] for t in page3['transcripts']]
        assert seqs_3 == list(range(21, 26)), '第 3 页 sequence 应为 21-25'

    # ─── 游标超出范围 ─────────────────────────────────────

    def test_transcript_cursor_eof(self, client, app):
        """
        使用超出范围的 cursor (999)，验证：
        - transcripts 为空列表
        - next_cursor 为 null
        - has_more 为 false
        """
        ctx = _create_session_with_transcripts(client, app, count=10)
        session_id = ctx['session_id']

        resp = client.get(f'/api/sessions/{session_id}/transcript?cursor=999')
        assert resp.status_code == 200
        body = resp.get_json()

        assert body['transcripts'] == [], '超出范围时应返回空列表'
        assert body['next_cursor'] is None, '超出范围时 next_cursor 应为 null'
        assert body['has_more'] is False, '超出范围时 has_more 应为 false'

    # ─── after 参数 ───────────────────────────────────────

    def test_transcript_after_parameter(self, client, app):
        """
        使用 after 参数 (after=5)，验证：
        - 只返回 sequence > 5 的发言
        - 返回的记录按 sequence 升序排列
        """
        ctx = _create_session_with_transcripts(client, app, count=15)
        session_id = ctx['session_id']

        resp = client.get(f'/api/sessions/{session_id}/transcript?after=5')
        assert resp.status_code == 200
        body = resp.get_json()

        # after=5 应返回 sequence 6-15
        assert len(body['transcripts']) == 10, f'after=5 应返回 10 条，实际 {len(body["transcripts"])}'

        seqs = [t['sequence'] for t in body['transcripts']]
        assert seqs == list(range(6, 16)), f'after=5 应返回 sequence 6-15，实际 {seqs}'

    def test_transcript_after_and_cursor_equivalent(self, client, app):
        """
        验证 after 参数与 cursor 参数功能等价：
        after=5 和 cursor=5 应返回完全相同的结果。
        """
        ctx = _create_session_with_transcripts(client, app, count=15)
        session_id = ctx['session_id']

        resp_after = client.get(f'/api/sessions/{session_id}/transcript?after=5')
        resp_cursor = client.get(f'/api/sessions/{session_id}/transcript?cursor=5')

        assert resp_after.status_code == 200
        assert resp_cursor.status_code == 200

        body_after = resp_after.get_json()
        body_cursor = resp_cursor.get_json()

        assert len(body_after['transcripts']) == len(body_cursor['transcripts']), \
            'after 和 cursor 应返回相同数量的记录'
        for ta, tc in zip(body_after['transcripts'], body_cursor['transcripts']):
            assert ta['sequence'] == tc['sequence']
            assert ta['id'] == tc['id']

    # ─── 会话不存在 ───────────────────────────────────────

    def test_transcript_session_not_found(self, client):
        """
        请求不存在的 session_id，验证：
        - 返回 404
        - 错误码为 SESSION_NOT_FOUND
        """
        resp = client.get('/api/sessions/non-existent-id/transcript')
        assert resp.status_code == 404
        data = resp.get_json()
        assert data['error']['code'] == 'SESSION_NOT_FOUND'

    # ─── 排序 ─────────────────────────────────────────────

    def test_transcript_ordering(self, client, app):
        """
        验证返回的记录严格按 sequence 升序排列。
        （Transcript.create 插入时 sequence 递增，但需确保端点排序正确）
        """
        ctx = _create_session_with_transcripts(client, app, count=20)
        session_id = ctx['session_id']

        resp = client.get(f'/api/sessions/{session_id}/transcript')
        assert resp.status_code == 200
        body = resp.get_json()

        seqs = [t['sequence'] for t in body['transcripts']]
        assert seqs == sorted(seqs), f'sequence 应严格升序，实际 {seqs}'
        assert seqs == list(range(1, 21)), f'应包含 1-20 所有 sequence'

    # ─── 会话信息 ─────────────────────────────────────────

    def test_transcript_includes_session_info(self, client, app):
        """
        验证响应中包含：
        - session 基本信息（id、topic、status、expert_count）
        - 专家列表（experts），包含会话的各位专家
        """
        data = _create_session(client)
        session_id = data['id']

        # 先插入几条发言，让会话有数据
        with app.app_context():
            from app.models import Transcript
            Transcript.create(
                session_id=session_id,
                speaker_type='host',
                speaker_name='主持人',
                content='开场白',
                avatar_emoji='🎙️',
            )

        resp = client.get(f'/api/sessions/{session_id}/transcript')
        assert resp.status_code == 200
        body = resp.get_json()

        # session 信息
        assert 'session' in body, '响应应包含 session 字段'
        assert body['session'] is not None, 'session 不应为 null'
        assert body['session']['id'] == session_id
        assert body['session']['topic'] == 'Transcript 测试话题'
        assert body['session']['status'] in ('pending', 'generating', 'discussing', 'concluded', 'error')
        assert 'expert_count' in body['session']

        # 专家列表
        assert 'experts' in body, '响应应包含 experts 字段'
        assert isinstance(body['experts'], list), 'experts 应为列表'
        assert len(body['experts']) > 0, 'experts 不应为空列表'

        for expert in body['experts']:
            assert 'id' in expert
            assert 'name' in expert
            assert 'title' in expert
            assert 'stance' in expert
            assert 'color' in expert
            assert 'avatar_emoji' in expert
            assert 'sort_order' in expert

        # 验证 experts 属于该会话
        for expert in body['experts']:
            assert expert['session_id'] == session_id, \
                f'专家 {expert["name"]} 的 session_id 应与会话一致'

    # ─── 限制条数 ─────────────────────────────────────────

    def test_transcript_limit_parameter(self, client, app):
        """
        使用 limit=3 参数，验证：
        - 只返回 3 条记录
        - next_cursor 非空（因为还有更多）
        - has_more 为 true
        """
        ctx = _create_session_with_transcripts(client, app, count=10)
        session_id = ctx['session_id']

        resp = client.get(f'/api/sessions/{session_id}/transcript?limit=3')
        assert resp.status_code == 200
        body = resp.get_json()

        assert len(body['transcripts']) == 3, f'limit=3 应返回 3 条，实际 {len(body["transcripts"])}'
        assert body['has_more'] is True, 'limit=3 时还有更多记录'
        assert body['next_cursor'] is not None, 'limit=3 时 next_cursor 不应为 null'
        assert body['next_cursor'] == 3, f'limit=3 时 next_cursor 应为 3，实际 {body["next_cursor"]}'
