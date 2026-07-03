<template>
  <!-- ════════════════════════════════════════════════════════════════
       创建区 — 话题输入 + 配置
       ════════════════════════════════════════════════════════════════ -->
  <div v-if="!session.started" class="landing">
    <div class="landing-bg">
      <div class="landing-orbs">
        <div class="orb orb-1"></div>
        <div class="orb orb-2"></div>
        <div class="orb orb-3"></div>
      </div>
    </div>

    <div class="landing-content">
      <!-- Logo / Brand -->
      <div class="landing-brand">
        <span class="brand-icon">🎙️</span>
        <h1 class="brand-title">AI 圆桌讨论</h1>
        <p class="brand-subtitle">智能演播厅 —— 让思想碰撞，让观点发光</p>
      </div>

      <!-- 配置卡片 -->
      <div class="landing-card">
        <div class="landing-card-glow"></div>

        <div class="form-group">
          <label class="form-label" for="topicInput">
            <span class="label-icon">💬</span>
            讨论话题
          </label>
          <div class="textarea-wrapper">
            <textarea
              id="topicInput"
              v-model="session.topic"
              class="form-textarea"
              placeholder="输入一个你感兴趣的话题，例如：人工智能是否会取代人类工作？"
              rows="3"
              maxlength="500"
            ></textarea>
            <span class="textarea-count">{{ session.topic.length }}/500</span>
          </div>
        </div>

        <div class="form-group">
          <label class="form-label" for="expertCount">
            <span class="label-icon">👥</span>
            专家人数
          </label>
          <div class="expert-count-row">
            <input
              id="expertCount"
              v-model.number="session.expert_count"
              type="range"
              class="form-slider"
              min="2"
              max="10"
              step="1"
            />
            <div class="count-display">
              <span class="count-value">{{ session.expert_count }}</span>
              <span class="count-unit">位专家</span>
            </div>
          </div>
          <div class="slider-labels">
            <span>最少 2 位</span>
            <span>最多 10 位</span>
          </div>
        </div>

        <button
          class="btn-start"
          @click="startDiscussion"
          :disabled="!session.topic.trim() || session.loading"
        >
          <span class="btn-start-icon">🎬</span>
          <span class="btn-start-text">{{ session.loading ? '创建中…' : '开始讨论' }}</span>
          <span class="btn-start-glow"></span>
        </button>

        <p class="landing-hint">你将看到 AI 专家们围绕话题展开实时讨论，精彩观点实时呈现</p>
      </div>
    </div>
  </div>

  <!-- ════════════════════════════════════════════════════════════════
       演播厅模式
       ════════════════════════════════════════════════════════════════ -->
  <div v-else class="studio">
    <!-- 背景装饰 -->
    <div class="studio-bg">
      <div class="studio-grid"></div>
      <div class="studio-vignette"></div>
    </div>

    <!-- ─── 顶部标题栏 ─── -->
    <header class="studio-header">
      <div class="header-left">
        <span class="header-logo">🎙️</span>
        <h2 class="header-topic">{{ session.topic }}</h2>
      </div>
      <div class="header-center">
        <div class="live-indicator" :class="statusVariant">
          <span class="live-dot"></span>
          <span class="live-label">{{ statusLabel }}</span>
        </div>
      </div>
      <div class="header-right">
        <button class="btn-icon" title="重置" @click="resetSession">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>
            <path d="M3 3v5h5"/>
          </svg>
        </button>
      </div>
    </header>

    <!-- ─── 错误提示 ─── -->
    <div v-if="session.error" class="studio-error">
      <span>⚠️</span>
      <span>{{ session.error }}</span>
      <button @click="session.error = ''">&times;</button>
    </div>

    <!-- ─── 主体区域 ─── -->
    <div class="studio-body">
      <!-- 左侧嘉宾席 -->
      <aside class="panel panel-left">
        <div class="panel-header">
          <span class="panel-icon">🎭</span>
          <span class="panel-title">嘉宾阵容</span>
          <span class="panel-count">{{ allParticipants.length }} 位</span>
        </div>
        <div class="panel-body">
          <div
            v-for="p in allParticipants"
            :key="p.id"
            class="guest-card"
            :class="{
              'guest-host': p.is_host,
              'guest-speaking': currentSpeakerId === p.id,
            }"
          >
            <div
              class="guest-avatar"
              :style="{ background: p.color + '22', borderColor: p.color }"
            >
              <span class="guest-emoji">{{ p.avatar_emoji }}</span>
              <div
                v-if="currentSpeakerId === p.id"
                class="guest-speaking-ring"
                :style="{ borderColor: p.color }"
              ></div>
            </div>
            <div class="guest-info">
              <div class="guest-name-row">
                <span class="guest-name" :style="{ color: p.color }">
                  {{ p.name }}
                </span>
                <span v-if="p.is_host" class="guest-badge">主持</span>
              </div>
              <div class="guest-title">{{ p.title }}</div>
              <div class="guest-stance" :style="{ background: p.color + '18' }">
                {{ p.stance }}
              </div>
            </div>
            <div class="guest-color-bar" :style="{ background: p.color }"></div>
            <!-- 正在发言光效 -->
            <div
              v-if="currentSpeakerId === p.id"
              class="guest-soundwave"
              :style="{ '--wave-color': p.color }"
            >
              <span></span><span></span><span></span><span></span><span></span>
            </div>
          </div>
        </div>
      </aside>

      <!-- 中间发言区 -->
      <main class="panel panel-center">
        <div class="panel-header">
          <span class="panel-icon">📋</span>
          <span class="panel-title">讨论实况</span>
          <span class="panel-count">{{ session.totalSpeeches }} 条发言</span>
        </div>
        <div
          ref="speechAreaRef"
          class="panel-body speech-area"
          @scroll="handleScroll"
        >
          <!-- 空状态 -->
          <div v-if="session.transcripts.length === 0" class="speech-empty">
            <div class="empty-icon">🤖</div>
            <p class="empty-text">等待讨论开始……</p>
            <p class="empty-hint">AI 专家正在准备观点</p>
            <div class="empty-loader">
              <span></span><span></span><span></span>
            </div>
          </div>

          <!-- 发言列表 -->
          <div
            v-for="(t, idx) in session.transcripts"
            :key="t.id"
            class="speech-item"
            :class="{
              'speech-host': t.speaker_type === 'host',
              'speech-expert': t.speaker_type === 'expert',
            }"
          >
            <!-- 时间线 + 色条 -->
            <div class="speech-timeline">
              <div
                class="timeline-dot"
                :style="{
                  background: t.speaker_type === 'host' ? '#fbbf24' : (t.speakerColor || '#6366f1'),
                  boxShadow: '0 0 8px ' + (t.speaker_type === 'host' ? '#fbbf24' : (t.speakerColor || '#6366f1')) + '66'
                }"
              ></div>
              <div
                v-if="idx < session.transcripts.length - 1"
                class="timeline-line"
                :style="{
                  background: 'linear-gradient(to bottom, ' + (t.speaker_type === 'host' ? '#fbbf24' : (t.speakerColor || '#6366f1')) + '44, transparent)'
                }"
              ></div>
            </div>

            <!-- 发言卡片 -->
            <div
              class="speech-card"
              :style="{
                borderImage: t.speaker_type === 'host'
                  ? 'linear-gradient(135deg, #fbbf24, #f59e0b) 1'
                  : 'none',
                borderColor: t.speaker_type === 'host' ? '#fbbf24' : 'transparent',
              }"
            >
              <!-- 专家颜色边条 -->
              <div
                v-if="t.speaker_type === 'expert'"
                class="speech-color-bar"
                :style="{ background: t.speakerColor || '#6366f1' }"
              ></div>

              <div class="speech-header">
                <div class="speech-avatar-wrapper">
                  <span class="speech-emoji">{{ t.avatar_emoji }}</span>
                </div>
                <div class="speech-meta">
                  <div class="speech-speaker-row">
                    <span
                      class="speech-name"
                      :style="{ color: t.speaker_type === 'host' ? '#fbbf24' : (t.speakerColor || '#6366f1') }"
                    >
                      {{ t.speaker_name }}
                    </span>
                    <span v-if="t.speaker_type === 'host'" class="speech-badge">主持人</span>
                  </div>
                  <div class="speech-title">{{ t.speakerTitle || '' }}</div>
                </div>
                <div class="speech-time">{{ formatTime(t.created_at) }}</div>
              </div>

              <div class="speech-content">{{ t.content }}</div>
            </div>
          </div>

          <!-- 讨论已结束 -->
          <div v-if="session.status === 'concluded'" class="speech-concluded">
            <div class="concluded-icon">🏁</div>
            <p class="concluded-text">讨论已结束</p>
            <p class="concluded-hint">共 {{ session.totalSpeeches }} 条发言</p>
          </div>
        </div>

        <!-- 滚动到底部按钮 -->
        <button
          v-if="!isAutoScroll && session.transcripts.length > 0"
          class="btn-scroll-bottom"
          @click="scrollToBottom"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="m6 9 6 6 6-6"/>
          </svg>
          <span>最新发言</span>
        </button>
      </main>

      <!-- 右侧信息面板 -->
      <aside class="panel panel-right">
        <div class="panel-header">
          <span class="panel-icon">📊</span>
          <span class="panel-title">讨论数据</span>
        </div>
        <div class="panel-body">
          <!-- 讨论状态 -->
          <div class="stat-card">
            <div class="stat-label">讨论状态</div>
            <div class="stat-value-row">
              <span class="stat-dot" :class="statusVariant"></span>
              <span class="stat-text">{{ statusLabel }}</span>
            </div>
          </div>

          <!-- 发言统计 -->
          <div class="stat-card">
            <div class="stat-label">发言总数</div>
            <div class="stat-value large">{{ session.totalSpeeches }}</div>
          </div>

          <!-- 嘉宾统计 -->
          <div class="stat-card">
            <div class="stat-label">嘉宾阵容</div>
            <div class="stat-avatars">
              <span
                v-for="p in allParticipants"
                :key="p.id"
                class="stat-avatar-item"
                :class="{ 'stat-speaking': currentSpeakerId === p.id }"
                :style="{ borderColor: p.color }"
                :title="p.name"
              >
                {{ p.avatar_emoji }}
              </span>
            </div>
          </div>

          <!-- 发言活跃度 -->
          <div class="stat-card">
            <div class="stat-label">发言活跃度</div>
            <div class="activity-list">
              <div
                v-for="p in allParticipants"
                :key="p.id"
                class="activity-row"
              >
                <span class="activity-emoji">{{ p.avatar_emoji }}</span>
                <span class="activity-name" :style="{ color: p.color }">{{ p.name }}</span>
                <div class="activity-bar-bg">
                  <div
                    class="activity-bar"
                    :style="{
                      width: getActivityPercent(p.id) + '%',
                      background: p.color,
                    }"
                  ></div>
                </div>
                <span class="activity-count">{{ getSpeakerCount(p.id) }}</span>
              </div>
            </div>
          </div>

          <!-- ─── 结论展示 ─── -->
          <div v-if="session.conclusion" class="stat-card">
            <div class="stat-label">讨论结论</div>
            <div class="conclusion-section">
              <div v-for="c in session.conclusion?.consensus || []" :key="c.id" class="conclusion-item">
                <span class="conclusion-icon">📌</span>
                <span class="conclusion-text">{{ c.summary }}</span>
                <span class="conclusion-tag" :class="'tag-' + c.degree">{{ c.degree }}</span>
              </div>
              <div v-if="session.conclusion?.divergences?.length">
                <div v-for="d in session.conclusion?.divergences || []" :key="d.id" class="conclusion-item">
                  <span class="conclusion-icon">⚡</span>
                  <span class="conclusion-text">{{ d.description }}</span>
                  <span class="conclusion-tag" :class="'tag-' + d.severity">{{ d.severity }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- ─── 结论生成按钮 ─── -->
          <div v-if="session.status === 'concluded' && !session.conclusion" class="stat-card" style="text-align:center;padding:0.6rem">
            <button @click="generateConclusion" class="btn-conclusion">🏁 生成讨论结论</button>
          </div>
        </div>
      </aside>
    </div>

    <!-- ─── 底部信息栏 ─── -->
    <footer class="studio-footer">
      <div class="footer-item">
        <span class="footer-icon">📌</span>
        <span class="footer-label">话题：</span>
        <span class="footer-value">{{ session.topic }}</span>
      </div>
      <div class="footer-divider"></div>
      <div class="footer-item">
        <span class="footer-icon">🗣️</span>
        <span class="footer-label">发言：</span>
        <span class="footer-value">{{ session.totalSpeeches }} 条</span>
      </div>
      <div class="footer-divider"></div>
      <div class="footer-item">
        <span class="footer-icon">👥</span>
        <span class="footer-label">嘉宾：</span>
        <span class="footer-value">{{ allParticipants.length }} 位</span>
      </div>
      <div class="footer-divider" v-if="session.status === 'discussing'"></div>
      <div class="footer-item" v-if="session.status === 'discussing'">
        <span class="footer-pulse"></span>
        <span class="footer-label status-live">讨论进行中</span>
      </div>
    </footer>
  </div>
</template>

<script setup>
/**
 * AI 圆桌讨论 — 主页面组件
 *
 * 通过真实 API 与 Flask 后端交互：
 *   POST /api/sessions          — 创建讨论会话
 *   EventSource /api/sessions/{id}/events — SSE 实时事件流
 *   GET  /api/sessions/{id}/transcript    — 获取历史发言
 *   POST /api/sessions/{id}/conclusion    — 生成共识结论
 */
import { ref, reactive, computed, watch, nextTick, onUnmounted } from 'vue'

// ══════════════════════════════════════════════════════════════════════════
// 常量
// ══════════════════════════════════════════════════════════════════════════

const API_BASE = 'http://localhost:8080/api'

/** 主持人（前端本地构造，后端不返回此对象） */
const HOST = {
  id: 'host',
  name: '主持人',
  title: 'AI 圆桌讨论 · 主持人',
  stance: '引导讨论，汇聚观点',
  color: '#fbbf24',
  avatar_emoji: '🎙️',
  sort_order: 0,
  is_host: true,
}

// ══════════════════════════════════════════════════════════════════════════
// 响应式状态
// ══════════════════════════════════════════════════════════════════════════

const session = reactive({
  id: '',
  topic: '',
  expert_count: 4,
  status: 'pending',
  created_at: '',
  started: false,
  loading: false,
  error: '',
  experts: [],
  transcripts: [],
  totalSpeeches: 0,
  eventSource: null,
  conclusion: null,
})

const currentSpeakerId = ref(null)
const speechAreaRef = ref(null)
const isAutoScroll = ref(true)

// ─── 计算属性 ────────────────────────────────────────────
const allParticipants = computed(() => [HOST, ...session.experts])

const statusLabel = computed(() => {
  const map = {
    pending: '待生成',
    generating: '专家生成中',
    discussing: '讨论中',
    concluded: '已结束',
    error: '出错',
  }
  return map[session.status] || session.status
})

const statusVariant = computed(() => {
  const map = {
    pending: 'pending',
    generating: 'generating',
    discussing: 'discussing',
    concluded: 'concluded',
    error: 'error',
  }
  return map[session.status] || 'pending'
})

// ─── 发言人信息查询 ──────────────────────────────────
function getSpeakerInfo(speakerType, speakerId) {
  if (speakerType === 'host') return HOST
  return session.experts.find(e => e.id === speakerId) || null
}

function getSpeakerColor(speakerType, speakerId) {
  const info = getSpeakerInfo(speakerType, speakerId)
  return info ? info.color : '#6366f1'
}

function getSpeakerTitle(speakerType, speakerId) {
  const info = getSpeakerInfo(speakerType, speakerId)
  return info ? info.title : ''
}

// ─── 开始讨论 — POST /api/sessions ─────────────────────
async function startDiscussion() {
  if (!session.topic.trim()) return

  session.loading = true
  session.error = ''

  try {
    const resp = await fetch(API_BASE + '/sessions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        topic: session.topic,
        expert_count: session.expert_count,
      }),
    })

    if (!resp.ok) {
      const err = await resp.json()
      throw new Error(err.error?.message || '创建会话失败')
    }

    const data = await resp.json()

    session.id = data.id
    session.status = data.status
    session.created_at = data.created_at
    session.experts = data.experts || []
    session.transcripts = []
    session.totalSpeeches = 0
    session.started = true
    session.loading = false

    nextTick(() => window.scrollTo({ top: 0, behavior: 'smooth' }))

    connectSSE(data.id)
    fetchTranscripts(data.id)

  } catch (err) {
    session.loading = false
    session.error = err.message
  }
}

