"""Validate proxy identity before OctoPrint's native remote-user authentication."""
import hmac
import os
import octoprint.plugin


class AuroraIdentityPlugin(octoprint.plugin.StartupPlugin):
    def on_startup(self, host, port):
        from octoprint.server import app
        from flask import request, abort
        from flask_login import login_user
        import octoprint.server
        secret = os.environ.get('AURORA_SSO_SECRET', '')
        if len(secret) < 32:
            raise RuntimeError('Private SSO proxy secret required')

        @app.before_request
        def authenticate_proxy_identity():
            if request.headers.get('X-Aurora-Identity'):
                supplied = request.headers.get('X-Aurora-Proxy-Secret', '')
                if not hmac.compare_digest(supplied.encode(), secret.encode()):
                    abort(403)
                user = octoprint.server.userManager.find_user(userid=request.headers['X-Aurora-Identity'])
                # Explicitly replace an old native browser session with the mapped user.
                if not user or not login_user(user, remember=False, fresh=True):
                    abort(403)


__plugin_name__ = 'AuroraLAB Identity'
__plugin_pythoncompat__ = '>=3.12,<4'
__plugin_implementation__ = AuroraIdentityPlugin()
