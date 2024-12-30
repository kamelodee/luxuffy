# Google OAuth2 settings
GOOGLE_OAUTH2_CLIENT_ID = '162461087312-s2gmfbm4o30vjsiurib7c8f30lkc3o6n.apps.googleusercontent.com'  # Get this from Google Cloud Console

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': GOOGLE_OAUTH2_CLIENT_ID,
            'secret': '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',
            'key': ''
        },
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'offline',  # Enable refresh tokens
            'prompt': 'select_account consent'  # Force consent screen
        },
        'OAUTH_PKCE_ENABLED': True,  # Enable PKCE
    }
}

# OAuth settings
OAUTH2_REDIRECT_URIS = [
    'http://127.0.0.1:3000',
    'http://127.0.0.1:8000',
    'http://127.0.0.1:8000/accounts/google/login/callback'
]

AUTHENTICATION_BACKENDS = (
    'accounts.backends.EmailOrUsernameModelBackend',
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
)

# AllAuth settings
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_VERIFICATION = 'optional'  # Changed to optional for easier testing
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_EMAIL_VERIFICATION = 'none'
LOGIN_REDIRECT_URL = '/'

# CORS settings for OAuth
CORS_ORIGIN_WHITELIST = [
    'http://127.0.0.1:3000',
    'http://127.0.0.1:8000',
]
CORS_ALLOW_CREDENTIALS = True
