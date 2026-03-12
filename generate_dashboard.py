import json
import os
from datetime import datetime, timezone, timedelta

INPUT_FILE = "pharma_data.json"
OUTPUT_FILE = "index.html"

def generate_html(data):
    JST = timezone(timedelta(hours=9), 'JST')
    updated_at = data.get("updated_at", datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S"))
    
    # Escape data for JS injection
    json_data = json.dumps(data, ensure_ascii=False)

    template = """<!DOCTYPE html>
<html lang="ja">
<head>
  <base target="_top">
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>医薬品調達・在庫ダッシュボード</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://unpkg.com/vue@3/dist/vue.global.js"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    body { font-family: 'Inter', sans-serif; background-color: #f3f4f6; }
    .glass-card { background: rgba(255, 255, 255, 0.95); backdrop-filter: blur(10px); box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06); }
    .spinner { animation: spin 1s linear infinite; }
    @keyframes spin { to { transform: rotate(360deg); } }
    .fade-in { animation: fadeIn 0.4s ease-in-out; }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
    .alternative-card { background: linear-gradient(to right, #ffffff, #f0fdf4); border-left-color: #10b981 !important; }
    .badge-alt { background-color: #10b981; color: white; font-size: 0.7rem; padding: 0.15rem 0.4rem; border-radius: 4px; margin-right: 0.5rem; font-weight: bold; }
    .status-badge { display: inline-block; padding: 0.2rem 0.6rem; border-radius: 6px; font-size: 0.75rem; font-weight: 600; }
    .status-danger { background-color: #fee2e2; color: #b91c1c; border: 1px solid rgba(185, 28, 28, 0.1); }
    .status-success { background-color: #dcfce7; color: #166534; border: 1px solid rgba(22, 101, 52, 0.1); }
    .status-warning { background-color: #fef3c7; color: #b45309; border: 1px solid rgba(180, 83, 9, 0.1); }
    .card-header { padding: 0.75rem 1rem; color: white; font-weight: 600; }
    [v-cloak] { display: none; }
  </style>
</head>
<body class="antialiased text-gray-800">
  <div id="app" v-cloak class="min-h-screen flex flex-col items-center p-4 sm:p-6 md:p-8">
    <header class="w-full max-w-6xl mb-6 text-center">
      <h1 class="text-3xl font-bold text-indigo-700 flex items-center justify-center gap-3">
        <i class="fa-solid fa-pills"></i> 医薬品調達・在庫ダッシュボード
      </h1>
      <p class="text-gray-400 text-xs mt-2">最終更新: {{UPDATED_AT}}</p>
    </header>

    <nav class="w-full max-w-5xl mb-6">
      <div class="glass-card rounded-xl p-1 flex gap-1">
        <button @click="activeTab = 'dashboard'" :class="activeTab === 'dashboard' ? 'bg-indigo-600 text-white shadow' : 'text-gray-500 hover:bg-gray-100'" class="flex-1 py-2.5 rounded-lg text-sm font-semibold transition-all flex items-center justify-center gap-1">
          <i class="fa-solid fa-chart-line"></i> 統合
        </button>
        <button @click="activeTab = 'search'" :class="activeTab === 'search' ? 'bg-indigo-600 text-white shadow' : 'text-gray-500 hover:bg-gray-100'" class="flex-1 py-2.5 rounded-lg text-sm font-semibold transition-all flex items-center justify-center gap-1">
          <i class="fa-solid fa-magnifying-glass"></i> 薬を探す
        </button>
        <button @click="switchTab('live')" :class="activeTab === 'live' ? 'bg-indigo-600 text-white shadow' : 'text-gray-500 hover:bg-gray-100'" class="flex-1 py-2.5 rounded-lg text-sm font-semibold transition-all flex items-center justify-center gap-1">
          <i class="fa-solid fa-clock-rotate-left"></i> リアルタイム在庫
        </button>
      </div>
    </nav>

    <main class="w-full max-w-7xl">
      <!-- Dashboard Tab -->
      <div v-if="activeTab === 'dashboard'" class="grid grid-cols-1 md:grid-cols-3 gap-6 fade-in">
        <!-- Collabo Card -->
        <section class="glass-card rounded-2xl overflow-hidden flex flex-col h-[700px]">
          <div class="card-header bg-sky-400 flex justify-between">
            <span>Collabo Portal</span>
            <span class="text-xs bg-white/20 px-2 rounded-full">{{ pharmaData.collabo ? pharmaData.collabo.length : 0 }}件</span>
          </div>
          <div class="overflow-y-auto p-2 space-y-2">
            <div v-for="item in pharmaData.collabo" class="p-3 bg-white border border-gray-100 rounded-lg shadow-sm">
              <div class="text-[10px] text-gray-400 font-bold mb-1">{{ item.maker }}</div>
              <div class="font-bold text-sm text-gray-800 mb-1 leading-tight">{{ item.name }}</div>
              <div class="flex justify-between items-center mt-2">
                <span :class="getStatusClass(item.status)" class="status-badge">{{ item.status }}</span>
                <span class="text-[10px] text-gray-400">{{ item.date }}</span>
              </div>
              <div v-if="item.remarks" class="mt-2 text-[10px] text-amber-600 bg-amber-50 p-1.5 rounded border-l-2 border-amber-300">
                {{ item.remarks }}
              </div>
            </div>
          </div>
        </section>

        <!-- Medipal Card -->
        <section class="glass-card rounded-2xl overflow-hidden flex flex-col h-[700px]">
          <div class="card-header bg-green-600 flex justify-between">
            <span>MEDIPAL</span>
            <span class="text-xs bg-white/20 px-2 rounded-full">{{ pharmaData.medipal ? pharmaData.medipal.length : 0 }}件</span>
          </div>
          <div class="overflow-y-auto p-2 space-y-2">
            <div v-for="item in pharmaData.medipal" class="p-3 bg-white border border-gray-100 rounded-lg shadow-sm">
              <div class="text-[10px] text-gray-400 font-bold mb-1">{{ item.maker }}</div>
              <div class="font-bold text-sm text-gray-800 mb-1 leading-tight">{{ item.name }}</div>
              <div class="mt-2">
                <span :class="item.remarks && item.remarks.includes('調整') ? 'status-danger' : 'status-success'" class="status-badge">
                  {{ item.remarks && item.remarks.includes('調整') ? '出荷調整' : '通常' }}
                </span>
                <p class="text-[10px] text-gray-500 mt-1">{{ item.remarks }}</p>
              </div>
            </div>
          </div>
        </section>

        <!-- AlfWeb Card -->
        <section class="glass-card rounded-2xl overflow-hidden flex flex-col h-[700px]">
          <div class="card-header bg-blue-500 flex justify-between">
            <span>ALF-Web</span>
            <span class="text-xs bg-white/20 px-2 rounded-full">{{ pharmaData.alfweb ? pharmaData.alfweb.length : 0 }}件</span>
          </div>
          <div class="overflow-y-auto p-2 space-y-2">
            <div v-for="item in pharmaData.alfweb" class="p-3 bg-white border border-gray-100 rounded-lg shadow-sm">
              <div class="text-[10px] text-gray-400 font-bold mb-1">{{ item.maker }}</div>
              <div class="font-bold text-sm text-gray-800 mb-1 leading-tight">{{ item.name }}</div>
              <div class="flex justify-between items-center mt-2">
                <span class="status-badge status-danger">{{ item.status || '入荷未定' }}</span>
                <span v-if="item.date" class="text-[10px] text-gray-400">更新: {{ item.date }}</span>
              </div>
            </div>
          </div>
        </section>
      </div>

      <!-- Search Tab -->
      <div v-if="activeTab === 'search'" class="max-w-3xl mx-auto fade-in">
        <div class="glass-card rounded-2xl p-6 mb-6">
          <div class="relative flex items-center w-full h-14 rounded-xl bg-white overflow-hidden border-2 border-indigo-100 focus-within:border-indigo-500 transition-all">
            <div class="grid place-items-center h-full w-12 text-indigo-400">
              <i class="fa-solid fa-magnifying-glass"></i>
            </div>
            <input v-model="query" @keyup.enter="performLocalSearch" class="h-full w-full outline-none text-gray-700 text-lg font-medium pl-2" type="text" placeholder="薬の名前を入力...">
            <button @click="performLocalSearch" class="bg-indigo-600 text-white h-full px-8 font-semibold hover:bg-indigo-700 transition-colors">
              <span v-if="searching" class="flex items-center gap-2"><i class="fa-solid fa-circle-notch spinner"></i> 検索中</span>
              <span v-else>検索</span>
            </button>
          </div>
        </div>

        <div v-if="results.length > 0" class="space-y-4">
          <div v-for="item in results" :class="item.isPrimary === false ? 'alternative-card' : ''" class="glass-card rounded-xl p-5 border-l-4 border-indigo-500">
            <div class="flex justify-between items-start gap-4">
              <div class="flex-1">
                <div class="flex items-center gap-2 mb-1">
                  <span v-if="item.isPrimary === false" class="badge-alt">代替提案</span>
                  <span class="text-[10px] font-bold text-indigo-500 uppercase">薬品名</span>
                </div>
                <h3 class="text-xl font-bold text-gray-900 leading-tight">{{ item.name }}</h3>
                <div class="mt-3 flex gap-4">
                  <div class="bg-indigo-50 px-3 py-1 rounded border border-indigo-100 text-sm">
                    <span class="text-xs text-indigo-400 block font-bold">棚番</span>
                    <span class="font-bold text-indigo-800">{{ item.shelf || '-' }}</span>
                  </div>
                  <div class="bg-gray-50 px-3 py-1 rounded border border-gray-100 text-sm">
                    <span class="text-xs text-gray-400 block font-bold">在庫</span>
                    <span class="font-bold text-gray-800">{{ item.stock !== '' && item.stock !== undefined ? item.stock : '-' }}</span>
                  </div>
                  <div v-if="item.source" class="bg-gray-100 px-3 py-1 rounded border border-gray-200 text-sm">
                    <span class="text-xs text-gray-400 block font-bold">情報源</span>
                    <span class="font-medium text-gray-600 uppercase">{{ item.source }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div v-else-if="hasSearched && !searching" class="glass-card rounded-2xl p-10 text-center text-gray-400">
          <p v-if="errorMsg" class="text-red-500 mb-2">{{ errorMsg }}</p>
          <p>「{{ lastQuery }}」に一致する結果はありませんでした。</p>
        </div>
      </div>

      <!-- Real-time Stock Tab -->
      <div v-if="activeTab === 'live'" class="max-w-7xl mx-auto fade-in">
        <div class="glass-card rounded-2xl p-4 mb-6 flex justify-between items-center bg-indigo-50">
          <h2 class="text-lg font-bold text-indigo-800 flex items-center gap-2">
            <i class="fa-solid fa-signal"></i> 在庫一覧 (LIVE)
          </h2>
          <button @click="fetchLiveStocks" class="text-indigo-600 hover:text-indigo-800 text-sm font-bold flex items-center gap-1 transition-all">
            <i class="fa-solid fa-arrows-rotate" :class="{ 'spinner': loadingLive }"></i> 更新
          </button>
        </div>

        <div v-if="loadingLive" class="p-20 text-center">
          <i class="fa-solid fa-circle-notch spinner text-4xl text-indigo-600"></i>
          <p class="mt-4 text-gray-500 font-medium">GASバックエンドからデータを取得中...</p>
        </div>

        <div v-else-if="liveError" class="glass-card rounded-2xl p-10 text-center bg-red-50 border border-red-100">
          <i class="fa-solid fa-triangle-exclamation text-4xl text-red-500 mb-4 block"></i>
          <p class="text-red-700 font-bold">エラーが発生しました</p>
          <p class="text-red-500 text-sm mt-2">{{ liveError }}</p>
          <button @click="fetchLiveStocks" class="mt-6 bg-red-600 text-white px-6 py-2 rounded-lg font-bold hover:bg-red-700 transition-all">再試行</button>
        </div>

        <div v-else-if="liveStocks.length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div v-for="item in liveStocks" class="glass-card rounded-xl p-4 border border-gray-100 hover:border-indigo-200 transition-all flex flex-col">
            <div class="flex justify-between items-start mb-2 gap-2">
              <span class="text-[10px] font-bold text-gray-400 break-words">{{ item.maker || item.manufacturer || '不明' }}</span>
              <span class="bg-indigo-100 text-indigo-700 text-[10px] px-2 py-0.5 rounded font-bold shrink-0">{{ item.shelf || '棚番無' }}</span>
            </div>
            <h4 class="font-bold text-gray-800 text-sm leading-tight mb-2">{{ item.name || item.medicineName }}</h4>
            
            <div class="flex flex-wrap gap-1 mb-3">
              <span v-if="item.yj_code || item.code" class="text-[9px] bg-gray-100 text-gray-500 px-1.5 py-0.5 rounded font-mono">
                {{ item.yj_code || item.code }}
              </span>
              <span v-if="item.lot" class="text-[9px] bg-blue-50 text-blue-600 px-1.5 py-0.5 rounded">
                LOT: {{ item.lot }}
              </span>
              <span v-if="item.expiry" class="text-[9px] bg-orange-50 text-orange-600 px-1.5 py-0.5 rounded">
                期限: {{ item.expiry }}
              </span>
            </div>

            <div class="mt-auto flex justify-between items-end border-t border-gray-50 pt-2">
              <div class="text-[10px] text-gray-400">
                <span v-if="item.last_action">最終: {{ item.last_action }}</span>
              </div>
              <div class="flex items-baseline gap-1">
                <span class="text-[10px] text-gray-400 font-bold uppercase">在庫:</span>
                <span class="text-2xl font-black" :class="Number(item.stock || item.quantity) <= 0 ? 'text-red-500' : Number(item.stock || item.quantity) <= 10 ? 'text-orange-500' : 'text-gray-700'">
                  {{ item.stock !== undefined ? item.stock : (item.quantity !== undefined ? item.quantity : '-') }}
                </span>
              </div>
            </div>
          </div>
        </div>
        
        <div v-else-if="!loadingLive" class="glass-card rounded-2xl p-20 text-center text-gray-400">
          <i class="fa-solid fa-box-open text-4xl mb-4 block"></i>
          <p>在庫データがありません。</p>
          <button @click="fetchLiveStocks" class="mt-4 bg-indigo-600 text-white px-6 py-2 rounded-lg font-bold hover:bg-indigo-700 transition-all">データを取得する</button>
        </div>
      </div>
    </main>

    <footer class="mt-10 pb-6 text-center text-xs text-gray-400">
      <p>© 2026 薬の在庫・棚番検索システム (GitHub Pages版)</p>
    </footer>
  </div>

  <script>
    // --- Utils ---
    const toHalfWidth = (str) => {
      if (!str) return "";
      return str.replace(/[！-～]/g, s => String.fromCharCode(s.charCodeAt(0) - 0xfee0))
                .replace(/　/g, " ")
                .replace(/[ァ-ン]/g, s => {
                  const map = {
                    "ァ":"ｧ","ィ":"ｨ","ゥ":"ｩ","ェ":"ｪ","ォ":"ｫ","ッ":"ｯ","ャ":"ｬ","ュ":"ｭ","ョ":"ｮ",
                    "ア":"ｱ","イ":"ｲ","ウ":"ｳ","エ":"ｴ","オ":"ｵ","カ":"ｶ","キ":"ｷ","ク":"ｸ","ケ":"ｹ","コ":"ｺ",
                    "サ":"ｻ","シ":"ｼ","ス":"ｽ","セ":"ｾ","ソ":"ｿ","タ":"ﾀ","チ":"ﾁ","ツ":"ﾂ","テ":"ﾃ","ト":"ﾄ",
                    "ナ":"ﾅ","ニ":"ﾆ","ヌ":"ﾇ","ネ":"ﾈ","ノ":"ﾉ","ハ":"ﾊ","ヒ":"ﾋ","フ":"ﾌ","ヘ":"ﾍ","ホ":"ﾎ",
                    "マ":"ﾏ","ミ":"ﾐ","ム":"ﾑ","メ":"ﾒ","モ":"ﾓ","ヤ":"ﾔ","ユ":"ﾕ","ヨ":"ﾖ","ラ":"ﾗ","リ":"ﾘ",
                    "ル":"ﾙ","レ":"ﾚ","ロ":"ﾛ","ワ":"ﾜ","ヲ":"ｦ","ン":"ﾝ"
                  };
                  return map[s] || s;
                })
                .replace(/ガ/g,"ｶﾞ").replace(/ギ/g,"ｷﾞ").replace(/グ/g,"ｸﾞ").replace(/ゲ/g,"ｹﾞ").replace(/ゴ/g,"ｺﾞ")
                .replace(/ザ/g,"ｻﾞ").replace(/ジ/g,"ｼﾞ").replace(/ズ/g,"ｽﾞ").replace(/ゼ/g,"ｾﾞ").replace(/ゾ/g,"ｿﾞ")
                .replace(/ダ/g,"ﾀﾞ").replace(/ヂ/g,"ﾁﾞ").replace(/ヅ/g,"ﾂﾞ").replace(/デ/g,"ﾃﾞ").replace(/ド/g,"ﾄﾞ")
                .replace(/バ/g,"ﾊﾞ").replace(/ビ/g,"ﾋﾞ").replace(/ブ/g,"ﾌﾞ").replace(/ベ/g,"ﾍﾞ").replace(/ボ/g,"ﾎﾞ")
                .replace(/パ/g,"ﾊﾟ").replace(/ピ/g,"ﾋﾟ").replace(/プ/g,"ﾌﾟ").replace(/ペ/g,"ﾍﾟ").replace(/ポ/g,"ﾎﾟ")
                .replace(/ヴ/g,"ｳﾞ");
    };

    // --- GAS Polyfill for GitHub Pages ---
    const GAS_URL = 'https://script.google.com/macros/s/AKfycbwDhj91LpWaF6OWhTmr6hbYLgScu0tlBcs2Y4nyXvg2WAwybHYGd5-V579tf0I5_H2dCQ/exec';
    if (typeof google === 'undefined') {
      window.google = { script: { run: {} } };
      const createRun = () => {
        return {
          _onSuccess: null,
          _onFailure: null,
          withSuccessHandler(h) { this._onSuccess = h; return this; },
          withFailureHandler(h) { this._onFailure = h; return this; },
          _execute(action, params) {
            const hSuccess = this._onSuccess;
            const hFailure = this._onFailure;
            fetch(GAS_URL, {
              method: 'POST',
              headers: { 'Content-Type': 'text/plain;charset=utf-8' },
              body: JSON.stringify({ action: action, params: params })
            })
            .then(res => {
              if (!res.ok) throw new Error('HTTP ' + res.status);
              return res.json();
            })
            .then(data => {
              if (data.error) {
                console.error('GAS API Error:', data.error);
                if (hFailure) hFailure(data.error);
              }
              else if (hSuccess) hSuccess(data.result !== undefined ? data.result : data);
            })
            .catch(err => {
              console.error('Fetch Error:', err);
              if (hFailure) hFailure(err.message || err);
            });
          },
          searchMedicine(q) { this._execute('search', q); },
          getLiveStocks(p) { this._execute('live', p); }
        };
      };
      Object.defineProperty(window.google.script, 'run', { get: createRun });
    }

    // --- Vue Application ---
    const createApp = Vue.createApp;
    const ref = Vue.ref;
    const pharmaData = {{JSON_DATA}};

    createApp({
      setup() {
        const activeTab = ref('dashboard');
        const query = ref('');
        const lastQuery = ref('');
        const results = ref([]);
        const hasSearched = ref(false);
        const searching = ref(false);
        const errorMsg = ref('');
        const liveStocks = ref([]);
        const loadingLive = ref(false);
        const liveError = ref('');

        const getStatusClass = (status) => {
          if (!status) return 'status-warning';
          const s = status.toLowerCase();
          if (s.indexOf('辞退') !== -1 || s.indexOf('停止') !== -1 || s.indexOf('未定') !== -1 || s.indexOf('欠品') !== -1) return 'status-danger';
          if (s.indexOf('納品済') !== -1 || s.indexOf('準備中') !== -1 || s.indexOf('中') !== -1 || s.indexOf('済') !== -1) return 'status-success';
          return 'status-warning';
        };

        const performLocalSearch = () => {
          const rawQ = query.value.trim();
          if (!rawQ) return;
          const q = toHalfWidth(rawQ).toLowerCase();
          const tokens = q.split(/\s+/).filter(t => t);
          
          lastQuery.value = rawQ;
          hasSearched.value = true;
          searching.value = true;
          errorMsg.value = '';
          
          const localRes = [];
          ['collabo', 'medipal', 'alfweb'].forEach(function(key) {
            if (pharmaData[key]) {
              pharmaData[key].forEach(function(item) {
                const name = toHalfWidth(item.name || "").toLowerCase();
                const maker = toHalfWidth(item.maker || "").toLowerCase();
                const source = key.toLowerCase();
                
                // tokens match logic (AND search)
                const isMatch = tokens.every(token => 
                  name.indexOf(token) !== -1 || 
                  maker.indexOf(token) !== -1 ||
                  source.indexOf(token) !== -1
                );
                
                if (isMatch) {
                  localRes.push({
                    name: item.name,
                    shelf: item.shelf || '',
                    stock: item.stock || item.quantity || item.order_qty || item.deliv_qty || '',
                    source: key,
                    isPrimary: true
                  });
                }
              });
            }
          });
          
          results.value = localRes;

          // Call GAS for deeper inventory search
          google.script.run
            .withSuccessHandler(function(gasResults) {
              if (gasResults && Array.isArray(gasResults)) {
                gasResults.forEach(function(gi) {
                  // Normalize field names from GAS
                  const normItem = {
                    name: gi.name || gi.medicineName || gi.MedicineName || gi.displayName || '',
                    shelf: gi.shelf || gi.Shelf || gi.location || '',
                    stock: gi.stock !== undefined ? gi.stock : (gi.quantity !== undefined ? gi.quantity : (gi.Stock || '')),
                    source: 'inventory',
                    isPrimary: true
                  };

                  if (!normItem.name) return;

                  const exists = results.value.some(r => r.name === normItem.name);
                  if (!exists) {
                    results.value.push(normItem);
                  } else {
                    const matching = results.value.find(r => r.name === normItem.name);
                    if (!matching.shelf) matching.shelf = normItem.shelf;
                    if (!matching.stock) matching.stock = normItem.stock;
                  }
                });
              }
              searching.value = false;
            })
            .withFailureHandler(function(err) {
              console.error('GAS Search Failed:', err);
              errorMsg.value = '在庫データベースへの接続に失敗しました ( ' + err + ' )';
              searching.value = false;
            })
            .searchMedicine(rawQ);
        };

        const fetchLiveStocks = () => {
          loadingLive.value = true;
          liveError.value = '';
          google.script.run
            .withSuccessHandler(function(data) {
              console.log('Live Data:', data);
              // Handle various possible return structures from GAS
              let items = [];
              if (Array.isArray(data)) {
                items = data;
              } else if (data && data.items && Array.isArray(data.items)) {
                items = data.items;
              } else if (data && typeof data === 'object') {
                // If it's a single object or something else, wrap it if it looks like an item
                if (data.name || data.medicineName) items = [data];
                else items = [];
              }
              liveStocks.value = items;
              loadingLive.value = false;
            })
            .withFailureHandler(function(err) {
              console.error('GAS Live Failed:', err);
              liveError.value = 'リアルタイムデータの取得に失敗しました: ' + err;
              loadingLive.value = false;
            })
            .getLiveStocks(1);
        };

        const switchTab = (tab) => {
          activeTab.value = tab;
          if (tab === 'live' && liveStocks.value.length === 0) {
            fetchLiveStocks();
          }
        };

        return { 
          activeTab, pharmaData, query, lastQuery, results, hasSearched, 
          searching, errorMsg, liveStocks, loadingLive, liveError,
          getStatusClass, performLocalSearch, fetchLiveStocks, switchTab 
        };
      }
    }).mount('#app');
  </script>
</body>
</html>"""

    html = template.replace("{{JSON_DATA}}", json_data).replace("{{UPDATED_AT}}", updated_at)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Dashboard generated at: {os.path.abspath(OUTPUT_FILE)}")

if __name__ == "__main__":
    if os.path.exists(INPUT_FILE):
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        generate_html(data)
    else:
        print(f"Error: {INPUT_FILE} not found. Please run fetch_data.py first.")
