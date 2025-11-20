import requests
import os
import sys

WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY")
WEATHER_CITY = os.environ.get("WEATHER_CITY","Ishioka,JP")

SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
SLACK_CHANNEL = ("#お天気情報")

if not WEATHER_API_KEY:
    print("WEATHER_API_KEYが設定されていません")
    sys.exit(1)

if not SLACK_BOT_TOKEN:
    print("SLACK_BOT_TOKENが設定されていません")
    sys.exit(1)

def send_to_discord(webhook_url,message):
    payload = {"content": message}
    r = requests.post(webhook_url, json=payload)
    r.raise_for_status()

def send_to_slack(message):
    url = "https://slack.com/api/chat.postMessage"
    headers = { 
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
        "Content-type": "application/json"
        }
    data = {
        "channel": SLACK_CHANNEL,
        "text": message
    }
    payload = {"channel": SLACK_CHANNEL, "text":message}
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=10)
    except requests.RequestException as e:
        print("Slack送信で例外", e)
        return False
    
    try:
        resp = r.json()
    except ValueError:
        print("SlackからJSONが返ってこない。ステータス:", r.status_code, "本文:", r.text)
        return False
    
    if not resp.get("ok"):
        print("Slack APIエラー", resp)
        return False
    return True

def fetch_weather():
    weather_url = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?q={WEATHER_CITY}&appid={WEATHER_API_KEY}&lang=ja&units=metric"
    )
    try:
        r = requests.get(weather_url, timeout=10)
        r.raise_for_status()
    except requests.RequestException as e:
        print("天気取得で例外:",e)
        return None
    
    try:
        return r.json()
    except ValueError:
        print("天気APIのレスポンスがJSONではありません")
        return None
    
def build_message(data):
    try:
        weather = data["weather"][0]["description"] # 天気
        temp_max = data["main"]["temp_max"] # 最高気温
        temp_min = data["main"]["temp_min"] # 最低気温
        city_name = data.get("name",WEATHER_CITY) # 都市の名前
    except (KeyError,TypeError):
        return None
    
    return (
        f"{city_name}の今日の天気:{weather}\n"
        f"最高気温:{temp_max}℃\n"
        f"最低気温:{temp_min}℃"
    )

def main():
    data = fetch_weather()
    if not data:
        print("天気データ取得失敗。終了します。")
        return
    
    message = build_message(data)
    if not message:
        print("メッセージの作成に失敗しました。終了します。")
        return
    # Discord送信
    if DISCORD_WEBHOOK_URL:
        try:
            send_to_discord(DISCORD_WEBHOOK_URL,message)
            print("Discordに送信しました。")
        except Exception as e:
            print("Discord送信でエラー", e)
    else:
        print("DISCORD_WEBHOOL_URLが設定されていません。")
    
    # Slack送信
    ok = send_to_slack(message)
    if ok:
        print("Slackに送信しました。")
    else:
        print("Slack送信失敗。ログを確認してください。")
if __name__ == "__main__":
    main()
