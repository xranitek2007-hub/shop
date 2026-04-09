/**
 * FrozenShop Backend v2 — Buypin API + Uzum Bank receipt check
 *
 * Эндпоинты:
 *  POST /api/order          — создать заказ (из Mini App)
 *  POST /api/status         — статус заказа (polling из Mini App)
 *  POST /api/validate       — проверить игрока по ID
 *  POST /api/check-receipt  — проверить чек Uzum Bank (номер карты + сумма)
 *  GET  /api/balance        — баланс Buypin кошелька
 *  GET  /api/products/:game — список продуктов из Buypin
 *  GET  /api/games          — список игр Buypin
 *  POST /api/done           — вручную пометить выданным
 *  POST /api/reject         — отклонить заказ
 *  GET  /api/orders         — все заказы
 *  POST /tg-hook            — Telegram webhook (/done_xxx /reject_xxx /balance /orders)
 */

import express  from 'express';
import cors     from 'cors';
import { readFileSync, writeFileSync, existsSync } from 'fs';

const app  = express();
const PORT = process.env.PORT || 3000;

// ─────────────────────────────────────────────────
//  КОНФИГ — заполни переменные окружения на Railway
// ─────────────────────────────────────────────────
const cfg = {
  BUYPIN_KEY    : process.env.BUYPIN_KEY    || '',
  BOT_TOKEN     : process.env.BOT_TOKEN     || '',
  ADMIN_CHAT    : process.env.ADMIN_CHAT    || '',
  ADMIN_SECRET  : process.env.ADMIN_SECRET  || 'frozen2006',
  BUYPIN_BASE   : 'https://buypin.net/api/v1',

  // Твои карты Uzum/Humo/UzCard — последние 4 цифры для проверки
  // Формат: { 'последние4': 'полный номер для отображения' }
  CARDS: {
    '3359': '9860 1606 3787 3359',   // HUMO карта 1
    '3951': '9860 3501 4482 3951',   // HUMO карта 2
    '7849': '8600 **** **** 7849',   // UzCard карта 3
    // ← добавь свои последние 4 цифры карт
  },
};

// ─────────────────────────────────────────────────
//  DB — заказы в JSON файле
// ─────────────────────────────────────────────────
const DB_FILE = './orders.json';
let orders = {};
try {
  if (existsSync(DB_FILE)) orders = JSON.parse(readFileSync(DB_FILE, 'utf-8'));
} catch {}
function saveOrders() {
  try { writeFileSync(DB_FILE, JSON.stringify(orders, null, 2)); } catch {}
}

// ─────────────────────────────────────────────────
//  UZUM BANK — список подтверждённых платежей в памяти
//  Ключ: "<last4>_<amount>_<date YYYY-MM-DD>"
// ─────────────────────────────────────────────────
const confirmedPayments = new Set(); // хранит использованные чеки

// ─────────────────────────────────────────────────
//  MLBB КОМБИНАЦИИ — список базовых пакетов для заказа
//  Ключ = количество алмазов, значение = массив базовых пакетов
// ─────────────────────────────────────────────────
const MLBB_COMBOS = {
  11:   [11],
  22:   [22],
  55:   [55],
  56:   [56],
  86:   [86],
  110:  [55,55],
  112:  [56,56],
  165:  [165],
  172:  [172],
  224:  [112,112],
  257:  [257],
  275:  [275],
  312:  [257,55],
  330:  [275,55],
  343:  [257,86],
  385:  [275,55,55],
  429:  [257,172],
  514:  [257,257],
  565:  [565],
  620:  [565,55],
  706:  [706],
  792:  [706,86],
  816:  [706,55,55],
  878:  [706,172],
  963:  [706,257],
  981:  [706,275],
  1018: [706,257,55],
  1036: [706,275,55],
  1135: [706,257,172],
  1185: [565,565,55],
  1216: [565,565,86],
  1271: [706,565],
  1302: [565,565,172],
  1387: [565,565,257],
  1405: [565,565,275],
  1412: [706,706],
  1498: [706,706,86],
  1584: [706,706,172],
  1687: [706,706,275],
  1977: [706,706,565],
  2195: [2195],
  2281: [2195,86],
  2367: [2195,172],
  2470: [2195,275],
  2760: [2195,565],
  2846: [2195,565,86],
  2932: [2195,565,172],
  3035: [2195,565,275],
  3325: [2195,565,565],
  3466: [2195,565,706],
  3688: [3688],
  3860: [3688,172],
  3963: [3688,275],
  4253: [3688,565],
  4394: [3688,706],
  4425: [3688,565,172],
  4528: [3688,565,275],
  4566: [3688,706,172],
  4669: [3688,706,275],
  4818: [3688,565,565],
  4959: [3688,706,565],
  5100: [3688,706,706],
  5532: [5532],
  9288: [9288],
};

