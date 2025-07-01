import pytest
from batches import tweet_monitor_batch

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