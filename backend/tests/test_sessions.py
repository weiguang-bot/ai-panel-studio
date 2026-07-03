"""
AI 圆桌讨论 — POST /api/sessions 接口测试

测试数据写入临时 SQLite 数据库（由 conftest.py 管理），
不依赖任何外部服务或持久化数据。
"""
import pytest


class TestCreateSession:
    """POST /api/sessions — 创建讨论会话"""

    # ─── 正向用例 ─────────────────────────────────────────

    def test_create_session_success(self, client, app):
        """
        输入有效的 topic 和 expert_count=4，验证：
        - 返回 201
        - 响应包含 id、topic、status='generating'
        - 数据库中确实存在对应记录
        """
        resp = client.post('/api/sessions', json={
            'topic': '人工智能是否会取代人类工作',
            'expert_count': 4,
        })
        assert resp.status_code == 201
        data = resp.get_json()

        # 响应字段验证
        assert data['id'], '创建成功应返回非空 id'
        assert data['topic'] == '人工智能是否会取代人类工作'
        assert data['expert_count'] == 4
        assert data['status'] == 'generating'
        assert data['created_at'], '创建成功应返回非空 created_at'

        # 数据库记录验证
        with app.app_context():
            from app.models import Session
            session = Session.get(data['id'])
            assert session is not None, '数据库应存在对应会话记录'
            assert session.topic == '人工智能是否会取代人类工作'
            assert session.expert_count == 4
            assert session.status in ('pending', 'generating')

    # ─── 参数校验：topic ──────────────────────────────────

    def test_create_session_missing_topic(self, client):
        """
        请求体缺少 topic 字段，验证：
        - 返回 400
        - 错误码为 VALIDATION_ERROR
        """
        resp = client.post('/api/sessions', json={'expert_count': 4})
        assert resp.status_code == 400
        data = resp.get_json()
        assert data['error']['code'] == 'VALIDATION_ERROR'

    def test_create_session_empty_topic(self, client):
        """
        topic 为空字符串，验证返回 400。
        """
        resp = client.post('/api/sessions', json={
            'topic': '',
            'expert_count': 4,
        })
        assert resp.status_code == 400

    def test_create_session_topic_too_short(self, client):
        """
        topic 长度小于 2，验证返回 400。
        """
        resp = client.post('/api/sessions', json={
            'topic': 'A',
            'expert_count': 4,
        })
        assert resp.status_code == 400
        data = resp.get_json()
        assert data['error']['code'] == 'VALIDATION_ERROR'

    def test_create_session_topic_max_length(self, client, app):
        """
        topic 长度为 500（最大值边界），验证创建成功。
        """
        long_topic = '测' * 500
        resp = client.post('/api/sessions', json={
            'topic': long_topic,
            'expert_count': 2,
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data['topic'] == long_topic

    # ─── 参数校验：expert_count ────────────────────────────

    def test_create_session_expert_count_out_of_range(self, client):
        """
        expert_count=0（低于下限 1），验证：
        - 返回 400
        - 错误码为 VALIDATION_ERROR
        """
        resp = client.post('/api/sessions', json={
            'topic': '有效话题',
            'expert_count': 0,
        })
        assert resp.status_code == 400
        data = resp.get_json()
        assert data['error']['code'] == 'VALIDATION_ERROR'

    def test_create_session_expert_count_above_max(self, client):
        """
        expert_count=11（超过上限 10），验证返回 400。
        """
        resp = client.post('/api/sessions', json={
            'topic': '有效话题',
            'expert_count': 11,
        })
        assert resp.status_code == 400

    def test_create_session_expert_count_minimum(self, client, app):
        """
        expert_count=1（下限边界），验证创建成功且返回 1 位专家。
        """
        resp = client.post('/api/sessions', json={
            'topic': '边界测试',
            'expert_count': 1,
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data['expert_count'] == 1

        # 验证数据库记录
        with app.app_context():
            from app.models import Session
            session = Session.get(data['id'])
            assert session is not None
            assert session.expert_count == 1

    def test_create_session_expert_count_maximum(self, client, app):
        """
        expert_count=10（上限边界），验证创建成功且返回 10 位专家。
        """
        resp = client.post('/api/sessions', json={
            'topic': '边界测试',
            'expert_count': 10,
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data['expert_count'] == 10

        with app.app_context():
            from app.models import Session
            session = Session.get(data['id'])
            assert session is not None
            assert session.expert_count == 10

    # ─── 默认值 ────────────────────────────────────────────

    def test_create_session_default_expert_count(self, client):
        """
        不传 expert_count 字段，验证：
        - 返回 201
        - expert_count 默认值为 4
        """
        resp = client.post('/api/sessions', json={'topic': '有效话题'})
        assert resp.status_code == 201
        data = resp.get_json()
        assert data['expert_count'] == 4

    def test_create_session_default_expert_count_none(self, client):
        """
        expert_count 传 null，验证默认值为 4。
        """
        resp = client.post('/api/sessions', json={
            'topic': '有效话题',
            'expert_count': None,
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data['expert_count'] == 4

    # ─── 生成专家 ──────────────────────────────────────────

    def test_create_session_generates_experts(self, client, app):
        """
        创建成功后，验证：
        - 生成了正确数量的专家（expert_count 个）
        - 每个专家都有 name、title、stance、color、avatar_emoji
        - 每个专家关联到正确的 session_id
        - sort_order 从 1 开始且连续不重复
        """
        resp = client.post('/api/sessions', json={
            'topic': 'AI 伦理与未来',
            'expert_count': 3,
        })
        assert resp.status_code == 201
        data = resp.get_json()

        # 验证返回的专家列表
        assert 'experts' in data
        assert len(data['experts']) == 3, f'应返回 3 位专家，实际返回 {len(data["experts"])}'

        # 验证每个专家的字段完整性
        for expert in data['experts']:
            # 必填字段存在
            assert 'id' in expert, f'专家 {expert.get("name")} 缺少 id'
            assert expert['id'], '专家 id 不能为空'

            assert 'session_id' in expert
            assert expert['session_id'] == data['id'], \
                f'专家 session_id 应与会话 id 一致'

            assert expert['name'], f'专家缺少 name'
            assert expert['title'], f'专家 {expert["name"]} 缺少 title'
            assert expert['stance'], f'专家 {expert["name"]} 缺少 stance'
            assert expert['color'], f'专家 {expert["name"]} 缺少 color'
            assert expert['avatar_emoji'], f'专家 {expert["name"]} 缺少 avatar_emoji'
            assert 'sort_order' in expert, f'专家 {expert["name"]} 缺少 sort_order'

            # color 应为有效的 hex 颜色值
            assert expert['color'].startswith('#'), \
                f'专家 {expert["name"]} 的 color 应使用 hex 格式'

        # sort_order 从 1 开始，连续递增，不重复
        orders = [e['sort_order'] for e in data['experts']]
        assert orders == sorted(orders), 'sort_order 应已排序'
        assert orders == list(range(1, 4)), f'sort_order 应为 [1, 2, 3]，实际为 {orders}'

        # 验证数据库记录
        with app.app_context():
            from app.models import Expert, Session

            session = Session.get(data['id'])
            assert session is not None

            db_experts = Expert.list_by_session(data['id'])
            assert len(db_experts) == 3, \
                f'数据库应包含 3 条专家记录，实际 {len(db_experts)}'

            # 数据库中的专家字段完整
            for expert in db_experts:
                assert expert['name']
                assert expert['title']
                assert expert['stance']
                assert expert['color'].startswith('#')
                assert expert['avatar_emoji']

            # sort_order 连续
            db_orders = [e['sort_order'] for e in db_experts]
            assert db_orders == list(range(1, 4))

    # ─── 幂等性与隔离性 ────────────────────────────────────

    def test_create_session_multiple_sessions(self, client, app):
        """
        连续创建两个会话，验证：
        - 各自返回独立的数据
        - 数据库中有两条记录
        - 互不干扰
        """
        resp1 = client.post('/api/sessions', json={
            'topic': '第一个话题',
            'expert_count': 2,
        })
        resp2 = client.post('/api/sessions', json={
            'topic': '第二个话题',
            'expert_count': 3,
        })
        assert resp1.status_code == 201
        assert resp2.status_code == 201
        data1 = resp1.get_json()
        data2 = resp2.get_json()

        # id 不同
        assert data1['id'] != data2['id'], '两次创建的会话 id 应不同'

        # topic 正确
        assert data1['topic'] == '第一个话题'
        assert data2['topic'] == '第二个话题'

        # expert_count 正确
        assert data1['expert_count'] == 2
        assert data2['expert_count'] == 3

        # 数据库记录验证
        with app.app_context():
            from app.models import Session
            sessions, total = Session.list(page=1, size=50)
            assert total == 2, '数据库应有 2 条会话记录'
