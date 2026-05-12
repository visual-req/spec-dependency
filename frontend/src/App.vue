<script setup>
import { computed, ref } from "vue";

const activeTab = ref("scan");
const files = ref([]);
const loading = ref(false);
const result = ref(null);
const error = ref("");

const depsLoading = ref(false);
const depsError = ref("");
const depsData = ref(null);
const systemQuery = ref("");
const selectedSystemId = ref("");

const systems = computed(() => {
  const arr = depsData.value?.systems;
  return Array.isArray(arr) ? arr : [];
});

const filteredSystems = computed(() => {
  const q = (systemQuery.value || "").trim().toLowerCase();
  if (!q) return systems.value;
  return systems.value.filter((s) => {
    const hay = [
      s?.id,
      s?.name,
      s?.type,
      s?.description,
      ...(Array.isArray(s?.aliases) ? s.aliases : []),
      ...(Array.isArray(s?.keywords) ? s.keywords : []),
    ]
      .filter(Boolean)
      .join(" ")
      .toLowerCase();
    return hay.includes(q);
  });
});

const currentSystemId = computed(() => {
  if (selectedSystemId.value) return selectedSystemId.value;
  return filteredSystems.value?.[0]?.id || "";
});

const currentSystem = computed(() => {
  const id = currentSystemId.value;
  if (!id) return null;
  return systems.value.find((s) => s?.id === id) || null;
});

const scanFiles = computed(() => {
  const arr = result.value?.files;
  return Array.isArray(arr) ? arr : [];
});

function asArray(v) {
  return Array.isArray(v) ? v : [];
}

function fmtConfidence(v) {
  const n = typeof v === "number" ? v : Number(v);
  if (!Number.isFinite(n)) return "-";
  return `${Math.round(n * 100)}%`;
}

function countModuleDeps(modules) {
  const ms = asArray(modules);
  let total = 0;
  for (const m of ms) {
    total += asArray(m?.dependencies).length;
  }
  return total;
}

function selectSystem(id) {
  selectedSystemId.value = id;
}

function onFilesChange(e) {
  const list = e?.target?.files ? Array.from(e.target.files) : [];
  files.value = list;
}

async function onExtract() {
  error.value = "";
  result.value = null;
  if (!files.value.length) {
    error.value = "请选择文件（.doc/.docx）";
    return;
  }
  loading.value = true;
  try {
    const fd = new FormData();
    for (const f of files.value) {
      fd.append("files", f);
    }
    const resp = await fetch("/api/extract", { method: "POST", body: fd });
    const data = await resp.json();
    if (!resp.ok) {
      error.value = data?.error || "请求失败";
      return;
    }
    result.value = data;
  } catch (e) {
    error.value = e?.message || String(e);
  } finally {
    loading.value = false;
  }
}

async function loadDependencies() {
  depsError.value = "";
  depsData.value = null;
  depsLoading.value = true;
  try {
    const resp = await fetch("/api/dependencies");
    const data = await resp.json();
    if (!resp.ok) {
      depsError.value = data?.error || "请求失败";
      return;
    }
    depsData.value = data;
    if (!selectedSystemId.value && Array.isArray(data?.systems) && data.systems[0]?.id) {
      selectedSystemId.value = data.systems[0].id;
    }
  } catch (e) {
    depsError.value = e?.message || String(e);
  } finally {
    depsLoading.value = false;
  }
}

async function switchTab(tab) {
  activeTab.value = tab;
  if (tab === "deps" && !depsData.value && !depsLoading.value) {
    await loadDependencies();
  }
}
</script>

