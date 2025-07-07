import logging
from repositories.settings_repository import SettingsRepository


def create_setting(args, integration):
    if len(args) < 2:
        return integration.build_response(
            "[create] パラメータ数が正しくありません。/tweet-watcher setting help を参照してください。"
        )
    keyword = args[0]
    slack_ch = args[1]
    like_threshold = int(args[2]) if len(args) > 2 and args[2] != "" else None
    retweet_threshold = int(args[3]) if len(args) > 3 and args[3] != "" else None
    settings_repo = SettingsRepository()
    try:
        resp = settings_repo.put(keyword, slack_ch, like_threshold, retweet_threshold)
        msg = f"[create] 登録しました: {keyword} {slack_ch} (id: {resp['id']}, publication_status: {resp['publication_status']})"
        if like_threshold is not None:
            msg += f" like閾値: {like_threshold}"
        if retweet_threshold is not None:
            msg += f" retweet閾値: {retweet_threshold}"
        return integration.build_response(msg)
    except Exception as e:
        logging.error(f"[create] エラーが発生しました: {str(e)}", exc_info=True)
        return integration.build_response(f"[create] エラー: {str(e)}")


def main(args, integration):
    return create_setting(args, integration)
