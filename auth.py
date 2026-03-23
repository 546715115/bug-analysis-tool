"""
认证模块 - 提供简单的登录认证功能
"""
import streamlit as st
import yaml
from pathlib import Path
import hashlib
import secrets


def get_config_path():
    """获取配置文件路径"""
    return Path(__file__).parent / "config" / "auth_config.yaml"


def load_auth_config():
    """加载认证配置"""
    config_path = get_config_path()
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    return {}


def hash_password(password: str, salt: str = "") -> str:
    """密码哈希"""
    return hashlib.sha256((password + salt).encode()).hexdigest()


def verify_password(password: str, hashed: str, salt: str = "") -> bool:
    """验证密码"""
    return hash_password(password, salt) == hashed


def init_auth_config():
    """初始化认证配置文件（首次运行时创建默认配置）"""
    config_path = get_config_path()
    if not config_path.exists():
        config_dir = config_path.parent
        config_dir.mkdir(parents=True, exist_ok=True)

        # 生成随机salt
        salt = secrets.token_hex(16)
        # 默认管理员账号: admin / admin123
        default_password_hash = hash_password("admin123", salt)

        default_config = {
            "salt": salt,
            "users": {
                "admin": {
                    "password": default_password_hash,
                    "role": "admin",
                    "name": "管理员"
                }
            },
            "session_timeout_minutes": 120
        }

        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(default_config, f, allow_unicode=True)

        return default_config
    return load_auth_config()


def login_user(username: str, password: str) -> dict:
    """验证用户登录"""
    config = load_auth_config()
    salt = config.get("salt", "")

    if username in config.get("users", {}):
        user_data = config["users"][username]
        if verify_password(password, user_data["password"], salt):
            return {
                "success": True,
                "username": username,
                "role": user_data.get("role", "user"),
                "name": user_data.get("name", username)
            }

    return {"success": False, "error": "用户名或密码错误"}


def is_authenticated() -> bool:
    """检查用户是否已登录"""
    return st.session_state.get("authenticated", False)


def logout():
    """用户登出"""
    st.session_state.authenticated = False
    st.session_state.user = None
    st.rerun()


def require_auth():
    """要求用户登录（装饰器替代方案）"""
    if not is_authenticated():
        show_login_page()
        st.stop()


def show_login_page():
    """显示登录页面"""
    # st.set_page_config(
    #     page_title="问题单分析工具 - 登录",
    #     page_icon="🔐",
    #     layout="centered"
    # )

    # 居中显示登录框
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <style>
        .login-title {
            text-align: center;
            font-size: 28px;
            font-weight: bold;
            margin-bottom: 30px;
        }
        </style>
        """, unsafe_allow_html=True)

        st.markdown('<p class="login-title">🔐 问题单分析工具</p>', unsafe_allow_html=True)

        with st.form("login_form"):
            username = st.text_input("用户名", placeholder="请输入用户名")
            password = st.text_input("密码", type="password", placeholder="请输入密码")
            submit = st.form_submit_button("登录", type="primary", use_container_width=True)

            if submit:
                if username and password:
                    result = login_user(username, password)
                    if result["success"]:
                        st.session_state.authenticated = True
                        st.session_state.user = result
                        st.rerun()
                    else:
                        st.error(result["error"])
                else:
                    st.warning("请输入用户名和密码")

        st.markdown("---")
        st.caption("💡 默认账号: admin / admin123")


def init_session_state():
    """初始化认证相关的session state"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user' not in st.session_state:
        st.session_state.user = None