// ─── SSE 事件流 — EventSource ──────────────────────────
let sseRetryCount = 0

function connectSSE(sessionId) {
  if (session.eventSource) {
    session.eventSource.close()
  }

  sseRetryCount = 0
  const es = new EventSource(API_BASE + '/sessions/' + sessionId + '/events')
  session.eventSource = es

  es.addEventListener('session.status', (e) => {
    try {
      const data = JSON.parse(e.data)
      session.status = data.status
    } catch (err) {
      console.error('SSE parse session.status error:', err)
    }
  })

  es.addEventListener('transcript.new', (e) => {
    try {
      const data = JSON.parse(e.data)
      addTranscriptFromSSE(data)
    } catch (err) {
      console.error('SSE parse transcript.new error:', err)
    }
  })

  es.addEventListener('heartbeat', () => {
    // 保活信号，无需处理
  })

  es.onerror = () => {
    sseRetryCount++
    if (sseRetryCount > 5) {
      session.error = '与服务器的实时连接已断开，请刷新页面重试'
    }
  }

  es.onopen = () => {
    sseRetryCount = 0
  }
}

// ─── 处理 SSE 新发言 ──────────────────────────────────
function addTranscriptFromSSE(data) {
  const t = {
    ...data,
    speakerColor: getSpeakerColor(data.speaker_type, data.speaker_id),
    speakerTitle: getSpeakerTitle(data.speaker_type, data.speaker_id),
  }

  session.transcripts.push(t)
  session.totalSpeeches++

  currentSpeakerId.value = data.speaker_type === 'host' ? 'host' : data.speaker_id

  if (isAutoScroll.value) {
    nextTick(() => {
      const el = speechAreaRef.value
      if (el) {
        el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' })
      }
    })
  }
}

