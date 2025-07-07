import os
import hmac
import hashlib
import time
import logging
from integration.slack_integration import SlackIntegration
from repositories.settings_repository import SettingsRepository
from lambda_functions.api_gateway.setting.create import main as create_setting_main
from lambda_functions.api_gateway.setting.list import main as list_setting_main
from lambda_functions.api_gateway.setting.update import main as update_setting_main
from lambda_functions.api_gateway.setting.update_like_threshold import main as update_like_threshold_main
from lambda_functions.api_gateway.setting.update_retweet_threshold import main as update_retweet_threshold_main
from lambda_functions.api_gateway.setting.delete import main as delete_setting_main
from lambda_functions.api_gateway.setting.active import main as activate_setting_main


def get_slack_signing_secret():
    return os.environ.get("SLACK_SIGNING_SECRET")


def verify_slack_request(headers, body, signing_secret):
    timestamp = headers.get("X-Slack-Request-Timestamp")
    slack_signature = headers.get("X-Slack-Signature")
    if not timestamp or not slack_signature:
        return False
    # リプレイ攻撃対策: 5分以上前のリクエストは拒否
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
    # Slack署名検証はmain.pyで実施済み
    integration = SlackIntegration()
    args = integration.parse_input(event)

    print(f"request with args: {args}, body: {event.get('body', '')}")
    if len(args) < 2 or args[0] != "setting":
        return integration.build_response(
            "コマンド形式が正しくありません。/tweet-watcher setting help を参照してください。"
        )
    action = args[1]
    if action == "help":
        return integration.build_response(help_text())
    elif action == "create":
        return create_setting_main(args[2:], integration)
    elif action == "list":
        return list_setting_main(args[2:], integration)
    elif action == "update":
        return update_setting_main(args[2:], integration)
    elif action == "update_like_threshold":
        return update_like_threshold_main(args[2:], integration)
    elif action == "update_retweet_threshold":
        return update_retweet_threshold_main(args[2:], integration)
    elif action == "delete":
        return delete_setting_main(args[2:], integration)
    elif action == "active":
        return activate_setting_main(args[2:], integration)
    elif action == "inactive":
        return deactivate_setting(args[2:], integration)
    else:
        return integration.build_response(
            "不明なアクションです。/tweet-watcher setting help を参照してください。"
        )


def help_text():
    return (
        "使い方: /tweet-watcher setting [create|list|update|update_like_threshold|update_retweet_threshold|delete|active|inactive|help] ...\n"
        "例:\n"
        "/tweet-watcher setting create 'キーワード1 キーワード2' #slackチャンネル [like閾値] [retweet閾値]\n"
        "/tweet-watcher setting list (-a)\n"
        "/tweet-watcher setting update id '新キーワード'\n"
        "/tweet-watcher setting update_like_threshold id 値\n"
        "/tweet-watcher setting update_retweet_threshold id 値\n"
        "/tweet-watcher setting delete id\n"
        "/tweet-watcher setting active id\n"
        "/tweet-watcher setting inactive id\n"
        "/tweet-watcher setting help"
    )


def get_setting(args, integration):
    settings_repo = SettingsRepository()
    try:
        if len(args) == 0:
            # アクティブな設定のみ取得
            resp = settings_repo.list_valid_settings()
            items = resp.get("Items", [])
            if not items:
                return integration.build_response(
                    "[list] アクティブな設定が1件もありません"
                )
            msg = "[list] アクティブな設定一覧:\n" + "\n".join(
                [
                    f"{item['id']}: {item['keyword']} {item['slack_ch']} like: {item.get('like_threshold', '-')}, rt: {item.get('retweet_threshold', '-')}"
                    for item in items
                ]
            )
            return integration.build_response(msg)
        elif len(args) == 1 and args[0] == "-a":
            # 全件取得（明示的に-aオプション指定）
            resp = settings_repo.list_all()
            items = resp.get("Items", [])
            if not items:
                return integration.build_response("[list] 設定が1件もありません")
            msg = "[list] 全設定一覧:\n" + "\n".join(
                [
                    f"{item['id']}: {item['keyword']} {item['slack_ch']} (publication_status: {item.get('publication_status', 'unknown')}) like: {item.get('like_threshold', '-')}, rt: {item.get('retweet_threshold', '-')}"
                    for item in items
                ]
            )
            return integration.build_response(msg)
        elif len(args) == 1:
            return integration.build_response(
                "[list] パラメータが正しくありません。/tweet-watcher setting help を参照してください。"
            )
        else:
            return integration.build_response(
                "[list] パラメータ数が正しくありません。/tweet-watcher setting help を参照してください。"
            )
    except Exception as e:
        logging.error(f"[list] エラーが発生しました: {str(e)}", exc_info=True)
        return integration.build_response(f"[list] エラー: {str(e)}")


