# X（Twitter）API 設定手順

このプロジェクトで X（旧 Twitter）API を利用するための設定手順をまとめます。

## 1. 開発者アカウントの作成

1. https://developer.twitter.com/ にアクセスし、Twitter アカウントでログイン
2. Developer Portal で「プロジェクトと App」を作成

## 2. API キー・トークンの取得

1. 作成した App の「Keys and tokens」タブを開く
2. 以下の情報を取得
   - API Key（Consumer Key）
   - API Secret Key（Consumer Secret）
   - Bearer Token
   - Access Token
   - Access Token Secret

※本プロジェクトでは主に Bearer Token を利用します

## 3. 必要な権限の設定

- 「Read」権限が必須
- 検索やツイート取得のみの場合は「Read」権限で OK
- 書き込みや DM 送信が必要な場合は「Write」や「Direct Message」権限も付与

## 4. 環境変数の設定

Lambda やローカル実行環境で、以下の環境変数を設定してください。

```
TWITTER_BEARER_TOKEN=取得したBearer Token
# 必要に応じて下記も設定
TWITTER_CONSUMER_KEY=取得したAPI Key
TWITTER_CONSUMER_SECRET=取得したAPI Secret Key
TWITTER_ACCESS_TOKEN=取得したAccess Token
TWITTER_ACCESS_TOKEN_SECRET=取得したAccess Token Secret
```

## 5. 注意事項

- API 利用には申請・審査が必要な場合があります
- 無料枠では検索件数や取得範囲に制限があります
- 有料プランや Elevated 権限が必要な場合は公式ドキュメントを参照

## 6. 参考リンク

- [Twitter API 公式ドキュメント](https://developer.twitter.com/en/docs)
- [Bearer Token の取得方法](https://developer.twitter.com/en/docs/authentication/oauth-2-0/bearer-tokens)
