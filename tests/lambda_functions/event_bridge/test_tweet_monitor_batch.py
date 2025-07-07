from lambda_functions.event_bridge import tweet_monitor_batch

class MockTweet:
    def __init__(self, id, like, retweet):
        self.id = id
        self.public_metrics = {'like_count': like, 'retweet_count': retweet}

def test_filter_tweets_by_thresholds():
    tweets = [
        MockTweet('1', 5, 2),   # 閾値未満
        MockTweet('2', 10, 5),  # ちょうど閾値
        MockTweet('3', 20, 10), # 閾値超え
    ]
    like_th = 10
    rt_th = 5
    filtered = tweet_monitor_batch.filter_tweets_by_thresholds(tweets, like_th, rt_th)
    ids = [t.id for t in filtered]
    assert '2' in ids
    assert '3' in ids
    assert '1' not in ids

    # like_threshold=None（like数は無視、retweetのみ判定）
    filtered2 = tweet_monitor_batch.filter_tweets_by_thresholds(tweets, None, 5)
    ids2 = [t.id for t in filtered2]
    assert '2' in ids2
    assert '3' in ids2
    assert '1' not in ids2

    # retweet_threshold=None（retweet数は無視、likeのみ判定）
    filtered3 = tweet_monitor_batch.filter_tweets_by_thresholds(tweets, 10, None)
    ids3 = [t.id for t in filtered3]
    assert '2' in ids3
    assert '3' in ids3
    assert '1' not in ids3

    # 両方None（全件通過）
    filtered4 = tweet_monitor_batch.filter_tweets_by_thresholds(tweets, None, None)
    ids4 = [t.id for t in filtered4]
    assert set(ids4) == {'1', '2', '3'}
