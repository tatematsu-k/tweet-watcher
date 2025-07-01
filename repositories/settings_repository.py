import os
import boto3
import uuid
import random
import string

class SettingsRepository:
    def __init__(self, table_name=None):
        self.dynamodb = boto3.resource("dynamodb")
        self.table_name = table_name or os.environ.get("SETTINGS_TABLE", "SettingsTable")
        self.table = self.dynamodb.Table(self.table_name)

    def get_by_id(self, id):
        return self.table.get_item(Key={"id": id})

    def get_by_keyword_slackch(self, keyword, slack_ch):
        resp = self.table.query(
            IndexName="keyword-index",
            KeyConditionExpression=boto3.dynamodb.conditions.Key('keyword').eq(keyword) & boto3.dynamodb.conditions.Key('slack_ch').eq(slack_ch)
        )
        items = resp.get('Items', [])
        return items[0] if items else None

    def _generate_short_id(self, length=6):
        chars = string.ascii_letters + string.digits
        return ''.join(random.choices(chars, k=length))

    def put(self, keyword, slack_ch, end_at):
        for _ in range(10):
            id = self._generate_short_id()
            if not self.get_by_id(id).get('Item'):
                break
        else:
            raise Exception('ID生成に失敗しました')
        self.table.put_item(Item={"id": id, "keyword": keyword, "slack_ch": slack_ch, "end_at": end_at})
        return id

    def update_by_id(self, id, end_at):
        return self.table.update_item(
            Key={"id": id},
            UpdateExpression="SET end_at = :end_at",
            ExpressionAttributeValues={":end_at": end_at}
        )

    def delete_by_id(self, id):
        return self.table.delete_item(Key={"id": id})

    def query_by_keyword(self, keyword):
        from boto3.dynamodb.conditions import Key
        return self.table.query(IndexName="keyword-index", KeyConditionExpression=Key('keyword').eq(keyword))
