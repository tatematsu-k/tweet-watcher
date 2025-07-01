import json
import os
import boto3

dynamodb = boto3.resource("dynamodb")
SETTINGS_TABLE = os.environ.get("SETTINGS_TABLE", "SettingsTable")

def lambda_handler(event, context):
    # Slackコマンドはapplication/x-www-form-urlencodedでPOSTされる
    body = event.get("body", "")
    params = parse_slack_body(body)
    text = params.get("text", "")
    args = text.strip().split()
    if len(args) < 2 or args[0] != "setting":
        return slack_response("コマンド形式が正しくありません。/tweet-watcher setting help を参照してください。")
    action = args[1]
    if action == "help":
        return slack_response(help_text())
    elif action == "create":
        return create_setting(args[2:])
    elif action == "read":
        return get_setting(args[2:])
    elif action == "update":
        return update_setting(args[2:])
    elif action == "delete":
        return delete_setting(args[2:])
    else:
        return slack_response("不明なアクションです。/tweet-watcher setting help を参照してください。")

def parse_slack_body(body):
    # application/x-www-form-urlencoded を dict化
    from urllib.parse import parse_qs
    return {k: v[0] for k, v in parse_qs(body).items()}

def slack_response(message):
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "text/plain"},
        "body": message
    }

def help_text():
    return (
        "使い方: /tweet-watcher setting [create|read|update|delete|help] ...\n"
        "例:\n"
        "/tweet-watcher setting create キーワード #slackチャンネル 2024-12-31\n"
        "/tweet-watcher setting read キーワード\n"
        "/tweet-watcher setting update キーワード #slackチャンネル 2025-01-01\n"
        "/tweet-watcher setting delete キーワード\n"
        "/tweet-watcher setting help"
    )

def create_setting(args):
    if len(args) != 3:
        return slack_response("[create] パラメータ数が正しくありません。/tweet-watcher setting help を参照してください。")
    keyword, slack_ch, end_at = args
    table = dynamodb.Table(SETTINGS_TABLE)
    # 既存チェック
    try:
        resp = table.get_item(Key={"keyword": keyword, "slack_ch": slack_ch})
        if "Item" in resp:
            return slack_response(f"[create] 既に登録済みです: {keyword} {slack_ch}")
        table.put_item(Item={"keyword": keyword, "slack_ch": slack_ch, "end_at": end_at})
        return slack_response(f"[create] 登録しました: {keyword} {slack_ch} {end_at}")
    except Exception as e:
        return slack_response(f"[create] エラー: {str(e)}")

def get_setting(args):
    # TODO: 実装
    return slack_response("[read] 未実装")

def update_setting(args):
    # TODO: 実装
    return slack_response("[update] 未実装")

def delete_setting(args):
    # TODO: 実装
    return slack_response("[delete] 未実装")
