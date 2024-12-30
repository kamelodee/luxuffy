from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed

class BearerTokenAuthentication(TokenAuthentication):
    keyword = 'Bearer'  # Change Token to Bearer

    def authenticate_credentials(self, key):
        try:
            return super().authenticate_credentials(key)
        except AuthenticationFailed as e:
            raise AuthenticationFailed('Invalid token or token has expired')
