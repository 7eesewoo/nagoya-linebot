import os
import urllib.parse
from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration, ApiClient, MessagingApi, ReplyMessageRequest,
    TextMessage, FlexMessage, FlexContainer
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent

app = Flask(__name__)

# LINE 憑證金鑰
CHANNEL_SECRET = os.getenv('CHANNEL_SECRET', '584092b6329a8e6891b282fb3fde05ff')
CHANNEL_ACCESS_TOKEN = os.getenv('CHANNEL_ACCESS_TOKEN', 'HkiX7oDDjyjpp7o5RPdWVeaIUOYs05AjmDwNJ6Nv5VV86qEne9qGQXRAjvbRMXMIlTIhMtKmURKHv19ZNToYhc7xaN/S3DR+JKKDhsIDhKKBt3jbqsxBDUy9tTZtX8+JfoEnb2wsXrtKAeugvllCMQdB04t89/1O/w1cDnyilFU=')

configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# 完整賽事資料庫（卡片皆以代表隊呈現，不顯示選手人名）
EVENTS = [
  # --- 五人制男籃 (5x5) ---
  {"d": "9/10 (四)", "s": "五人制男籃 (5x5)", "t": "13:00 - 15:00", "loc": "愛知國際競技場", "sub": "中華男籃代表隊 🏀", "focus": "分組預賽 G1：中華男籃 vs. 約旦"},
  {"d": "9/12 (六)", "s": "五人制男籃 (5x5)", "t": "10:00 - 12:00", "loc": "愛知國際競技場", "sub": "中華男籃代表隊 🏀", "focus": "分組預賽 G2：中華男籃 vs. 伊朗"},
  {"d": "9/13 (日)", "s": "五人制男籃 (5x5)", "t": "13:00 - 15:00", "loc": "愛知國際競技場", "sub": "中華男籃代表隊 🏀", "focus": "分組預賽 G3：中華男籃 vs. 卡達 (搶八強門票)"},
  {"d": "9/16 (三)", "s": "五人制男籃 (5x5)", "t": "19:20 - 21:30", "loc": "愛知國際競技場", "sub": "中華男籃代表隊 🏀", "focus": "🔥 男籃八強生死戰：中華台北 vs. 地主日本隊！"},
  {"d": "9/18 (五)", "s": "五人制男籃 (5x5)", "t": "19:20 - 21:30", "loc": "愛知國際競技場", "sub": "中華男籃代表隊 🏀", "focus": "🔥 男籃四強準決賽：爭奪金牌戰門票！"},
  {"d": "9/20 (日)", "s": "五人制男籃 (5x5) 🥉", "t": "16:40 - 18:40", "loc": "愛知國際競技場", "sub": "中華男籃代表隊 🏀", "focus": "🔥 男籃季軍銅牌戰"},
  {"d": "9/20 (日)", "s": "五人制男籃 (5x5) 🥇", "t": "19:40 - 21:40", "loc": "愛知國際競技場", "sub": "中華男籃代表隊 🏀", "focus": "🔥 亞運男籃金牌大決戰 暨頒獎典禮！"},

  # --- 三人制男籃 (3x3) ---
  {"d": "9/21 (一)", "s": "籃球 3x3 (BK301)", "t": "12:00 - 15:20", "loc": "金城埠頭廣場", "sub": "中華 3x3 男籃 🏀", "focus": "男籃分組預賽 第 1 輪 (搶首勝)"},
  {"d": "9/22 (二)", "s": "籃球 3x3 (BK304)", "t": "17:40 - 21:00", "loc": "金城埠頭廣場", "sub": "中華 3x3 男籃 🏀", "focus": "男籃分組預賽 第 4 輪 (夜戰外線火力對決)"},
  {"d": "9/23 (三)", "s": "籃球 3x3 (BK305)", "t": "12:00 - 15:20", "loc": "金城埠頭廣場", "sub": "中華 3x3 男籃 🏀", "focus": "男籃分組預賽 第 5 輪 (力拚小組第一種子)"},
  {"d": "9/24 (四)", "s": "籃球 3x3 (BK307)", "t": "12:00 - 15:20", "loc": "金城埠頭廣場", "sub": "中華 3x3 男籃 🏀", "focus": "男籃八強資格淘汰賽 (爭四強席次)"},
  {"d": "9/25 (五)", "s": "籃球 3x3 (BK309) 🥇", "t": "13:00 - 15:30", "loc": "金城埠頭廣場", "sub": "中華 3x3 男籃 🏀", "focus": "🔥 3x3 男籃四強準決賽 ＆ 金牌大決戰！"},

  # --- 棒球 ---
  {"d": "9/21 (一)", "s": "棒球 (BBL03)", "t": "18:30 - 21:30", "loc": "岡崎中央綜合公園棒球場", "sub": "中華成棒代表隊 ⚾", "focus": "🔥 台韓大戰！世仇前哨戰首戰"},
  {"d": "9/22 (二)", "s": "棒球 (BBL06)", "t": "12:00 - 15:00", "loc": "豐橋市民球場", "sub": "中華成棒代表隊 ⚾", "focus": "中華台北 vs. 泰國 (分組循環賽)"},
  {"d": "9/23 (三)", "s": "棒球 (BBL12)", "t": "18:30 - 21:30", "loc": "豐橋市立棒球場", "sub": "中華成棒代表隊 ⚾", "focus": "中華台北 vs. 中國香港 (預賽調整衝刺)"},
  {"d": "9/25 (五)", "s": "棒球 (BBL15/16)", "t": "18:30 - 21:30", "loc": "岡崎中央綜合公園棒球場", "sub": "中華成棒代表隊 ⚾", "focus": "🔥 超級循環賽 Super Round (爭金牌戰門票)"},
  {"d": "9/26 (六)", "s": "棒球 (BBL19/20)", "t": "18:30 - 21:30", "loc": "豐橋市立棒球場", "sub": "中華成棒代表隊 ⚾", "focus": "🔥 超級循環賽次日 (鎖定決賽名額)"},
  {"d": "9/27 (日)", "s": "棒球 (BBL22) 🥇", "t": "18:30 - 22:30", "loc": "豐橋市立棒球場", "sub": "中華成棒代表隊 ⚾", "focus": "🔥 亞運棒球金牌大決戰 暨頒獎典禮！"},

  # --- 競技體操 (李智凱 鞍馬決賽 + 唐嘉鴻 單槓決賽) ---
  {"d": "9/24 (四)", "s": "競技體操 (鞍馬決賽) 🥇", "t": "17:00 - 21:35", "loc": "名古屋市綜合體育館【彩虹館】", "sub": "中華競技體操代表隊 🤸‍♂️", "focus": "🔥 男子鞍馬個人單項金牌大決賽！"},
  {"d": "9/25 (五)", "s": "競技體操 (單槓決賽) 🥇", "t": "15:00 - 19:35", "loc": "名古屋市綜合體育館【彩虹館】", "sub": "中華競技體操代表隊 🤸‍♂️", "focus": "🔥 男子單槓個人單項金牌大決賽！(門票 15,000 日圓)"},

  # --- 柔道 ---
  {"d": "9/30 (三)", "s": "柔道 (JUD02) 🥇", "t": "17:00 - 19:30", "loc": "愛知國際競技場", "sub": "中華柔道代表隊 🥋", "focus": "🔥 男子 60kg 級金牌衛冕大決賽！"},
  {"d": "10/1 (四)", "s": "柔道 (JUD04) 🥇", "t": "17:00 - 19:30", "loc": "愛知國際競技場", "sub": "中華柔道代表隊 🥋", "focus": "🔥 女子 57kg 級金牌衛冕大決賽！"},
  {"d": "10/3 (六)", "s": "柔道 (JUD08) 🥇", "t": "17:00 - 19:30", "loc": "愛知國際競技場", "sub": "中華柔道代表隊 🥋", "focus": "🔥 男女混合團體金牌大決賽"},

  # --- 網球 ---
  {"d": "9/28 (一)", "s": "網球 (TEN02)", "t": "10:00 - 21:00", "loc": "東山公園網球中心", "sub": "中華網球代表隊 🎾", "focus": "男單第 2 輪 / 雙打第 1、2 輪"},
  {"d": "9/29 (二)", "s": "網球 (TEN03)", "t": "10:00 - 21:00", "loc": "東山公園網球中心", "sub": "中華網球代表隊 🎾", "focus": "男雙第 3 輪 (卡位晉級八強)"},
  {"d": "9/30 (三)", "s": "網球 (TEN04)", "t": "10:00 - 21:00", "loc": "東山公園網球中心", "sub": "中華網球代表隊 🎾", "focus": "雙打八強卡位戰 (爭進四強獎牌區)"},
  {"d": "10/1 (四)", "s": "網球 (TEN05) 🥉", "t": "10:00 - 17:00", "loc": "東山公園網球中心", "sub": "中華網球代表隊 🎾", "focus": "🔥 男雙四強準決賽 (晉級保底銅牌、搶進金牌戰！)"},
  {"d": "10/2 (五)", "s": "網球 (TEN06) 🥇", "t": "10:00 - 16:00", "loc": "東山公園網球中心", "sub": "中華網球代表隊 🎾", "focus": "🔥 中華男雙金牌大決戰 暨頒獎典禮！"},
  {"d": "10/3 (六)", "s": "網球 (TEN07) 🥇", "t": "10:00 - 21:00", "loc": "東山公園網球中心", "sub": "中華網球代表隊 🎾", "focus": "🔥 網球壓軸日（男單/女雙/混雙三金大決賽）"},

  # --- 運動攀登 ---
  {"d": "9/29 (二)", "s": "運動攀登 (CLB01)", "t": "10:00 - 13:15", "loc": "名古屋國際展示場", "sub": "中華攀登代表隊 🧗", "focus": "男子抱石準決賽 / 速度資格賽"},
  {"d": "9/30 (三)", "s": "運動攀登 (CLB02)", "t": "10:00 - 13:15", "loc": "名古屋國際展示場", "sub": "中華攀登代表隊 🧗", "focus": "男子速度攀岩預賽"},
  {"d": "10/1 (四)", "s": "運動攀登 (CLB04) 🥇", "t": "18:00 - 21:05", "loc": "名古屋國際展示場", "sub": "中華攀登代表隊 🧗", "focus": "🔥 男子速度攀登金牌大決戰！"},

  # --- 拳擊 ---
  {"d": "10/2 (五)", "s": "拳擊 (BOX20) 🥇", "t": "17:30 - 19:45", "loc": "西尾市體育館", "sub": "中華拳擊代表隊 🥊", "focus": "🔥 女子 54kg 級金牌衝刺戰！"},

  # --- 霹靂舞 ---
  {"d": "10/2 (五)", "s": "霹靂舞 (BKG01)", "t": "下午至晚間", "loc": "Aichi Sky Expo", "sub": "中華霹靂舞代表隊 🕺", "focus": "🔥 頂尖十六強小組資格循環戰！"},
  {"d": "10/3 (六)", "s": "霹靂舞 (BKG02) 🥇", "t": "晚間", "loc": "Aichi Sky Expo", "sub": "中華霹靂舞代表隊 🕺", "focus": "🔥 終極八強淘汰賽 ＆ 金牌大決戰！"}
]

