from integration.integration_base import IntegrationBase
from urllib.parse import parse_qs
import http.client
import json
import os
import shlex

class SlackIntegration(IntegrationBase):
    def __init__(self, bot_token=None):
        self.bot_token = bot_token or os.environ.get("SLACK_BOT_TOKEN")

    def parse_input(self, event):
        body = event.get("body", "")
        params = {k: v[0] for k, v in parse_qs(body).items()}
        text = params.get("text", "")

        return shlex.split(text)

    def build_response(self, message):
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "text/plain"},
            "body": message
        }

    def _slack_api_post(self, endpoint, payload):
        if not self.bot_token:
            raise ValueError("SLACK_BOT_TOKENが設定されていません")
        conn = http.client.HTTPSConnection("slack.com")
        headers = {
            "Authorization": f"Bearer {self.bot_token}",
            "Content-Type": "application/json; charset=utf-8"
        }
        body = json.dumps(payload)
        conn.request("POST", f"/api/{endpoint}", body, headers)
        res = conn.getresponse()
        data = res.read()
        conn.close()
        if res.status != 200:
            raise Exception(f"Slack API HTTP error: {res.status} {data}")
        resp_json = json.loads(data)
        if not resp_json.get("ok"):
            raise Exception(f"Slack API error: {resp_json}")
        return resp_json

    def send_message(self, channel, message, thread_ts=None):
        """
        Slack Bot Token方式でchat.postMessage APIを使いメッセージ送信。thread_ts指定でスレッド返信も可能。
        戻り値はSlackのメッセージts。
        """
        payload = {
            "channel": channel,
            "text": message
        }
        if thread_ts:
            payload["thread_ts"] = thread_ts
        try:
            data = self._slack_api_post("chat.postMessage", payload)
            print(f"[SlackIntegration] Slack API response: {data}")
            if not data.get("ok"):
                raise Exception(f"Slack API error: {data}")
            return data["ts"]
        except Exception as e:
            raise Exception(f"Slackメッセージ送信に失敗しました: {str(e)}") from e
