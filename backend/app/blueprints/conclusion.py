"""
AI 圆桌讨论 — 结论管理蓝图

端点：
  POST /api/sessions/{id}/conclusion — 生成共识与分歧摘要
"""
from flask import Blueprint, jsonify

conclusion_bp = Blueprint('conclusion', __name__)


@conclusion_bp.route('/sessions/<session_id>/conclusion', methods=['POST'])
def generate_conclusion(session_id):
    """生成指定会话的共识与分歧摘要（幂等）。"""
    # TODO: 检查会话状态，生成结论
    return jsonify({
        'error': {'code': 'SESSION_NOT_FOUND', 'message': '讨论会话不存在'}
    }), 404
