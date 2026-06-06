import os
from dotenv import load_dotenv
load_dotenv()

# ── Telegram ──────────────────────────────────────────────
BOT_TOKEN  = os.getenv("BOT_TOKEN",  "8165503899:AAGlY0wz8vMqtWftiOXIDPTh95Gppk06FPs")
ADMIN_ID   = int(os.getenv("ADMIN_ID", "6673616910"))
BOT_USER   = "frozenld_bot"
ADMIN_USER = "frozenld1"

# ── Buypin ────────────────────────────────────────────────
BUYPIN_KEY = os.getenv("BUYPIN_KEY", "")
BUYPIN_URL = "https://buypin.net/api/v1"

# ── Server ────────────────────────────────────────────────
PORT    = int(os.getenv("PORT", "8000"))
SECRET  = os.getenv("SECRET", "frozen2006")

# ── Payment cards ─────────────────────────────────────────
CARDS = {
    "3359": "9860 1606 3787 3359",  # HUMO
    "3951": "9860 3501 4482 3951",  # HUMO
    "7849": "8600 **** **** 7849",  # UzCard
}

# ── Buypin game keys ──────────────────────────────────────
GAME_KEYS = {
    "mlbb":    "mobile-legends-ru",
    "genshin": "genshin-impact",
    "hsr":     "honkai-star-rail",
    "zzz":     "zenless-zone-zero",
    "pubg":    "pubg-mobile",
    "ff":      "free-fire",
    "hok":     "honor-of-kings",
    "s2":      "standoff-2",
}

# Manual fulfillment games (no Buypin auto-delivery)
MANUAL_GAMES = {"roblox", "brawl", "steam", "tgprem", "jutsu"}

# ── Game display ──────────────────────────────────────────
GAME_NAMES = {
    "mlbb": "Mobile Legends", "genshin": "Genshin Impact",
    "hsr": "Honkai: Star Rail", "zzz": "Zenless Zone Zero",
    "pubg": "PUBG Mobile", "ff": "Free Fire",
    "hok": "Honor of Kings", "s2": "Standoff 2",
    "roblox": "Roblox", "brawl": "Brawl Stars",
    "tgprem": "Telegram Premium", "steam": "Steam", "jutsu": "Jutsu+",
}

GAME_EMOJI = {
    "mlbb": "⚔️", "genshin": "🌸", "hsr": "🚂", "zzz": "⚡",
    "pubg": "🎯", "ff": "🔥", "hok": "👑", "s2": "🗡️",
    "roblox": "🎮", "brawl": "💥", "tgprem": "⭐",
    "steam": "🎮", "jutsu": "🎌",
}

# ── MLBB diamond combinations ─────────────────────────────
MLBB_COMBOS = {
    11:[11],22:[22],55:[55],56:[56],86:[86],
    110:[55,55],112:[56,56],165:[165],172:[172],
    224:[112,112],257:[257],275:[275],312:[257,55],330:[275,55],
    343:[257,86],385:[275,55,55],429:[257,172],514:[257,257],
    565:[565],620:[565,55],706:[706],792:[706,86],816:[706,55,55],
    878:[706,172],963:[706,257],981:[706,275],1018:[706,257,55],
    1036:[706,275,55],1135:[706,257,172],1185:[565,565,55],
    1216:[565,565,86],1271:[706,565],1302:[565,565,172],
    1387:[565,565,257],1405:[565,565,275],1412:[706,706],
    1498:[706,706,86],1584:[706,706,172],1687:[706,706,275],
    1977:[706,706,565],2195:[2195],2281:[2195,86],2367:[2195,172],
    2470:[2195,275],2760:[2195,565],2846:[2195,565,86],
    2932:[2195,565,172],3035:[2195,565,275],3325:[2195,565,565],
    3466:[2195,565,706],3688:[3688],3860:[3688,172],3963:[3688,275],
    4253:[3688,565],4394:[3688,706],4425:[3688,565,172],
    4528:[3688,565,275],4566:[3688,706,172],4669:[3688,706,275],
    4818:[3688,565,565],4959:[3688,706,565],5100:[3688,706,706],
    5532:[5532],9288:[9288],
}

