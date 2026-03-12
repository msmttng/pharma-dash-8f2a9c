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
        <div class="glass-card rounded-2xl p-4 mb-6 flex flex-col md:flex-row justify-between items-center gap-4 bg-indigo-50">
          <h2 class="text-lg font-bold text-indigo-800 flex items-center gap-2 shrink-0">
            <i class="fa-solid fa-signal"></i> 在庫一覧 (LIVE)
          </h2>
          
          <div class="relative w-full max-w-md">
            <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-indigo-400">
              <i class="fa-solid fa-magnifying-glass text-xs"></i>
            </div>
            <input v-model="liveQuery" type="text" placeholder="名前・メーカー・棚番で絞り込み..." class="block w-full pl-9 pr-3 py-2 border border-indigo-200 rounded-lg bg-white text-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all">
          </div>

          <button @click="fetchLiveStocks" class="text-indigo-600 hover:text-indigo-800 text-sm font-bold flex items-center gap-1 transition-all shrink-0">
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

        <div v-else-if="filteredLiveStocks.length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div v-for="item in filteredLiveStocks" class="glass-card rounded-xl p-4 border border-gray-100 hover:border-indigo-200 transition-all flex flex-col">
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
          <p v-if="liveQuery">「{{ liveQuery }}」に一致する在庫はありません。</p>
          <p v-else>在庫データがありません。</p>
          <button v-if="!liveQuery" @click="fetchLiveStocks" class="mt-4 bg-indigo-600 text-white px-6 py-2 rounded-lg font-bold hover:bg-indigo-700 transition-all">データを取得する</button>
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
        const liveQuery = ref('');
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
          const tokens = q.split(/\\s+/).filter(t => t);
          
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
                const shelf = toHalfWidth(item.shelf || "").toLowerCase();
                const source = key.toLowerCase();
                
                // tokens match logic (AND search)
                const isMatch = tokens.every(token => 
                  name.indexOf(token) !== -1 || 
                  maker.indexOf(token) !== -1 ||
                  shelf.indexOf(token) !== -1 ||
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

        const filteredLiveStocks = Vue.computed(() => {
          if (!liveQuery.value.trim()) return liveStocks.value;
          const q = toHalfWidth(liveQuery.value.trim()).toLowerCase();
          const tokens = q.split(/\\s+/).filter(t => t);
          return liveStocks.value.filter(item => {
            const name = toHalfWidth(item.name || item.medicineName || "").toLowerCase();
            const maker = toHalfWidth(item.maker || item.manufacturer || "").toLowerCase();
            const shelf = toHalfWidth(item.shelf || "").toLowerCase();
            return tokens.every(t => 
              name.indexOf(t) !== -1 || 
              maker.indexOf(t) !== -1 || 
              shelf.indexOf(t) !== -1
            );
          });
        });

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
          searching, errorMsg, liveStocks, liveQuery, filteredLiveStocks, loadingLive, liveError,
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
        print(f"Error: {INPUT_FILE} not found. Please run fetch_data.py first.")import json
import os
from datetime import datetime, timezone, timedelta

INPUT_FILE = "pharma_data.json"
OUTPUT_FILE = "index.html"

def generate_html(data):
    collabo_data = data.get("collabo", [])
    medipal_data = data.get("medipal", [])
    alfweb_data = data.get("alfweb", [])
    JST = timezone(timedelta(hours=9), 'JST')
    updated_at = data.get("updated_at", datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S"))

    html = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta name="robots" content="noindex, nofollow"> <!-- Prevent Search Engine Indexing -->
        <title>医薬品調達情報 統合ダッシュボード</title>
        <style>
            :root {{
                --primary: #42A5F5; /* ALF-Web Blue */
                --secondary: #008B3E; /* MEDIPAL Green */
                --tertiary: #4FC3F7; /* Collabo Water Blue */
                --bg: #f8fafc;
                --surface: #ffffff;
                --text: #1e293b;
                --text-secondary: #64748b;
                --border: #e2e8f0;
                --danger: #ef4444;
                --warning: #f59e0b;
                --status-bg-danger: #fee2e2;
                --status-text-danger: #b91c1c;
                --status-bg-warning: #fef3c7;
                --status-text-warning: #b45309;
            }}
            
            body {{
                font-family: 'Segoe UI', 'Noto Sans JP', sans-serif;
                background-color: var(--bg);
                color: var(--text);
                margin: 0;
                padding: 0;
                line-height: 1.6;
            }}
            
            .header {{
                background-color: var(--surface);
                padding: 1rem 1.5rem;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                display: flex;
                justify-content: space-between;
                align-items: center;
                position: sticky;
                top: 0;
                z-index: 100;
            }}
            
            .header h1 {{
                margin: 0;
                font-size: 1.2rem;
                color: var(--text);
                font-weight: 600;
            }}
            
            .last-updated {{
                font-size: 0.8rem;
                color: var(--text-secondary);
                background-color: #f0f0f0;
                padding: 0.3rem 0.6rem;
                border-radius: 20px;
            }}
            
            .container {{
                max-width: 100%;
                margin: 0.5rem auto;
                padding: 0 0.5rem;
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 0.75rem;
            }}
            
            .card {{
                background: var(--surface);
                border-radius: 8px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.05);
                overflow: hidden;
                display: flex;
                flex-direction: column;
                height: calc(100vh - 100px); /* Fill most of the screen height */
            }}
            
            .card-header {{
                padding: 0.75rem 1rem;
                color: white;
                font-weight: 600;
                display: flex;
                justify-content: space-between;
                align-items: center;
                font-size: 0.9rem;
            }}
            
            .card-collabo {{ background-color: #0000cd; }}
            .card-medipal {{ background-color: var(--secondary); }}
            .card-alfweb {{ background-color: var(--primary); }}
            
            .item-count {{
                background: rgba(255,255,255,0.2);
                padding: 0.1rem 0.5rem;
                border-radius: 12px;
                font-size: 0.8rem;
            }}
            
            /* High density for vertical monitors */
            .table-container {{
                overflow-x: auto;
                flex-grow: 1;
                overflow-y: auto;
                max-height: none;
            }}

            .fullscreen-btn {{
                background-color: var(--primary);
                color: white;
                border: none;
                padding: 0.4rem 0.8rem;
                border-radius: 4px;
                cursor: pointer;
                font-weight: 600;
                font-size: 0.8rem;
                display: flex;
                align-items: center;
                gap: 0.4rem;
                transition: background-color 0.2s;
            }}
            
            .fullscreen-btn:hover {{
                background-color: #1565C0;
            }}
            
            table {{
                width: 100%;
                border-collapse: collapse;
                text-align: left;
                font-size: 0.9rem;
            }}
            
            th {{
                background-color: #f8f9fa;
                padding: 0.8rem 1rem;
                font-weight: 600;
                color: var(--text-secondary);
                border-bottom: 2px solid var(--border);
                position: sticky;
                top: 0;
                z-index: 10;
                white-space: nowrap;
            }}
            
            td {{
                padding: 0.8rem 1rem;
                border-bottom: 1px solid var(--border);
                vertical-align: top;
            }}
            
            tr:hover td {{
                background-color: #f5f8ff;
            }}
            
            .status-badge {{
                display: inline-block;
                padding: 0.2rem 0.6rem;
                border-radius: 6px;
                font-size: 0.75rem;
                font-weight: 600;
                background-color: var(--status-bg-warning);
                color: var(--status-text-warning);
                border: 1px solid rgba(180, 83, 9, 0.1);
                white-space: nowrap;
            }}
            
            .status-danger {{
                background-color: var(--status-bg-danger);
                color: var(--status-text-danger);
                border: 1px solid rgba(185, 28, 28, 0.1);
            }}
            
            .status-success {{
                background-color: #dcfce7;
                color: #166534;
                border: 1px solid rgba(22, 101, 52, 0.1);
            }}
            
            .maker-name {{
                font-size: 0.8rem;
                color: var(--text-secondary);
                display: block;
                margin-bottom: 0.2rem;
            }}
            
            .product-name {{
                font-weight: 600;
                color: var(--text);
                margin-bottom: 0.2rem;
            }}
            
            .product-code {{
                font-size: 0.75rem;
                color: #888;
                font-family: monospace;
            }}
            
            .remarks {{
                font-size: 0.8rem;
                color: var(--text-secondary);
                background-color: #fff8e1;
                padding: 0.3rem 0.5rem;
                border-radius: 4px;
                border-left: 3px solid #ffca28;
                margin-top: 0.4rem;
                display: inline-block;
            }}
            
            .empty-state {{
                padding: 3rem;
                text-align: center;
                color: var(--text-secondary);
                font-style: italic;
            }}
        </style>
        <script>
            function toggleFullScreen() {{
                if (!document.fullscreenElement) {{
                    document.documentElement.requestFullscreen().catch(err => {{
                        alert(`Error attempting to enable full-screen mode: ${{err.message}} (${{err.name}})`);
                    }});
                }} else {{
                    if (document.exitFullscreen) {{
                        document.exitFullscreen();
                    }}
                }}
            }}
            
            function toggleWarningsOnly() {{
                const btn = document.getElementById("filter-btn");
                const isFiltering = btn.dataset.filtering === "true";
                
                // Toggle state
                btn.dataset.filtering = !isFiltering;
                btn.innerHTML = !isFiltering ? "🔄 すべて表示" : "⚠️ 警告・保留・調達中のみ";
                btn.style.backgroundColor = !isFiltering ? "var(--status-bg-warning)" : "#fff";
                btn.style.color = !isFiltering ? "var(--status-text-warning)" : "var(--text)";
                btn.style.border = !isFiltering ? "none" : "1px solid var(--border)";
                
                // Filter rows
                const rows = document.querySelectorAll("tbody tr");
                rows.forEach(row => {{
                    if (!isFiltering) {{
                        // Only show rows that contain danger OR warning statuses (調達中, 保留)
                        const hasDanger = row.querySelector(".status-danger") !== null;
                        const textContent = row.innerText;
                        const hasWarning = textContent.includes("保留") || textContent.includes("調達中");
                        
                        if (!hasDanger && !hasWarning) {{
                            row.style.display = "none";
                        }}
                    }} else {{
                        // Show all
                        row.style.display = "";
                    }}
                }});
                
                // Update counts on cards based on visible rows
                document.querySelectorAll('.card').forEach(card => {{
                    const visibleRows = card.querySelectorAll("tbody tr:not([style*='display: none'])").length;
                    const countSpan = card.querySelector(".item-count");
                    if (countSpan && card.querySelector("tbody")) {{
                        countSpan.innerText = visibleRows + "件";
                    }}
                }});
            }}
        </script>
    </head>
    <body>
        <div class="header">
            <div style="display: flex; align-items: center; gap: 1.5rem;">
                <h1>💊 医薬品調達情報 統合ダッシュボード</h1>
                <button class="fullscreen-btn" onclick="toggleFullScreen()">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"></path></svg>
                    全画面表示
                </button>
                <button id="filter-btn" data-filtering="false" onclick="toggleWarningsOnly()" style="
                    background-color: #fff;
                    color: var(--text);
                    border: 1px solid var(--border);
                    padding: 0.4rem 0.8rem;
                    border-radius: 4px;
                    cursor: pointer;
                    font-weight: 600;
                    font-size: 0.8rem;
                    transition: all 0.2s;
                ">⚠️ 警告・保留・調達中のみ</button>
            </div>
            <div class="last-updated">最終更新: {updated_at}</div>
        </div>
        
        <div class="container">
    """

    # Collabo Card
    html += f"""
            <div class="card">
                <div class="card-header card-collabo">
                    <span>Collabo Portal (全ステータス表示)</span>
                    <span class="item-count">{len(collabo_data)}件</span>
                </div>
                <div class="table-container">
    """
    if collabo_data:
        html += "<table><thead><tr><th>品名/メーカー</th><th>状況/納期</th><th style='min-width:110px;white-space:nowrap;'>数量</th></tr></thead><tbody>"
        for item in collabo_data:
            remarks_html = f'<div class="remarks">{item.get("remarks", "")}</div>' if item.get("remarks") else ""
            
            status_text = item.get("status", "")
            if "辞退" in status_text or "停止" in status_text:
                status_class = "status-danger"
            elif "納品済" in status_text or "出荷準備中" in status_text or "本日" in status_text or "明日" in status_text:
                status_class = "status-success"
            else:
                status_class = ""
                
            date_html = f'<div style="font-size:0.8rem; margin-top:4px;">受付: {item.get("date")}</div>' if item.get("date") else ""
            
            html += f"""
                        <tr>
                            <td>
                                <span class="maker-name">{item.get("maker", "")}</span>
                                <div class="product-name">{item.get("name", "")}</div>
                                <span class="product-code">JAN: {item.get("code", "")}</span>
                                {remarks_html}
                            </td>
                            <td style="white-space: nowrap;">
                                <span class="status-badge {status_class}">{item.get("status", "")}</span>
                                {date_html}
                            </td>
                            <td style="white-space: nowrap; min-width: 110px;">
                                <div>発注: <b>{item.get("order_qty", "-")}</b></div>
                                <div>納品予定: <b>{item.get("deliv_qty", "-")}</b></div>
                            </td>
                        </tr>
        """
        html += "</tbody></table>"
    else:
        html += '<div class="empty-state">該当データなし</div>'
    html += "</div></div>"

    # Medipal Card
    html += f"""
            <div class="card">
                <div class="card-header card-medipal">
                    <span>MEDIPAL (全ステータス表示)</span>
                    <span class="item-count">{len(medipal_data)}件</span>
                </div>
                <div class="table-container">
    """
    if medipal_data:
        html += "<table style='table-layout: fixed; width: 100%;'><thead><tr><th style='width: 55%;'>品名/メーカー</th><th style='width: 25%;'>状況・備考</th><th style='width: 20%; white-space:nowrap;'>数量</th></tr></thead><tbody>"
        for item in medipal_data:
            remarks = item.get("remarks", "")
            is_warning = "調整" in remarks or "未定" in remarks or "欠品" in remarks
            status_class = "status-danger" if is_warning else "status-success"
            status_label = "入荷未定" if is_warning else "通常"
            remarks_html = f'<div style="font-size:0.8rem; margin-top:4px; white-space:normal;">{remarks}</div>' if is_warning else ""

            html += f"""
                        <tr>
                            <td style="word-break: break-all;">
                                <span class="maker-name">{item.get("maker", "")}</span>
                                <div class="product-name">{item.get("name", "")}</div>
                                <span class="product-code">{item.get("code", "")}</span>
                            </td>
                            <td style="white-space: nowrap;">
                                <span class="status-badge {status_class}">{status_label}</span>
                                {remarks_html}
                            </td>
                            <td style="white-space: nowrap;">
                                <div>発注: <b>{item.get("order_qty", "-")}</b></div>
                                <div>納品予定: <b>{item.get("deliv_qty", "-")}</b></div>
                            </td>
                        </tr>
        """
        html += "</tbody></table>"
    else:
        html += '<div class="empty-state">該当データなし</div>'
    html += "</div></div>"

    # ALF-Web Card
    html += f"""
            <div class="card">
                <div class="card-header card-alfweb">
                    <span>ALF-Web (出荷停止・入荷未定)</span>
                    <span class="item-count">{len(alfweb_data)}件</span>
                </div>
                <div class="table-container">
    """
    if alfweb_data:
        html += "<table><thead><tr><th>品名/メーカー</th><th>状況・備考</th><th>数量</th></tr></thead><tbody>"
        for item in alfweb_data:
            date_html = f'<div style="font-size:0.8rem; margin-top:4px;">更新: {item.get("date")}</div>' if item.get("date") else ""
            html += f"""
                        <tr>
                            <td>
                                <span class="maker-name">{item.get("maker", "")}</span>
                                <div class="product-name">{item.get("name", "")}</div>
                            </td>
                            <td style="white-space: nowrap;">
                                <span class="status-badge status-danger">{item.get("status", "入荷未定")}</span>
                                {date_html}
                            </td>
                            <td>
                                <div>発注: <b>{item.get("order_qty", "-")}</b></div>
                                <div>納品予定: <b>{item.get("deliv_qty", "-")}</b></div>
                            </td>
                        </tr>
        """
        html += "</tbody></table>"
    else:
        html += '<div class="empty-state">該当データなし</div>'
    html += "</div></div>"

    html += """
        </div>
    </body>
    </html>
    """

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