// ─── 获取历史发言 — GET /api/sessions/{id}/transcript ──
async function fetchTranscripts(sessionId, after) {
  try {
    let url = API_BASE + '/sessions/' + sessionId + '/transcript'
    if (after != null) url += '?after=' + after
    const resp = await fetch(url)
    if (!resp.ok) return

    const data = await resp.json()
    const mapped = (data.transcripts || []).map(t => ({
      ...t,
      speakerColor: getSpeakerColor(t.speaker_type, t.speaker_id),
      speakerTitle: getSpeakerTitle(t.speaker_type, t.speaker_id),
    }))

    if (after == null) {
      session.transcripts = mapped
    } else {
      mapped.forEach(t => {
        if (!session.transcripts.find(et => et.id === t.id)) {
          session.transcripts.push(t)
        }
      })
    }
    session.totalSpeeches = session.transcripts.length

    if (data.has_more && data.next_cursor) {
      fetchTranscripts(sessionId, data.next_cursor)
    }
  } catch (err) {
    console.error('Fetch transcripts error:', err)
  }
}

// ─── 生成结论 — POST /api/sessions/{id}/conclusion ─────
async function generateConclusion() {
  if (!session.id || session.conclusion) return

  try {
    const resp = await fetch(API_BASE + '/sessions/' + session.id + '/conclusion', {
      method: 'POST',
    })
    if (resp.ok) {
      session.conclusion = await resp.json()
    }
  } catch (err) {
    console.error('Generate conclusion error:', err)
  }
}

// ─── 监听状态变更，自动生成结论 ──────────────────────────
watch(() => session.status, (newStatus) => {
  if (newStatus === 'concluded') {
    generateConclusion()
  }
})

// ─── 重置 ────────────────────────────────────────────────
function resetSession() {
  if (session.eventSource) {
    session.eventSource.close()
    session.eventSource = null
  }
  session.id = ''
  session.status = 'pending'
  session.started = false
  session.loading = false
  session.error = ''
  session.experts = []
  session.transcripts = []
  session.totalSpeeches = 0
  session.conclusion = null
  currentSpeakerId.value = null
}
// ─── 滚动控制 ────────────────────────────────────────────
function handleScroll() {
  const el = speechAreaRef.value
  if (!el) return
  const threshold = 80
  isAutoScroll.value = (el.scrollHeight - el.scrollTop - el.clientHeight) < threshold
}