# ── All products ──────────────────────────────────────────
PRODUCTS = {
  "mlbb": [
    {
      "id": "m01",
      "cat": "diamonds",
      "name": "11 💎",
      "amt": 11,
      "price": 2500,
      "tag": null,
      "desc": null
    },
    {
      "id": "m02",
      "cat": "diamonds",
      "name": "22 💎",
      "amt": 22,
      "price": 5000,
      "tag": null,
      "desc": null
    },
    {
      "id": "m03",
      "cat": "diamonds",
      "name": "55 💎",
      "amt": 55,
      "price": 13000,
      "tag": null,
      "desc": null
    },
    {
      "id": "m04",
      "cat": "diamonds",
      "name": "56 💎",
      "amt": 56,
      "price": 13500,
      "tag": null,
      "desc": null
    },
    {
      "id": "m05",
      "cat": "diamonds",
      "name": "86 💎",
      "amt": 86,
      "price": 17500,
      "tag": null,
      "desc": null
    },
    {
      "id": "m06",
      "cat": "diamonds",
      "name": "110 💎",
      "amt": 110,
      "price": 27000,
      "tag": null,
      "desc": null
    },
    {
      "id": "m07",
      "cat": "diamonds",
      "name": "112 💎",
      "amt": 112,
      "price": 27500,
      "tag": null,
      "desc": null
    },
    {
      "id": "m08",
      "cat": "diamonds",
      "name": "165 💎",
      "amt": 165,
      "price": 35000,
      "tag": null,
      "desc": null
    },
    {
      "id": "m09",
      "cat": "diamonds",
      "name": "172 💎",
      "amt": 172,
      "price": 37000,
      "tag": null,
      "desc": null
    },
    {
      "id": "m10",
      "cat": "diamonds",
      "name": "224 💎",
      "amt": 224,
      "price": 48000,
      "tag": null,
      "desc": null
    },
    {
      "id": "m11",
      "cat": "diamonds",
      "name": "257 💎",
      "amt": 257,
      "price": 50000,
      "tag": null,
      "desc": null
    },
    {
      "id": "m12",
      "cat": "diamonds",
      "name": "275 💎",
      "amt": 275,
      "price": 54000,
      "tag": null,
      "desc": null
    },
    {
      "id": "m13",
      "cat": "diamonds",
      "name": "312 💎",
      "amt": 312,
      "price": 61000,
      "tag": null,
      "desc": null
    },
    {
      "id": "m14",
      "cat": "diamonds",
      "name": "330 💎",
      "amt": 330,
      "price": 64500,
      "tag": null,
      "desc": null
    },
    {
      "id": "m15",
      "cat": "diamonds",
      "name": "343 💎",
      "amt": 343,
      "price": 67000,
      "tag": null,
      "desc": null
    },
    {
      "id": "m16",
      "cat": "diamonds",
      "name": "385 💎",
      "amt": 385,
      "price": 75000,
      "tag": null,
      "desc": null
    },
    {
      "id": "m17",
      "cat": "diamonds",
      "name": "429 💎",
      "amt": 429,
      "price": 84000,
      "tag": null,
      "desc": null
    },
    {
      "id": "m18",
      "cat": "diamonds",
      "name": "514 💎",
      "amt": 514,
      "price": 98000,
      "tag": null,
      "desc": null
    },
    {
      "id": "m19",
      "cat": "diamonds",
      "name": "565 💎",
      "amt": 565,
      "price": 108000,
      "tag": null,
      "desc": null
    },
    {
      "id": "m20",
      "cat": "diamonds",
      "name": "620 💎",
      "amt": 620,
      "price": 120000,
      "tag": null,
      "desc": null
    },
    {
      "id": "m21",
      "cat": "diamonds",
      "name": "706 💎",
      "amt": 706,
      "price": 135000,
      "tag": null,
      "desc": null
    },
    {
      "id": "m22",
      "cat": "diamonds",
      "name": "792 💎",
      "amt": 792,
      "price": 150000,
      "tag": null,
      "desc": null
    },
    {
      "id": "m23",
      "cat": "diamonds",
      "name": "816 💎",
      "amt": 816,
      "price": 155000,
      "tag": null,
      "desc": null
    },
    {
      "id": "m24",
      "cat": "diamonds",
      "name": "878 💎",
      "amt": 878,
      "price": 170000,
      "tag": null,
      "desc": null
    },
    {
      "id": "m25",
      "cat": "diamonds",
      "name": "963 💎",
      "amt": 963,
      "price": 185000,
      "tag": null,
      "desc": null
    },
    {
      "id": "m26",
      "cat": "diamonds",
      "name": "981 💎",
      "amt": 981,
      "price": 190000,
      "tag": null,
      "desc": null
    },
    {
      "id": "m27",
      "cat": "diamonds",
      "name": "1018 💎",
      "amt": 1018,
      "price": 195000,
      "tag": null,
      "desc": null
    },
    {
      "id": "m28",
      "cat": "diamonds",
      "name": "1036 💎",
      "amt": 1036,
      "price": 200000,
      "tag": null,
      "desc": null
    },
    {
      "id": "m29",
      "cat": "diamonds",
      "name": "1135 💎",
      "amt": 1135,
      "price": 215000,
      "tag": null,
      "desc": null
    },
    {
      "id": "m30",
      "cat": "diamonds",
      "name": "1185 💎",
      "amt": 1185,
      "price": 225000,
      "tag": null,
      "desc": null
    },
    {
      "id": "m31",
      "cat": "diamonds",
      "name": "1216 💎",
      "amt": 1216,
      "price": 230000,
      "tag": null,
      "desc": null
    },
    {
      "id": "m32",
      "cat": "diamonds",
      "name": "1271 💎",
      "amt": 1271,
      "price": 240000,
      "tag": null,
      "desc": null
    },
    {
      "id": "m33",
      "cat": "diamonds",
      "name": "1302 💎",
      "amt": 1302,
      "price": 250000,
      "tag": null,
      "desc": null
    },
    {
      "id": "m34",
      "cat": "diamonds",
      "name": "1387 💎",
      "amt": 1387,
      "price": 265000,
      "tag": null,
      "desc": null
    },
    {
      "id": "m35",
      "cat": "diamonds",
      "name": "1405 💎",
      "amt": 1405,
      "price": 270000,
      "tag": null,
      "desc": null
    },
    {
      "id": "m36",
      "cat": "diamonds",
      "name": "1412 💎",
      "amt": 1412,
      "price": 275000,
      "tag": null,
      "desc": null
    },
    {
      "id": "m37",
      "cat": "diamonds",
      "name": "1498 💎",
      "amt": 1498,
      "price": 285000,
      "tag": null,
      "desc": null
    },
    {
      "id": "m38",
      "cat": "diamonds",
      "name": "1584 💎",
      "amt": 1584,
      "price": 300000,
      "tag": null,
      "desc": null
    },
    {
      "id": "m39",
      "cat": "diamonds",
      "name": "1687 💎",
      "amt": 1687,
      "price": 320000,
      "tag": null,
      "desc": null
    },
    {
      "id": "m40",
      "cat": "diamonds",
      "name": "1977 💎",
      "amt": 1977,
      "price": 390000,
      "tag": null,
      "desc": null
    },
    {
      "id": "m41",
      "cat": "diamonds",
      "name": "2195 💎",
      "amt": 2195,
      "price": 400000,
      "tag": null,
      "desc": null
    },
    {
      "id": "m42",
      "cat": "diamonds",
      "name": "2281 💎",
      "amt": 2281,
      "price": 420000,
      "tag": null,
      "desc": null
    },
    {
      "id": "m43",
      "cat": "diamonds",
      "name": "2367 💎",
      "amt": 2367,
      "price": 440000,
      "tag": null,
      "desc": null
    },
    {
      "id": "m44",
      "cat": "diamonds",
      "name": "2470 💎",
      "amt": 2470,
      "price": 455000,
      "tag": null,
      "desc": null
    },
    {
      "id": "m45",
      "cat": "diamonds",
      "name": "2760 💎",
      "amt": 2760,
      "price": 510000,
      "tag": null,
      "desc": null
    },
    {
      "id": "m46",
      "cat": "diamonds",
      "name": "2846 💎",
      "amt": 2846,
      "price": 525000,
      "tag": null,
      "desc": null
    },
    {
      "id": "m47",
      "cat": "diamonds",
      "name": "2932 💎",
      "amt": 2932,
      "price": 550000,
      "tag": null,
      "desc": null
    },
    {
      "id": "m48",
      "cat": "diamonds",
      "name": "3035 💎",
      "amt": 3035,
      "price": 575000,
      "tag": null,
      "desc": null
    },
    {
      "id": "m49",
      "cat": "diamonds",
      "name": "3325 💎",
      "amt": 3325,
      "price": 620000,
      "tag": null,
      "desc": null
    },
    {
      "id": "m50",
      "cat": "diamonds",
      "name": "3466 💎",
      "amt": 3466,
      "price": 635000,
      "tag": null,
      "desc": null
    },
    {
      "id": "m51",
      "cat": "diamonds",
      "name": "3688 💎",
      "amt": 3688,
      "price": 640000,
      "tag": null,
      "desc": null
    },
    {
      "id": "m52",
      "cat": "diamonds",
      "name": "3860 💎",
      "amt": 3860,
      "price": 655000,
      "tag": null,
      "desc": null
    },
    {
      "id": "m53",
      "cat": "diamonds",
      "name": "3963 💎",
      "amt": 3963,
      "price": 675000,
      "tag": null,
      "desc": null
    },
    {
      "id": "m54",
      "cat": "diamonds",
      "name": "4253 💎",
      "amt": 4253,
      "price": 730000,
      "tag": null,
      "desc": null
    },
    {
      "id": "m55",
      "cat": "diamonds",
      "name": "4394 💎",
      "amt": 4394,
      "price": 765000,
      "tag": null,
      "desc": null
    },
    {
      "id": "m56",
      "cat": "diamonds",
      "name": "4425 💎",
      "amt": 4425,
      "price": 775000,
      "tag": null,
      "desc": null
    },
    {
      "id": "m57",
      "cat": "diamonds",
      "name": "4528 💎",
      "amt": 4528,
      "price": 790000,
      "tag": null,
      "desc": null
    },
    {
      "id": "m58",
      "cat": "diamonds",
      "name": "4566 💎",
      "amt": 4566,
      "price": 810000,
      "tag": null,
      "desc": null
    },
    {
      "id": "m59",
      "cat": "diamonds",
      "name": "4669 💎",
      "amt": 4669,
      "price": 825000,
      "tag": null,
      "desc": null
    },
    {
      "id": "m60",
      "cat": "diamonds",
      "name": "4818 💎",
      "amt": 4818,
      "price": 850000,
      "tag": null,
      "desc": null
    },
    {
      "id": "m61",
      "cat": "diamonds",
      "name": "4959 💎",
      "amt": 4959,
      "price": 880000,
      "tag": null,
      "desc": null
    },
    {
      "id": "m62",
      "cat": "diamonds",
      "name": "5100 💎",
      "amt": 5100,
      "price": 910000,
      "tag": null,
      "desc": null
    },
    {
      "id": "m63",
      "cat": "diamonds",
      "name": "5532 💎",
      "amt": 5532,
      "price": 950000,
      "tag": null,
      "desc": null
    },
    {
      "id": "m64",
      "cat": "diamonds",
      "name": "9288 💎",
      "amt": 9288,
      "price": 1590000,
      "tag": null,
      "desc": null
    },
    {
      "id": "md1",
      "cat": "double",
      "name": "50+50 💎",
      "amt": null,
      "price": 12000,
      "tag": "dbl",
      "desc": "Двойные алмазы"
    },
    {
      "id": "md2",
      "cat": "double",
      "name": "150+150 💎",
      "amt": null,
      "price": 34000,
      "tag": "dbl",
      "desc": "Двойные алмазы"
    },
    {
      "id": "md3",
      "cat": "double",
      "name": "250+250 💎",
      "amt": null,
      "price": 53000,
      "tag": "dbl",
      "desc": "Двойные алмазы"
    },
    {
      "id": "md4",
      "cat": "double",
      "name": "500+500 💎",
      "amt": null,
      "price": 108000,
      "tag": "dbl",
      "desc": "Двойные алмазы"
    },
    {
      "id": "mp1",
      "cat": "pass",
      "name": "Недельник",
      "amt": null,
      "price": 20000,
      "tag": "pass",
      "desc": "Weekly Diamond Pass"
    },
    {
      "id": "mp2",
      "cat": "pass",
      "name": "Сумеречный",
      "amt": null,
      "price": 110000,
      "tag": "pass",
      "desc": "Twilight Pass"
    },
    {
      "id": "mp3",
      "cat": "pass",
      "name": "Эл. набор (неделя)",
      "amt": null,
      "price": 12000,
      "tag": "pass",
      "desc": "55 алм + 20 авроры"
    },
    {
      "id": "mp4",
      "cat": "pass",
      "name": "Эпик набор (месяц)",
      "amt": null,
      "price": 56000,
      "tag": "pass",
      "desc": "275 алм + 180 авроры"
    },
    {
      "id": "mb1",
      "cat": "boost",
      "name": "Warrior->Elite",
      "amt": null,
      "price": 4000,
      "tag": "boost",
      "desc": "~10-20 stars"
    },
    {
      "id": "mb2",
      "cat": "boost",
      "name": "Master->Epic",
      "amt": null,
      "price": 5000,
      "tag": "boost",
      "desc": "~20-30 stars"
    },
    {
      "id": "mb3",
      "cat": "boost",
      "name": "Epic->Legend",
      "amt": null,
      "price": 6000,
      "tag": "boost",
      "desc": "~30-40 stars"
    },
    {
      "id": "mb4",
      "cat": "boost",
      "name": "Legend->Mythic",
      "amt": null,
      "price": 7000,
      "tag": "boost",
      "desc": "~40-50 stars"
    },
    {
      "id": "mb5",
      "cat": "boost",
      "name": "Mythic->Glory",
      "amt": null,
      "price": 8000,
      "tag": "boost",
      "desc": "~50+ stars"
    },
    {
      "id": "mb6",
      "cat": "boost",
      "name": "Glory+",
      "amt": null,
      "price": 11000,
      "tag": "boost",
      "desc": "Mythic Glory+"
    }
  ],
  "brawl": [
    {
      "id": "bwl1",
      "cat": "login_brawl",
      "name": "С входом — любая сумма",
      "amt": null,
      "price": 0,
      "tag": "login",
      "desc": "Логин + пароль + код Gmail"
    },
    {
      "id": "bw1",
      "cat": "gems_brawl",
      "name": "33 Gems",
      "amt": null,
      "price": 14000,
      "tag": "new",
      "desc": "Гемы Brawl Stars"
    },
    {
      "id": "bw2",
      "cat": "gems_brawl",
      "name": "88 Gems",
      "amt": null,
      "price": 35000,
      "tag": "new",
      "desc": "Гемы Brawl Stars"
    },
    {
      "id": "bw3",
      "cat": "gems_brawl",
      "name": "187 Gems",
      "amt": null,
      "price": 71000,
      "tag": null,
      "desc": "Гемы Brawl Stars"
    },
    {
      "id": "bw4",
      "cat": "gems_brawl",
      "name": "396 Gems",
      "amt": null,
      "price": 142000,
      "tag": null,
      "desc": "Гемы Brawl Stars"
    },
    {
      "id": "bw5",
      "cat": "gems_brawl",
      "name": "1045 Gems",
      "amt": null,
      "price": 360000,
      "tag": null,
      "desc": "Гемы Brawl Stars"
    },
    {
      "id": "bwp1",
      "cat": "pass_brawl",
      "name": "Brawl Pass",
      "amt": null,
      "price": 65000,
      "tag": "pass",
      "desc": "≈ $5.4 · Сезонный пропуск"
    },
    {
      "id": "bwp2",
      "cat": "pass_brawl",
      "name": "Brawl Pass Plus",
      "amt": null,
      "price": 97000,
      "tag": "pass",
      "desc": "≈ $8.1 · Пропуск + бонусы"
    },
    {
      "id": "bwp3",
      "cat": "pass_brawl",
      "name": "Pro Pass",
      "amt": null,
      "price": 175000,
      "tag": "pass",
      "desc": "≈ $14.6 · Профессиональный пропуск"
    }
  ],
  "steam": [
    {
      "id": "st1",
      "cat": "steam_rub",
      "name": "100 ₽",
      "amt": null,
      "price": 4120,
      "tag": null,
      "desc": "Steam кошелёк · логин"
    },
    {
      "id": "st2",
      "cat": "steam_rub",
      "name": "200 ₽",
      "amt": null,
      "price": 8240,
      "tag": null,
      "desc": "Steam кошелёк · логин"
    },
    {
      "id": "st3",
      "cat": "steam_rub",
      "name": "300 ₽",
      "amt": null,
      "price": 12360,
      "tag": null,
      "desc": "Steam кошелёк · логин"
    },
    {
      "id": "st4",
      "cat": "steam_rub",
      "name": "500 ₽",
      "amt": null,
      "price": 20600,
      "tag": null,
      "desc": "Steam кошелёк · логин"
    },
    {
      "id": "st5",
      "cat": "steam_rub",
      "name": "1 000 ₽",
      "amt": null,
      "price": 41200,
      "tag": null,
      "desc": "Steam кошелёк · логин"
    },
    {
      "id": "st6",
      "cat": "steam_rub",
      "name": "2 000 ₽",
      "amt": null,
      "price": 82400,
      "tag": null,
      "desc": "Steam кошелёк · логин"
    },
    {
      "id": "st7",
      "cat": "steam_rub",
      "name": "3 000 ₽",
      "amt": null,
      "price": 123600,
      "tag": null,
      "desc": "Steam кошелёк · логин"
    },
    {
      "id": "st8",
      "cat": "steam_rub",
      "name": "5 000 ₽",
      "amt": null,
      "price": 206000,
      "tag": null,
      "desc": "Steam кошелёк · логин"
    }
  ],
  "roblox": [
    {
      "id": "rf01",
      "cat": "robux_fast",
      "name": "40 Robux",
      "amt": 40,
      "price": 10000,
      "desc": "Моментально · вход в акк"
    },
    {
      "id": "rf02",
      "cat": "robux_fast",
      "name": "80 Robux",
      "amt": 80,
      "price": 20000,
      "desc": "Моментально · вход в акк"
    },
    {
      "id": "rf03",
      "cat": "robux_fast",
      "name": "400 Robux",
      "amt": 400,
      "price": 70000,
      "desc": "Моментально · вход в акк"
    },
    {
      "id": "rf04",
      "cat": "robux_fast",
      "name": "800 Robux",
      "amt": 800,
      "price": 145000,
      "desc": "Моментально · вход в акк"
    },
    {
      "id": "rf05",
      "cat": "robux_fast",
      "name": "1700 Robux",
      "amt": 1700,
      "price": 280000,
      "tag": "hot",
      "desc": "Моментально · вход в акк"
    },
    {
      "id": "rf06",
      "cat": "robux_fast",
      "name": "4500 Robux",
      "amt": 4500,
      "price": 680000,
      "desc": "Моментально · вход в акк"
    },
    {
      "id": "rf07",
      "cat": "robux_fast",
      "name": "10000 Robux",
      "amt": 10000,
      "price": 1350000,
      "desc": "Моментально · вход в акк"
    },
    {
      "id": "rf08",
      "cat": "robux_fast",
      "name": "22500 Robux",
      "amt": 22500,
      "price": 2700000,
      "tag": "new",
      "desc": "Моментально · вход в акк"
    }
  ],
  "genshin": [
    {
      "id": "g01",
      "cat": "primogems",
      "name": "60 💠 Примогемов",
      "price": 14000
    },
    {
      "id": "g02",
      "cat": "primogems",
      "name": "330 💠 Примогемов",
      "price": 68000
    },
    {
      "id": "g03",
      "cat": "primogems",
      "name": "1090 💠 Примогемов",
      "price": 205000
    },
    {
      "id": "g04",
      "cat": "primogems",
      "name": "2240 💠 Примогемов",
      "price": 410000
    },
    {
      "id": "g05",
      "cat": "primogems",
      "name": "3880 💠 Примогемов",
      "price": 680000
    },
    {
      "id": "g06",
      "cat": "primogems",
      "name": "8080 💠 Примогемов",
      "price": 1360000
    },
    {
      "id": "g07",
      "cat": "moon",
      "name": "🌗 Луна благословения",
      "price": 68000,
      "tag": "hot"
    }
  ],
  "zzz": [
    {
      "id": "z1",
      "cat": "mono",
      "name": "60 Monochrome",
      "amt": null,
      "price": 13000,
      "tag": null,
      "desc": null
    },
    {
      "id": "z2",
      "cat": "mono",
      "name": "330 Monochrome",
      "amt": null,
      "price": 59000,
      "tag": null,
      "desc": null
    },
    {
      "id": "z3",
      "cat": "mono",
      "name": "1090 Monochrome",
      "amt": null,
      "price": 180000,
      "tag": null,
      "desc": null
    },
    {
      "id": "z4",
      "cat": "mono",
      "name": "2240 Monochrome",
      "amt": null,
      "price": 370000,
      "tag": null,
      "desc": null
    },
    {
      "id": "z5",
      "cat": "mono",
      "name": "3880 Monochrome",
      "amt": null,
      "price": 590000,
      "tag": null,
      "desc": null
    },
    {
      "id": "z6",
      "cat": "mono",
      "name": "8080 Monochrome",
      "amt": null,
      "price": 1150000,
      "tag": null,
      "desc": null
    },
    {
      "id": "zp1",
      "cat": "pass_z",
      "name": "Welkin",
      "amt": null,
      "price": 57000,
      "tag": "pass",
      "desc": null
    },
    {
      "id": "zp2",
      "cat": "pass_z",
      "name": "BP Advanced",
      "amt": null,
      "price": 150000,
      "tag": "pass",
      "desc": null
    },
    {
      "id": "zp3",
      "cat": "pass_z",
      "name": "BP Premium",
      "amt": null,
      "price": 300000,
      "tag": "pass",
      "desc": null
    },
    {
      "id": "zs1",
      "cat": "sets",
      "name": "Welcome Set",
      "amt": null,
      "price": 15000,
      "tag": "gift",
      "desc": null
    },
    {
      "id": "zs2",
      "cat": "sets",
      "name": "Sympathy Set",
      "amt": null,
      "price": 70000,
      "tag": "gift",
      "desc": null
    },
    {
      "id": "zs3",
      "cat": "sets",
      "name": "Just for You Set",
      "amt": null,
      "price": 250000,
      "tag": "gift",
      "desc": null
    }
  ],
  "hsr": [
    {
      "id": "h1",
      "cat": "essence",
      "name": "60 Jade",
      "amt": null,
      "price": 13000,
      "tag": null,
      "desc": null
    },
    {
      "id": "h2",
      "cat": "essence",
      "name": "330 Jade",
      "amt": null,
      "price": 60000,
      "tag": null,
      "desc": null
    },
    {
      "id": "h3",
      "cat": "essence",
      "name": "1090 Jade",
      "amt": null,
      "price": 160000,
      "tag": null,
      "desc": null
    },
    {
      "id": "h4",
      "cat": "essence",
      "name": "1420 Jade",
      "amt": null,
      "price": 225000,
      "tag": null,
      "desc": null
    },
    {
      "id": "h5",
      "cat": "essence",
      "name": "2240 Jade",
      "amt": null,
      "price": 330000,
      "tag": null,
      "desc": null
    },
    {
      "id": "h6",
      "cat": "essence",
      "name": "3880 Jade",
      "amt": null,
      "price": 510000,
      "tag": null,
      "desc": null
    },
    {
      "id": "h7",
      "cat": "essence",
      "name": "8080 Jade",
      "amt": null,
      "price": 1000000,
      "tag": null,
      "desc": null
    },
    {
      "id": "hp1",
      "cat": "pass_h",
      "name": "Supply Pass",
      "amt": null,
      "price": 50000,
      "tag": "pass",
      "desc": "Express Supply Pass"
    }
  ],
  "pubg": [
    {
      "id": "p1",
      "cat": "uc",
      "name": "325 UC",
      "amt": null,
      "price": 64000,
      "tag": null,
      "desc": null
    },
    {
      "id": "p2",
      "cat": "uc",
      "name": "385 UC",
      "amt": null,
      "price": 75000,
      "tag": null,
      "desc": null
    },
    {
      "id": "p3",
      "cat": "uc",
      "name": "660 UC",
      "amt": null,
      "price": 120000,
      "tag": null,
      "desc": null
    },
    {
      "id": "p4",
      "cat": "uc",
      "name": "985 UC",
      "amt": null,
      "price": 190000,
      "tag": null,
      "desc": null
    },
    {
      "id": "p5",
      "cat": "uc",
      "name": "1320 UC",
      "amt": null,
      "price": 250000,
      "tag": null,
      "desc": null
    },
    {
      "id": "p6",
      "cat": "uc",
      "name": "1800 UC",
      "amt": null,
      "price": 300000,
      "tag": null,
      "desc": null
    },
    {
      "id": "p7",
      "cat": "uc",
      "name": "2460 UC",
      "amt": null,
      "price": 450000,
      "tag": null,
      "desc": null
    },
    {
      "id": "p8",
      "cat": "uc",
      "name": "5650 UC",
      "amt": null,
      "price": 900000,
      "tag": null,
      "desc": null
    },
    {
      "id": "p9",
      "cat": "uc",
      "name": "8100 UC",
      "amt": null,
      "price": 1200000,
      "tag": null,
      "desc": null
    },
    {
      "id": "p10",
      "cat": "uc",
      "name": "16200 UC",
      "amt": null,
      "price": 2300000,
      "tag": null,
      "desc": null
    },
    {
      "id": "p11",
      "cat": "uc",
      "name": "20050 UC",
      "amt": null,
      "price": 2900000,
      "tag": null,
      "desc": null
    }
  ],
  "ff": [
    {
      "id": "f1",
      "cat": "fire",
      "name": "100 Diamonds",
      "amt": null,
      "price": 26000,
      "tag": null,
      "desc": null
    },
    {
      "id": "f2",
      "cat": "fire",
      "name": "200 Diamonds",
      "amt": null,
      "price": 50000,
      "tag": null,
      "desc": null
    },
    {
      "id": "f3",
      "cat": "fire",
      "name": "300 Diamonds",
      "amt": null,
      "price": 76000,
      "tag": null,
      "desc": null
    },
    {
      "id": "f4",
      "cat": "fire",
      "name": "500 Diamonds",
      "amt": null,
      "price": 90000,
      "tag": null,
      "desc": null
    },
    {
      "id": "f5",
      "cat": "fire",
      "name": "1000 Diamonds",
      "amt": null,
      "price": 165000,
      "tag": null,
      "desc": null
    },
    {
      "id": "f6",
      "cat": "fire",
      "name": "3000 Diamonds",
      "amt": null,
      "price": 400000,
      "tag": null,
      "desc": null
    }
  ],
  "hok": [
    {
      "id": "hk1",
      "cat": "token_hok",
      "name": "80 Tokens",
      "amt": null,
      "price": 15000,
      "tag": null,
      "desc": null
    },
    {
      "id": "hk2",
      "cat": "token_hok",
      "name": "240 Tokens",
      "amt": null,
      "price": 40000,
      "tag": null,
      "desc": null
    },
    {
      "id": "hk3",
      "cat": "token_hok",
      "name": "400 Tokens",
      "amt": null,
      "price": 70000,
      "tag": null,
      "desc": null
    },
    {
      "id": "hk4",
      "cat": "token_hok",
      "name": "560 Tokens",
      "amt": null,
      "price": 90000,
      "tag": null,
      "desc": null
    },
    {
      "id": "hk5",
      "cat": "token_hok",
      "name": "830 Tokens",
      "amt": null,
      "price": 130000,
      "tag": null,
      "desc": null
    },
    {
      "id": "hk6",
      "cat": "token_hok",
      "name": "1245 Tokens",
      "amt": null,
      "price": 200000,
      "tag": null,
      "desc": null
    },
    {
      "id": "hk7",
      "cat": "token_hok",
      "name": "2508 Tokens",
      "amt": null,
      "price": 355000,
      "tag": null,
      "desc": null
    },
    {
      "id": "hk8",
      "cat": "token_hok",
      "name": "4180 Tokens",
      "amt": null,
      "price": 600000,
      "tag": null,
      "desc": null
    },
    {
      "id": "hk9",
      "cat": "token_hok",
      "name": "8360 Tokens",
      "amt": null,
      "price": 1200000,
      "tag": null,
      "desc": null
    }
  ],
  "s2": [
    {
      "id": "s1",
      "cat": "gold",
      "name": "100 Gold",
      "amt": null,
      "price": 26000,
      "tag": null,
      "desc": null
    },
    {
      "id": "s2",
      "cat": "gold",
      "name": "200 Gold",
      "amt": null,
      "price": 50000,
      "tag": null,
      "desc": null
    },
    {
      "id": "s3",
      "cat": "gold",
      "name": "300 Gold",
      "amt": null,
      "price": 76000,
      "tag": null,
      "desc": null
    },
    {
      "id": "s4",
      "cat": "gold",
      "name": "500 Gold",
      "amt": null,
      "price": 90000,
      "tag": null,
      "desc": null
    },
    {
      "id": "s5",
      "cat": "gold",
      "name": "1000 Gold",
      "amt": null,
      "price": 165000,
      "tag": null,
      "desc": null
    },
    {
      "id": "s6",
      "cat": "gold",
      "name": "3000 Gold",
      "amt": null,
      "price": 400000,
      "tag": null,
      "desc": null
    }
  ],
  "tgprem": [
    {
      "id": "tp1",
      "cat": "login",
      "name": "1 month (login)",
      "amt": null,
      "price": 38000,
      "tag": "login",
      "desc": "Login required"
    },
    {
      "id": "tp2",
      "cat": "login",
      "name": "12 months (login)",
      "amt": null,
      "price": 280000,
      "tag": "login",
      "desc": "Login required"
    },
    {
      "id": "tg1",
      "cat": "gift",
      "name": "3 months Gift",
      "amt": null,
      "price": 170000,
      "tag": "gift",
      "desc": "Gift - no login"
    },
    {
      "id": "tg2",
      "cat": "gift",
      "name": "6 months Gift",
      "amt": null,
      "price": 225000,
      "tag": "gift",
      "desc": "Gift - no login"
    },
    {
      "id": "tg3",
      "cat": "gift",
      "name": "12 months Gift",
      "amt": null,
      "price": 400000,
      "tag": "gift",
      "desc": "Gift - no login"
    }
  ],
  "jutsu": [
    {
      "id": "j1",
      "cat": "month",
      "name": "1 month Jutsu+",
      "amt": null,
      "price": 15000,
      "tag": "new",
      "desc": null
    },
    {
      "id": "j2",
      "cat": "month",
      "name": "6 months Jutsu+",
      "amt": null,
      "price": 85000,
      "tag": "new",
      "desc": "Better deal!"
    }
  ]
}