// ─────────────────────────────────────────────────
//  МАППИНГ: игра FrozenShop → ключ Buypin
// ─────────────────────────────────────────────────
const GAME_MAP = {
  'mlbb':    'mobile-legends-ru',
  'genshin': 'genshin-impact',
  'hsr':     'honkai-star-rail',
  'zzz':     'zenless-zone-zero',
  'pubg':    'pubg-mobile',
  'ff':      'free-fire',
  'hok':     'honor-of-kings',
  's2':      'standoff-2',
  'tgprem':  'telegram-premium',  // если доступно в buypin
  'tgstars': 'telegram-stars',
  // roblox — вручную, не в buypin
};

// ─────────────────────────────────────────────────
//  МАППИНГ: pid FrozenShop → buypin product_id
//  ЗАПОЛНИ после запроса GET /api/products/:game !
//  Пример: после деплоя открой /api/products/mobile-legends-ru
//  и скопируй реальные id из ответа
// ─────────────────────────────────────────────────
const PRODUCT_MAP = {
  // MLBB базовые пакеты (заполни реальными buypin id)
  // 'mlbb_11':   'product_id_из_buypin',
  // 'mlbb_22':   'product_id_из_buypin',
  // 'mlbb_55':   'product_id_из_buypin',
  // 'mlbb_56':   'product_id_из_buypin',
  // 'mlbb_86':   'product_id_из_buypin',
  // 'mlbb_172':  'product_id_из_buypin',
  // 'mlbb_257':  'product_id_из_buypin',
  // 'mlbb_275':  'product_id_из_buypin',
  // 'mlbb_565':  'product_id_из_buypin',
  // 'mlbb_706':  'product_id_из_buypin',
  // 'mlbb_2195': 'product_id_из_buypin',
  // 'mlbb_3688': 'product_id_из_buypin',
  // 'mlbb_5532': 'product_id_из_buypin',
  // 'mlbb_9288': 'product_id_из_buypin',

  // Genshin
  // 'genshin_60primogems':   'product_id_из_buypin',
  // 'genshin_330primogems':  'product_id_из_buypin',
  // ...

  // Добавь остальные после GET /api/products/:game
};

// ─────────────────────────────────────────────────
//  ИГРЫ БЕЗ АВТОВЫДАЧИ (ручная обработка)
// ─────────────────────────────────────────────────
const MANUAL_GAMES = new Set(['roblox', 'brawl', 'steam', 'jutsu']);

// ─────────────────────────────────────────────────
//  BUYPIN HELPER
// ─────────────────────────────────────────────────
async function bpFetch(path, method = 'GET', body = null) {
  if (!cfg.BUYPIN_KEY) throw new Error('BUYPIN_KEY не настроен');
  const opts = {
    method,
    headers: {
      'Accept': 'application/json',
      'Content-Type': 'application/json',
      'X-API-Key': cfg.BUYPIN_KEY,
    },
  };
  if (body) opts.body = JSON.stringify(body);
  const res  = await fetch(cfg.BUYPIN_BASE + path, opts);
  const data = await res.json();
  if (!data.success) throw new Error(data.message || data.error || `HTTP ${res.status}`);
  return data.data;
}

