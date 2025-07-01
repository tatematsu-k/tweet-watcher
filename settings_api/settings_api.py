import json
import os
import boto3
from datetime import datetime, timezone
import re
from common.datetime_util import parse_end_at
from integration.integration_base import IntegrationBase
from integration.slack_integration import SlackIntegration
from repositories.settings_repository import SettingsRepository

def lambda_handler(event, context):
    integration = SlackIntegration()
    args = integration.parse_input(event)
    if len(args) < 2 or args[0] != "setting":
        return integration.build_response("コマンド形式が正しくありません。/tweet-watcher setting help を参照してください。")
    action = args[1]
    if action == "help":
        return integration.build_response(help_text())
    elif action == "create":
        return create_setting(args[2:], integration)
    elif action == "read":
        return get_setting(args[2:], integration)
    elif action == "update":
        return update_setting(args[2:], integration)
    elif action == "delete":
        return delete_setting(args[2:], integration)
    else:
        return integration.build_response("不明なアクションです。/tweet-watcher setting help を参照してください。")

def help_text():
    return (
        "使い方: /tweet-watcher setting [create|read|update|delete|help] ...\n"
        "例:\n"
        "/tweet-watcher setting create キーワード #slackチャンネル 2024-12-31\n"
        "/tweet-watcher setting read キーワード\n"
        "/tweet-watcher setting update id 2025-01-01\n"
        "/tweet-watcher setting delete id\n"
        "/tweet-watcher setting help"
    )

def create_setting(args, integration):
    if len(args) != 3:
        return integration.build_response("[create] パラメータ数が正しくありません。/tweet-watcher setting help を参照してください。")
    keyword, slack_ch, end_at = args
    try:
        dt = parse_end_at(end_at)
        end_at_iso = dt.isoformat()
    except ValueError as e:
        return integration.build_response(f"[create] {str(e)}")
    settings_repo = SettingsRepository()
    try:
        # keyword+slack_ch重複チェック
        if settings_repo.get_by_keyword_slackch(keyword, slack_ch):
            return integration.build_response(f"[create] 既に登録済みです: {keyword} {slack_ch}")
        id = settings_repo.put(keyword, slack_ch, end_at_iso)
        return integration.build_response(f"[create] 登録しました: {keyword} {slack_ch} {end_at_iso} (id: {id})")
    except Exception as e:
        return integration.build_response(f"[create] エラー: {str(e)}")

def get_setting(args, integration):
    if len(args) != 1:
        return integration.build_response("[read] パラメータ数が正しくありません。/tweet-watcher setting help を参照してください。")
    keyword = args[0]
    settings_repo = SettingsRepository()
    try:
        resp = settings_repo.query(keyword)
        items = resp.get('Items', [])
        if not items:
            return integration.build_response(f"[read] 該当設定がありません: {keyword}")
        msg = "[read] 設定一覧:\n" + "\n".join([
            f"{item['keyword']} {item['slack_ch']} {item['end_at']}" for item in items
        ])
        return integration.build_response(msg)
    except Exception as e:
        return integration.build_response(f"[read] エラー: {str(e)}")

def update_setting(args, integration):
    if len(args) != 2:
        return integration.build_response("[update] パラメータ数が正しくありません。/tweet-watcher setting help を参照してください。\n例: /tweet-watcher setting update id 2025-01-01")
    id, end_at = args
    try:
        dt = parse_end_at(end_at)
        end_at_iso = dt.isoformat()
    except ValueError as e:
        return integration.build_response(f"[update] {str(e)}")
    settings_repo = SettingsRepository()
    try:
        resp = settings_repo.get_by_id(id)
        if "Item" not in resp:
            return integration.build_response(f"[update] 該当設定がありません: id={id}")
        settings_repo.update_by_id(id, end_at_iso)
        return integration.build_response(f"[update] 更新しました: id={id} {end_at_iso}")
    except Exception as e:
        return integration.build_response(f"[update] エラー: {str(e)}")

def delete_setting(args, integration):
    if len(args) != 1:
        return integration.build_response("[delete] パラメータ数が正しくありません。/tweet-watcher setting help を参照してください。\n例: /tweet-watcher setting delete id")
    id = args[0]
    settings_repo = SettingsRepository()
    try:
        resp = settings_repo.get_by_id(id)
        if "Item" not in resp:
            return integration.build_response(f"[delete] 該当設定がありません: id={id}")
        settings_repo.delete_by_id(id)
        return integration.build_response(f"[delete] 削除しました: id={id}")
    except Exception as e:
        return integration.build_response(f"[delete] エラー: {str(e)}")
