import logging
from repositories.settings_repository import SettingsRepository

def inactive_setting(args, integration):
    if len(args) != 1:
        return integration.build_response(
            "[inactive] パラメータ数が正しくありません。/tweet-watcher setting help を参照してください。\n例: /tweet-watcher setting inactive id"
        )
    id = args[0]
    settings_repo = SettingsRepository()
    try:
        resp = settings_repo.get_by_id(id)
        if "Item" not in resp:
            return integration.build_response(f"[inactive] 該当設定がありません: id={id}")
        settings_repo.update_publication_status_inactive_by_id(id)
        return integration.build_response(f"[inactive] 非アクティブにしました: id={id}")
    except Exception as e:
        logging.error(f"[inactive] エラーが発生しました: {str(e)}", exc_info=True)
        return integration.build_response(f"[inactive] エラー: {str(e)}")

def main(args, integration):
    return inactive_setting(args, integration)