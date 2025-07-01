from integration.integration_base import IntegrationBase
from urllib.parse import parse_qs

class SlackIntegration(IntegrationBase):
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