<template>
  <div>
    <div class="header">
      <div class="header-inner">
        <div class="brand">spec_dep</div>
        <div class="tabs">
          <button class="tab" :class="{ active: activeTab === 'scan' }" @click="switchTab('scan')">识别依赖</button>
          <button class="tab" :class="{ active: activeTab === 'deps' }" @click="switchTab('deps')">依赖列表</button>
        </div>
      </div>
    </div>

    <div class="wrap">
      <div v-if="activeTab === 'scan'">
        <div class="card">
          <div class="title">识别依赖</div>
          <div class="hint">上传需求文件，识别模块到外部系统/API 的映射。</div>
          <div class="row">
            <input type="file" multiple @change="onFilesChange" />
            <button class="btn" :disabled="loading" @click="onExtract">
              {{ loading ? "识别中..." : "开始识别" }}
            </button>
          </div>
          <div v-if="error" class="error">{{ error }}</div>
        </div>

        <div v-if="result" class="card">
          <div class="title">结果</div>
          <div class="scan-files">
            <div class="file-card" v-for="(f, fi) in scanFiles" :key="`${f?.file || 'file'}:${fi}`">
              <div class="file-head">
                <div class="file-title">{{ f?.file || "未命名文件" }}</div>
                <div class="file-meta">模块：{{ asArray(f?.modules).length }} / 依赖：{{ countModuleDeps(f?.modules) }}</div>
              </div>

              <div class="module" v-for="(m, mi) in asArray(f?.modules)" :key="`${m?.module || 'module'}:${mi}`">
                <div class="module-title">{{ m?.module || "global" }}</div>
                <div class="deps" v-if="asArray(m?.dependencies).length">
                  <div class="dep" v-for="(d, di) in asArray(m?.dependencies)" :key="`${d?.id || 'dep'}:${di}`">
                    <div class="dep-top">
                      <div class="dep-name">{{ d?.name || d?.id }}</div>
                      <div class="dep-meta">
                        <span class="mono">{{ d?.id }}</span>
                        <span class="sep">·</span>
                        <span class="mono">{{ d?.type }}</span>
                        <span class="sep">·</span>
                        <span class="mono">{{ fmtConfidence(d?.confidence) }}</span>
                      </div>
                    </div>
                    <div class="dep-evidence" v-if="d?.evidence">{{ d.evidence }}</div>
                    <div class="api-hits" v-if="asArray(d?.apis).length">
                      <div class="api-hit" v-for="(a, ai) in asArray(d?.apis)" :key="`${a?.id || 'api'}:${ai}`">
                        <div class="api-left">
                          <span class="method mono" v-if="a?.method">{{ a.method }}</span>
                          <span class="path mono" v-if="a?.path">{{ a.path }}</span>
                        </div>
                        <div class="api-right">
                          <div class="api-name">{{ a?.name || a?.id }}</div>
                          <div class="api-meta mono" v-if="a?.id">{{ a.id }} · {{ fmtConfidence(a?.confidence) }}</div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                <div class="empty" v-else>未识别到依赖</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-else>
        <div class="card">
          <div class="title">依赖列表</div>
          <div class="hint">来自 work/input/dependencies 下的 JSON。</div>
          <div class="row">
            <button class="btn secondary" :disabled="depsLoading" @click="loadDependencies">
              {{ depsLoading ? "加载中..." : "刷新" }}
            </button>
            <div class="meta" v-if="depsData?.file">文件：{{ depsData.file }}</div>
          </div>
          <div v-if="depsError" class="error">{{ depsError }}</div>
        </div>

        <div class="deps-layout" v-if="systems.length">
          <div class="card deps-sidebar">
            <div class="title">系统</div>
            <div class="hint">列表来自 {{ depsData?.file }}</div>
            <input class="search" v-model="systemQuery" placeholder="搜索：系统名 / ID / 关键词 / 描述" />
            <div class="system-list" v-if="filteredSystems.length">
              <button
                class="system-item"
                :class="{ active: s?.id === currentSystemId }"
                v-for="s in filteredSystems"
                :key="s.id"
                @click="selectSystem(s.id)"
              >
                <div class="system-top">
                  <div class="system-name">{{ s?.name }}</div>
                  <div class="system-count mono">{{ asArray(s?.apis).length }}</div>
                </div>
                <div class="system-sub">
                  <span class="mono">{{ s?.id }}</span>
                  <span class="sep">·</span>
                  <span class="mono">{{ s?.type }}</span>
                </div>
                <div class="system-desc" v-if="s?.description">{{ s.description }}</div>
              </button>
            </div>
            <div class="empty" v-else>没有匹配的系统</div>
          </div>

          <div class="card deps-detail" v-if="currentSystem">
            <div class="detail-head">
              <div class="detail-title">{{ currentSystem?.name }}</div>
              <div class="detail-meta">
                <span class="mono">{{ currentSystem?.id }}</span>
                <span class="sep">·</span>
                <span class="mono">{{ currentSystem?.type }}</span>
                <span class="sep">·</span>
                <span class="mono">{{ asArray(currentSystem?.apis).length }} APIs</span>
              </div>
            </div>

            <div class="detail-desc" v-if="currentSystem?.description">{{ currentSystem.description }}</div>

            <div class="tag-row" v-if="asArray(currentSystem?.aliases).length">
              <div class="tag-label">别名</div>
              <div class="tag-wrap">
                <span class="pill" v-for="(x, xi) in asArray(currentSystem?.aliases)" :key="`a:${xi}`">{{ x }}</span>
              </div>
            </div>

            <div class="tag-row" v-if="asArray(currentSystem?.keywords).length">
              <div class="tag-label">关键词</div>
              <div class="tag-wrap">
                <span class="pill" v-for="(x, xi) in asArray(currentSystem?.keywords)" :key="`k:${xi}`">{{ x }}</span>
              </div>
            </div>

            <div class="apis">
              <div class="apis-title">API 列表</div>
              <div class="api-list" v-if="asArray(currentSystem?.apis).length">
                <div class="api-item" v-for="(a, ai) in asArray(currentSystem?.apis)" :key="`${a?.id || 'api'}:${ai}`">
                  <div class="api-left">
                    <span class="method mono" v-if="a?.method">{{ a.method }}</span>
                    <span class="path mono" v-if="a?.path">{{ a.path }}</span>
                  </div>
                  <div class="api-right">
                    <div class="api-name">{{ a?.name || a?.id }}</div>
                    <div class="api-meta mono" v-if="a?.id">{{ a.id }}</div>
                    <div class="tag-wrap" v-if="asArray(a?.keywords).length">
                      <span class="pill" v-for="(x, xi) in asArray(a?.keywords).slice(0, 8)" :key="`ak:${ai}:${xi}`">{{ x }}</span>
                    </div>
                  </div>
                </div>
              </div>
              <div class="empty" v-else>该系统暂无 API</div>
            </div>
          </div>

          <div class="card deps-detail" v-else>
            <div class="empty">请选择一个系统查看详情</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.header {
  position: sticky;
  top: 0;
  background: white;
  border-bottom: 1px solid rgba(17, 24, 39, 0.1);
  z-index: 10;
}

