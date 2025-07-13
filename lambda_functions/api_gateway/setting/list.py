import logging
from repositories.settings_repository import SettingsRepository
from datetime import datetime, timezone, timedelta


def format_jst(dt_str):
    if not dt_str:
        return "-"
    try:
        # ISO8601文字列をパース
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        # JSTへ変換
        jst = dt.astimezone(timezone(timedelta(hours=9)))
        return jst.strftime("%Y/%m/%d %H:%M:%S")
    except Exception:
        return dt_str  # パース失敗時はそのまま返す


def get_setting(args, integration):
    settings_repo = SettingsRepository()
    try:
        if len(args) == 0:
            resp = settings_repo.list_valid_settings()
            items = resp.get("Items", [])
            if not items:
                return integration.build_response(
                    "[list] アクティブな設定が1件もありません"
                )
            msg = "[list] アクティブな設定一覧:\n" + "\n".join(
                [
                    f"{item['id']}: {item['keyword']} {item['slack_ch']} like: {item.get('like_threshold', '-')}, rt: {item.get('retweet_threshold', '-')} lastExecuted: {format_jst(item.get('lastExecutedTime'))}"
                    for item in items
                ]
            )
            return integration.build_response(msg)
        elif len(args) == 1 and args[0] == "-a":
            resp = settings_repo.list_all()
            items = resp.get("Items", [])
            if not items:
                return integration.build_response("[list] 設定が1件もありません")
            msg = "[list] 全設定一覧:\n" + "\n".join(
                [
                    f"{item['id']}: {item['keyword']} {item['slack_ch']} (publication_status: {item.get('publication_status', 'unknown')}) like: {item.get('like_threshold', '-')}, rt: {item.get('retweet_threshold', '-')} lastExecuted: {format_jst(item.get('lastExecutedTime'))}"
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


def main(args, integration):
    return get_setting(args, integration)
