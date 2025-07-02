from integration.integration_base import IntegrationBase
from urllib.parse import parse_qs
import requests
import os

class SlackIntegration(IntegrationBase):
    def __init__(self, bot_token=None):
        self.bot_token = bot_token or os.environ.get("SLACK_BOT_TOKEN")

    def parse_input(self, event):
        body = event.get("body", "")
        params = {k: v[0] for k, v in parse_qs(body).items()}
        text = params.get("text", "")
        args = text.strip().split()
        return args

    def build_response(self, message):
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "text/plain"},
            "body": message
        }

    def send_message(self, channel, message, thread_ts=None):
        """
        Slack Bot Token方式でchat.postMessage APIを使いメッセージ送信。thread_ts指定でスレッド返信も可能。
        戻り値はSlackのメッセージts。
        """
        if not self.bot_token:
            raise ValueError("SLACK_BOT_TOKENが設定されていません")
        url = "https://slack.com/api/chat.postMessage"
        headers = {
            "Authorization": f"Bearer {self.bot_token}",
            "Content-Type": "application/json; charset=utf-8"
        }
        payload = {
            "channel": channel,
            "text": message
        }
        if thread_ts:
            payload["thread_ts"] = thread_ts
        resp = requests.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        if not data.get("ok"):
            raise Exception(f"Slack API error: {data}")
        return data["ts"]