.header-inner {
  width: 100%;
  margin: 0 auto;
  padding: 12px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.brand {
  font-weight: 800;
  letter-spacing: 0.3px;
}

.tabs {
  display: flex;
  align-items: center;
  gap: 8px;
}

.tab {
  border: 1px solid rgba(17, 24, 39, 0.12);
  background: white;
  color: rgba(17, 24, 39, 0.85);
  padding: 8px 12px;
  border-radius: 10px;
  font-weight: 600;
}

.tab.active {
  background: rgba(37, 99, 235, 0.08);
  border-color: rgba(37, 99, 235, 0.35);
  color: #1d4ed8;
}

.wrap {
  width: 100%;
  margin: 0 auto;
  padding: 18px 24px 48px;
}

.card {
  background: white;
  border: 1px solid rgba(17, 24, 39, 0.12);
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 16px;
}

.title {
  font-size: 18px;
  font-weight: 700;
}

.hint {
  margin-top: 8px;
  color: rgba(17, 24, 39, 0.65);
  font-size: 13px;
}

.row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 12px;
  flex-wrap: wrap;
}

.btn {
  background: #2563eb;
  border: 0;
  color: white;
  padding: 10px 14px;
  border-radius: 10px;
  font-weight: 600;
}

.btn.secondary {
  background: rgba(17, 24, 39, 0.06);
  color: rgba(17, 24, 39, 0.85);
  border: 1px solid rgba(17, 24, 39, 0.12);
}

.btn:disabled {
  opacity: 0.6;
}

.error {
  margin-top: 12px;
  color: #b91c1c;
}

.pre {
  margin-top: 12px;
  padding: 12px;
  border-radius: 10px;
  background: rgba(17, 24, 39, 0.04);
  overflow: auto;
  max-height: 540px;
  font-size: 12px;
}

.meta {
  color: rgba(17, 24, 39, 0.65);
  font-size: 12px;
}

.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
}

.sep {
  color: rgba(17, 24, 39, 0.35);
}

.empty {
  margin-top: 12px;
  color: rgba(17, 24, 39, 0.55);
  font-size: 13px;
}

.deps-layout {
  display: grid;
  grid-template-columns: 380px 1fr;
  gap: 16px;
}

.deps-layout .card {
  margin-bottom: 0;
}

.deps-sidebar {
  display: flex;
  flex-direction: column;
}

