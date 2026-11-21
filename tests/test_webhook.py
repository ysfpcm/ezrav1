import unittest
from unittest.mock import patch

import requests
from flask import Flask

from my_project.webhook import last_received_message, send_sms_response, webhook_bp


class SmsHandlerTests(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__)
        app.register_blueprint(webhook_bp)
        self.client = app.test_client()
        last_received_message.clear()
        self.addCleanup(last_received_message.clear)

    def test_sender_number_is_normalized_before_replying(self):
        event = {
            "data": {
                "event_type": "message.received",
                "payload": {
                    "text": " Hello ",
                    "from": {"phone_number": "  +15551234567  "},
                },
            }
        }
        with patch(
            "my_project.webhook.process_incoming_message", return_value="Hi"
        ) as process, patch("my_project.webhook.send_sms_response") as send:
            response = self.client.post("/sms", json=event)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["from_number"], "+15551234567")
        self.assertEqual(last_received_message["from"], "+15551234567")
        process.assert_called_once_with("Hello")
        send.assert_called_once_with("+15551234567", "Hi")

    def test_whitespace_only_sender_is_rejected(self):
        event = {
            "data": {
                "event_type": "message.received",
                "payload": {"text": "Hello", "from": {"phone_number": "  "}},
            }
        }
        with patch("my_project.webhook.process_incoming_message") as process, patch(
            "my_project.webhook.send_sms_response"
        ) as send:
            response = self.client.post("/sms", json=event)

        self.assertEqual(response.status_code, 400)
        process.assert_not_called()
        send.assert_not_called()

    def test_missing_or_invalid_event_type_is_rejected(self):
        events = [
            {},
            {"data": {}},
            {"data": {"event_type": None}},
            {"data": {"event_type": ""}},
            {"data": {"event_type": "  "}},
            {"data": {"event_type": 123}},
        ]
        with patch("my_project.webhook.process_incoming_message") as process, patch(
            "my_project.webhook.send_sms_response"
        ) as send:
            for event in events:
                with self.subTest(event=event):
                    response = self.client.post("/sms", json=event)
                    self.assertEqual(response.status_code, 400)
                    self.assertEqual(response.json["status"], "error")

        process.assert_not_called()
        send.assert_not_called()

    def test_other_event_type_is_ignored(self):
        with patch("my_project.webhook.process_incoming_message") as process, patch(
            "my_project.webhook.send_sms_response"
        ) as send:
            response = self.client.post(
                "/sms", json={"data": {"event_type": "message.sent"}}
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["status"], "ignored")
        process.assert_not_called()
        send.assert_not_called()

    def test_telnyx_non_success_is_not_reported_as_success(self):
        event = {
            "data": {
                "event_type": "message.received",
                "payload": {
                    "text": "Hello",
                    "from": {"phone_number": "+15551234567"},
                },
            }
        }
        for status_code in (302, 400, 500):
            with self.subTest(status_code=status_code):
                telnyx_response = requests.Response()
                telnyx_response.status_code = status_code
                telnyx_response._content = b"{}"
                with patch(
                    "my_project.webhook.process_incoming_message", return_value="Hi"
                ), patch(
                    "my_project.webhook.requests.post", return_value=telnyx_response
                ):
                    response = self.client.post("/sms", json=event)

                self.assertEqual(response.status_code, 500)
                self.assertEqual(response.json["status"], "error")

    def test_telnyx_success_does_not_follow_redirects(self):
        telnyx_response = requests.Response()
        telnyx_response.status_code = 202
        telnyx_response._content = b'{"data": {"id": "message-id"}}'
        with self.client.application.app_context(), patch(
            "my_project.webhook.requests.post", return_value=telnyx_response
        ) as post:
            result = send_sms_response("+15551234567", "Hi")

        self.assertEqual(result, {"data": {"id": "message-id"}})
        self.assertIs(post.call_args.kwargs["allow_redirects"], False)

    def test_telnyx_success_without_json_is_reported_as_success(self):
        event = {
            "data": {
                "event_type": "message.received",
                "payload": {
                    "text": "Hello",
                    "from": {"phone_number": "+15551234567"},
                },
            }
        }
        for status_code, content in ((202, b""), (202, b"accepted"), (204, b"")):
            with self.subTest(status_code=status_code, content=content):
                telnyx_response = requests.Response()
                telnyx_response.status_code = status_code
                telnyx_response._content = content
                with patch(
                    "my_project.webhook.process_incoming_message", return_value="Hi"
                ), patch(
                    "my_project.webhook.requests.post", return_value=telnyx_response
                ) as post:
                    response = self.client.post("/sms", json=event)

                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json["status"], "success")
                post.assert_called_once()


if __name__ == "__main__":
    unittest.main()
