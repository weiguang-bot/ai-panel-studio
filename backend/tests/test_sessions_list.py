"""
AI 圆桌讨论 — GET /api/sessions 接口测试

测试列表查询的分页、筛选、参数校验功能。
会话通过 POST 接口创建，状态通过模型直接更新。
"""
import pytest


def _create_session(client, topic='测试话题'):
    """辅助函数：通过 POST 创建一个会话，返回其响应 JSON。"""
    resp = client.post('/api/sessions', json={
        'topic': topic,
        'expert_count': 2,
    })
    assert resp.status_code == 201
    return resp.get_json()


def _create_sessions(client, count, topic_prefix='话题'):
    """辅助函数：批量创建 count 个会话，返回 id 列表。"""
    ids = []
    for i in range(count):
        data = _create_session(client, f'{topic_prefix}-{i:03d}')
        ids.append(data['id'])
    return ids


class TestListSessions:
    """GET /api/sessions — 获取会话列表"""

    # ─── 空列表 ──────────────────────────────────────────

    def test_list_sessions_empty(self, client):
        """
        数据库中无会话时，验证：
        - 返回 200
        - data 为空列表
        - total 为 0
        - page 和 size 为默认值
        """
        resp = client.get('/api/sessions')
        assert resp.status_code == 200
        data = resp.get_json()

        assert data['data'] == [], '无会话时应返回空列表'
        assert data['total'] == 0
        assert data['page'] == 1
        assert data['size'] == 20

    # ─── 分页 ────────────────────────────────────────────

    def test_list_sessions_pagination(self, client, app):
        """
        创建 25 个会话后，请求 page=2, size=10，验证：
        - 返回 200
        - data 长度为 10
        - total 为 25
        - page=2, size=10
        - 按 created_at 倒序排列（最新的在前）
        - 第 2 页的数据应是第 11~20 条（倒序）
        """
        ids = _create_sessions(client, 25)

        resp = client.get('/api/sessions?page=2&size=10')
        assert resp.status_code == 200
        body = resp.get_json()

        assert len(body['data']) == 10, f'第 2 页应有 10 条，实际 {len(body["data"])}'
        assert body['total'] == 25
        assert body['page'] == 2
        assert body['size'] == 10

        # 按 created_at 倒序：ids[-1] 是最新创建的
        # page=1: ids[24]~ids[15] (10 条)
        # page=2: ids[14]~ids[5]  (10 条)
        # page=3: ids[4]~ids[0]   (5 条)
        returned_ids = [item['id'] for item in body['data']]
        expected_ids = ids[-11:-21:-1]  # ids[-11] 到 ids[-20]（倒序步进 -1）
        # ids[-11:-21:-1] 在 Python 中取索引 -11, -12, ..., -20
        assert returned_ids == expected_ids, \
            f'分页返回的 id 顺序不匹配\n预期: {expected_ids}\n实际: {returned_ids}'

        # 每个条目是 SessionBrief 格式
        for item in body['data']:
            assert 'id' in item
            assert 'topic' in item
            assert 'expert_count' in item
            assert 'status' in item
            assert 'created_at' in item
            assert item.get('experts') is None, \
                '列表应返回 SessionBrief，不包含 experts'

    def test_list_sessions_last_page_partial(self, client, app):
        """
        创建 25 个会话，请求 page=3, size=10，验证：
        - 最后一页返回 5 条数据
        - has_more 为 False（或等价语义）
        """
        _create_sessions(client, 25)

        resp = client.get('/api/sessions?page=3&size=10')
        assert resp.status_code == 200
        body = resp.get_json()

        assert len(body['data']) == 5, f'最后一页应有 5 条，实际 {len(body["data"])}'
        assert body['total'] == 25
        assert body['page'] == 3
        assert body['size'] == 10

    def test_list_sessions_page_exceeds_total(self, client, app):
        """
        创建 5 个会话，请求 page=10（超出总页数），验证：
        - data 为空列表
        - total 仍为 5
        """
        _create_sessions(client, 5)

        resp = client.get('/api/sessions?page=10&size=10')
        assert resp.status_code == 200
        body = resp.get_json()

        assert body['data'] == [], '超出总页数时应返回空列表'
        assert body['total'] == 5

    # ─── 状态筛选 ─────────────────────────────────────────

    def test_list_sessions_status_filter(self, client, app):
        """
        创建不同状态的会话后，筛选 status=discussing，验证：
        - 只返回匹配的会话
        - 不返回其他状态的会话
        """
        # 创建 5 个会话（默认 status = generating）
        ids = _create_sessions(client, 5)

        # 将前 2 个改为 discussing，后 2 个改为 concluded，保留 1 个为 generating
        with app.app_context():
            from app.models import Session

            Session.update_status(ids[0], 'discussing')
            Session.update_status(ids[1], 'discussing')
            Session.update_status(ids[2], 'concluded')
            Session.update_status(ids[3], 'concluded')
            # ids[4] 保持 generating

        # 筛选 discussing
        resp = client.get('/api/sessions?status=discussing')
        assert resp.status_code == 200
        body = resp.get_json()

        assert body['total'] == 2, f'应有 2 条 discussing 记录，实际 {body["total"]}'
        assert len(body['data']) == 2
        for item in body['data']:
            assert item['status'] == 'discussing', \
                f'筛选结果为非 discussing 状态: {item["status"]}'

        # 筛选 concluded
        resp = client.get('/api/sessions?status=concluded')
        assert resp.status_code == 200
        body = resp.get_json()
        assert body['total'] == 2

        # 筛选 generating（默认）
        resp = client.get('/api/sessions?status=generating')
        assert resp.status_code == 200
        body = resp.get_json()
        assert body['total'] == 1

    def test_list_sessions_status_filter_no_match(self, client, app):
        """
        筛选一个数据库中不存在的状态，验证：
        - data 为空列表
        - total 为 0
        """
        _create_sessions(client, 3)

        resp = client.get('/api/sessions?status=error')
        assert resp.status_code == 200
        body = resp.get_json()

        assert body['data'] == []
        assert body['total'] == 0

    def test_list_sessions_status_filter_invalid(self, client, app):
        """
        筛选一个无效的状态值，验证：
        - 返回 400
        - 错误码为 VALIDATION_ERROR
        """
        _create_sessions(client, 2)

        resp = client.get('/api/sessions?status=invalid_status')
        assert resp.status_code == 400
        data = resp.get_json()
        assert data['error']['code'] == 'INVALID_STATUS'

    # ─── 默认分页 ────────────────────────────────────────

    def test_list_sessions_default_pagination(self, client, app):
        """
        不传 page 和 size 参数时，验证：
        - 默认 page=1，size=20
        - 数据正确分页
        """
        _create_sessions(client, 5)

        resp = client.get('/api/sessions')
        assert resp.status_code == 200
        body = resp.get_json()

        assert body['page'] == 1, 'page 默认值应为 1'
        assert body['size'] == 20, 'size 默认值应为 20'
        assert len(body['data']) == 5, '应返回全部 5 条数据'
        assert body['total'] == 5

    def test_list_sessions_default_size_when_omitted(self, client, app):
        """
        只传 page 不传 size 时，size 默认为 20。
        """
        _create_sessions(client, 30)

        resp = client.get('/api/sessions?page=1')
        assert resp.status_code == 200
        body = resp.get_json()

        assert body['size'] == 20
        assert len(body['data']) == 20, '默认 size=20，应返回 20 条'

    # ─── 参数校验：page ───────────────────────────────────

    def test_list_sessions_invalid_page(self, client):
        """
        page=0（低于下限 1），验证：
        - 返回 400
        - 错误码为 VALIDATION_ERROR
        """
        resp = client.get('/api/sessions?page=0')
        assert resp.status_code == 400, 'page=0 应返回 400'
        data = resp.get_json()
        assert data['error']['code'] == 'INVALID_PAGE'

    def test_list_sessions_negative_page(self, client):
        """
        page=-1（负数），验证返回 400。
        """
        resp = client.get('/api/sessions?page=-1')
        assert resp.status_code == 400
        data = resp.get_json()
        assert data['error']['code'] == 'INVALID_PAGE'

    # ─── 参数校验：size ───────────────────────────────────

    def test_list_sessions_size_below_minimum(self, client):
        """
        size=0（低于下限 1），验证返回 400。
        """
        resp = client.get('/api/sessions?size=0')
        assert resp.status_code == 400

    def test_list_sessions_size_above_maximum(self, client):
        """
        size=51（超过上限 50），验证返回 400。
        """
        resp = client.get('/api/sessions?size=51')
        assert resp.status_code == 400

    def test_list_sessions_size_maximum(self, client, app):
        """
        size=50（上限边界），验证创建 60 条时仅返回 50 条。
        """
        _create_sessions(client, 60)

        resp = client.get('/api/sessions?size=50')
        assert resp.status_code == 200
        body = resp.get_json()

        assert body['size'] == 50
        assert len(body['data']) == 50, 'size=50 时最多返回 50 条'
        assert body['total'] == 60

    # ─── 组合场景 ─────────────────────────────────────────

    def test_list_sessions_pagination_with_status(self, client, app):
        """
        分页与状态筛选组合使用时，验证：
        - total 反映匹配条件的总数
        - data 长度符合分页大小
        """
        ids = _create_sessions(client, 20)

        with app.app_context():
            from app.models import Session
            for i in range(10):
                Session.update_status(ids[i], 'discussing')
            # ids[10:] 保持 generating

        # 筛选 discussing，page=1, size=5
        resp = client.get('/api/sessions?status=discussing&page=1&size=5')
        assert resp.status_code == 200
        body = resp.get_json()

        assert body['total'] == 10, 'discussing 共 10 条'
        assert len(body['data']) == 5, '第 1 页应返回 5 条'
        assert body['page'] == 1
        assert body['size'] == 5

        for item in body['data']:
            assert item['status'] == 'discussing'

        # 第 2 页
        resp = client.get('/api/sessions?status=discussing&page=2&size=5')
        assert resp.status_code == 200
        body = resp.get_json()
        assert len(body['data']) == 5
        assert body['total'] == 10