def make_flex_bubble(item):
    encoded_loc = urllib.parse.quote(item['loc'])
    map_url = f"https://www.google.com/maps/search/?api=1&query={encoded_loc}"
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
                {"type": "text", "text": item["sub"], "weight": "bold", "size": "md", "color": "#2563eb"},
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

    # 1. 棒球 24 位選手清單
    baseball_players = [
        "劉致榮", "徐翔聖", "陽柏翔", "王彥程", "黃玠瀚", "林昱珉", 
        "潘文輝", "郭子銓", "林佾葳", "王宇傑", "王政浩", "蔡瑋泰", 
        "張翔", "陳敏賜", "高育瑋", "李亦崴", "黃韋盛", "游宗儒", 
        "林雨力", "劉基鴻", "陳晨威", "朱迦恩", "楊振裕", "陳孝允"
    ]
    
    # 2. 三人籃球選手清單
    three_x_three_players = ["鄒子羲", "葉惟捷", "張俊生", "徐堂琪", "3x3", "三人籃球", "3對3"]

    # 3. 五人制男籃選手清單
    five_x_five_players = [
        "陳盈駿", "林庭謙", "游艾喆", "陳冠全", "譚傑龍", 
        "盧峻翔", "李家慷", "雷蒙恩", "馬建豪", "胡瓏貿", 
        "高柏鎧", "曾祥鈞", "男籃", "5x5", "五人制男籃", "五人籃球"
    ]

    target_category = None
    if any(p.lower() in raw_q for p in baseball_players) or raw_q in ["棒球", "baseball"]:
        target_category = "baseball"
    elif any(p.lower() in raw_q for p in three_x_three_players):
        target_category = "3x3"
    elif any(p.lower() in raw_q for p in five_x_five_players):
        target_category = "5x5"
    elif raw_q in ["籃球", "basketball"]:
        target_category = "all_basketball"

    matches = []
    if target_category == "baseball":
        matches = [e for e in EVENTS if "棒球" in e["s"]]
    elif target_category == "3x3":
        matches = [e for e in EVENTS if "3x3" in e["s"]]
    elif target_category == "5x5":
        matches = [e for e in EVENTS if "五人制男籃" in e["s"]]
    elif target_category == "all_basketball":
        matches = [e for e in EVENTS if ("3x3" in e["s"] or "五人制男籃" in e["s"])]
    
    # 體操個別選手精確篩選
    elif any(k in raw_q for k in ["李智凱", "鞍馬"]):
        matches = [e for e in EVENTS if "鞍馬" in e["s"]]
    elif any(k in raw_q for k in ["唐嘉鴻", "單槓"]):
        matches = [e for e in EVENTS if "單槓" in e["s"]]
    elif "體操" in raw_q:
        matches = [e for e in EVENTS if "競技體操" in e["s"]]

    # 其他項目查詢
    else:
        alias_map = {
            "柔道": ["柔道", "楊勇緯", "連珍羚"],
            "網球": ["網球", "許育修", "黃琮豪"],
            "攀岩": ["攀岩", "運動攀登", "伍鵬"],
            "拳擊": ["拳擊", "黃筱雯"],
            "霹靂舞": ["霹靂舞", "breaking", "孫振", "shigekix"]
        }
        matched_cat = None
        for cat, kws in alias_map.items():
            if any(k in raw_q for k in kws):
                matched_cat = cat
                break
        
        if matched_cat:
            matches = [e for e in EVENTS if matched_cat in e["s"]]
        else:
            # 日期或場館字串模糊查詢
            for e in EVENTS:
                combined_text = (e["s"] + e["d"] + e["loc"] + e["focus"] + e["sub"]).lower()
                if raw_q in combined_text:
                    matches.append(e)

    with ApiClient(configuration) as api_client:
        bot = MessagingApi(api_client)
        if matches:
            bubbles = [make_flex_bubble(m) for m in matches[:10]]
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
                    messages=[TextMessage(text="查無此賽程！\n試試輸入：李智凱、唐嘉鴻、陳晨威、陳盈駿、鄒子羲、體操、棒球、男籃，或點選下方選單開啟完整 App。")]
                )
            )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
