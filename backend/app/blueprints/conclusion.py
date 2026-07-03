"""
AI 圆桌讨论 — 结论管理蓝图

端点：
  POST /api/sessions/{id}/conclusion — 生成共识与分歧摘要
"""
from flask import Blueprint, jsonify
from app.models import Session
from app.services.conclusion_generator import generate_conclusion

conclusion_bp = Blueprint('conclusion', __name__)


@conclusion_bp.route('/sessions/<session_id>/conclusion', methods=['POST'])
def handle_generate_conclusion(session_id):
    """生成指定会话的共识与分歧摘要（幂等）。

    状态校验：
      - discussing / concluded  → 允许生成结论
      - pending / generating / error → 返回 400 INVALID_STATUS
    """
    # ── 校验会话是否存在 ────────────────────────────────
    session = Session.get(session_id)
    if session is None:
        return jsonify({
            'error': {'code': 'SESSION_NOT_FOUND', 'message': '讨论会话不存在'}
        }), 404

    # ── 校验会话状态 ────────────────────────────────────
    if session.status not in ('discussing', 'concluded'):
        return jsonify({
            'error': {
                'code': 'INVALID_STATUS',
                'message': f'当前状态 {session.status} 不允许生成结论',
            }
        }), 400

    # ── 生成结论 ─────────────────────────────────────────
    result = generate_conclusion(session_id)

    return jsonify(result), 200