// ─────────────────────────────────────────────────
//  TELEGRAM HELPER
// ─────────────────────────────────────────────────
async function tgSend(chatId, text, extra = {}) {
  if (!cfg.BOT_TOKEN || !chatId) return;
  try {
    await fetch(`https://api.telegram.org/bot${cfg.BOT_TOKEN}/sendMessage`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ chat_id: chatId, text, parse_mode: 'HTML', ...extra }),
    });
  } catch (e) { console.warn('tgSend:', e.message); }
}

// ─────────────────────────────────────────────────
//  MIDDLEWARE
// ─────────────────────────────────────────────────
app.use(cors({ origin: '*' }));
app.use(express.json());
app.use((req, _res, next) => {
  console.log(`[${new Date().toISOString()}] ${req.method} ${req.path}`);
  next();
});

const isAdmin = (req, res) => {
  if (req.headers['x-admin-secret'] !== cfg.ADMIN_SECRET) {
    res.status(403).json({ ok: false, error: 'Forbidden' });
    return false;
  }
  return true;
};

// ─────────────────────────────────────────────────
//  GET / — healthcheck
// ─────────────────────────────────────────────────
app.get('/', (_req, res) => {
  res.json({ ok: true, service: 'FrozenShop Backend v2', uptime: Math.floor(process.uptime()) + 's' });
});

// ─────────────────────────────────────────────────
//  POST /api/check-receipt
//  Проверяет факт оплаты по номеру карты + сумме + дате
//  Фронтенд отправляет: { card_last4, amount, date? }
//  Если совпадает с pending заказом — помечает оплаченным
// ─────────────────────────────────────────────────
app.post('/api/check-receipt', async (req, res) => {
  const { card_last4, amount, order_id, buyer_tg_id, buyer_name } = req.body;

  if (!card_last4 || !amount || !order_id) {
    return res.status(400).json({ ok: false, error: 'card_last4, amount, order_id обязательны' });
  }

  // Проверяем что карта наша
  if (!cfg.CARDS[String(card_last4)]) {
    return res.json({ ok: false, error: 'Карта не найдена. Проверь последние 4 цифры.' });
  }

  // Проверяем сумму — должна совпасть с суммой заказа
  const order = orders[order_id];
  if (!order) {
    return res.json({ ok: false, error: 'Заказ не найден' });
  }
  if (order.status === 'done') {
    return res.json({ ok: false, error: 'Этот заказ уже выдан' });
  }

  // Допустимая погрешность ±100 сум (конвертация комиссий)
  const expectedPrice = Number(order.price);
  const paidAmount    = Number(amount);
  if (Math.abs(expectedPrice - paidAmount) > 500) {
    return res.json({
      ok: false,
      error: `Сумма не совпадает. Ожидалось: ${expectedPrice.toLocaleString('ru-RU')} сум, получено: ${paidAmount.toLocaleString('ru-RU')} сум`
    });
  }

  // Проверяем дубликат (защита от повторного использования чека)
  const receiptKey = `${card_last4}_${paidAmount}_${order_id}`;
  if (confirmedPayments.has(receiptKey)) {
    return res.json({ ok: false, error: 'Этот чек уже был использован' });
  }
  confirmedPayments.add(receiptKey);

  // Помечаем как оплаченный
  order.status        = 'paid';
  order.paid_amount   = paidAmount;
  order.paid_card     = cfg.CARDS[String(card_last4)];
  order.paid_at       = new Date().toISOString();
  order.buyer_tg_id   = order.buyer_tg_id || buyer_tg_id || null;
  order.buyer_name    = order.buyer_name  || buyer_name  || 'Покупатель';
  order.updated_at    = new Date().toISOString();
  orders[order_id]    = order;
  saveOrders();

  console.log(`💳 Payment confirmed: order ${order_id}, ${paidAmount} сум, card *${card_last4}`);

  // Уведомляем тебя с кнопками выдачи
  await notifyAdminNewOrder(order, `✅ Оплата подтверждена: ${paidAmount.toLocaleString('ru-RU')} сум · *${card_last4}`);

  // Пробуем автовыдачу
  const autoResult = await tryAutoFulfill(order);

  if (autoResult.ok) {
    res.json({ ok: true, message: 'Оплата подтверждена! Товар выдаётся автоматически.' });
  } else {
    res.json({ ok: true, message: 'Оплата подтверждена! Продавец выдаст товар в ближайшее время.' });
  }
});

