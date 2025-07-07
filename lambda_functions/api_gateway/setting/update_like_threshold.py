import logging
from repositories.settings_repository import SettingsRepository

def update_like_threshold(args, integration):
    if len(args) != 2:
        return integration.build_response(
            "[update_like_threshold] パラメータ数が正しくありません。/tweet-watcher setting help を参照してください。\n例: /tweet-watcher setting update_like_threshold id 値"
        )
    id, value = args
    settings_repo = SettingsRepository()
    try:
        resp = settings_repo.get_by_id(id)
        if "Item" not in resp:
            return integration.build_response(f"[update_like_threshold] 該当設定がありません: id={id}")
        settings_repo.update_like_threshold_by_id(id, value)
        return integration.build_response(f"[update_like_threshold] 更新しました: id={id} like_threshold={value}")
    except Exception as e:
        logging.error(f"[update_like_threshold] エラーが発生しました: {str(e)}", exc_info=True)
        return integration.build_response(f"[update_like_threshold] エラー: {str(e)}")

def main(args, integration):
    return update_like_threshold(args, integration)