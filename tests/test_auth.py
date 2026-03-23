"""
认证模块测试
"""
import pytest
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from auth import hash_password, verify_password, login_user, load_auth_config


class TestAuth:
    """认证模块测试类"""

    def test_hash_password(self):
        """测试密码哈希"""
        password = "test123"
        salt = "testsalt"
        hashed = hash_password(password, salt)
        assert hashed is not None
        assert len(hashed) == 64  # SHA256 产生64字符的十六进制字符串

    def test_verify_password_correct(self):
        """测试正确密码验证"""
        password = "test123"
        salt = "testsalt"
        hashed = hash_password(password, salt)
        assert verify_password(password, hashed, salt) is True

    def test_verify_password_incorrect(self):
        """测试错误密码验证"""
        password = "test123"
        wrong_password = "wrong456"
        salt = "testsalt"
        hashed = hash_password(password, salt)
        assert verify_password(wrong_password, hashed, salt) is False

    def test_login_user_success(self):
        """测试成功登录"""
        # 使用配置中的默认账号测试
        result = login_user("admin", "admin123")
        assert result["success"] is True
        assert result["username"] == "admin"
        assert result["role"] == "admin"

    def test_login_user_wrong_password(self):
        """测试错误密码登录"""
        result = login_user("admin", "wrongpassword")
        assert result["success"] is False
        assert "error" in result

    def test_login_user_nonexistent(self):
        """测试不存在用户登录"""
        result = login_user("nonexistent", "password")
        assert result["success"] is False

    def test_load_auth_config(self):
        """测试加载认证配置"""
        config = load_auth_config()
        assert config is not None
        assert "users" in config
        assert "admin" in config["users"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