// ─────────────────────────────────────────────────
//  POST /api/order — создать заказ
// ─────────────────────────────────────────────────
app.post('/api/order', async (req, res) => {
  const {
    id, pid, gid, name, gameName, price,
    buyer_tg_id, buyer_name, buyer_username,
    cred_data, cred_label, cred_fields,
    bp_game_key, bp_user_id, bp_server_id,
  } = req.body;

  if (!id || !pid || !gid) {
    return res.status(400).json({ ok: false, error: 'Missing id, pid, gid' });
  }

  const order = {
    id, pid, gid, name, gameName, price,
    buyer_tg_id: buyer_tg_id || null,
    buyer_name:  buyer_name  || 'Покупатель',
    buyer_username: buyer_username || null,
    cred_data, cred_label, cred_fields,
    bp_game_key: bp_game_key || GAME_MAP[gid] || null,
    bp_user_id:  bp_user_id  || null,
    bp_server_id: bp_server_id || null,
    bp_order_ids: [],  // массив — для комбо-заказов
    status:      'awaiting_payment',  // ждём оплату
    created_at:  new Date().toISOString(),
    updated_at:  new Date().toISOString(),
    error: null,
  };

  orders[id] = order;
  saveOrders();

  // Уведомляем тебя о новом заказе (ещё без оплаты)
  await notifyAdminNewOrder(order, '⏳ Ожидает оплаты');

  res.json({ ok: true, status: 'awaiting_payment' });
});

// ─────────────────────────────────────────────────
//  АВТОВЫДАЧА — пробуем через Buypin
// ─────────────────────────────────────────────────
async function tryAutoFulfill(order) {
  const gid        = order.gid;
  const bp_game    = order.bp_game_key || GAME_MAP[gid];
  const bp_user_id = order.bp_user_id;
  const pid        = order.pid;

  // Игры без автовыдачи
  if (MANUAL_GAMES.has(gid)) {
    return { ok: false, reason: 'manual_game' };
  }

  if (!bp_game || !bp_user_id || !cfg.BUYPIN_KEY) {
    return { ok: false, reason: 'no_config' };
  }

  // Определяем список buypin product_id для заказа
  let productIds = [];

  if (gid === 'mlbb') {
    // Используем комбо-логику по количеству алмазов
    const diamondAmt = order.cred_data?.diamonds || extractDiamonds(order.name);
    const combo      = diamondAmt ? MLBB_COMBOS[diamondAmt] : null;

    if (combo) {
      // Каждая часть комбо — отдельный buypin product
      for (const amt of combo) {
        const key = `mlbb_${amt}`;
        const pid = PRODUCT_MAP[key];
        if (!pid) {
          console.warn(`Product not mapped: ${key}`);
          return { ok: false, reason: `product_not_mapped:${key}` };
        }
        productIds.push(pid);
      }
    } else {
      // Попробуем прямой маппинг по pid
      const directPid = PRODUCT_MAP[pid];
      if (directPid) productIds = [directPid];
      else return { ok: false, reason: `no_combo_or_map:${pid}` };
    }
  } else {
    // Для остальных игр — прямой маппинг pid → buypin product_id
    const bpPid = PRODUCT_MAP[pid];
    if (!bpPid) return { ok: false, reason: `product_not_mapped:${pid}` };
    productIds = [bpPid];
  }

  // Создаём заказы в Buypin (по одному для каждой части комбо)
  try {
    order.status      = 'processing';
    order.bp_order_ids = [];
    order.updated_at  = new Date().toISOString();
    orders[order.id]  = order;
    saveOrders();

    for (const bpProductId of productIds) {
      const body = { product_id: bpProductId, user_id: String(bp_user_id) };
      if (order.bp_server_id) body.server_id = String(order.bp_server_id);

      const result = await bpFetch(`/games/${bp_game}/order`, 'POST', body);
      const bpOrderId = result.order_id || result.id;
      order.bp_order_ids.push(bpOrderId);
      orders[order.id] = order;
      saveOrders();

      console.log(`✅ Buypin order: ${bpOrderId} (part of ${order.id})`);
    }

    // Уведомляем покупателя
    if (order.buyer_tg_id) {
      await tgSend(order.buyer_tg_id,
        `⚙️ <b>Заказ принят и обрабатывается!</b>\n\n` +
        `📦 ${order.name}\n🆔 <code>#${order.id.slice(0,8).toUpperCase()}</code>\n\n` +
        `⏳ Товар будет выдан через 1–5 минут автоматически.\n` +
        `Если что-то не так — пиши @frozenld1`
      );
    }

    // Следим за каждым bp заказом
    for (const bpOrderId of order.bp_order_ids) {
      scheduleStatusCheck(order.id, bp_game, bpOrderId, productIds.length);
    }

    return { ok: true };
  } catch (e) {
    console.warn(`Auto-fulfill failed for ${order.id}:`, e.message);
    order.status  = 'paid';  // откатываем к "оплачен, ждёт ручной выдачи"
    order.error   = e.message;
    order.updated_at = new Date().toISOString();
    orders[order.id] = order;
    saveOrders();

    await tgSend(cfg.ADMIN_CHAT,
      `⚠️ <b>Автовыдача не удалась!</b>\n` +
      `🆔 #${order.id.slice(0,8).toUpperCase()}\n📦 ${order.name}\n` +
      `Ошибка: ${e.message}\n\n` +
      `Нужна ручная выдача → /done_${order.id.slice(0,8).toLowerCase()}`
    );

    return { ok: false, reason: e.message };
  }
}

