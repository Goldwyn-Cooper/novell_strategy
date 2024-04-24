import os

def get_assets():
    return os.getenv('assets').split(',')

def get_periods():
    return list(map(int, os.getenv('periods').split(',')))

def get_closes(assets):
    import yfinance as yf
    return yf.download(assets, period='1y').Close

def get_scores():
    periods = get_periods()
    assets = get_assets()
    closes = get_closes(assets)
    scores = {}
    for asset in assets:
        tmp = 0
        for p in periods:
            tmp_series = closes[asset].tail(p)
            tmp += tmp_series.iloc[-1] / tmp_series.iloc[0] - 1
        scores[asset] = (tmp / len(periods)) * 100
    return scores

def get_table():
    import pandas as pd
    scores = get_scores()
    df = pd.DataFrame(scores, index=['score']).T
    df.sort_values('score', ascending=False, inplace=True)
    return df

def send_issue(title, body):
    import requests
    token = os.getenv('GH_TOKEN')
    owner = os.getenv('GH_OWNER')
    repo = os.getenv('GH_REPO')
    url = f'https://api.github.com/repos/{owner}/{repo}/issues'
    headers = dict(Authorization=f'Bearer {token}')
    data = dict(title=title, body=body)
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()

def get_kst_time(format):
    import datetime
    utc_dt = datetime.datetime.now(datetime.timezone.utc)
    kst_dt = utc_dt + datetime.timedelta(hours=9)
    return kst_dt.strftime(format)

def get_signal(df):
    BIL = df.loc['BIL', 'score']
    top3 = df.iloc[2]['score']
    handler = lambda x: '🤗' if x > BIL and x >= top3 else '🫥'
    return df['score'].apply(handler)

if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    df = get_table()
    df['signal'] = get_signal(df)
    title = f'Novell 커스텀 전략 모니터링 ({get_kst_time("%Y-%m-%d %H:%M:%S")})'
    body = df.to_markdown()
    send_issue(title, body)
