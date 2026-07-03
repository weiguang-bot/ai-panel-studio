"""
AI 圆桌讨论 — 发言记录蓝图

端点：
  GET /api/sessions/{id}/transcript — 获取完整发言记录（游标分页）
"""
from flask import Blueprint, jsonify, request

transcripts_bp = Blueprint('transcripts', __name__)


@transcripts_bp.route('/sessions/<session_id>/transcript', methods=['GET'])
def get_transcript(session_id):
    """获取指定会话的完整发言记录（游标分页）。"""
    cursor = request.args.get('cursor', None, type=int)
    limit = request.args.get('limit', 100, type=int)

    if limit < 1 or limit > 500:
        limit = 100

    # TODO: 从数据库查询发言记录
    return jsonify({
        'session': None,
        'experts': [],
        'transcripts': [],
        'next_cursor': None,
        'has_more': False,
    }), 200