// Извлечь количество алмазов из названия товара (например "86 💎")
function extractDiamonds(name) {
  if (!name) return null;
  const m = String(name).match(/^(\d+)/);
  return m ? parseInt(m[1]) : null;
}

// ─────────────────────────────────────────────────
//  Следить за статусом buypin заказа
// ─────────────────────────────────────────────────
const completedParts = {}; // orderId → count of done parts

function scheduleStatusCheck(orderId, bpGameKey, bpOrderId, totalParts = 1) {
  if (!bpOrderId) return;
  if (!completedParts[orderId]) completedParts[orderId] = 0;

  let attempts = 0;
  const timer = setInterval(async () => {
    attempts++;
    if (attempts > 24) { // 24 × 15s = 6 минут
      clearInterval(timer);
      const order = orders[orderId];
      if (order?.status === 'processing') {
        order.status = 'timeout';
        order.updated_at = new Date().toISOString();
        orders[orderId] = order;
        saveOrders();
        await tgSend(cfg.ADMIN_CHAT,
          `⏰ <b>Таймаут!</b>\n🆔 #${orderId.slice(0,8).toUpperCase()}\n` +
          `Buypin: <code>${bpOrderId}</code>\nПроверь вручную!`
        );
      }
      return;
    }

    try {
      const data      = await bpFetch(`/games/${bpGameKey}/order/status`, 'POST', { order_id: bpOrderId });
      const bpStatus  = (data.status || '').toLowerCase();
      const order     = orders[orderId];
      if (!order) { clearInterval(timer); return; }

      if (['delivered','success','completed'].includes(bpStatus)) {
        clearInterval(timer);
        completedParts[orderId]++;

        if (completedParts[orderId] >= totalParts) {
          // Все части доставлены
          order.status     = 'done';
          order.updated_at = new Date().toISOString();
          orders[orderId]  = order;
          saveOrders();

          if (order.buyer_tg_id) {
            await tgSend(order.buyer_tg_id,
              `🎉 <b>Ваш заказ выдан!</b>\n\n` +
              `📦 ${order.name}\n🆔 <code>#${orderId.slice(0,8).toUpperCase()}</code>\n\n` +
              `✨ Спасибо за покупку в FrozenShop! ❄️\n` +
              `Если что-то не так — пиши сюда или @frozenld1`
            );
          }
          await tgSend(cfg.ADMIN_CHAT,
            `✅ <b>Авто-выдан!</b> #${orderId.slice(0,8).toUpperCase()} — ${order.name}`
          );
        }
      } else if (['failed','error','cancelled'].includes(bpStatus)) {
        clearInterval(timer);
        order.status     = 'failed';
        order.error      = data.error || bpStatus;
        order.updated_at = new Date().toISOString();
        orders[orderId]  = order;
        saveOrders();

        await tgSend(cfg.ADMIN_CHAT,
          `❌ <b>Buypin ошибка!</b>\n🆔 #${orderId.slice(0,8).toUpperCase()}\n` +
          `Ошибка: ${order.error}\nТребует ручной обработки!`
        );
        if (order.buyer_tg_id) {
          await tgSend(order.buyer_tg_id,
            `❌ <b>Технический сбой</b>\n\n📦 ${order.name}\n` +
            `Деньги будут возвращены. Напиши: @frozenld1`
          );
        }
      }
    } catch (e) {
      console.warn(`Status check ${orderId}:`, e.message);
    }
  }, 15000);
}

