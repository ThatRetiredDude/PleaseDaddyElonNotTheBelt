"""Unit tests for offline analytics parsers (no GUI, no network)."""

import textwrap

import xeraser_analytics


def test_parse_tweets_js_prefix_before_array(tmp_path):
    """Comment or other text before the JSON array is found via find('[')."""
    js = textwrap.dedent(
        r"""
        window.YTD.tweets.part0 = /* not JSON yet */ [ {
        "tweet" : { "id_str" : "1", "created_at" :
        "Mon Apr 15 10:00:00 +0000 2024", "full_text" : "p", "source" : "x" } } ];
        """
    )
    p = tmp_path / "tweets.js"
    p.write_text(js, encoding="utf-8")
    out = xeraser_analytics.parse_tweets_js(str(p))
    assert len(out) == 1
    assert out[0]["id_str"] == "1"


def test_parse_tweets_js_minimal(tmp_path):
    js = textwrap.dedent(
        """
        window.YTD.tweets.part0 = [ {
        "tweet" : {
        "id_str" : "123",
        "created_at" : "Mon Apr 15 10:00:00 +0000 2024",
        "full_text" : "Hello world",
        "source" : "<a>Web App</a>",
        "retweeted" : false
        }
        } ];
        """
    )
    p = tmp_path / "tweets.js"
    p.write_text(js, encoding="utf-8")
    out = xeraser_analytics.parse_tweets_js(str(p))
    assert len(out) == 1
    t = out[0]
    assert t["id_str"] == "123"
    assert "Hello" in t["full_text"]
    assert t.get("is_retweet") is False


def test_tweets_activity_by_month():
    tweets = [
        {"created_at": "Mon Apr 15 10:00:00 +0000 2024", "id_str": "1"},
        {"created_at": "Tue May 10 10:00:00 +0000 2024", "id_str": "2"},
    ]
    m = xeraser_analytics.tweets_activity_by_month(tweets)
    assert ("2024-04", 1) in m
    assert ("2024-05", 1) in m


def test_tweets_source_stats():
    tweets = [
        {"source": '<a href="http://twitter.com">X for iPhone</a>'},
        {"source": "bad"},
    ]
    s = xeraser_analytics.tweets_source_stats(tweets)
    assert len(s) >= 1
    assert sum(c for _, c in s) == 2


def test_parse_overview_csv(tmp_path):
    csv = (
        "Date,Impressions,Engagements,Likes,Replies,Reposts,New follows,Unfollows,"
        "Bookmarks,Shares,Profile visits,Create Post,Video views,Media views\n"
        '"Fri, Apr 26, 2024",100,10,2,0,0,0,0,0,0,0,0,0,0\n'
    )
    p = tmp_path / "o.csv"
    p.write_text(csv, encoding="utf-8")
    rows = xeraser_analytics.parse_overview_csv(str(p))
    assert len(rows) == 1
    assert rows[0]["impressions"] == 100


def test_parse_content_csv(tmp_path):
    csv = (
        "Post id,Date,Post text,Post Link,Impressions,Engagements,Likes\n"
        "999,2024-04-26,Hi,https://x.com/x/status/999,50,5,1\n"
    )
    p = tmp_path / "c.csv"
    p.write_text(csv, encoding="utf-8")
    rows = xeraser_analytics.parse_content_csv(str(p))
    assert len(rows) == 1
    assert rows[0]["post_id"] == "999"
    assert rows[0]["impressions"] == 50
