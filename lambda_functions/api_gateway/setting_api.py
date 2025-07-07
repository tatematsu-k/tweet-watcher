from integration.slack_integration import SlackIntegration
from lambda_functions.api_gateway.setting.create import main as create_setting_main
from lambda_functions.api_gateway.setting.list import main as list_setting_main
from lambda_functions.api_gateway.setting.update import main as update_setting_main
from lambda_functions.api_gateway.setting.update_like_threshold import (
    main as update_like_threshold_main,
)
from lambda_functions.api_gateway.setting.update_retweet_threshold import (
    main as update_retweet_threshold_main,
)
from lambda_functions.api_gateway.setting.delete import main as delete_setting_main
from lambda_functions.api_gateway.setting.active import main as activate_setting_main
from lambda_functions.api_gateway.setting.inactive import main as inactive_setting_main


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
        return inactive_setting_main(args[2:], integration)
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