function scrollToBottom() {
  isAutoScroll.value = true
  nextTick(() => {
    const el = speechAreaRef.value
    if (el) {
      el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' })
    }
  })
}

// ─── 格式化时间 ───────────────────────────────────────────
function formatTime(isoString) {
  const d = new Date(isoString)
  const h = d.getHours().toString().padStart(2, '0')
  const m = d.getMinutes().toString().padStart(2, '0')
  const s = d.getSeconds().toString().padStart(2, '0')
  return `${h}:${m}:${s}`
}

// ─── 清理 ────────────────────────────────────────────────
onUnmounted(() => {
  if (session.eventSource) {
    session.eventSource.close()
  }
})

// ─── 获取发言计数 ─────────────────────────────────────────
function getSpeakerCount(speakerId) {
  return session.transcripts.filter(t => {
    if (speakerId === 'host') return t.speaker_type === 'host'
    return t.speaker_id === speakerId
  }).length
}

// ─── 获取发言活跃度百分比 ─────────────────────────────────
function getActivityPercent(speakerId) {
  if (session.totalSpeeches === 0) return 0
  const count = getSpeakerCount(speakerId)
  // 找到最大发言数
  const maxCount = Math.max(
    ...allParticipants.value.map(p => getSpeakerCount(p.id)),
    1
  )
  return Math.round((count / maxCount) * 100)
}
</script>

<style scoped>
/* ═════════════════════════════════════════════════════════════════════════════
   AI 圆桌讨论 — 沉浸式演播厅样式
   视觉风格：深色渐变背景 · 霓虹蓝紫光效 · Glassmorphism · 响应式
   ═════════════════════════════════════════════════════════════════════════════ */

/* ─── CSS 变量 ───────────────────────────────────────────────────────────── */
.landing, .studio {
  --bg-primary: #0b0e1a;
  --bg-secondary: #111627;
  --bg-card: rgba(18, 24, 48, 0.75);
  --bg-card-hover: rgba(24, 32, 64, 0.85);
  --bg-elevated: rgba(30, 40, 80, 0.5);
  --border-glow: rgba(99, 102, 241, 0.25);
  --border-active: rgba(99, 102, 241, 0.6);
  --neon-blue: #6366f1;
  --neon-cyan: #06b6d4;
  --neon-purple: #8b5cf6;
  --neon-amber: #fbbf24;
  --text-primary: #e8ecf4;
  --text-secondary: #8892b0;
  --text-muted: #525a7a;
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --radius-xl: 24px;
  --transition-fast: 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  --transition-normal: 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  --transition-slow: 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

/* ═══════════════════════════════════════════════════════════════════════════
   首页 / 创建区
   ═══════════════════════════════════════════════════════════════════════════ */

.landing {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 2rem;
  overflow: hidden;
}

/* ─── 背景动画 ──────────────────────────────────────────────────────────── */
.landing-bg {
  position: fixed;
  inset: 0;
  z-index: 0;
  background: linear-gradient(135deg, #0b0e1a 0%, #0f1429 30%, #0a1628 60%, #0b0e1a 100%);
}

.landing-orbs {
  position: absolute;
  inset: 0;
  overflow: hidden;
}

.orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.35;
  animation: orbFloat 12s ease-in-out infinite;
}

.orb-1 {
  width: 500px;
  height: 500px;
  background: radial-gradient(circle, rgba(99, 102, 241, 0.4), transparent 70%);
  top: -10%;
  left: -5%;
  animation-delay: 0s;
}

.orb-2 {
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, rgba(6, 182, 212, 0.3), transparent 70%);
  bottom: -15%;
  right: -8%;
  animation-delay: -4s;
}

.orb-3 {
  width: 350px;
  height: 350px;
  background: radial-gradient(circle, rgba(139, 92, 246, 0.3), transparent 70%);
  top: 40%;
  left: 50%;
  transform: translate(-50%, -50%);
  animation-delay: -8s;
}

@keyframes orbFloat {
  0%, 100% { transform: translate(0, 0) scale(1); }
  25% { transform: translate(30px, -40px) scale(1.05); }
  50% { transform: translate(-20px, 20px) scale(0.95); }
  75% { transform: translate(-40px, -30px) scale(1.02); }
}

/* ─── 首页内容 ──────────────────────────────────────────────────────────── */
.landing-content {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  max-width: 580px;
  width: 100%;
  animation: fadeInUp 0.8s ease-out;
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(30px); }
  to { opacity: 1; transform: translateY(0); }
}

/* ─── 品牌标识 ──────────────────────────────────────────────────────────── */
.landing-brand {
  text-align: center;
  margin-bottom: 2rem;
}

.brand-icon {
  font-size: 3.5rem;
  display: block;
  margin-bottom: 0.5rem;
  filter: drop-shadow(0 0 20px rgba(251, 191, 36, 0.3));
  animation: brandPulse 3s ease-in-out infinite;
}

@keyframes brandPulse {
  0%, 100% { transform: scale(1); filter: drop-shadow(0 0 20px rgba(251, 191, 36, 0.3)); }
  50% { transform: scale(1.05); filter: drop-shadow(0 0 30px rgba(251, 191, 36, 0.5)); }
}

.brand-title {
  font-size: 2.2rem;
  font-weight: 700;
  background: linear-gradient(135deg, #e8ecf4 0%, #a5b4fc 50%, #6366f1 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: 2px;
}

.brand-subtitle {
  color: var(--text-secondary);
  font-size: 1rem;
  margin-top: 0.5rem;
  letter-spacing: 1px;
}

/* ─── 配置卡片 ──────────────────────────────────────────────────────────── */
.landing-card {
  position: relative;
  width: 100%;
  padding: 2rem 2rem 1.8rem;
  background: var(--bg-card);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: var(--radius-xl);
  border: 1px solid rgba(99, 102, 241, 0.15);
  box-shadow: 0 8px 60px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.05);
  overflow: hidden;
}

.landing-card-glow {
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle at 30% 30%, rgba(99, 102, 241, 0.06), transparent 50%);
  pointer-events: none;
}

/* ─── 表单控件 ──────────────────────────────────────────────────────────── */
.form-group {
  margin-bottom: 1.5rem;
  position: relative;
}

.form-label {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 0.6rem;
  letter-spacing: 0.5px;
}

.label-icon {
  font-size: 1.1rem;
}

.textarea-wrapper {
  position: relative;
}

