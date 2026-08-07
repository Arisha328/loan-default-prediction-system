"""
utils/template_filters.py
--------------------------
Small Jinja2 filters used across templates (currency formatting, etc).
"""


def register_filters(app):
    @app.template_filter("currency")
    def currency_filter(value):
        try:
            return f"${float(value):,.0f}"
        except (TypeError, ValueError):
            return value

    @app.template_filter("percent")
    def percent_filter(value):
        try:
            return f"{float(value) * 100:.1f}%"
        except (TypeError, ValueError):
            return value

    @app.template_filter("avatar_url")
    def avatar_url_filter(user):
        """Returns the URL for a user's uploaded avatar, or None if they
        haven't set one (the template falls back to an initials badge)."""
        if user and getattr(user, "profile_image", None):
            from flask import url_for

            return url_for("static", filename=f"uploads/avatars/{user.profile_image}")
        return None
