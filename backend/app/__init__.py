"""
AI 圆桌讨论 — Flask 应用工厂

使用 create_app() 创建应用实例，支持不同环境配置。
"""
import os
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

# 加载 .env 文件（项目根目录或 backend/ 下均可）
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))
load_dotenv()  # 也尝试当前目录


def create_app(testing=False):
    """创建并配置 Flask 应用实例。"""
    app = Flask(__name__)

    # ── 配置 ──────────────────────────────────────────
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-prod'),
        # SQLite 数据库路径
        DATABASE=os.environ.get(
            'DATABASE_URL',
            os.path.join(app.instance_path, 'roundtable.db'),
        ),
        TESTING=testing,
    )

    # ── 跨域 ──────────────────────────────────────────
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # ── 确保 instance 目录存在 ─────────────────────────
    os.makedirs(app.instance_path, exist_ok=True)

    # ── 注册蓝图 ──────────────────────────────────────
    from app.blueprints.sessions import sessions_bp
    from app.blueprints.transcripts import transcripts_bp
    from app.blueprints.conclusion import conclusion_bp

    app.register_blueprint(sessions_bp, url_prefix='/api')
    app.register_blueprint(transcripts_bp, url_prefix='/api')
    app.register_blueprint(conclusion_bp, url_prefix='/api')

    # ── 初始化数据库（首次运行建表）─────────────────────
    with app.app_context():
        from app.utils.db import init_db
        init_db()

    # ── 根路由（健康检查）──────────────────────────────
    @app.route('/api/health')
    def health_check():
        return {'status': 'ok', 'message': 'AI 圆桌讨论 API 运行中'}

    return app
