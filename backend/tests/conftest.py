"""
pytest 配置 — 提供 Flask 测试客户端和设备。
"""
import os
import tempfile
import pytest
from app import create_app


@pytest.fixture
def app():
    """创建测试用的 Flask 应用（使用临时数据库）。"""
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    app = create_app(testing=True)
    app.config['DATABASE'] = db_path
    app.config['TESTING'] = True

    with app.app_context():
        from app.utils.db import init_db
        init_db()

    yield app

    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """Flask 测试客户端。"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Flask CLI 测试运行器。"""
    return app.test_cli_runner()
