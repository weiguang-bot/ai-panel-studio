"""
AI 圆桌讨论 — 会话管理蓝图

端点：
  POST   /api/sessions          — 创建讨论会话
  GET    /api/sessions           — 获取会话列表
  GET    /api/sessions/{id}      — 获取会话详情（含专家列表）
  GET    /api/sessions/{id}/events  — SSE 事件流
"""
from flask import Blueprint, jsonify, request, Response
from app.models import Session, Expert
from app.services.expert_generator import generate_experts
from app.services.transcript_stream import event_generator

sessions_bp = Blueprint('sessions', __name__)


@sessions_bp.route('/sessions', methods=['POST'])
def create_session():
    """创建新的讨论会话。

    流程：
      1. 校验 topic（非空，2-500字符）和 expert_count（整数，1-10）
      2. 创建 Session 记录（status = 'pending'）
      3. 生成专家列表并写入 experts 表
      4. 更新 Session 状态为 'generating'
      5. 返回 SessionDetail（含专家列表）
    """
    data = request.get_json(silent=True) or {}
    topic = data.get('topic', '').strip()
    expert_count = data.get('expert_count', 4)

    # ── 校验 topic ──────────────────────────────────────
    if not topic or len(topic) < 2 or len(topic) > 500:
        return jsonify({
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': 'topic 长度须在 2-500 之间',
            }
        }), 400

    # ── 校验 expert_count ────────────────────────────────
    if expert_count is None:
        expert_count = 4
    elif not isinstance(expert_count, int) or expert_count < 1 or expert_count > 10:
        return jsonify({
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': 'expert_count 须为 1-10 之间的整数',
            }
        }), 400

    # ── 创建会话 ─────────────────────────────────────────
    session = Session.create(topic, expert_count)
    if session is None:
        return jsonify({
            'error': {'code': 'INTERNAL_ERROR', 'message': '创建会话失败'},
        }), 500

    # ── 生成专家 ─────────────────────────────────────────
    experts_data = generate_experts(topic, expert_count)
    experts = Expert.bulk_create(session.id, experts_data)

    # ── 更新状态为 generating ────────────────────────────
    session = Session.update_status(session.id, 'generating')

    # ── 构造响应 ─────────────────────────────────────────
    result = session.to_dict()
    result['experts'] = experts

    return jsonify(result), 201


@sessions_bp.route('/sessions', methods=['GET'])
def list_sessions():
    """获取会话列表（分页、按状态筛选）。"""
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 20, type=int)
    status = request.args.get('status', None)

    # ── 校验 page ────────────────────────────────────────
    if page is None or page < 1:
        return jsonify({
            'error': {'code': 'INVALID_PAGE', 'message': 'page 必须 ≥ 1'}
        }), 400

    # ── 校验 size ────────────────────────────────────────
    if size is None or size < 1 or size > 50:
        return jsonify({
            'error': {'code': 'INVALID_SIZE', 'message': 'size 须在 1-50 之间'}
        }), 400

    # ── 校验 status ──────────────────────────────────────
    if status is not None and status not in Session.ALLOWED_STATUSES:
        return jsonify({
            'error': {
                'code': 'INVALID_STATUS',
                'message': f'status 必须是 {", ".join(Session.ALLOWED_STATUSES)} 之一',
            }
        }), 400

    # ── 查询数据库 ────────────────────────────────────────
    sessions, total = Session.list(page, size, status)
    data = [s.to_dict() for s in sessions]

    return jsonify({
        'data': data,
        'total': total,
        'page': page,
        'size': size,
    }), 200


@sessions_bp.route('/sessions/<session_id>', methods=['GET'])
def get_session(session_id):
    """获取指定会话的详情（含专家列表）。"""
    # TODO: 从数据库查询
    return jsonify({
        'error': {'code': 'SESSION_NOT_FOUND', 'message': '讨论会话不存在'}
    }), 404


@sessions_bp.route('/sessions/<session_id>/events', methods=['GET'])
def sse_events(session_id):
    """SSE 事件流：订阅指定会话的实时事件。

    返回 text/event-stream 流式响应。
    连接建立后立即发送 session.status 事件，之后每 30 秒发送 heartbeat。
    """
    # ── 检查会话是否存在 ────────────────────────────────
    session = Session.get(session_id)
    if session is None:
        return jsonify({
            'error': {'code': 'SESSION_NOT_FOUND', 'message': '讨论会话不存在'}
        }), 404

    # ── 立即更新数据库状态为 discussing ────────────────────
    # 在生成器执行前更新，避免结论 API 调用时的 INVALID_STATUS 错误
    if session.status == 'generating':
        Session.update_status(session_id, 'discussing')
        session = Session.get(session_id)  # 重新获取最新状态

    # ── 获取专家列表 ──────────────────────────────────────
    experts = Expert.list_by_session(session_id)

    # ── 创建 SSE 事件流生成器（含讨论引擎）────────────────
    generator = event_generator(
        session_id=session_id,
        current_status=session.status,
        previous_status='pending',
        topic=session.topic,
        experts=experts,
    )

    return Response(
        generator,
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no',
        },
    )