def update_setting(args, integration):
    if len(args) != 2:
        return integration.build_response(
            "[update] パラメータ数が正しくありません。/tweet-watcher setting help を参照してください。\n例: /tweet-watcher setting update id 新キーワード"
        )
    id, new_keyword = args
    settings_repo = SettingsRepository()
    try:
        resp = settings_repo.get_by_id(id)
        if "Item" not in resp:
            return integration.build_response(f"[update] 該当設定がありません: id={id}")
        settings_repo.update_keyword_by_id(id, new_keyword)
        return integration.build_response(
            f"[update] 更新しました: id={id} {new_keyword}"
        )
    except Exception as e:
        logging.error(f"[update] エラーが発生しました: {str(e)}", exc_info=True)
        return integration.build_response(f"[update] エラー: {str(e)}")


def delete_setting(args, integration):
    if len(args) != 1:
        return integration.build_response(
            "[delete] パラメータ数が正しくありません。/tweet-watcher setting help を参照してください。\n例: /tweet-watcher setting delete id"
        )
    id = args[0]
    settings_repo = SettingsRepository()
    try:
        resp = settings_repo.get_by_id(id)
        if "Item" not in resp:
            return integration.build_response(f"[delete] 該当設定がありません: id={id}")
        settings_repo.delete_by_id(id)
        return integration.build_response(f"[delete] 削除しました: id={id}")
    except Exception as e:
        logging.error(f"[delete] エラーが発生しました: {str(e)}", exc_info=True)
        return integration.build_response(f"[delete] エラー: {str(e)}")


def deactivate_setting(args, integration):
    if len(args) != 1:
        return integration.build_response(
            "[inactive] パラメータ数が正しくありません。/tweet-watcher setting help を参照してください。\n例: /tweet-watcher setting inactive id"
        )
    id = args[0]
    settings_repo = SettingsRepository()
    try:
        resp = settings_repo.get_by_id(id)
        if "Item" not in resp:
            return integration.build_response(
                f"[inactive] 該当設定がありません: id={id}"
            )
        settings_repo.update_publication_status_inactive_by_id(id)
        return integration.build_response(f"[inactive] 非アクティブにしました: id={id}")
    except Exception as e:
        logging.error(f"[inactive] エラーが発生しました: {str(e)}", exc_info=True)
        return integration.build_response(f"[inactive] エラー: {str(e)}")


def update_retweet_threshold(args, integration):
    if len(args) != 2:
        return integration.build_response(
            "[update_retweet_threshold] パラメータ数が正しくありません。/tweet-watcher setting help を参照してください。\n例: /tweet-watcher setting update_retweet_threshold id 値"
        )
    id, value = args
    settings_repo = SettingsRepository()
    try:
        resp = settings_repo.get_by_id(id)
        if "Item" not in resp:
            return integration.build_response(
                f"[update_retweet_threshold] 該当設定がありません: id={id}"
            )
        settings_repo.update_retweet_threshold_by_id(id, value)
        return integration.build_response(
            f"[update_retweet_threshold] 更新しました: id={id} retweet_threshold={value}"
        )
    except Exception as e:
        logging.error(
            f"[update_retweet_threshold] エラーが発生しました: {str(e)}", exc_info=True
        )
        return integration.build_response(
            f"[update_retweet_threshold] エラー: {str(e)}"
        )