// ─────────────────────────────────────────────────
//  Уведомить тебя о заказе в Telegram
// ─────────────────────────────────────────────────
async function notifyAdminNewOrder(order, note) {
  if (!cfg.ADMIN_CHAT) return;
  const shortId = order.id.slice(0,8).toUpperCase();
  const lines = [
    note ? `${note}` : `🛒 <b>Новый заказ</b>`,
    ``,
    `📦 <b>${order.name}</b>  (${order.gameName || order.gid})`,
    `💰 ${order.price ? Number(order.price).toLocaleString('ru-RU') + ' сум' : '—'}`,
    `🆔 <code>#${shortId}</code>`,
    ``,
    order.buyer_name ? `👤 ${order.buyer_name}${order.buyer_username ? ` (@${order.buyer_username})` : ''}` : '',
    order.buyer_tg_id ? `🔗 TG: <code>${order.buyer_tg_id}</code>` : '',
  ].filter(Boolean);

  if (order.cred_fields?.length) {
    lines.push('');
    lines.push('📋 <b>Данные:</b>');
    order.cred_fields.forEach(f => lines.push(`  • ${f.label}: <code>${f.value}</code>`));
  }

  lines.push('');
  lines.push(`✅ /done_${shortId.toLowerCase()}    ❌ /reject_${shortId.toLowerCase()}`);

  await tgSend(cfg.ADMIN_CHAT, lines.join('\n'));
}

// ─────────────────────────────────────────────────
//  POST /api/status
// ─────────────────────────────────────────────────
app.post('/api/status', (req, res) => {
  const order = orders[req.body.id];
  if (!order) return res.json({ status: 'pending' });
  res.json({ status: order.status, error: order.error || null });
});

// ─────────────────────────────────────────────────
//  POST /api/validate
// ─────────────────────────────────────────────────
app.post('/api/validate', async (req, res) => {
  const { game_key, player_id, server_id } = req.body;
  if (!game_key || !player_id)
    return res.status(400).json({ ok: false, error: 'game_key and player_id required' });
  try {
    const body = { player_id: String(player_id) };
    if (server_id) body.server_id = String(server_id);
    const data = await bpFetch(`/games/${game_key}/validate-player`, 'POST', body);
    res.json({ ok: true, username: data.username || data.name || '' });
  } catch (e) {
    res.json({ ok: false, error: e.message });
  }
});

