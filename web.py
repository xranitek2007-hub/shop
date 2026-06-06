"""
FrozenShop Website — HTML generator
Clean shop page with all 185+ products
"""
from config import PRODUCTS, GAME_NAMES, GAME_EMOJI, CARDS, GAME_KEYS


def render() -> str:
    # ── Nav buttons ────────────────────────────────────────────
    nav = ""
    for gid in PRODUCTS:
        e = GAME_EMOJI.get(gid, "🎮")
        n = GAME_NAMES.get(gid, gid)
        nav += (
            f'<button class="nb" onclick="scrollGame(\'game-{gid}\')">'
            f'{e} {n}</button>'
        )

    # ── Cards list for modal ───────────────────────────────────
    cards_html = ""
    for last4, num in CARDS.items():
        bank = "HUMO" if num.startswith("9860") else "UzCard"
        cards_html += (
            f'<div class="ci" data-last4="{last4}" '
            f'onclick="selCard(\'{last4}\')">'
            f'<span class="cn">{num}</span>'
            f'<span class="cb">{bank}</span>'
            f'</div>'
        )

    # ── Game keys JS object ────────────────────────────────────
    gkeys_js = "{" + ",".join(
        f'"{gid}":"{key}"' for gid, key in GAME_KEYS.items()
    ) + "}"

    # ── Product sections ───────────────────────────────────────
    sections = ""
    for gid, items in PRODUCTS.items():
        name  = GAME_NAMES.get(gid, gid)
        emoji = GAME_EMOJI.get(gid, "🎮")

        # Category headers inside game
        cats_seen = []
        cat_labels = {
            "robux_slow":   "🕐 Трейд (5-7 дней)",
            "robux_fast":   "⚡ Моментально (вход в аккаунт)",
            "gems_uid":     "💠 По UID (без входа)",
            "gems_login":   "🔐 С входом Hoyoverse",
        }

        prods_html = ""
        prev_cat = None
        for p in items:
            cat = p.get("cat", "")
            # Add category separator if needed
            if cat in cat_labels and cat != prev_cat:
                prods_html += (
                    f'<div class="cat-sep">'
                    f'{cat_labels[cat]}'
                    f'</div>'
                )
                prev_cat = cat

            tag = ""
            if p.get("tag") == "hot":
                tag = '<span class="tag hot">🔥 ХИТ</span>'
            elif p.get("tag") == "new":
                tag = '<span class="tag new">⭐ NEW</span>'

            price_str = (
                f"{p['price']:,}".replace(",", " ") + " сум"
                if p["price"] else "Договорная"
            )
            desc_html = (
                f'<div class="pd">{p["desc"]}</div>'
                if p.get("desc") else ""
            )

            name_esc = p["name"].replace("'", "\\'")
            js = (
                f"openOrder("
                f"'{gid}','{p['id']}',"
                f"'{name_esc}',{p['price']},"
                f"'{p.get('cat','')}')"
            )

            prods_html += (
                f'<div class="pc" onclick="{js}">'
                f'<div class="pn">{p["name"]} {tag}</div>'
                f'<div class="pp">{price_str}</div>'
                f'{desc_html}'
                f'</div>'
            )

        sections += (
            f'<div class="gs" id="game-{gid}">'
            f'<h2 class="gt">{emoji} {name}</h2>'
            f'<div class="pg">{prods_html}</div>'
            f'</div>'
        )

    # ── Full HTML ──────────────────────────────────────────────
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>FrozenShop ❄️ — Игровые товары</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
:root{{
  --bg:#0a0a1a;--bg2:#12122a;--bg3:#1a1a35;
  --ac:#6c63ff;--ac2:#a78bfa;
  --gold:#ffd54f;--green:#4caf50;
  --tx:#e8e8ff;--mt:#8888aa;
  --br:rgba(108,99,255,.2);
}}
body{{background:var(--bg);color:var(--tx);font-family:'Segoe UI',sans-serif;min-height:100vh}}
a{{color:var(--ac2);text-decoration:none}}

