import unittest
from unittest.mock import patch

from flask import Flask

from my_project.main import run_app


class RunAppTests(unittest.TestCase):
    def test_runs_without_debugger(self):
        with patch("my_project.main.create_app") as create_app:
            run_app()

        create_app.return_value.run.assert_called_once_with(debug=False, port=5001)

    def test_debug_environment_does_not_enable_debugger(self):
        with patch.dict("os.environ", {"FLASK_DEBUG": "1"}, clear=True):
            app = Flask(__name__)
            self.assertTrue(app.debug)

            with patch("my_project.main.create_app", return_value=app):
                with patch("flask.cli.load_dotenv"):
                    with patch("werkzeug.serving.run_simple") as serve:
                        run_app()

        self.assertFalse(app.debug)
        self.assertFalse(serve.call_args.kwargs["use_debugger"])
        self.assertFalse(serve.call_args.kwargs["use_reloader"])


if __name__ == "__main__":
    unittest.main()
