import os
from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration, ApiClient, MessagingApi, ReplyMessageRequest,
    TextMessage, FlexMessage, FlexContainer
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent

app = Flask(__name__)

# 你的專屬金鑰
CHANNEL_SECRET = os.getenv('CHANNEL_SECRET', '584092b6329a8e6891b282fb3fde05ff')
CHANNEL_ACCESS_TOKEN = os.getenv('CHANNEL_ACCESS_TOKEN', 'HkiX7oDDjyjpp7o5RPdWVeaIUOYs05AjmDwNJ6Nv5VV86qEne9qGQXRAjvbRMXMIlTIhMtKmURKHv19ZNToYhc7xaN/S3DR+JKKDhsIDhKKBt3jbqsxBDUy9tTZtX8+JfoEnb2wsXrtKAeugvllCMQdB04t89/1O/w1cDnyilFU=')

configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# 完整賽事資料庫（已完整加入 3x3 鄒子羲 與 5x5 籃球賽程）
EVENTS = [
  # --- 3x3 籃球系列 (鄒子羲) ---
  {"d": "9/21 (一)", "s": "籃球 3x3 (BK301)", "t": "12:00 - 15:20", "loc": "金城埠頭廣場", "focus": "男女分組預賽 第 1 輪 (鄒子羲領銜出擊)", "athlete": "鄒子羲 🏀 3x3搶首勝"},
  {"d": "9/22 (二)", "s": "籃球 3x3 (BK304)", "t": "17:40 - 21:00", "loc": "金城埠頭廣場", "focus": "分組預賽 第 4 輪 (夜間高張力外線對決)", "athlete": "鄒子羲 🏀 3x3火力全開"},
  {"d": "9/23 (三)", "s": "籃球 3x3 (BK305)", "t": "12:00 - 15:20", "loc": "金城埠頭廣場", "focus": "分組預賽 第 5 輪 (力拚小組第一種子晉級)", "athlete": "鄒子羲 🏀 3x3爭分組龍頭"},
  {"d": "9/24 (四)", "s": "籃球 3x3 (BK307)", "t": "12:00 - 15:20", "loc": "金城埠頭廣場", "focus": "男女資格晉級淘汰賽 (爭進八強準決席次)", "athlete": "鄒子羲 🏀 3x3晉級淘汰賽"},
  {"d": "9/25 (五)", "s": "籃球 3x3 (BK309) 🥇", "t": "13:00 - 15:30", "loc": "金城埠頭廣場", "focus": "🔥 男女四強準決賽 ＆ 金牌大決戰！", "athlete": "鄒子羲 🏀 3x3衝擊金牌戰！"},

  # --- 5x5 籃球系列 (五人制) ---
  {"d": "9/20 (日)", "s": "五人制籃球 (5x5)", "t": "13:30 - 21:00", "loc": "愛知國際競技場 (IG Arena)", "focus": "男籃/女籃 分組預賽 首戰亮相", "athlete": "中華男籃代表隊 🏀"},
  {"d": "9/22 (二)", "s": "五人制籃球 (5x5)", "t": "15:00 - 21:00", "loc": "愛知國際競技場 (IG Arena)", "focus": "男女籃分組預賽 第二戰", "athlete": "中華男籃代表隊 🏀"},
  {"d": "9/24 (四)", "s": "五人制籃球 (5x5)", "t": "13:30 - 21:00", "loc": "愛知國際競技場 (IG Arena)", "focus": "分組預賽 關鍵卡位戰", "athlete": "中華代表隊 🏀"},
  {"d": "9/26 (六)", "s": "五人制籃球 (5x5) 🥇", "t": "16:00 - 21:30", "loc": "愛知國際競技場 (IG Arena)", "focus": "🔥 亞運男籃八強/準決賽 高張力激戰", "athlete": "中華男籃主力群 🏀"},

  # --- 棒球系列 (林昱珉) ---
  {"d": "9/21 (一)", "s": "棒球 (BBL03)", "t": "18:30 - 21:30", "loc": "岡崎中央綜合公園棒球場", "focus": "🔥 台韓大戰！世仇前哨戰首戰", "athlete": "林昱珉 ⚾ 壓制韓國強打"},
  {"d": "9/22 (二)", "s": "棒球 (BBL06)", "t": "12:00 - 15:00", loc": "豐橋市民球場", "focus": "中華台北 vs 泰國 (穩抓分組戰績)", "athlete": "中華成棒隊 (林昱珉壓陣) ⚾"},
  {"d": "9/23 (三)", "s": "棒球 (BBL12)", "t": "18:30 - 21:30", "loc": "豐橋市立棒球場", "focus": "中華台北 vs 中國香港 (預賽調整最後衝刺)", "athlete": "中華成棒隊 (林昱珉備戰) ⚾"},
  {"d": "9/25 (五)", "s": "棒球 (BBL15/16)", "t": "18:30 - 21:30", "loc": "岡崎 / 豐橋", "focus": "🔥 超級循環賽 Super Round (爭金牌戰門票)", "athlete": "林昱珉 ⚾ 領銜四強主投"},
  {"d": "9/26 (六)", "s": "棒球 (BBL19/20)", "t": "18:30 - 21:30", "loc": "岡崎 / 豐橋", "focus": "🔥 超級循環賽次日 (鎖定決賽名額)", "athlete": "中華隊 (林昱珉坐鎮) ⚾"},
  {"d": "9/27 (日)", "s": "棒球 (BBL22) 🥇", "t": "18:30 - 22:30", "loc": "豐橋市立棒球場", "focus": "🔥 亞運棒球金牌大決戰 暨頒獎典禮！", "athlete": "林昱珉 ⚾ 冠軍戰王牌登板！"},

  # --- 體操系列 (李智凱) ---
  {"d": "9/24 (四)", "s": "競技體操 (GYM05) 🥇", "t": "17:00 - 21:35", "loc": "名古屋綜合體育館 (彩虹館)", "focus": "🔥 李智凱鞍馬決賽衝金日！完美落地爭金！", "athlete": "李智凱 🤸‍♂️ 鞍馬爭金"},

  # --- 柔道系列 (楊勇緯 / 連珍羚) ---
  {"d": "9/30 (三)", "s": "柔道 (JUD02) 🥇", "t": "17:00 - 19:30", "loc": "愛知國際競技場 (IG Arena)", "focus": "🔥 楊勇緯男子 60kg 金牌衛冕大決賽！", "athlete": "楊勇緯 🥋 柔道男神衝金"},
  {"d": "10/1 (四)", "s": "柔道 (JUD04) 🥇", "t": "17:00 - 19:30", "loc": "愛知國際競技場 (IG Arena)", "focus": "🔥 連珍羚女子 57kg 衛冕衝金！", "athlete": "連珍羚 🥋 柔道女王衛冕"},
  {"d": "10/3 (六)", "s": "柔道 (JUD08) 🥇", "t": "17:00 - 19:30", "loc": "愛知國際競技場 (IG Arena)", "focus": "🔥 男女混合團體金牌大決賽", "athlete": "中華柔道男女代表隊 🥋"},

  # --- 網球系列 (許育修 / 黃琮豪) ---
  {"d": "9/28 (一)", "s": "網球 (TEN02)", "t": "10:00 - 21:00", "loc": "東山公園網球中心", "focus": "男單第 2 輪 / 雙打第 1、2 輪", "athlete": "許育修 / 黃琮豪 🎾 男雙首輪"},
  {"d": "9/29 (二)", "s": "網球 (TEN03)", "t": "10:00 - 21:00", "loc": "東山公園網球中心", "focus": "男雙第 3 輪 (卡位晉級八強)", "athlete": "許育修 / 黃琮豪 🎾 金牌雙打組合"},
  {"d": "9/30 (三)", "s": "網球 (TEN04)", "t": "10:00 - 21:00", "loc": "東山公園網球中心", "focus": "雙打八強卡位戰 (爭進四強獎牌區)", "athlete": "許育修 / 黃琮豪 🎾 爭進準決賽"},
  {"d": "10/1 (四)", "s": "網球 (TEN05) 🥉", "t": "10:00 - 17:00", "loc": "東山公園網球中心", "focus": "🔥 男雙四強準決賽 (晉級保底銅牌、搶進金牌戰！)", "athlete": "許育修 / 黃琮豪 🎾 爭金牌戰門票"},
  {"d": "10/2 (五)", "s": "網球 (TEN06) 🥇", "t": "10:00 - 16:00", "loc": "東山公園網球中心", "focus": "🔥 中華網球男雙金牌大決戰 暨頒獎典禮！", "athlete": "許育修 / 黃琮豪 🎾 衛冕男雙金牌！"},
  {"d": "10/3 (六)", "s": "網球 (TEN07) 🥇", "t": "10:00 - 21:00", "loc": "東山公園網球中心", "focus": "🔥 網球壓軸日（男單/女雙/混雙三金大決賽）", "athlete": "許育修 / 黃琮豪 🎾 壓軸金牌日"},

  # --- 攀岩系列 (伍鵬) ---
  {"d": "9/29 (二)", "s": "運動攀登 (CLB01)", "t": "10:00 - 13:15", "loc": "名古屋國際展示場 1 館", "focus": "男子抱石準決賽 / 速度資格賽", "athlete": "伍鵬 🧗 速度攀登"},
  {"d": "9/30 (三)", "s": "運動攀登 (CLB02)", "t": "10:00 - 13:15", "loc": "名古屋國際展示場 1 館", "focus": "男子速度攀岩預賽", "athlete": "伍鵬 🧗 速度預賽"},
  {"d": "10/1 (四)", "s": "運動攀登 (CLB04) 🥇", "t": "18:00 - 21:05", "loc": "名古屋國際展示場 1 館", "focus": "🔥 伍鵬男子速度攀岩金牌大決戰！", "athlete": "伍鵬 🧗 4秒台飛人"},

  # --- 拳擊系列 (黃筱雯) ---
  {"d": "10/2 (五)", "s": "拳擊 (BOX20) 🥇", "t": "17:30 - 19:45", "loc": "西尾市體育館", "focus": "🔥 黃筱雯女子 54kg 金牌衝刺戰！", "athlete": "黃筱雯 🥊 拳擊衝金"},

  # --- 霹靂舞系列 (孫振 vs. Shigekix) ---
  {"d": "10/2 (五)", "s": "霹靂舞 (BKG01)", "t": "下午至晚間", "loc": "愛知 Sky Expo (常滑)", "focus": "🔥 孫振 vs. Shigekix 台日頂尖十六強資格戰！", "athlete": "孫振 vs. Shigekix 🕺 Breaking"},
  {"d": "10/3 (六)", "s": "霹靂舞 (BKG02) 🥇", "t": "晚間", "loc": "愛知 Sky Expo (常滑)", "focus": "🔥 孫振 ＆ Shigekix 終極金牌大決戰！", "athlete": "孫振 vs. Shigekix 🕺🥇 金牌大決鬥"}
]

def make_flex_bubble(item):
    map_url = f"https://www.google.com/maps/search/?api=1&query={item['loc']}"
    return {
        "type": "bubble",
        "header": {
            "type": "box", "layout": "vertical", "backgroundColor": "#1e3a8a", "paddingAll": "12px",
            "contents": [
                {"type": "text", "text": item["d"], "color": "#ffffff", "weight": "bold", "size": "xs"},
                {"type": "text", "text": item["s"], "color": "#ffffff", "weight": "bold", "size": "md", "margin": "xs"}
            ]
        },
        "body": {
            "type": "box", "layout": "vertical", "paddingAll": "12px",
            "contents": [
                {"type": "text", "text": item["athlete"], "weight": "bold", "size": "md", "color": "#2563eb"},
                {"type": "text", "text": f"🕒 {item['t']} ｜ 📍 {item['loc']}", "size": "xs", "color": "#64748b", "margin": "sm"},
                {"type": "text", "text": item["focus"], "size": "sm", "color": "#15803d", "weight": "bold", "wrap": True, "margin": "sm"}
            ]
        },
        "footer": {
            "type": "box", "layout": "vertical", "paddingAll": "10px",
            "contents": [
                {
                    "type": "button", "style": "primary", "color": "#0284c7", "height": "sm",
                    "action": {"type": "uri", "label": "📍 一鍵開啟 Google Maps 導航", "uri": map_url}
                }
            ]
        }
    }

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    raw_q = event.message.text.strip().lower()
    
    # 智慧別名對應：讓輸入「籃球」也能自動包含 3x3 與五人制
    alias_map = {
        "籃球": ["籃球", "3x3", "鄒子羲"],
        "3x3": ["3x3", "鄒子羲"],
        "棒球": ["棒球", "林昱珉"],
        "霹靂舞": ["霹靂舞", "breaking", "孫振", "shigekix"],
        "柔道": ["柔道", "楊勇緯", "連珍羚"],
        "網球": ["網球", "許育修", "黃琮豪"]
    }
    search_keywords = alias_map.get(raw_q, [raw_q])

    matches = []
    for e in EVENTS:
        combined_text = (e["s"] + e["athlete"] + e["d"] + e["loc"] + e["focus"]).lower()
        if any(k in combined_text for k in search_keywords):
            matches.append(e)

    with ApiClient(configuration) as api_client:
        bot = MessagingApi(api_client)
        if matches:
            bubbles = [make_flex_bubble(m) for m in matches[:10]] # 支援最多 10 筆賽程輪播滑動
            flex_payload = {"type": "carousel", "contents": bubbles} if len(bubbles) > 1 else bubbles[0]
            bot.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[FlexMessage(alt_text="亞運賽程速查結果", contents=FlexContainer.from_dict(flex_payload))]
                )
            )
        else:
            bot.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text="查無此賽程！\n試試輸入：籃球、鄒子羲、林昱珉、棒球、孫振、楊勇緯、9/25，或點擊下方選單開啟完整 App。")]
                )
            )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