.search {
  margin-top: 12px;
  width: 100%;
  box-sizing: border-box;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid rgba(17, 24, 39, 0.12);
  outline: none;
  font-size: 13px;
}

.system-list {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  overflow: auto;
  max-height: 72vh;
  padding-right: 2px;
}

.system-item {
  text-align: left;
  border: 1px solid rgba(17, 24, 39, 0.12);
  background: white;
  border-radius: 12px;
  padding: 12px;
}

.system-item.active {
  border-color: rgba(37, 99, 235, 0.4);
  background: rgba(37, 99, 235, 0.05);
}

.system-top {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 10px;
}

.system-name {
  font-weight: 750;
}

.system-count {
  font-size: 12px;
  color: rgba(17, 24, 39, 0.65);
}

.system-sub {
  margin-top: 6px;
  color: rgba(17, 24, 39, 0.6);
  font-size: 12px;
}

.system-desc {
  margin-top: 8px;
  color: rgba(17, 24, 39, 0.75);
  font-size: 12px;
  line-height: 1.4;
}

.detail-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.detail-title {
  font-size: 18px;
  font-weight: 800;
}

.detail-meta {
  color: rgba(17, 24, 39, 0.65);
  font-size: 12px;
}

.detail-desc {
  margin-top: 10px;
  color: rgba(17, 24, 39, 0.8);
  line-height: 1.5;
}

.tag-row {
  margin-top: 14px;
  display: grid;
  grid-template-columns: 60px 1fr;
  gap: 10px;
  align-items: start;
}

.tag-label {
  color: rgba(17, 24, 39, 0.6);
  font-size: 12px;
  padding-top: 3px;
}

.tag-wrap {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.pill {
  border: 1px solid rgba(17, 24, 39, 0.12);
  background: rgba(17, 24, 39, 0.03);
  padding: 4px 8px;
  border-radius: 999px;
  font-size: 12px;
  color: rgba(17, 24, 39, 0.8);
}

.apis {
  margin-top: 16px;
}

.apis-title {
  font-weight: 750;
}

.api-list {
  margin-top: 10px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.api-item {
  border: 1px solid rgba(17, 24, 39, 0.12);
  border-radius: 12px;
  padding: 12px;
  display: grid;
  grid-template-columns: 260px 1fr;
  gap: 12px;
}

.api-left {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.method {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 12px;
  border: 1px solid rgba(37, 99, 235, 0.35);
  color: #1d4ed8;
  background: rgba(37, 99, 235, 0.06);
}

.path {
  font-size: 12px;
  color: rgba(17, 24, 39, 0.7);
}

.api-name {
  font-weight: 700;
}

.api-meta {
  margin-top: 4px;
  font-size: 12px;
  color: rgba(17, 24, 39, 0.6);
}

.scan-files {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.file-card {
  border: 1px solid rgba(17, 24, 39, 0.12);
  border-radius: 12px;
  padding: 14px;
}

.file-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.file-title {
  font-weight: 800;
}

.file-meta {
  color: rgba(17, 24, 39, 0.65);
  font-size: 12px;
}

.module {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(17, 24, 39, 0.08);
}

.module-title {
  font-weight: 750;
}

.deps {
  margin-top: 10px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.dep {
  border: 1px solid rgba(17, 24, 39, 0.12);
  border-radius: 12px;
  padding: 12px;
}

.dep-top {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.dep-name {
  font-weight: 750;
}

.dep-meta {
  color: rgba(17, 24, 39, 0.6);
  font-size: 12px;
}

.dep-evidence {
  margin-top: 8px;
  color: rgba(17, 24, 39, 0.75);
  font-size: 12px;
  line-height: 1.45;
  background: rgba(17, 24, 39, 0.03);
  border: 1px solid rgba(17, 24, 39, 0.08);
  border-radius: 10px;
  padding: 10px;
}

.api-hits {
  margin-top: 10px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.api-hit {
  border: 1px solid rgba(17, 24, 39, 0.1);
  border-radius: 12px;
  padding: 10px;
  display: grid;
  grid-template-columns: 260px 1fr;
  gap: 12px;
  background: rgba(17, 24, 39, 0.02);
}

.api-right {
  min-width: 0;
}

@media (max-width: 960px) {
  .deps-layout {
    grid-template-columns: 1fr;
  }

  .api-item,
  .api-hit {
    grid-template-columns: 1fr;
  }
}
</style>