// ─────────────────────────────────────────────────
//  GET /api/balance
// ─────────────────────────────────────────────────
app.get('/api/balance', async (req, res) => {
  if (!isAdmin(req, res)) return;
  try {
    const data = await bpFetch('/me');
    res.json({ ok: true, balance: data.wallet?.balance ?? 0 });
  } catch (e) {
    res.status(500).json({ ok: false, error: e.message });
  }
});

// ─────────────────────────────────────────────────
//  GET /api/products/:game  — список продуктов из Buypin
//  ИСПОЛЬЗУЙ ЭТО чтобы заполнить PRODUCT_MAP!
// ─────────────────────────────────────────────────
app.get('/api/products/:game', async (req, res) => {
  if (!isAdmin(req, res)) return;
  try {
    const data = await bpFetch(`/games/${req.params.game}/products`);
    // Удобный формат для заполнения PRODUCT_MAP
    const formatted = Array.isArray(data) ? data.map(p => ({
      id: p.id, name: p.name, price: p.price, sku: p.sku
    })) : data;
    res.json({ ok: true, products: formatted });
  } catch (e) {
    res.status(500).json({ ok: false, error: e.message });
  }
});

// ─────────────────────────────────────────────────
//  GET /api/games
// ─────────────────────────────────────────────────
app.get('/api/games', async (req, res) => {
  if (!isAdmin(req, res)) return;
  try {
    const data = await bpFetch('/games');
    res.json({ ok: true, games: data });
  } catch (e) {
    res.status(500).json({ ok: false, error: e.message });
  }
});

// ─────────────────────────────────────────────────
//  POST /api/done
// ─────────────────────────────────────────────────
app.post('/api/done', async (req, res) => {
  if (!isAdmin(req, res)) return;
  const order = orders[req.body.id];
  if (!order) return res.status(404).json({ ok: false, error: 'Not found' });

  order.status     = 'done';
  order.updated_at = new Date().toISOString();
  orders[req.body.id] = order;
  saveOrders();

  if (order.buyer_tg_id) {
    await tgSend(order.buyer_tg_id,
      `🎉 <b>Ваш заказ выдан!</b>\n\n📦 ${order.name}\n🆔 <code>#${req.body.id.slice(0,8).toUpperCase()}</code>\n\n` +
      `✨ Спасибо за покупку в FrozenShop! ❄️\nЕсли что-то не так — @frozenld1`
    );
  }
  res.json({ ok: true });
});

// ─────────────────────────────────────────────────
//  POST /api/reject
// ─────────────────────────────────────────────────
app.post('/api/reject', async (req, res) => {
  if (!isAdmin(req, res)) return;
  const { id, reason } = req.body;
  const order = orders[id];
  if (!order) return res.status(404).json({ ok: false, error: 'Not found' });

  order.status     = 'rejected';
  order.error      = reason || 'Отклонён';
  order.updated_at = new Date().toISOString();
  orders[id]       = order;
  saveOrders();

  if (order.buyer_tg_id) {
    await tgSend(order.buyer_tg_id,
      `❌ <b>Заказ отклонён</b>\n\n📦 ${order.name}\n\n` +
      `😔 ${reason || 'Заказ был отклонён.'}\nПо вопросам: @frozenld1`
    );
  }
  res.json({ ok: true });
});

// ─────────────────────────────────────────────────
//  GET /api/orders
// ─────────────────────────────────────────────────
app.get('/api/orders', (req, res) => {
  if (!isAdmin(req, res)) return;
  const list = Object.values(orders).sort((a,b) => new Date(b.created_at)-new Date(a.created_at));
  res.json({ ok: true, orders: list, total: list.length });
});