.form-textarea {
  width: 100%;
  padding: 0.9rem 1rem;
  background: rgba(11, 14, 26, 0.6);
  border: 1px solid rgba(99, 102, 241, 0.2);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  font-size: 0.95rem;
  font-family: var(--font-sans, 'Inter', sans-serif);
  line-height: 1.6;
  resize: vertical;
  min-height: 80px;
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
  outline: none;
}

.form-textarea:focus {
  border-color: var(--neon-blue);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15), 0 0 20px rgba(99, 102, 241, 0.08);
}

.form-textarea::placeholder {
  color: var(--text-muted);
}

.textarea-count {
  position: absolute;
  bottom: 0.5rem;
  right: 0.8rem;
  font-size: 0.75rem;
  color: var(--text-muted);
  background: rgba(11, 14, 26, 0.8);
  padding: 0.1rem 0.4rem;
  border-radius: 4px;
}

/* ─── 滑块 ──────────────────────────────────────────────────────────────── */
.expert-count-row {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.form-slider {
  flex: 1;
  -webkit-appearance: none;
  appearance: none;
  height: 4px;
  background: linear-gradient(to right, var(--neon-blue), var(--neon-cyan));
  border-radius: 2px;
  outline: none;
  cursor: pointer;
}

.form-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: radial-gradient(circle at 30% 30%, #818cf8, #6366f1);
  border: 2px solid rgba(255, 255, 255, 0.3);
  box-shadow: 0 0 15px rgba(99, 102, 241, 0.4);
  cursor: pointer;
  transition: box-shadow var(--transition-fast);
}

.form-slider::-webkit-slider-thumb:hover {
  box-shadow: 0 0 25px rgba(99, 102, 241, 0.6);
}

.form-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: radial-gradient(circle at 30% 30%, #818cf8, #6366f1);
  border: 2px solid rgba(255, 255, 255, 0.3);
  box-shadow: 0 0 15px rgba(99, 102, 241, 0.4);
  cursor: pointer;
}

.count-display {
  display: flex;
  align-items: baseline;
  gap: 0.3rem;
  min-width: 80px;
  text-align: center;
}

.count-value {
  font-size: 1.8rem;
  font-weight: 700;
  background: linear-gradient(135deg, #818cf8, #6366f1);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1;
}

.count-unit {
  font-size: 0.85rem;
  color: var(--text-secondary);
}

.slider-labels {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-top: 0.3rem;
  padding: 0 2px;
}

/* ─── 开始按钮 ──────────────────────────────────────────────────────────── */
.btn-start {
  position: relative;
  width: 100%;
  padding: 1rem;
  border: none;
  border-radius: var(--radius-md);
  background: linear-gradient(135deg, #6366f1 0%, #4f46e5 50%, #6366f1 100%);
  background-size: 200% 200%;
  color: white;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.6rem;
  overflow: hidden;
  transition: transform var(--transition-fast), box-shadow var(--transition-fast);
  animation: btnShimmer 3s ease-in-out infinite;
}

@keyframes btnShimmer {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}

.btn-start:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 30px rgba(99, 102, 241, 0.4);
}

.btn-start:active:not(:disabled) {
  transform: translateY(0);
}

.btn-start:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  animation: none;
}

.btn-start-icon {
  font-size: 1.2rem;
}

.btn-start-text {
  letter-spacing: 1px;
}

.btn-start-glow {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, transparent 30%, rgba(255, 255, 255, 0.1) 50%, transparent 70%);
  transform: translateX(-100%);
  transition: transform 0.6s;
}

.btn-start:hover:not(:disabled) .btn-start-glow {
  transform: translateX(100%);
}

.landing-hint {
  text-align: center;
  color: var(--text-muted);
  font-size: 0.8rem;
  margin-top: 1.2rem;
  line-height: 1.5;
}

/* ═══════════════════════════════════════════════════════════════════════════
   演播厅模式 — 布局
   ═══════════════════════════════════════════════════════════════════════════ */

