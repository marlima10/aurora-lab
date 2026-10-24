"""Native Flask/OctoPrint packages, synthetic users, no server or printer devices."""
import importlib.util
import os
from pathlib import Path
import unittest
from flask import Flask, jsonify
from flask_login import LoginManager, UserMixin, current_user
import octoprint.server


class User(UserMixin):
    def __init__(self, name):
        self.id = name


class OctoPrintIdentityTests(unittest.TestCase):
    def setUp(self):
        os.environ['AURORA_SSO_SECRET']='fixture-private-proxy-secret-000000000'
        app = Flask('aurora-octoprint-fixture')
        app.secret_key='fixture-only'
        self.users={'mapped':User('mapped'),'old':User('old')}
        login=LoginManager(app)
        login.user_loader(lambda uid:self.users.get(uid))
        octoprint.server.app=app
        class Manager:
            find_user=lambda _,userid:self.users.get(userid)
        octoprint.server.userManager=Manager()
        spec=importlib.util.spec_from_file_location('fixture_plugin',Path(__file__).resolve().parents[1]/'adapters/octoprint_aurora.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        module.__plugin_implementation__.on_startup('fixture',0)
        @app.route('/fixture')
        def identity():
            return jsonify({'user':current_user.get_id()})
        self.client=app.test_client()
        self.headers={'X-Aurora-Identity':'mapped','X-Aurora-Proxy-Secret':os.environ['AURORA_SSO_SECRET']}

    def test_establishes_mapped_user_over_old_native_browser_session(self):
        with self.client.session_transaction() as session:
            session['_user_id']='old'
            session['_fresh']=True
        response=self.client.get('/fixture',headers=self.headers)
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json,{'user':'mapped'})

    def test_forged_or_unknown_user_is_denied(self):
        for change in [{'X-Aurora-Proxy-Secret':'forged'},{'X-Aurora-Identity':'missing'}]:
            self.assertEqual(self.client.get('/fixture',headers=self.headers|change).status_code,403)


if __name__=='__main__':
    unittest.main()
