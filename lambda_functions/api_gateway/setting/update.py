import logging
from repositories.settings_repository import SettingsRepository


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


def main(args, integration):
    return update_setting(args, integration)
