import logging
from repositories.settings_repository import SettingsRepository

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

def main(args, integration):
    return delete_setting(args, integration)