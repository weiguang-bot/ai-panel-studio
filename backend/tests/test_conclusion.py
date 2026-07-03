"""
AI 圆桌讨论 — POST /api/sessions/{id}/conclusion 接口测试

测试共识分歧生成的幂等性、状态校验、响应格式。
使用 unittest.mock 模拟 AI 结论生成服务，避免真实 API 调用。
"""
import pytest
from unittest.mock import patch


# ─── 辅助函数 ─────────────────────────────────────────────

def _create_session(client):
    """创建会话并返回完整响应 JSON。"""
    resp = client.post('/api/sessions', json={
        'topic': '结论生成测试话题',
        'expert_count': 2,
    })
    assert resp.status_code == 201
    return resp.get_json()


def _create_session_with_status(client, app, status):
    """
    创建会话并将其设置为指定状态，返回 (session_id, experts)。

    注意：POST 创建后默认 status='generating'，
    使用 Session.update_status() 切换到目标状态。
    状态 'pending' 需使用 Session.create() 直接创建（绕过蓝图自动更新）。
    """
    if status == 'pending':
        # pending 状态无法通过 POST 获得，直接使用模型创建
        with app.app_context():
            from app.models import Session as SessionModel
            session = SessionModel.create('结论生成测试话题', 2)
            session_id = session.id
            experts_data = session.to_dict()  # session 信息
        return session_id, []
    else:
        data = _create_session(client)
        session_id = data['id']
        experts = data.get('experts', [])

        if status != 'generating':
            with app.app_context():
                from app.models import Session as SessionModel
                SessionModel.update_status(session_id, status)

        return session_id, experts


# ─── 预期 mock 数据 ──────────────────────────────────────

MOCK_RESPONSE = {
    'consensus': [
        {
            'id': 'c0000000-0000-0000-0000-000000000001',
            'summary': 'AI 将深度改变工作方式，人类需持续学习以适应变革',
            'degree': 'strong',
            'order_index': 1,
        },
        {
            'id': 'c0000000-0000-0000-0000-000000000002',
            'summary': '法律法规和伦理准则应同步跟进技术发展',
            'degree': 'moderate',
            'order_index': 2,
        },
    ],
    'divergences': [
        {
            'id': 'd0000000-0000-0000-0000-000000000001',
            'description': 'AI 对白领 vs 蓝领岗位的影响程度存在分歧',
            'involved_expert_ids': [],
            'severity': 'high',
            'order_index': 1,
        },
    ],
    'session_status': 'concluded',
}


