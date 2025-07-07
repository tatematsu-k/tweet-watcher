import os
import boto3
import random
import string
from boto3.dynamodb.conditions import Key

class SettingsRepository:
    # アクティブな設定の最大件数
    MAX_ACTIVE_SETTINGS = 3

    def __init__(self, table_name=None):
        self.dynamodb = boto3.resource("dynamodb")
        self.table_name = table_name or os.environ.get("SETTINGS_TABLE", "TweetWacherSettingsTable")
        self.table = self.dynamodb.Table(self.table_name)

    def get_by_id(self, id):
        return self.table.get_item(Key={"id": id})

    def _generate_short_id(self, length=6):
        chars = string.ascii_letters + string.digits
        return ''.join(random.choices(chars, k=length))

    def put(self, keyword, slack_ch, like_threshold=None, retweet_threshold=None):
        for _ in range(10):
            id = self._generate_short_id()
            if not self.get_by_id(id).get('Item'):
                break
        else:
            raise Exception('ID生成に失敗しました')

        # 現在のアクティブ設定数をチェックしてpublication_statusを決定
        current_active_count = self.valid_setting_count()
        publication_status = "active" if current_active_count < self.MAX_ACTIVE_SETTINGS else "inactive"

        item = {
            "id": id,
            "keyword": keyword,
            "slack_ch": slack_ch,
            "publication_status": publication_status
        }
        if like_threshold is not None:
            item["like_threshold"] = int(like_threshold)
        if retweet_threshold is not None:
            item["retweet_threshold"] = int(retweet_threshold)
        self.table.put_item(Item=item)
        return {"id": id, "publication_status": publication_status}

    def update_keyword_by_id(self, id, keyword):
        update_expr = "SET keyword = :keyword"
        expr_attr = {":keyword": keyword}
        return self.table.update_item(
            Key={"id": id},
            UpdateExpression=update_expr,
            ExpressionAttributeValues=expr_attr
        )

    def update_publication_status_active_by_id(self, id):
        # アクティブな設定がMAX_ACTIVE_SETTINGS件以上ある場合はエラーを返す
        if self.valid_setting_count() >= self.MAX_ACTIVE_SETTINGS:
            raise Exception('アクティブな設定は3件までしか登録できません')

        update_expr = "SET publication_status = :publication_status"
        expr_attr = {":publication_status": "active"}
        return self.table.update_item(
            Key={"id": id},
            UpdateExpression=update_expr,
            ExpressionAttributeValues=expr_attr
        )

    def update_publication_status_inactive_by_id(self, id):
        update_expr = "SET publication_status = :publication_status"
        expr_attr = {":publication_status": "inactive"}
        return self.table.update_item(
            Key={"id": id},
            UpdateExpression=update_expr,
            ExpressionAttributeValues=expr_attr
        )

    def delete_by_id(self, id):
        return self.table.delete_item(Key={"id": id})

    def list_all(self):
        return self.table.scan()

    def list_valid_settings(self):
        response = self.table.query(
            IndexName="publication_status-index",
            KeyConditionExpression=Key('publication_status').eq('active')
        )
        return response

    def valid_setting_count(self):
        return len(self.list_valid_settings().get('Items', []))

    def update_like_threshold_by_id(self, id, like_threshold):
        update_expr = "SET like_threshold = :like_threshold"
        expr_attr = {":like_threshold": int(like_threshold) if like_threshold is not None else None}
        return self.table.update_item(
            Key={"id": id},
            UpdateExpression=update_expr,
            ExpressionAttributeValues=expr_attr
        )

    def update_retweet_threshold_by_id(self, id, retweet_threshold):
        update_expr = "SET retweet_threshold = :retweet_threshold"
        expr_attr = {":retweet_threshold": int(retweet_threshold) if retweet_threshold is not None else None}
        return self.table.update_item(
            Key={"id": id},
            UpdateExpression=update_expr,
            ExpressionAttributeValues=expr_attr
        )