/* Header */
.hdr{{background:linear-gradient(135deg,#0d0d2b,#1a0a3d);
  padding:13px 20px;display:flex;align-items:center;
  justify-content:space-between;border-bottom:1px solid var(--br);
  position:sticky;top:0;z-index:100;backdrop-filter:blur(12px)}}
.logo{{font-size:20px;font-weight:800;letter-spacing:1px}}
.logo span{{color:var(--ac2)}}
.hbtns{{display:flex;gap:8px}}
.hbtn{{background:rgba(108,99,255,.15);border:1px solid var(--br);
  color:var(--tx);padding:7px 14px;border-radius:20px;cursor:pointer;
  font-size:13px;transition:.2s;text-decoration:none}}
.hbtn:hover{{background:rgba(108,99,255,.3)}}

/* Nav */
.nav{{background:var(--bg2);padding:10px 16px;display:flex;gap:7px;
  overflow-x:auto;border-bottom:1px solid var(--br);scrollbar-width:none}}
.nav::-webkit-scrollbar{{display:none}}
.nb{{background:transparent;border:1px solid var(--br);color:var(--mt);
  padding:7px 14px;border-radius:20px;cursor:pointer;white-space:nowrap;
  font-size:13px;transition:.2s;flex-shrink:0}}
.nb:hover{{background:var(--ac);border-color:var(--ac);color:#fff}}

/* Main */
.main{{max-width:940px;margin:0 auto;padding:20px}}
.gs{{margin-bottom:30px}}
.gt{{font-size:19px;font-weight:700;margin-bottom:12px;
  padding-bottom:10px;border-bottom:1px solid var(--br)}}
.pg{{display:grid;grid-template-columns:repeat(auto-fill,minmax(155px,1fr));gap:10px}}
.cat-sep{{grid-column:1/-1;font-size:12px;font-weight:700;color:var(--ac2);
  padding:6px 2px 2px;border-bottom:1px solid var(--br);margin-top:4px}}
.pc{{background:var(--bg2);border:1px solid var(--br);border-radius:14px;
  padding:13px;cursor:pointer;transition:.2s;position:relative}}
.pc:hover{{border-color:var(--ac);background:var(--bg3);
  transform:translateY(-2px);box-shadow:0 8px 24px rgba(108,99,255,.2)}}
.pn{{font-size:14px;font-weight:600;margin-bottom:6px}}
.pp{{font-size:13px;color:var(--ac2);font-weight:700}}
.pd{{font-size:10px;color:var(--mt);margin-top:4px}}
.tag{{font-size:10px;padding:2px 6px;border-radius:5px;margin-left:3px}}
.tag.hot{{background:rgba(244,67,54,.2);color:#ff6b6b}}
.tag.new{{background:rgba(255,213,79,.15);color:var(--gold)}}

/* Promo */
.promo{{background:linear-gradient(135deg,rgba(108,99,255,.1),rgba(167,139,250,.05));
  border:1px solid var(--br);border-radius:16px;padding:18px;
  margin-bottom:22px;text-align:center}}
.promo h3{{font-size:16px;margin-bottom:5px}}
.promo p{{font-size:12px;color:var(--mt)}}

/* Modal */
.ov{{display:none;position:fixed;inset:0;background:rgba(0,0,0,.8);
  z-index:200;align-items:flex-end;justify-content:center;padding:0}}
.ov.on{{display:flex}}
@media(min-width:600px){{.ov{{align-items:center;padding:20px}}}}
.mb{{background:var(--bg2);border:1px solid var(--br);
  border-radius:20px 20px 0 0;padding:22px;width:100%;
  max-width:460px;max-height:92vh;overflow-y:auto}}
@media(min-width:600px){{.mb{{border-radius:20px}}}}
.mb h3{{font-size:17px;margin-bottom:14px}}
.mpi{{background:var(--bg3);border-radius:12px;padding:13px;margin-bottom:14px}}
.mprice{{font-size:22px;font-weight:800;color:var(--gold)}}

/* Steps */
.steps{{display:flex;gap:4px;margin-bottom:16px}}
.step{{flex:1;height:3px;border-radius:2px;background:var(--br)}}
.step.on{{background:var(--ac)}}

/* Form */
.fg{{margin-bottom:13px}}
.fg label{{font-size:12px;color:var(--mt);margin-bottom:4px;display:block}}
.fi{{width:100%;background:var(--bg3);border:1px solid var(--br);
  color:var(--tx);padding:11px 13px;border-radius:10px;
  font-size:15px;outline:none;font-family:inherit}}
.fi:focus{{border-color:var(--ac)}}

/* Cards */
.ci{{background:var(--bg3);border:1.5px solid var(--br);border-radius:10px;
  padding:11px 13px;cursor:pointer;display:flex;
  justify-content:space-between;align-items:center;
  transition:.2s;margin-bottom:8px}}
.ci.on{{border-color:var(--ac);background:rgba(108,99,255,.1)}}
.ci:hover{{border-color:var(--ac2)}}
.cn{{font-family:monospace;font-size:13px;font-weight:600}}
.cb{{font-size:11px;color:var(--mt)}}

/* Buttons */
.btn{{width:100%;padding:13px;border-radius:12px;border:none;
  cursor:pointer;font-size:15px;font-weight:700;transition:.2s;
  font-family:inherit;margin-top:6px}}
.btn-p{{background:linear-gradient(135deg,var(--ac),var(--ac2));color:#fff}}
.btn-p:hover{{opacity:.9;transform:translateY(-1px)}}
.btn-p:disabled{{opacity:.5;cursor:not-allowed;transform:none}}
.btn-g{{background:rgba(255,213,79,.08);border:1px solid rgba(255,213,79,.25);color:var(--gold)}}
.btn-c{{background:transparent;border:1px solid var(--br);color:var(--mt)}}
.btn-link{{display:block;text-align:center;text-decoration:none;
  background:rgba(41,182,246,.1);border:1px solid rgba(41,182,246,.25);
  color:#29b6f6;padding:12px;border-radius:12px;font-weight:700;
  font-size:14px;margin-top:6px}}

/* Alerts */
.alert{{padding:11px 13px;border-radius:10px;margin-bottom:11px;
  font-size:13px;font-weight:600;text-align:center;display:none}}
.alert.ok{{background:rgba(76,175,80,.1);border:1px solid rgba(76,175,80,.3);color:#81c784}}
.alert.err{{background:rgba(244,67,54,.1);border:1px solid rgba(244,67,54,.3);color:#e57373}}
.alert.info{{background:rgba(108,99,255,.1);border:1px solid var(--br);color:var(--ac2)}}

/* Validate */
.vr{{font-size:12px;padding:8px;border-radius:8px;margin:6px 0;display:none}}
.vr.ok{{background:rgba(76,175,80,.1);color:#81c784}}
.vr.err{{color:#e57373}}

/* Fast notice */
.fast-notice{{background:rgba(41,182,246,.08);border:1.5px solid rgba(41,182,246,.25);
  border-radius:12px;padding:12px 13px;margin-bottom:12px;display:none}}
.fast-notice h4{{color:#29b6f6;font-size:13px;margin-bottom:5px}}
.fast-notice p{{font-size:11px;color:var(--mt)}}

/* Done screen */
.done-ico{{font-size:52px;margin-bottom:12px}}

/* Footer */
.ftr{{background:var(--bg2);border-top:1px solid var(--br);
  padding:18px;text-align:center;color:var(--mt);font-size:13px;margin-top:36px}}

@media(max-width:500px){{
  .pg{{grid-template-columns:repeat(2,1fr)}}
  .hdr{{padding:11px 14px}}
  .logo{{font-size:17px}}
}}
</style>
</head>
<body>

<div class="hdr">
  <div class="logo">FROZEN<span>SHOP</span> ❄️</div>
  <div class="hbtns">
    <a href="https://t.me/frozenld_bot" target="_blank" class="hbtn">🤖 Бот</a>
    <a href="https://t.me/frozenld1" target="_blank" class="hbtn">📞 Поддержка</a>
  </div>
</div>

<div class="nav">
  <button class="nb" onclick="scrollTo({{top:0,behavior:'smooth'}})">🎮 Все игры</button>
  {nav}
</div>

<div class="main">
  <div class="promo">
    <h3>🎁 Моментальные Robux и алмазы MLBB по лучшим ценам!</h3>
    <p>Выдача 1–5 мин · Работаем 24/7 · Безопасно и надёжно</p>
  </div>
  {sections}
</div>

<div class="ftr">
  FrozenShop ❄️ — Игровые товары · 24/7<br>
  <a href="https://t.me/frozenld_bot">@frozenld_bot</a> ·
  <a href="https://t.me/frozenld1">@frozenld1</a>
</div>

<!-- ── Order Modal ──────────────────────────────────────── -->
<div class="ov" id="ov" onclick="if(event.target===this)closeModal()">
<div class="mb">
  <div class="steps">
    <div class="step on" id="st1"></div>
    <div class="step"    id="st2"></div>
    <div class="step"    id="st3"></div>
  </div>
  <div class="alert" id="al"></div>

  <!-- Step 1: Product info + UID input -->
  <div id="s1">
    <h3>📋 Оформление заказа</h3>
    <div class="mpi">
      <div id="mn" style="font-weight:700;margin-bottom:5px"></div>
      <div class="mprice" id="mp"></div>
    </div>
    <!-- Fast Robux notice -->
    <div class="fast-notice" id="fast-notice">
      <h4>⚡ Моментальные Robux</h4>
      <p>После оплаты сразу пишем и выдаём!</p>
    </div>
    <!-- UID input (hidden for steam/tgprem) -->
    <div class="fg" id="uid-wrap">
      <label>Игровой ID *</label>
      <input class="fi" id="uid" placeholder="Например: 1510395929" oninput="onUid()">
      <div style="font-size:11px;color:var(--mt);margin-top:4px" id="uid-hint"></div>
    </div>
    <div class="fg" id="srv-wrap" style="display:none">
      <label>Сервер (в скобках рядом с ID)</label>
      <input class="fi" id="srv" placeholder="Например: 16321">
    </div>
    <div class="vr" id="vr"></div>
    <button class="btn btn-p" onclick="goStep2()">Далее →</button>
    <button class="btn btn-c" onclick="closeModal()">Отмена</button>
  </div>

  <!-- Step 2: Payment -->
  <div id="s2" style="display:none">
    <h3>💳 Оплата</h3>
    <div style="font-size:13px;color:var(--mt);margin-bottom:13px">
      Переведи точную сумму на одну из карт ниже:
    </div>
    <div id="cards">{cards_html}</div>
    <div class="fg" style="margin-top:4px">
      <label>Точная сумма перевода (из истории банка)</label>
      <input class="fi" id="amt" type="number" placeholder="0">
    </div>
    <button class="btn btn-p" id="paybtn" onclick="confirmPay()">
      ✅ Подтвердить оплату
    </button>
    <button class="btn btn-g" id="coinsbtn" onclick="payCoins()" style="display:none">
      🪙 Оплатить FrozenCoins (<span id="coinbal">0</span> FC)
    </button>
    <button class="btn btn-c" onclick="goStep1()">◀️ Назад</button>
  </div>

  <!-- Step 3: Success -->
  <div id="s3" style="display:none;text-align:center;padding:14px 0">
    <div class="done-ico">🎉</div>
    <h3>Заказ принят!</h3>
    <div style="color:var(--mt);font-size:14px;margin:10px 0 6px">
      Товар будет выдан в течение 1–5 минут
    </div>
    <div id="oidtxt" style="font-family:monospace;color:var(--ac2);font-size:13px;margin-bottom:16px"></div>
    <a href="https://t.me/frozenld_bot" target="_blank" class="btn-link">
      🤖 Открыть бот для уведомлений
    </a>
    <a href="https://t.me/frozenld1" target="_blank" class="btn-link" id="fast-contact" style="display:none;background:rgba(41,182,246,.1);border-color:rgba(41,182,246,.3);color:#29b6f6">
      💬 Написать @frozenld1 для выдачи
    </a>
    <button class="btn btn-c" onclick="closeModal()">Закрыть</button>
  </div>
</div>
</div>

<script>
const GKEYS = {gkeys_js};
const NEEDS_UID = ["mlbb","genshin","hsr","zzz","pubg","ff","hok","s2","roblox","brawl"];
const NEEDS_SRV = ["mlbb"];
const HINTS = {{
  mlbb:    "Профиль → под ником · Пример: 1510395929",
  genshin: "Меню → Аккаунт → UID",
  hsr:     "Меню → Аккаунт → UID",
  zzz:     "Профиль → UID",
  pubg:    "Инвентарь → ID персонажа",
  ff:      "Главный экран → под именем",
  hok:     "Профиль → UID",
  s2:      "Профиль → ID",
  roblox:  "Профиль → URL (числа в конце)",
  brawl:   "Профиль → тег",
}};

let _game="", _pid="", _name="", _price=0, _cat="", _card="", _oid="";

function scrollGame(id){{
  const el = document.getElementById(id);
  if(el) el.scrollIntoView({{behavior:"smooth", block:"start"}});
}}

function showAlert(t, type){{
  const el = document.getElementById("al");
  el.textContent = t; el.className = "alert " + type; el.style.display = "block";
}}
function clearAlert(){{ document.getElementById("al").style.display = "none"; }}

function showStep(n){{
  [1,2,3].forEach(i => {{
    document.getElementById("s"+i).style.display = i===n ? "block" : "none";
    document.getElementById("st"+i).className = "step" + (i<=n ? " on" : "");
  }});
  clearAlert();
}}

function goStep1(){{ showStep(1); }}

function openOrder(gid, pid, name, price, cat){{
  _game=gid; _pid=pid; _name=name; _price=price; _cat=cat; _card=""; _oid="";

  document.getElementById("mn").textContent = name;
  document.getElementById("mp").textContent = price
    ? price.toLocaleString("ru") + " сум" : "Договорная";
  document.getElementById("uid").value = "";
  document.getElementById("srv").value = "";
  document.getElementById("amt").value = "";
  document.getElementById("vr").style.display = "none";
  document.querySelectorAll(".ci").forEach(c => c.classList.remove("on"));

  // UID field visibility
  document.getElementById("uid-wrap").style.display =
    NEEDS_UID.includes(gid) ? "block" : "none";
  document.getElementById("srv-wrap").style.display =
    NEEDS_SRV.includes(gid) ? "block" : "none";
  document.getElementById("uid-hint").textContent = HINTS[gid] || "";

  // Fast robux notice
  const fastN = document.getElementById("fast-notice");
  fastN.style.display = cat === "robux_fast" ? "block" : "none";

  // Wallet balance
  const tgUid = localStorage.getItem("tg_uid");
  if(tgUid){{
    fetch("/api/wallet/" + tgUid).then(r=>r.json()).then(d=>{{
      if(d.ok && d.balance > 0){{
        document.getElementById("coinbal").textContent =
          Math.floor(d.balance).toLocaleString("ru");
        document.getElementById("coinsbtn").style.display = "block";
      }}
    }}).catch(()=>{{}});
  }}

  showStep(1);
  document.getElementById("ov").classList.add("on");
}}

function closeModal(){{
  document.getElementById("ov").classList.remove("on");
}}

let _vtimer;
function onUid(){{
  clearTimeout(_vtimer);
  const uid = document.getElementById("uid").value.trim();
  const vr  = document.getElementById("vr");
  if(!uid || !GKEYS[_game]){{ vr.style.display="none"; return; }}
  _vtimer = setTimeout(async () => {{
    vr.textContent = "🔍 Проверяем...";
    vr.className = "vr"; vr.style.display = "block";
    try{{
      const r = await fetch("/api/validate", {{
        method:"POST", headers:{{"Content-Type":"application/json"}},
        body: JSON.stringify({{
          game_key: GKEYS[_game],
          player_id: uid,
          server_id: document.getElementById("srv").value.trim()
        }})
      }});
      const d = await r.json();
      if(d.ok && d.username){{
        vr.textContent = "✅ Игрок найден: " + d.username;
        vr.className = "vr ok";
      }} else {{
        vr.textContent = "⚠️ " + (d.error || "Не удалось проверить");
        vr.className = "vr err";
      }}
    }} catch {{ vr.style.display = "none"; }}
  }}, 700);
}}

function goStep2(){{
  const uid = document.getElementById("uid").value.trim();
  if(NEEDS_UID.includes(_game) && !uid){{
    showAlert("❌ Введи игровой ID", "err"); return;
  }}
  showStep(2);
}}

function selCard(last4){{
  _card = last4;
  document.querySelectorAll(".ci").forEach(c => {{
    c.classList.toggle("on", c.dataset.last4 === last4);
  }});
}}

async function _createAndPay(method, extra={{}}){{
  const uid = document.getElementById("uid").value.trim();
  const srv = document.getElementById("srv").value.trim();

  // Step 1: create order
  const r1 = await fetch("/api/order", {{
    method: "POST",
    headers: {{"Content-Type":"application/json"}},
    body: JSON.stringify({{
      pid: _pid, gid: _game, name: _name, price: _price,
      diamonds: _game === "mlbb" ? parseInt(_name) : null,
      cred_fields: uid
        ? [{{"label":"Игровой ID","value":uid}},
           ...( srv ? [{{"label":"Сервер","value":srv}}] : [])]
        : [],
      bp_uid:   uid  || null,
      bp_server: srv || null,
    }})
  }});
  const d1 = await r1.json();
  if(!d1.ok) throw new Error(d1.error);
  _oid = d1.order_id;

  // Step 2: confirm payment
  const r2 = await fetch("/api/pay", {{
    method: "POST",
    headers: {{"Content-Type":"application/json"}},
    body: JSON.stringify({{
      order_id: _oid, method,
      amount: extra.amount || _price,
      card_last4: extra.card_last4 || null,
      buyer_tg_id: extra.buyer_tg_id || null,
    }})
  }});
  const d2 = await r2.json();
  if(!d2.ok) throw new Error(d2.error);
  return d2;
}}

async function confirmPay(){{
  if(!_card){{ showAlert("❌ Выбери карту", "err"); return; }}
  const amt = parseInt(document.getElementById("amt").value);
  if(!amt || amt <= 0){{ showAlert("❌ Введи сумму перевода", "err"); return; }}

  const btn = document.getElementById("paybtn");
  btn.disabled = true; btn.textContent = "⏳ Проверяем...";
  showAlert("⏳ Проверяем оплату...", "info");

  try{{
    await _createAndPay("card", {{amount: amt, card_last4: _card}});
    document.getElementById("oidtxt").textContent =
      "Заказ #" + _oid.slice(0,8).toUpperCase();
    // Show fast contact button for robux_fast
    document.getElementById("fast-contact").style.display =
      _cat === "robux_fast" ? "block" : "none";
    showStep(3);
  }} catch(e){{
    showAlert("❌ " + e.message, "err");
    btn.disabled = false; btn.textContent = "✅ Подтвердить оплату";
  }}
}}

async function payCoins(){{
  const tgUid = localStorage.getItem("tg_uid");
  if(!tgUid){{
    showAlert("❌ Открой через Telegram бот для оплаты монетами", "err");
    return;
  }}
  showAlert("⏳ Оплачиваем FrozenCoins...", "info");
  try{{
    await _createAndPay("coins", {{
      amount: _price,
      buyer_tg_id: parseInt(tgUid)
    }});
    document.getElementById("oidtxt").textContent =
      "Заказ #" + _oid.slice(0,8).toUpperCase();
    document.getElementById("fast-contact").style.display =
      _cat === "robux_fast" ? "block" : "none";
    showStep(3);
  }} catch(e){{
    showAlert("❌ " + e.message, "err");
  }}
}}
</script>
</body>
</html>"""
