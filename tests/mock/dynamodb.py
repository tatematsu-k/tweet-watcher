import os
import yaml
import boto3
from moto import mock_dynamodb
from contextlib import contextmanager

TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), '../../template.yaml')

# CloudFormationの!Ref等を無視するカスタムローダー
class IgnoreCfnTagsLoader(yaml.SafeLoader):
    pass

def _ignore_cfn_tag(loader, tag_suffix, node):
    if isinstance(node, yaml.ScalarNode):
        return node.value
    elif isinstance(node, yaml.SequenceNode):
        return loader.construct_sequence(node)
    elif isinstance(node, yaml.MappingNode):
        return loader.construct_mapping(node)
    return None

for tag in ['!Ref', '!Sub', '!GetAtt', '!Join', '!Select', '!Split', '!If', '!Equals', '!FindInMap', '!ImportValue', '!Base64', '!Cidr', '!And', '!Or', '!Not']:  # 必要に応じて追加
    IgnoreCfnTagsLoader.add_multi_constructor(tag, _ignore_cfn_tag)

def parse_dynamodb_tables_from_template(template_path=TEMPLATE_PATH):
    """
    template.yamlからDynamoDBテーブル定義を抽出する
    Returns: List[dict] (各テーブルのProperties)
    """
    with open(template_path, 'r') as f:
        template = yaml.load(f, Loader=IgnoreCfnTagsLoader)
    resources = template.get('Resources', {})
    tables = []
    for res in resources.values():
        if res.get('Type') == 'AWS::DynamoDB::Table':
            tables.append(res['Properties'])
    return tables


def create_all_tables_from_template():
    """
    template.yamlの全DynamoDBテーブルをmotoで作成する
    """
    tables = parse_dynamodb_tables_from_template()
    dynamodb = boto3.resource('dynamodb', region_name='ap-northeast-1')
    for props in tables:
        params = {
            'TableName': props['TableName'],
            'KeySchema': props['KeySchema'],
            'AttributeDefinitions': props['AttributeDefinitions'],
            'BillingMode': props.get('BillingMode', 'PAY_PER_REQUEST'),
        }
        if 'GlobalSecondaryIndexes' in props:
            params['GlobalSecondaryIndexes'] = props['GlobalSecondaryIndexes']
        if 'StreamSpecification' in props:
            # CloudFormation形式→boto3形式へ変換
            stream_spec = dict(props['StreamSpecification'])
            stream_spec['StreamEnabled'] = True
            params['StreamSpecification'] = stream_spec
        dynamodb.create_table(**params)

@contextmanager
def setup_dynamodb_all_tables():
    os.environ['AWS_DEFAULT_REGION'] = 'ap-northeast-1'
    with mock_dynamodb():
        create_all_tables_from_template()
        yield