"""
AI 圆桌讨论 — 发言记录蓝图

端点：
  GET /api/sessions/{id}/transcript — 获取完整发言记录（游标分页）
"""
from flask import Blueprint, jsonify, request
from app.models import Session, Expert, Transcript

transcripts_bp = Blueprint('transcripts', __name__)


@transcripts_bp.route('/sessions/<session_id>/transcript', methods=['GET'])
def get_transcript(session_id):
    """获取指定会话的完整发言记录（游标分页）。

    参数（查询字符串）：
        cursor: 游标值（sequence），返回该值之后的记录
        after:  增量拉取起点（与 cursor 语义相同）
        limit:  每页条数（默认 50，最大 200）

    返回：
        {session, experts, transcripts, next_cursor, has_more}
    """
    # ── 校验会话是否存在 ────────────────────────────────
    session = Session.get(session_id)
    if session is None:
        return jsonify({
            'error': {'code': 'SESSION_NOT_FOUND', 'message': '讨论会话不存在'}
        }), 404

    # ── 获取查询参数 ─────────────────────────────────────
    cursor = request.args.get('cursor', None, type=int)
    after = request.args.get('after', None, type=int)
    limit = request.args.get('limit', 50, type=int)

    if limit < 1:
        limit = 50
    if limit > 200:
        limit = 200

    # ── 查询数据 ─────────────────────────────────────────
    experts = Expert.list_by_session(session_id)
    transcripts, next_cursor = Transcript.list_by_session(
        session_id, cursor=cursor, limit=limit, after=after,
    )
    transcript_dicts = [t.to_dict() for t in transcripts]

    # ── 构造响应 ─────────────────────────────────────────
    return jsonify({
        'session': session.to_dict(),
        'experts': experts,
        'transcripts': transcript_dicts,
        'next_cursor': next_cursor,
        'has_more': next_cursor is not None,
    }), 200