.studio {
  position: relative;
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: linear-gradient(160deg, #070a15 0%, #0c1125 40%, #0a1628 100%);
  overflow: hidden;
}

/* ─── 演播厅顶部标题栏 ──────────────────────────────────────────────────── */
.studio-header {
  position: relative;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1.5rem;
  background: rgba(11, 14, 26, 0.85);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(99, 102, 241, 0.12);
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  min-width: 0;
  flex: 1;
}

.header-logo {
  font-size: 1.4rem;
  flex-shrink: 0;
}

.header-topic {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.header-center {
  flex-shrink: 0;
}

.live-indicator {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.35rem 1rem;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 500;
  border: 1px solid transparent;
  transition: all var(--transition-normal);
}

.live-indicator.pending {
  background: rgba(82, 90, 122, 0.2);
  color: var(--text-muted);
  border-color: rgba(82, 90, 122, 0.3);
}

.live-indicator.generating {
  background: rgba(99, 102, 241, 0.15);
  color: #818cf8;
  border-color: rgba(99, 102, 241, 0.25);
}

.live-indicator.discussing {
  background: rgba(16, 185, 129, 0.12);
  color: #34d399;
  border-color: rgba(16, 185, 129, 0.25);
}

.live-indicator.concluded {
  background: rgba(251, 191, 36, 0.12);
  color: #fbbf24;
  border-color: rgba(251, 191, 36, 0.2);
}

.live-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: currentColor;
}

.live-indicator.discussing .live-dot {
  animation: dotPulse 1.5s ease-in-out infinite;
}

@keyframes dotPulse {
  0%, 100% { opacity: 1; box-shadow: 0 0 0 0 currentColor; }
  50% { opacity: 0.5; box-shadow: 0 0 10px 4px currentColor; }
}

.live-indicator.pending .live-dot { background: var(--text-muted); }
.live-indicator.generating .live-dot { background: #818cf8; }
.live-indicator.concluded .live-dot { background: #fbbf24; }

.header-right {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.btn-icon {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: 1px solid rgba(99, 102, 241, 0.2);
  background: rgba(11, 14, 26, 0.6);
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--transition-fast);
}

.btn-icon:hover {
  background: rgba(99, 102, 241, 0.15);
  color: var(--text-primary);
  border-color: rgba(99, 102, 241, 0.4);
}

/* ─── 演播厅主体 ────────────────────────────────────────────────────────── */
.studio-body {
  position: relative;
  z-index: 1;
  display: flex;
  flex: 1;
  min-height: 0;
  gap: 0;
}

/* ─── 面板通用 ──────────────────────────────────────────────────────────── */
.panel {
  display: flex;
  flex-direction: column;
  background: var(--bg-card);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.8rem 1rem;
  border-bottom: 1px solid rgba(99, 102, 241, 0.08);
  flex-shrink: 0;
}

.panel-icon {
  font-size: 1rem;
}

.panel-title {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-primary);
  text-transform: uppercase;
  letter-spacing: 1px;
}

.panel-count {
  margin-left: auto;
  font-size: 0.78rem;
  color: var(--text-muted);
  background: rgba(99, 102, 241, 0.1);
  padding: 0.15rem 0.6rem;
  border-radius: 10px;
}

.panel-body {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 0.75rem;
}

/* ─── 左侧嘉宾席 ────────────────────────────────────────────────────────── */
.panel-left {
  width: 280px;
  min-width: 240px;
  border-right: 1px solid rgba(99, 102, 241, 0.08);
  flex-shrink: 0;
}

.guest-card {
  position: relative;
  display: flex;
  gap: 0.75rem;
  padding: 0.85rem;
  margin-bottom: 0.6rem;
  border-radius: var(--radius-md);
  background: rgba(11, 14, 26, 0.4);
  border: 1px solid rgba(99, 102, 241, 0.06);
  transition: all var(--transition-normal);
  cursor: default;
  overflow: hidden;
}

.guest-card:hover {
  background: rgba(11, 14, 26, 0.6);
  border-color: rgba(99, 102, 241, 0.12);
}

.guest-card.guest-speaking {
  background: rgba(11, 14, 26, 0.7);
  border-color: var(--border-active);
  box-shadow: 0 0 20px rgba(99, 102, 241, 0.1), inset 0 0 20px rgba(99, 102, 241, 0.03);
  animation: guestGlow 2s ease-in-out infinite;
}

@keyframes guestGlow {
  0%, 100% { box-shadow: 0 0 20px rgba(99, 102, 241, 0.1); }
  50% { box-shadow: 0 0 35px rgba(99, 102, 241, 0.2); }
}

.guest-card.guest-host {
  background: rgba(251, 191, 36, 0.06);
  border-color: rgba(251, 191, 36, 0.15);
}

.guest-card.guest-host:hover {
  border-color: rgba(251, 191, 36, 0.25);
}

/* ─── 嘉宾头像 ──────────────────────────────────────────────────────────── */
.guest-avatar {
  position: relative;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  border: 2px solid;
  transition: all var(--transition-normal);
}

.guest-emoji {
  font-size: 1.3rem;
  line-height: 1;
}

.guest-speaking-ring {
  position: absolute;
  inset: -4px;
  border-radius: 50%;
  border: 2px solid;
  animation: ringPulse 1.5s ease-out infinite;
}

@keyframes ringPulse {
  0% { transform: scale(1); opacity: 1; }
  100% { transform: scale(1.3); opacity: 0; }
}

/* ─── 嘉宾信息 ──────────────────────────────────────────────────────────── */
.guest-info {
  flex: 1;
  min-width: 0;
}

.guest-name-row {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  margin-bottom: 0.15rem;
}

.guest-name {
  font-size: 0.9rem;
  font-weight: 600;
  line-height: 1.3;
}

.guest-badge {
  font-size: 0.65rem;
  font-weight: 700;
  padding: 0.1rem 0.4rem;
  border-radius: 4px;
  background: rgba(251, 191, 36, 0.2);
  color: #fbbf24;
  border: 1px solid rgba(251, 191, 36, 0.3);
  line-height: 1.4;
}

.guest-title {
  font-size: 0.72rem;
  color: var(--text-secondary);
  line-height: 1.3;
  margin-bottom: 0.4rem;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.guest-stance {
  font-size: 0.7rem;
  color: var(--text-secondary);
  padding: 0.2rem 0.5rem;
  border-radius: 6px;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.guest-color-bar {
  position: absolute;
  top: 0;
  left: 0;
  width: 3px;
  height: 100%;
  border-radius: 3px 0 0 3px;
}

.guest-speaking .guest-color-bar {
  box-shadow: 0 0 8px currentColor;
}

/* ─── 发言声波动画 ──────────────────────────────────────────────────────── */
.guest-soundwave {
  position: absolute;
  bottom: 6px;
  right: 8px;
  display: flex;
  align-items: flex-end;
  gap: 2px;
  height: 16px;
}

.guest-soundwave span {
  display: block;
  width: 3px;
  background: var(--wave-color, #6366f1);
  border-radius: 2px;
  animation: soundwave 0.8s ease-in-out infinite alternate;
}

.guest-soundwave span:nth-child(1) { height: 30%; animation-delay: 0s; }
.guest-soundwave span:nth-child(2) { height: 60%; animation-delay: 0.15s; }
.guest-soundwave span:nth-child(3) { height: 100%; animation-delay: 0.3s; }
.guest-soundwave span:nth-child(4) { height: 50%; animation-delay: 0.2s; }
.guest-soundwave span:nth-child(5) { height: 80%; animation-delay: 0.1s; }

@keyframes soundwave {
  0% { height: 20%; opacity: 0.6; }
  100% { height: 100%; opacity: 1; }
}

/* ─── 面板：嘉宾席滚动条 ────────────────────────────────────────────────── */
.panel-left .panel-body::-webkit-scrollbar,
.panel-right .panel-body::-webkit-scrollbar {
  width: 4px;
}

.panel-left .panel-body::-webkit-scrollbar-track,
.panel-right .panel-body::-webkit-scrollbar-track {
  background: transparent;
}

.panel-left .panel-body::-webkit-scrollbar-thumb,
.panel-right .panel-body::-webkit-scrollbar-thumb {
  background: rgba(99, 102, 241, 0.2);
  border-radius: 2px;
}

/* ─── 中间发言区域 ──────────────────────────────────────────────────────── */
.panel-center {
  flex: 1;
  min-width: 0;
  border-right: 1px solid rgba(99, 102, 241, 0.06);
  position: relative;
}

.panel-center .panel-body {
  padding: 0;
}

.speech-area {
  height: 100%;
  padding: 0.75rem;
}

/* 发言区域滚动条 */
.speech-area::-webkit-scrollbar {
  width: 6px;
}

.speech-area::-webkit-scrollbar-track {
  background: transparent;
}

.speech-area::-webkit-scrollbar-thumb {
  background: rgba(99, 102, 241, 0.15);
  border-radius: 3px;
}

.speech-area::-webkit-scrollbar-thumb:hover {
  background: rgba(99, 102, 241, 0.3);
}

/* ─── 空状态 ────────────────────────────────────────────────────────────── */
.speech-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 0.5rem;
  padding: 2rem;
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: 0.5rem;
  animation: emptyBounce 2s ease-in-out infinite;
}

@keyframes emptyBounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

.empty-text {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--text-primary);
}

.empty-hint {
  font-size: 0.85rem;
  color: var(--text-muted);
}

.empty-loader {
  display: flex;
  gap: 6px;
  margin-top: 0.5rem;
}

.empty-loader span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--neon-blue);
  animation: loaderDot 1.4s ease-in-out infinite both;
}

.empty-loader span:nth-child(1) { animation-delay: 0s; }
.empty-loader span:nth-child(2) { animation-delay: 0.2s; }
.empty-loader span:nth-child(3) { animation-delay: 0.4s; }

@keyframes loaderDot {
  0%, 80%, 100% { transform: scale(0.4); opacity: 0.4; }
  40% { transform: scale(1); opacity: 1; }
}

/* ─── 发言条目 ──────────────────────────────────────────────────────────── */
.speech-item {
  display: flex;
  gap: 0.8rem;
  padding: 0.5rem 0.5rem 0.5rem 1rem;
  animation: speechSlideIn 0.4s ease-out;
  position: relative;
}

@keyframes speechSlideIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* ─── 时间线 ────────────────────────────────────────────────────────────── */
.speech-timeline {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 12px;
  flex-shrink: 0;
  padding-top: 4px;
}

.timeline-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
  z-index: 1;
}

