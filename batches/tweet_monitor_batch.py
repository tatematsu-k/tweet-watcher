import os
import boto3

def lambda_handler(event, context):
    # TODO: 設定テーブルから有効な設定を列挙
    # TODO: 各設定ごとにX(Twitter)APIでキーワード検索
    # TODO: like_count, retweet_countで閾値フィルタ
    # TODO: 通知テーブルに新規tweetを保存（重複防止）
    print("[BatchWatcher] Triggered by EventBridge schedule.")
    return {"statusCode": 200, "body": "Batch executed."}