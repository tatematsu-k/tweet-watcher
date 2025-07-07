import importlib
from integration.slack_integration import SlackIntegration
import os
import hmac
import hashlib
import time


def get_slack_signing_secret():
    return os.environ.get("SLACK_SIGNING_SECRET")


def verify_slack_request(headers, body, signing_secret):
    timestamp = headers.get("X-Slack-Request-Timestamp")
    slack_signature = headers.get("X-Slack-Signature")
    if not timestamp or not slack_signature:
        return False
    if abs(time.time() - int(timestamp)) > 60 * 5:
        return False
    sig_basestring = f"v0:{timestamp}:{body}".encode("utf-8")
    my_signature = (
        "v0="
        + hmac.new(
            signing_secret.encode("utf-8"), sig_basestring, hashlib.sha256
        ).hexdigest()
    )
    return hmac.compare_digest(my_signature, slack_signature)


def lambda_handler(event, context):
    signing_secret = get_slack_signing_secret()
    headers = event.get("headers", {})
    body = event.get("body", "")
    if not verify_slack_request(headers, body, signing_secret):
        return {"statusCode": 401, "body": "Invalid Slack signature."}
    integration = SlackIntegration()
    args = integration.parse_input(event)

    if len(args) < 1:
        return integration.build_response("コマンド形式が正しくありません。/tweet-watcher [setting] help を参照してください。")

    domain = args[0]
    module_name = f"lambda_functions.api_gateway.{domain}_api"
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError:
        return integration.build_response(f"不明なドメインです: {domain}")

    if hasattr(module, "lambda_handler"):
        # サブAPIのlambda_handlerにevent, context, argsを渡す
        return module.lambda_handler(event, context)
    else:
        return integration.build_response(f"{domain}_api.py にlambda_handlerが定義されていません")