.timeline-line {
  width: 2px;
  flex: 1;
  min-height: 20px;
  margin-top: 2px;
  border-radius: 1px;
}

/* ─── 发言卡片 ──────────────────────────────────────────────────────────── */
.speech-card {
  flex: 1;
  min-width: 0;
  padding: 0.8rem 1rem;
  border-radius: var(--radius-md);
  background: rgba(11, 14, 26, 0.5);
  border: 1px solid rgba(99, 102, 241, 0.08);
  position: relative;
  overflow: hidden;
  transition: border-color var(--transition-fast);
}

.speech-expert .speech-card:hover {
  border-color: rgba(99, 102, 241, 0.15);
}

.speech-host .speech-card {
  background: rgba(251, 191, 36, 0.04);
  border: 1px solid rgba(251, 191, 36, 0.15);
}

.speech-host .speech-card:hover {
  border-color: rgba(251, 191, 36, 0.25);
}

.speech-color-bar {
  position: absolute;
  top: 0;
  left: 0;
  width: 3px;
  height: 100%;
  border-radius: 3px 0 0 3px;
}

.speech-header {
  display: flex;
  align-items: flex-start;
  gap: 0.7rem;
  margin-bottom: 0.5rem;
}

.speech-avatar-wrapper {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: rgba(11, 14, 26, 0.5);
  border: 1px solid rgba(99, 102, 241, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.speech-emoji {
  font-size: 1rem;
  line-height: 1;
}

.speech-meta {
  flex: 1;
  min-width: 0;
}

.speech-speaker-row {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  margin-bottom: 0.1rem;
}

.speech-name {
  font-size: 0.88rem;
  font-weight: 600;
}

.speech-badge {
  font-size: 0.6rem;
  font-weight: 700;
  padding: 0.05rem 0.35rem;
  border-radius: 4px;
  background: rgba(251, 191, 36, 0.15);
  color: #fbbf24;
  border: 1px solid rgba(251, 191, 36, 0.25);
  line-height: 1.4;
}

.speech-title {
  font-size: 0.7rem;
  color: var(--text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.speech-time {
  font-size: 0.7rem;
  color: var(--text-muted);
  flex-shrink: 0;
  font-variant-numeric: tabular-nums;
}

.speech-content {
  font-size: 0.9rem;
  line-height: 1.7;
  color: var(--text-primary);
}

/* ─── 结束状态 ──────────────────────────────────────────────────────────── */
.speech-concluded {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.3rem;
  padding: 2rem;
  text-align: center;
}

.concluded-icon {
  font-size: 2.5rem;
  margin-bottom: 0.3rem;
}

.concluded-text {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
}

.concluded-hint {
  font-size: 0.85rem;
  color: var(--text-muted);
}

/* ─── 滚动到底部按钮 ────────────────────────────────────────────────────── */
.btn-scroll-bottom {
  position: absolute;
  bottom: 1rem;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.45rem 1rem;
  border-radius: 20px;
  background: rgba(99, 102, 241, 0.2);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border: 1px solid rgba(99, 102, 241, 0.3);
  color: #a5b4fc;
  font-size: 0.8rem;
  cursor: pointer;
  transition: all var(--transition-fast);
  z-index: 5;
  white-space: nowrap;
}

.btn-scroll-bottom:hover {
  background: rgba(99, 102, 241, 0.35);
  border-color: rgba(99, 102, 241, 0.5);
  box-shadow: 0 0 20px rgba(99, 102, 241, 0.2);
}

/* ─── 右侧信息面板 ──────────────────────────────────────────────────────── */
.panel-right {
  width: 260px;
  min-width: 220px;
  flex-shrink: 0;
}

/* ─── 统计卡片 ──────────────────────────────────────────────────────────── */
.stat-card {
  padding: 0.85rem;
  margin-bottom: 0.6rem;
  border-radius: var(--radius-md);
  background: rgba(11, 14, 26, 0.4);
  border: 1px solid rgba(99, 102, 241, 0.06);
  transition: border-color var(--transition-fast);
}

.stat-card:hover {
  border-color: rgba(99, 102, 241, 0.12);
}

.stat-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.8px;
  margin-bottom: 0.5rem;
}

.stat-value-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.stat-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.stat-dot.pending { background: var(--text-muted); }
.stat-dot.generating { background: #818cf8; }
.stat-dot.discussing { background: #34d399; animation: dotPulse 1.5s ease-in-out infinite; }
.stat-dot.concluded { background: #fbbf24; }

.stat-text {
  font-size: 0.9rem;
  font-weight: 500;
  color: var(--text-primary);
}

.stat-value.large {
  font-size: 2rem;
  font-weight: 700;
  background: linear-gradient(135deg, #818cf8, #6366f1);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1.2;
}

/* ─── 嘉宾头像集合 ──────────────────────────────────────────────────────── */
.stat-avatars {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}

.stat-avatar-item {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: rgba(11, 14, 26, 0.5);
  border: 2px solid;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
  transition: all var(--transition-fast);
}

.stat-avatar-item.stat-speaking {
  box-shadow: 0 0 15px currentColor;
  transform: scale(1.1);
  animation: avatarGlow 1.5s ease-in-out infinite;
}

@keyframes avatarGlow {
  0%, 100% { box-shadow: 0 0 10px currentColor; }
  50% { box-shadow: 0 0 20px currentColor; }
}

/* ─── 错误提示 ─────────────────────────────────────────────────────────── */
.studio-error {
  position: relative;
  z-index: 5;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  margin: 0 1rem;
  background: rgba(239, 68, 68, 0.12);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: var(--radius-md);
  color: #fca5a5;
  font-size: 0.85rem;
  flex-shrink: 0;
}
.studio-error button {
  margin-left: auto;
  background: none;
  border: none;
  color: #fca5a5;
  cursor: pointer;
  font-size: 1.1rem;
  opacity: 0.7;
}
.studio-error button:hover {
  opacity: 1;
}

/* ─── 结论展示 ─────────────────────────────────────────────────────────── */
.conclusion-section {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.conclusion-item {
  display: flex;
  align-items: flex-start;
  gap: 0.4rem;
  font-size: 0.78rem;
  line-height: 1.5;
}
.conclusion-icon {
  flex-shrink: 0;
  font-size: 0.85rem;
}
.conclusion-text {
  flex: 1;
  color: var(--text-primary);
}
.conclusion-tag {
  flex-shrink: 0;
  font-size: 0.65rem;
  padding: 0.1rem 0.4rem;
  border-radius: 4px;
  font-weight: 600;
  text-transform: uppercase;
}
.tag-strong, .tag-high { background: rgba(239, 68, 68, 0.15); color: #fca5a5; }
.tag-moderate, .tag-medium { background: rgba(251, 191, 36, 0.15); color: #fbbf24; }
.tag-weak, .tag-low { background: rgba(99, 102, 241, 0.15); color: #a5b4fc; }

.btn-conclusion {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid rgba(99, 102, 241, 0.3);
  border-radius: 8px;
  background: rgba(99, 102, 241, 0.15);
  color: #a5b4fc;
  cursor: pointer;
  font-size: 0.85rem;
  transition: all var(--transition-fast);
}
.btn-conclusion:hover {
  background: rgba(99, 102, 241, 0.25);
  border-color: rgba(99, 102, 241, 0.5);
}

/* ─── 发言活跃度 ────────────────────────────────────────────────────────── */
.activity-list {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.activity-row {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.activity-emoji {
  font-size: 0.9rem;
  width: 20px;
  flex-shrink: 0;
  text-align: center;
}

.activity-name {
  font-size: 0.78rem;
  font-weight: 500;
  width: 50px;
  flex-shrink: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.activity-bar-bg {
  flex: 1;
  height: 6px;
  background: rgba(11, 14, 26, 0.5);
  border-radius: 3px;
  overflow: hidden;
}

.activity-bar {
  height: 100%;
  border-radius: 3px;
  transition: width 0.5s ease-out;
  min-width: 2px;
}

.activity-count {
  font-size: 0.72rem;
  color: var(--text-muted);
  width: 20px;
  text-align: right;
  font-variant-numeric: tabular-nums;
}

/* ═══════════════════════════════════════════════════════════════════════════
   底部信息栏
   ═══════════════════════════════════════════════════════════════════════════ */

.studio-footer {
  position: relative;
  z-index: 10;
  display: flex;
  align-items: center;
  padding: 0.5rem 1.5rem;
  background: rgba(11, 14, 26, 0.9);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-top: 1px solid rgba(99, 102, 241, 0.08);
  flex-shrink: 0;
  gap: 0.5rem;
  flex-wrap: nowrap;
  overflow-x: auto;
}

.footer-item {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  white-space: nowrap;
}

.footer-icon {
  font-size: 0.85rem;
}

.footer-label {
  font-size: 0.78rem;
  color: var(--text-muted);
}

.footer-value {
  font-size: 0.78rem;
  color: var(--text-secondary);
  font-weight: 500;
}

.footer-divider {
  width: 1px;
  height: 14px;
  background: rgba(99, 102, 241, 0.15);
  flex-shrink: 0;
}

.footer-pulse {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #34d399;
  animation: dotPulse 1.5s ease-in-out infinite;
}

.status-live {
  color: #34d399;
  font-weight: 600;
}

/* ═══════════════════════════════════════════════════════════════════════════
   响应式布局
   ═══════════════════════════════════════════════════════════════════════════ */

/* ─── 超宽屏 (> 1600px) ───────────────────────────────────────────────── */
@media (min-width: 1600px) {
  .panel-left {
    width: 320px;
    min-width: 280px;
  }
  .panel-right {
    width: 300px;
    min-width: 260px;
  }
  .studio-header {
    padding: 0.9rem 2rem;
  }
  .guest-card {
    padding: 1rem;
  }
  .guest-avatar {
    width: 50px;
    height: 50px;
  }
  .guest-emoji {
    font-size: 1.5rem;
  }
  .guest-name {
    font-size: 1rem;
  }
  .speech-content {
    font-size: 1rem;
  }
}

/* ─── 窄屏 / 平板 (< 1024px) ───────────────────────────────────────────── */
@media (max-width: 1023px) {
  .panel-left {
    width: 220px;
    min-width: 180px;
  }
  .panel-right {
    width: 220px;
    min-width: 180px;
  }
  .guest-stance {
    display: none;
  }
  .guest-title {
    display: none;
  }
  .stat-card:last-child {
    display: none;
  }
}

/* ─── 移动端 (< 768px) ──────────────────────────────────────────────────── */
@media (max-width: 767px) {
  .studio-body {
    flex-direction: column;
  }

  .panel-left {
    width: 100%;
    min-width: 0;
    max-height: 180px;
    border-right: none;
    border-bottom: 1px solid rgba(99, 102, 241, 0.08);
  }

  .panel-left .panel-body {
    display: flex;
    gap: 0.4rem;
    overflow-x: auto;
    overflow-y: hidden;
    padding: 0.5rem;
  }

  .guest-card {
    min-width: 160px;
    max-width: 180px;
    flex-shrink: 0;
    flex-direction: column;
    align-items: center;
    text-align: center;
    padding: 0.6rem;
  }

  .guest-color-bar {
    width: 100%;
    height: 3px;
    top: 0;
    left: 0;
    border-radius: 3px 3px 0 0;
  }

  .guest-avatar {
    width: 36px;
    height: 36px;
  }

  .guest-info {
    min-width: 0;
  }

  .guest-name {
    font-size: 0.8rem;
  }

  .guest-stance,
  .guest-title {
    display: none;
  }

  .guest-soundwave {
    display: none;
  }

  .panel-center {
    border-right: none;
  }

  .panel-right {
    display: none;
  }

  .studio-header {
    padding: 0.5rem 0.8rem;
  }

  .header-topic {
    font-size: 0.85rem;
  }

  .live-indicator {
    font-size: 0.75rem;
    padding: 0.25rem 0.7rem;
  }

  .studio-footer {
    padding: 0.4rem 0.8rem;
    gap: 0.3rem;
  }

  .footer-value {
    max-width: 100px;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .landing {
    padding: 1.2rem;
  }

  .brand-title {
    font-size: 1.6rem;
  }

  .brand-icon {
    font-size: 2.5rem;
  }

  .landing-card {
    padding: 1.5rem 1.2rem;
  }

  .count-value {
    font-size: 1.5rem;
  }
}

/* ─── 极小屏 (< 480px) ──────────────────────────────────────────────────── */
@media (max-width: 479px) {
  .panel-left {
    max-height: 140px;
  }

  .guest-card {
    min-width: 130px;
    padding: 0.5rem;
  }

  .guest-avatar {
    width: 30px;
    height: 30px;
  }

  .guest-emoji {
    font-size: 0.9rem;
  }

  .guest-name {
    font-size: 0.75rem;
  }

  .speech-card {
    padding: 0.6rem 0.8rem;
  }

  .speech-content {
    font-size: 0.85rem;
  }

  .studio-footer .footer-divider:nth-child(6) {
    display: none;
  }
  .studio-footer .footer-item:last-child {
    display: none;
  }
}
</style>