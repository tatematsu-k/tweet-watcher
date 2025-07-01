import os
import boto3

class SettingsRepository:
    def __init__(self, table_name=None):
        self.dynamodb = boto3.resource("dynamodb")
        self.table_name = table_name or os.environ.get("SETTINGS_TABLE", "SettingsTable")
        self.table = self.dynamodb.Table(self.table_name)

    def get(self, keyword, slack_ch):
        return self.table.get_item(Key={"keyword": keyword, "slack_ch": slack_ch})

    def put(self, keyword, slack_ch, end_at):
        return self.table.put_item(Item={"keyword": keyword, "slack_ch": slack_ch, "end_at": end_at})

    def update(self, keyword, slack_ch, end_at):
        return self.table.update_item(
            Key={"keyword": keyword, "slack_ch": slack_ch},
            UpdateExpression="SET end_at = :end_at",
            ExpressionAttributeValues={":end_at": end_at}
        )

    def delete(self, keyword, slack_ch):
        return self.table.delete_item(Key={"keyword": keyword, "slack_ch": slack_ch})

    def query_by_keyword(self, keyword):
        from boto3.dynamodb.conditions import Key
        return self.table.query(KeyConditionExpression=Key('keyword').eq(keyword))
