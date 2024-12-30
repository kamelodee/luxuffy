from django.core.exceptions import ValidationError

class AllowEasyPasswordsValidator:
    def validate(self, password, user=None):
        # This validator does not enforce any strength requirements
        pass

    def get_help_text(self):
        return "This password validator allows easy passwords."
