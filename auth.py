"""Streamlit OIDC authentication gate. The app never handles user passwords."""
from utils.i18n import tr


LANGUAGES = ["English", "हिन्दी", "తెలుగు"]


def _login_shell(st):
    current_language = st.session_state.get("auth_language", "English")
    language = st.selectbox(tr("Language", current_language), LANGUAGES, key="auth_language")
    st.markdown("""<style>
    .stApp{background:linear-gradient(135deg,#f3f7ef 0%,#e7f0e5 50%,#f8f7ef 100%)}
    [data-testid="stMainBlockContainer"]{max-width:980px;padding-top:2.5rem}
    .login-brand{background:linear-gradient(120deg,#173d30,#347452);color:#fff;border-radius:24px;padding:30px 34px;margin:4px auto 20px;box-shadow:0 16px 40px #173d3020}
    .login-brand h1{color:#fff;font-size:2rem;margin:8px 0}.login-brand p{color:#e2eee2;margin:0}
    .login-kicker{letter-spacing:.12em;font-size:.75rem;font-weight:700;color:#d0e4d1}
    [data-testid="stForm"]{background:#fff;border:1px solid #e1e9df;border-radius:18px;padding:20px 22px;box-shadow:0 10px 28px #173d3010}
    </style>""", unsafe_allow_html=True)
    st.markdown(f'<div class="login-brand"><div class="login-kicker">🌱 AGRIASTRA</div><h1>{tr("Climate-smart farming, made clearer", language)}</h1><p>{tr("Your local weather, crop context, and trusted guidance in one private workspace.", language)}</p></div>', unsafe_allow_html=True)
    return language


def require_authenticated_user(st):
    """Render the login/configuration state and return a verified OIDC identity."""
    try:
        secrets = st.secrets.to_dict()
    except Exception:
        secrets = {}
    auth_config = secrets.get("auth")
    app_config = secrets.get("agriaastra", {})
    required_auth_keys = ("redirect_uri", "cookie_secret", "client_id", "client_secret", "server_metadata_url")
    missing_auth_keys = [key for key in required_auth_keys if not str((auth_config or {}).get(key, "")).strip()]
    if missing_auth_keys:
        if app_config.get("allow_local_auth") is True:
            return _local_sign_in(st)
        language = _login_shell(st)
        st.title(tr("Sign in to AgriAstra", language))
        st.error(tr("Authentication is not configured. Missing OIDC values:", language) + " " + ", ".join(missing_auth_keys) + ".")
        st.info(tr("For local development without an identity provider, turn on local sign-in. For deployment, configure the [auth] section with credentials from your identity provider.", language))
        st.code("""[auth]
redirect_uri = \"http://localhost:8501/oauth2callback\"
cookie_secret = \"generate-a-long-random-secret\"
client_id = \"your-oidc-client-id\"
client_secret = \"your-oidc-client-secret\"
server_metadata_url = \"https://accounts.google.com/.well-known/openid-configuration\"""", language="toml")
        st.stop()

    try:
        user = st.user
        if not user.is_logged_in:
            language = _login_shell(st)
            st.title(tr("Sign in to AgriAstra", language))
            st.caption(tr("Sign in with your organization or identity provider to access your private farm workspace.", language))
            st.button(tr("Continue with identity provider", language), type="primary", on_click=st.login, use_container_width=True)
            st.stop()
        claims = user.to_dict()
    except Exception as exc:
        language = st.session_state.get("auth_language", "English")
        st.error(f"{tr('Could not read the signed-in identity. Check the OIDC configuration.', language)} ({exc})")
        st.stop()

    # OIDC `sub` is the stable account key. Email is used for display and optional allowlisting only.
    subject = str(claims.get("sub", "")).strip()
    email = str(claims.get("email", "")).strip().lower()
    if not subject or not email or claims.get("email_verified") is not True:
        st.error(tr("Your identity provider must provide a stable account ID and a verified email address.", st.session_state.get("auth_language", "English")))
        st.logout()
        st.stop()

    allowlist = {str(item).strip().lower() for item in app_config.get("allowed_emails", []) if str(item).strip()}
    if allowlist and email not in allowlist:
        st.error(tr("This account is not on the AgriAstra access list. Contact the project administrator.", st.session_state.get("auth_language", "English")))
        st.logout()
        st.stop()

    return {
        "user_id": subject,
        "email": email,
        "display_name": str(claims.get("name") or claims.get("given_name") or email),
        "language": st.session_state.get("auth_language", "English"),
    }


def _local_sign_in(st):
    """Local-only self-service auth; deployed apps should use configured OIDC."""
    from database import authenticate_local_user, create_local_user

    language = _login_shell(st)
    st.title(tr("Sign in to AgriAstra", language))
    st.caption(tr("Local development sign-in. Configure OIDC before deploying this app publicly.", language))
    actions = ("Sign in", "Create account")
    action = st.radio(tr("Account", language), actions, format_func=lambda item: tr(item, language), horizontal=True)
    with st.form("local_auth_form"):
        email = st.text_input(tr("Email", language), autocomplete="email")
        display_name = ""
        if action == "Create account":
            display_name = st.text_input(tr("Name", language), autocomplete="name")
        password = st.text_input(tr("Password", language), type="password", autocomplete="current-password" if action == "Sign in" else "new-password")
        submitted = st.form_submit_button(tr(action, language), type="primary", use_container_width=True)
    if submitted:
        if action == "Create account":
            identity, error = create_local_user(email, password, display_name)
            if error:
                st.error(error)
            else:
                st.success(tr("Account created. Your private workspace is ready.", language))
                identity["language"] = language
                return identity
        else:
            identity = authenticate_local_user(email, password)
            if identity:
                identity["language"] = language
                return identity
            st.error(tr("Email or password is incorrect.", language))
    st.stop()