// ─────────────────────────────────────────────────
//  POST /tg-hook — Telegram webhook
// ─────────────────────────────────────────────────
app.post('/tg-hook', async (req, res) => {
  res.sendStatus(200);
  const msg = req.body?.message;
  if (!msg) return;
  if (String(msg.from?.id) !== String(cfg.ADMIN_CHAT)) return;

  const text    = (msg.text || '').trim();
  const statusE = { done:'✅',paid:'💳',processing:'⚙️',awaiting_payment:'⏳',rejected:'❌',failed:'🔴',timeout:'⏰',pending:'⏳' };

  if (text.startsWith('/done_')) {
    const sid = text.slice(6).toUpperCase();
    const o   = Object.values(orders).find(x => x.id.slice(0,8).toUpperCase() === sid);
    if (!o) { await tgSend(cfg.ADMIN_CHAT, `❌ Заказ #${sid} не найден`); return; }
    o.status = 'done'; o.updated_at = new Date().toISOString();
    orders[o.id] = o; saveOrders();
    await tgSend(cfg.ADMIN_CHAT, `✅ Заказ #${sid} выдан`);
    if (o.buyer_tg_id) await tgSend(o.buyer_tg_id,
      `🎉 <b>Ваш заказ выдан!</b>\n📦 ${o.name}\n🆔 <code>#${sid}</code>\n✨ Спасибо! ❄️\nВопросы: @frozenld1`);
  }

  else if (text.startsWith('/reject_')) {
    const sid = text.slice(8).toUpperCase();
    const o   = Object.values(orders).find(x => x.id.slice(0,8).toUpperCase() === sid);
    if (!o) { await tgSend(cfg.ADMIN_CHAT, `❌ Заказ #${sid} не найден`); return; }
    o.status = 'rejected'; o.updated_at = new Date().toISOString();
    orders[o.id] = o; saveOrders();
    await tgSend(cfg.ADMIN_CHAT, `❌ Заказ #${sid} отклонён`);
    if (o.buyer_tg_id) await tgSend(o.buyer_tg_id, `❌ Заказ #${sid} отклонён. Вопросы: @frozenld1`);
  }

  else if (text === '/balance') {
    try {
      const d = await bpFetch('/me');
      await tgSend(cfg.ADMIN_CHAT, `💰 Баланс Buypin: <b>$${d.wallet?.balance ?? '?'}</b>`);
    } catch(e) { await tgSend(cfg.ADMIN_CHAT, `❌ ${e.message}`); }
  }

  else if (text === '/orders') {
    const recent = Object.values(orders)
      .sort((a,b) => new Date(b.created_at)-new Date(a.created_at))
      .slice(0, 10);
    if (!recent.length) { await tgSend(cfg.ADMIN_CHAT, 'Заказов нет'); return; }
    const lines = recent.map(o =>
      `${statusE[o.status]||'❔'} <code>#${o.id.slice(0,8).toUpperCase()}</code> ${o.name} — ${o.buyer_name}`);
    await tgSend(cfg.ADMIN_CHAT, `📋 <b>Последние заказы:</b>\n\n${lines.join('\n')}`);
  }

  else if (text === '/help') {
    await tgSend(cfg.ADMIN_CHAT,
      `🤖 <b>Команды FrozenShop:</b>\n\n` +
      `/done_xxxxxxxx — выдать заказ\n` +
      `/reject_xxxxxxxx — отклонить заказ\n` +
      `/balance — баланс Buypin\n` +
      `/orders — последние 10 заказов`
    );
  }
});

// ─────────────────────────────────────────────────
//  ЗАПУСК
// ─────────────────────────────────────────────────
app.listen(PORT, () => {
  console.log(`🚀 FrozenShop Backend v2 on port ${PORT}`);
  console.log(`   BUYPIN_KEY  : ${cfg.BUYPIN_KEY  ? '✅ set' : '❌ NOT SET'}`);
  console.log(`   BOT_TOKEN   : ${cfg.BOT_TOKEN   ? '✅ set' : '❌ NOT SET'}`);
  console.log(`   ADMIN_CHAT  : ${cfg.ADMIN_CHAT  ? '✅ ' + cfg.ADMIN_CHAT : '❌ NOT SET'}`);
  console.log(`   Cards       : ${Object.keys(cfg.CARDS).join(', ') || 'none'}`);
  console.log(`   MLBB combos : ${Object.keys(MLBB_COMBOS).length} combinations`);
});