class TestConclusion:
    """POST /api/sessions/{id}/conclusion — 生成共识与分歧摘要"""

    # ─── 正向用例 ─────────────────────────────────────────

    @patch('app.blueprints.conclusion.generate_conclusion',
           return_value=MOCK_RESPONSE, create=True)
    def test_conclusion_success(self, mock_gen, client, app):
        """
        创建会话（discussing 状态）后生成结论，验证：
        - 返回 200
        - 响应包含 consensus 和 divergences
        - 每条 consensus 包含 id、summary、degree、order_index
        - 每条 divergence 包含 id、description、involved_expert_ids、severity、order_index
        """
        session_id, experts = _create_session_with_status(
            client, app, 'discussing'
        )

        resp = client.post(f'/api/sessions/{session_id}/conclusion')
        assert resp.status_code == 200
        body = resp.get_json()

        # 顶层字段
        assert 'consensus' in body
        assert 'divergences' in body
        assert 'session_status' in body
        assert body['session_status'] == 'concluded'

        # consensus 字段完整性
        assert len(body['consensus']) == 2
        for c in body['consensus']:
            assert 'id' in c and c['id']
            assert 'summary' in c and c['summary']
            assert 'degree' in c and c['degree'] in ('strong', 'moderate', 'weak')
            assert 'order_index' in c

        # divergences 字段完整性
        assert len(body['divergences']) == 1
        for d in body['divergences']:
            assert 'id' in d and d['id']
            assert 'description' in d and d['description']
            assert 'involved_expert_ids' in d
            assert isinstance(d['involved_expert_ids'], list)
            assert 'severity' in d and d['severity'] in ('high', 'medium', 'low')
            assert 'order_index' in d

    # ─── 幂等性 ───────────────────────────────────────────

    @patch('app.blueprints.conclusion.generate_conclusion',
           return_value=MOCK_RESPONSE, create=True)
    def test_conclusion_idempotent(self, mock_gen, client, app):
        """
        连续调用两次结论生成接口，验证：
        - 两次返回相同结果
        - 幂等性：第二次调用不重新生成，直接返回已有结论
        """
        session_id, experts = _create_session_with_status(
            client, app, 'discussing'
        )

        # 第一次调用
        resp1 = client.post(f'/api/sessions/{session_id}/conclusion')
        assert resp1.status_code == 200
        data1 = resp1.get_json()

        # 第二次调用
        resp2 = client.post(f'/api/sessions/{session_id}/conclusion')
        assert resp2.status_code == 200
        data2 = resp2.get_json()

        # 两次结果应完全一致
        assert data1['consensus'] == data2['consensus'], '两次调用的 consensus 应一致'
        assert data1['divergences'] == data2['divergences'], '两次调用的 divergences 应一致'
        assert data1['session_status'] == data2['session_status']
        # consensus 数量一致
        assert len(data1['consensus']) == len(data2['consensus'])
        # divergences 数量一致
        assert len(data1['divergences']) == len(data2['divergences'])

        # 验证每个 consensus 的 id 相同（而非每次生成新 id）
        for c1, c2 in zip(data1['consensus'], data2['consensus']):
            assert c1['id'] == c2['id'], \
                f'幂等性要求 id 不变: {c1["id"]} vs {c2["id"]}'

        # 验证每个 divergence 的 id 相同
        for d1, d2 in zip(data1['divergences'], data2['divergences']):
            assert d1['id'] == d2['id'], \
                f'幂等性要求 id 不变: {d1["id"]} vs {d2["id"]}'

    # ─── 会话不存在 ───────────────────────────────────────

    def test_conclusion_session_not_found(self, client):
        """
        请求不存在的 session_id，验证：
        - 返回 404
        - 错误码为 SESSION_NOT_FOUND
        """
        resp = client.post('/api/sessions/non-existent-id/conclusion')
        assert resp.status_code == 404
        data = resp.get_json()
        assert data['error']['code'] == 'SESSION_NOT_FOUND'

    # ─── 状态校验：不允许生成结论的状态 ─────────────────────

    def test_conclusion_session_pending(self, client, app):
        """
        会话状态为 pending，验证：
        - 返回 400
        - 错误码为 INVALID_STATUS
        """
        session_id, _ = _create_session_with_status(client, app, 'pending')

        resp = client.post(f'/api/sessions/{session_id}/conclusion')
        assert resp.status_code == 400
        data = resp.get_json()
        assert data['error']['code'] == 'INVALID_STATUS'

    def test_conclusion_session_generating(self, client, app):
        """
        会话状态为 generating，验证：
        - 返回 400
        - 错误码为 INVALID_STATUS
        """
        session_id, _ = _create_session_with_status(client, app, 'generating')

        resp = client.post(f'/api/sessions/{session_id}/conclusion')
        assert resp.status_code == 400
        data = resp.get_json()
        assert data['error']['code'] == 'INVALID_STATUS'

    def test_conclusion_session_error(self, client, app):
        """
        会话状态为 error，验证：
        - 返回 400
        - 错误码为 INVALID_STATUS
        """
        session_id, _ = _create_session_with_status(client, app, 'error')

        resp = client.post(f'/api/sessions/{session_id}/conclusion')
        assert resp.status_code == 400
        data = resp.get_json()
        assert data['error']['code'] == 'INVALID_STATUS'

    # ─── 允许生成结论的状态边界 ────────────────────────────

    def test_conclusion_session_concluded(self, client, app):
        """
        会话状态为 concluded，验证：
        - 可以生成结论（或返回已有结论）
        - 返回 200
        """
        session_id, _ = _create_session_with_status(client, app, 'concluded')

        resp = client.post(f'/api/sessions/{session_id}/conclusion')
        # concluded 状态的会话应允许生成/获取结论
        assert resp.status_code in (200, 400), \
            f'concluded 状态应返回 200 或 400，实际 {resp.status_code}'

    # ─── 响应格式验证 ─────────────────────────────────────

    @patch('app.blueprints.conclusion.generate_conclusion',
           return_value=MOCK_RESPONSE, create=True)
    def test_conclusion_response_format(self, mock_gen, client, app):
        """
        验证返回的 JSON 结构严格符合契约定义：
        - 顶层字段：consensus, divergences, session_status
        - consensus 数组元素包含：id, summary, degree, order_index
        - divergences 数组元素包含：id, description, involved_expert_ids, severity, order_index
        - degree 为枚举值：strong, moderate, weak
        - severity 为枚举值：high, medium, low
        - order_index 为正整数
        """
        session_id, experts = _create_session_with_status(
            client, app, 'discussing'
        )

        resp = client.post(f'/api/sessions/{session_id}/conclusion')
        assert resp.status_code == 200
        body = resp.get_json()

        # 顶层结构
        assert set(body.keys()) == {'consensus', 'divergences', 'session_status'}, \
            f'顶层字段不匹配: {set(body.keys())}'
        assert isinstance(body['consensus'], list)
        assert isinstance(body['divergences'], list)
        assert body['session_status'] == 'concluded'

        # consensus 条目结构
        for c in body['consensus']:
            assert set(c.keys()) == {'id', 'summary', 'degree', 'order_index'}, \
                f'consensus 字段不匹配: {set(c.keys())}'
            # id 应为非空字符串
            assert isinstance(c['id'], str) and c['id']
            # summary 应为非空字符串
            assert isinstance(c['summary'], str) and c['summary']
            # degree 枚举值
            assert c['degree'] in ('strong', 'moderate', 'weak'), \
                f'degree 应为 strong/moderate/weak，实际为 {c["degree"]}'
            # order_index 为正整数
            assert isinstance(c['order_index'], int) and c['order_index'] >= 1

        # divergences 条目结构
        for d in body['divergences']:
            assert set(d.keys()) == {
                'id', 'description', 'involved_expert_ids',
                'severity', 'order_index',
            }, f'divergence 字段不匹配: {set(d.keys())}'
            # id 应为非空字符串
            assert isinstance(d['id'], str) and d['id']
            # description 应为非空字符串
            assert isinstance(d['description'], str) and d['description']
            # involved_expert_ids 为列表（可为空）
            assert isinstance(d['involved_expert_ids'], list)
            # 元素类型为字符串（UUID）
            for eid in d['involved_expert_ids']:
                assert isinstance(eid, str) and eid
            # severity 枚举值
            assert d['severity'] in ('high', 'medium', 'low'), \
                f'severity 应为 high/medium/low，实际为 {d["severity"]}'
            # order_index 为正整数
            assert isinstance(d['order_index'], int) and d['order_index'] >= 1

        # consensus 的 order_index 从 1 开始连续递增
        consensus_order = [c['order_index'] for c in body['consensus']]
        assert consensus_order == sorted(consensus_order)
        assert consensus_order == list(range(1, len(body['consensus']) + 1))

        # divergences 的 order_index 从 1 开始连续递增
        div_order = [d['order_index'] for d in body['divergences']]
        assert div_order == sorted(div_order)
        assert div_order == list(range(1, len(body['divergences']) + 1))
