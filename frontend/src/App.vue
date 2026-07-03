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
          :disabled="!session.topic.trim()"
        >
          <span class="btn-start-icon">🎬</span>
          <span class="btn-start-text">开始讨论</span>
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
 * 数据模型与 API 契约保持一致 (参考 docs/api.yaml)，
 * 当前阶段使用前端 Mock 数据模拟全部交互。
 */
import { ref, reactive, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'

// ─── 模拟专家数据集 ──────────────────────────────────────
const EXPERT_POOL = [
  { id: 'e001', name: '张思远', title: 'AI 伦理研究员 · 清华大学', stance: '持审慎乐观态度，认为 AI 会重塑而非取代', color: '#6366f1', avatar_emoji: '🧑‍🔬', sort_order: 1 },
  { id: 'e002', name: '李敏', title: '算法工程师 · 字节跳动', stance: 'AI 将大规模创造新岗位', color: '#10b981', avatar_emoji: '👩‍💻', sort_order: 2 },
  { id: 'e003', name: '王建国', title: '劳动经济学教授 · 北京大学', stance: '结构性失业风险真实存在', color: '#f59e0b', avatar_emoji: '👨‍🏫', sort_order: 3 },
  { id: 'e004', name: '陈思睿', title: 'AI 政策研究顾问', stance: '需要全球协同治理框架', color: '#ef4444', avatar_emoji: '👩‍🎓', sort_order: 4 },
  { id: 'e005', name: '赵明宇', title: '机器人学专家 · 中科院', stance: '人机协作是未来主旋律', color: '#8b5cf6', avatar_emoji: '👨‍🚀', sort_order: 5 },
  { id: 'e006', name: '林小婉', title: '未来学家 · 腾讯研究院', stance: 'AI 将催生全新文明形态', color: '#ec4899', avatar_emoji: '🧙‍♀️', sort_order: 6 },
  { id: 'e007', name: '周浩然', title: '社会学家 · 复旦大学', stance: '技术中性，关键在于制度设计', color: '#14b8a6', avatar_emoji: '👨‍🎓', sort_order: 7 },
  { id: 'e008', name: '吴晓峰', title: 'AI 安全研究员 · 微软亚洲研究院', stance: '对齐问题比替代问题更紧迫', color: '#f97316', avatar_emoji: '🧑‍💻', sort_order: 8 },
  { id: 'e009', name: '孙雅文', title: '教育科技创业者', stance: '教育体系必须率先变革', color: '#06b6d4', avatar_emoji: '👩‍🏫', sort_order: 9 },
  { id: 'e010', name: '黄磊', title: '科技记者 · 36氪', stance: '公众认知与技术发展存在鸿沟', color: '#a855f7', avatar_emoji: '📝', sort_order: 10 },
]

// ─── 模拟发言池 ──────────────────────────────────────────
const MOCK_SPEECHES = {
  host: [
    '各位专家好，欢迎来到今天的 AI 圆桌讨论！我们今天聚焦的话题是：{topic}。请大家畅所欲言。',
    '非常精彩的观点！那么关于这个话题，其他专家有什么不同的看法？',
    '感谢各位的深入分享。我想把话题引向另一个角度——从社会层面来看，我们该如何为 AI 时代做准备？',
    '好的，让我们进入下一个议题。关于教育体系应该如何应对 AI 时代的挑战，各位有何高见？',
    '非常有意思的讨论！我来总结一下刚才几位专家的核心观点……',
    '时间关系，我们进行最后一个环节。请每位专家用一句话表达您的核心立场。',
  ],
  e001: [
    '我认为 AI 会重塑岗位结构，但不会完全取代人类。关键在于我们如何提前布局教育和培训体系。',
    '历史表明，每一次技术革命虽然会淘汰部分岗位，但最终都会创造出更多的就业机会。蒸汽机、电力、互联网都是先例。',
    '我们需要在教育体系中全面引入 AI 素养课程，让下一代具备与 AI 协作的能力。',
    '我持审慎乐观态度——前景光明，但中间过程可能充满阵痛。需要政府、企业、教育机构三方协同。',
  ],
  e002: [
    '作为一线从业者，我切身感受到 AI 正在创造大量全新岗位：提示工程师、AI 训练师、数据标注师、AI 产品经理……',
    'AI 将人类从重复性、低创造性的工作中解放出来，让我们能专注于更高层次的创新。这是生产力的又一次飞跃。',
    '我在字节跳动每天都看到 AI 工具如何让内容创作者效率翻倍。这不是取代，而是赋能。',
    '短期来看会出现岗位调整，但长期而言，AI 带来的就业增量远大于减量。',
  ],
  e003: [
    '结构性失业的风险是真实存在的，特别是在制造业和传统服务业领域。我们需要正视这个问题。',
    '低技能岗位受到的冲击最大，而转岗培训需要时间和大量资源投入。市场调节无法解决所有问题。',
    '我们需要完善社会保障体系，为转型期的劳动者提供足够的缓冲和支持。',
    '从经济学角度看，AI 的收益分配可能加剧不平等——技术所有者与普通劳动者之间的差距会拉大。',
  ],
  e004: [
    '各国政府需要加快 AI 治理框架的制定，确保技术发展的成果能够惠及所有人。',
    '欧盟的 AI 法案是一个好的开端，中国也需要建立自己的 AI 监管框架，平衡创新与安全。',
    '全球协同治理是关键——AI 不分国界，我们需要国际社会共同制定规则。',
    '我担心的是算法偏见和数据隐私问题。如果监管跟不上，技术可能加剧社会不公。',
  ],
  e005: [
    '人机协作是未来的主旋律。机器做机器擅长的事，人类做人类擅长的事——创造力、共情力、复杂决策。',
    '在工业领域，我们已经看到协作机器人如何提升生产效率，同时保障工人安全。',
    'AI 不是替代人类，而是扩展人类的能力边界。就像望远镜扩展了我们的视野一样。',
    '真正的突破在于人机融合——不是谁替代谁，而是产生 1+1>2 的协同效应。',
  ],
  e006: [
    '从更长的时间维度来看，AI 将催生全新的文明形态。就像工业革命改变了社会结构一样，AI 革命将彻底重塑人类社会的组织方式。',
    '未来的工作岗位很可能我们现在完全无法想象。20年前谁能想到"网红"、"主播"会成为职业？',
    '元宇宙 + AI 将创造全新的数字生存空间，人类的工作、学习、社交方式都将被重新定义。',
    '我们需要超越"替代"的思维定式，去想象一种人机共生、共同进化的未来图景。',
  ],
  e007: [
    '技术本身是中性的，影响取决于制度设计和社会选择。同样的技术在不同的社会制度下会产生截然不同的结果。',
    '我们需要关注的是：谁在开发 AI？为谁的利益服务？谁参与决策？这些问题比技术本身更重要。',
    'AI 治理需要多元利益相关方的参与——不仅仅是技术人员，还需要社会学家、伦理学家、法律专家和公众代表。',
    '社会韧性建设比技术升级更紧迫——我们需要全社会达成共识，明确 AI 发展的红线与底线。',
  ],
  e008: [
    '在我看来，AI 对齐问题比替代问题更紧迫。如何确保 AI 系统的目标与人类价值观一致，这是当前最重要的挑战。',
    '大语言模型的安全边界仍然很脆弱。我们见过太多 jailbreak（越狱）攻击成功的案例。',
    '红队测试和对抗性训练需要持续投入，安全研究不能因为商业压力而被削弱。',
    '我呼吁业内同行将安全性作为核心指标，而不仅仅是追求模型性能的提升。',
  ],
  e009: [
    '教育体系必须率先变革。我们还在用工业化时代的教育模式培养数字时代的学生，这本身就是个问题。',
    'AI 辅助个性化学习是教育领域最具潜力的应用方向。每个学生都能拥有一个 AI 私教。',
    '我在创业中看到，掌握 AI 工具的学生学习效率提升了 3 倍以上。这才是教育的未来。',
    '教育的目标要从"知识传授"转向"培养批判性思维和终身学习能力"——这些是 AI 难以替代的。',
  ],
  e010: [
    '我观察到公众对 AI 的认知存在两个极端：要么过度乐观，要么过度恐惧。媒体在这其中扮演了重要角色。',
    '负责任的技术报道应该既展示 AI 的能力边界，也坦诚讨论风险，而不是制造恐慌或泡沫。',
    '公众理解是技术良性发展的基础。我们现在最缺的不是技术，而是高质量的公众科普。',
    '从报道中我注意到，很多关于 AI"取代人类"的担忧其实源于对技术的误解。科普工作任重道远。',
  ],
}

// ─── 主持人 ──────────────────────────────────────────────
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

// ─── 响应式状态 ──────────────────────────────────────────
const session = reactive({
  id: '',
  topic: '',
  expert_count: 4,
  status: 'pending',
  created_at: '',
  started: false,
  experts: [],
  transcripts: [],
  currentRound: 0,
  totalSpeeches: 0,
  timer: null,
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

const displayExperts = computed(() => {
  // 从专家池选取前 expert_count 位
  return EXPERT_POOL.slice(0, session.expert_count)
})

// ─── 页面加载后自动生成专家 ──────────────────────────────
onMounted(() => {
  // 生成 Mock 专家
  session.experts = EXPERT_POOL.slice(0, session.expert_count).map(e => ({
    ...e,
    session_id: session.id || 'mock-session',
  }))
})

// ─── 生成 UUID ───────────────────────────────────────────
function genId() {
  return 'xxxx-xxxx'.replace(/x/g, () => (Math.random() * 16 | 0).toString(16))
}

// ─── 开始讨论 ─────────────────────────────────────────────
function startDiscussion() {
  if (!session.topic.trim()) {
    session.topic = '人工智能是否会取代人类工作'
  }

  session.id = 'session-' + genId()
  session.created_at = new Date().toISOString()
  session.status = 'generating'
  session.started = true
  session.currentRound = 0
  session.totalSpeeches = 0
  session.transcripts = []
  session.experts = EXPERT_POOL.slice(0, session.expert_count).map(e => ({
    ...e,
    session_id: session.id,
  }))

  // 自动滚动到演播厅模式顶部
  nextTick(() => {
    window.scrollTo({ top: 0, behavior: 'smooth' })
  })

  // 模拟专家生成完成
  setTimeout(() => {
    session.status = 'discussing'
    // 主持人开场白
    appendSpeech('host', null, MOCK_SPEECHES.host[0].replace('{topic}', session.topic))
  }, 800)

  // 启动模拟发言定时器
  startSimulation()
}

// ─── 模拟发言 ────────────────────────────────────────────
function getRandomItem(arr) {
  return arr[Math.floor(Math.random() * arr.length)]
}

function appendSpeech(speakerType, speakerId, content) {
  const isHost = speakerType === 'host'
  let speaker

  if (isHost) {
    speaker = HOST
  } else {
    speaker = session.experts.find(e => e.id === speakerId)
    if (!speaker) speaker = getRandomItem(session.experts)
  }

  const transcript = {
    id: 't' + genId(),
    session_id: session.id,
    speaker_type: speakerType,
    speaker_id: isHost ? null : speaker.id,
    speaker_name: speaker.name,
    avatar_emoji: speaker.avatar_emoji,
    content,
    sequence: session.transcripts.length + 1,
    created_at: new Date().toISOString(),
    speakerColor: speaker.color,
    speakerTitle: speaker.title,
  }

  session.transcripts.push(transcript)
  session.totalSpeeches++

  // 高亮当前发言人
  currentSpeakerId.value = speaker.id

  // 自动滚动到底部
  if (isAutoScroll.value) {
    nextTick(() => {
      const el = speechAreaRef.value
      if (el) {
        el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' })
      }
    })
  }
}

function getNextDelay() {
  return 2000 + Math.random() * 1500
}

function getMockSpeaker() {
  // 70% 概率是专家发言，30% 概率是主持人串场
  const isHost = Math.random() < 0.25
  if (isHost) {
    return { type: 'host', id: null, pool: 'host' }
  }
  const expert = getRandomItem(session.experts)
  return { type: 'expert', id: expert.id, pool: expert.id }
}

function getMockContent(type, poolKey) {
  const pool = MOCK_SPEECHES[poolKey]
  if (!pool || pool.length === 0) return '这是一个有趣的视角。'

  // 避免完全重复同一专家的最近一条发言
  const lastBySpeaker = session.transcripts
    .filter(t => t.speaker_type === type && t.speaker_id === (type === 'host' ? null : poolKey))
  const usedIndices = new Set()
  if (lastBySpeaker.length > 0) {
    const lastContent = lastBySpeaker[lastBySpeaker.length - 1].content
    const lastIdx = pool.indexOf(lastContent)
    if (lastIdx >= 0) usedIndices.add(lastIdx)
  }

  const available = pool.filter((_, i) => !usedIndices.has(i))
  const source = available.length > 0 ? available : pool
  return getRandomItem(source)
}

function startSimulation() {
  if (session.timer) clearTimeout(session.timer)

  function tick() {
    if (session.status !== 'discussing') return

    const speaker = getMockSpeaker()
    const content = getMockContent(speaker.type, speaker.pool)
    appendSpeech(speaker.type, speaker.id, content)

    // 检查是否讨论结束（模拟 15-20 条发言后结束）
    if (session.transcripts.length >= 18) {
      setTimeout(() => {
        endDiscussion()
      }, 2000)
      return
    }

    session.timer = setTimeout(tick, getNextDelay())
  }

  session.timer = setTimeout(tick, getNextDelay())
}

// ─── 结束讨论 ────────────────────────────────────────────
function endDiscussion() {
  session.status = 'concluded'
  currentSpeakerId.value = null
  if (session.timer) {
    clearTimeout(session.timer)
    session.timer = null
  }
  // 主持人总结
  appendSpeech('host', null, '感谢各位专家的精彩讨论！今天的圆桌交流让我们看到了 AI 时代的多元视角。期待下次再会！')
}

// ─── 重置 ────────────────────────────────────────────────
function resetSession() {
  if (session.timer) {
    clearTimeout(session.timer)
    session.timer = null
  }
  session.id = ''
  session.status = 'pending'
  session.started = false
  session.experts = EXPERT_POOL.slice(0, session.expert_count)
  session.transcripts = []
  session.currentRound = 0
  session.totalSpeeches = 0
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
  if (session.timer) {
    clearTimeout(session.timer)
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