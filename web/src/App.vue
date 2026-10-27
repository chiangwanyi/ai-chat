<script setup lang="ts">
import { ref, nextTick, onMounted } from 'vue'

interface Msg {
  role: 'user' | 'assistant'
  content: string
}

const messages = ref<Msg[]>([
  { role: 'assistant', content: '你好！有什么可以帮你的？' },
])
const input = ref('')
const sending = ref(false)
const listEl = ref<HTMLElement>()

// ---- 设置相关 ----
const showSettings = ref(false)
const model = ref('')
const models = ref<string[]>([])
const apiKeyInput = ref('')
const baseUrl = ref('')
const keyMasked = ref('')
const saving = ref(false)
const settingsMsg = ref('')
const loadingModels = ref(false)

async function loadConfig() {
  const res = await fetch('/api/config')
  const cfg = await res.json()
  model.value = cfg.model
  baseUrl.value = cfg.base_url
  keyMasked.value = cfg.key_masked
  apiKeyInput.value = ''
}

async function loadModels() {
  loadingModels.value = true
  try {
    const res = await fetch('/api/models')
    if (!res.ok) throw new Error((await res.json()).detail || `HTTP ${res.status}`)
    models.value = (await res.json()).models
    if (models.value.length && !models.value.includes(model.value)) model.value = models.value[0]
  } catch (e) {
    models.value = []
    settingsMsg.value = `获取模型列表失败：${e}`
  } finally {
    loadingModels.value = false
  }
}

async function saveSettings() {
  saving.value = true
  settingsMsg.value = ''
  try {
    const body: Record<string, string> = { model: model.value, base_url: baseUrl.value }
    if (apiKeyInput.value.trim()) body.api_key = apiKeyInput.value.trim()
    const res = await fetch('/api/config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    await loadConfig()
    await loadModels()
    settingsMsg.value = '已保存'
  } catch (e) {
    settingsMsg.value = `保存失败：${e}`
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  await loadConfig()
  await loadModels().catch(() => {})
})

async function send() {
  const text = input.value.trim()
  if (!text || sending.value) return
  input.value = ''
  messages.value.push({ role: 'user', content: text })
  const reply = { role: 'assistant' as const, content: '' }
  messages.value.push(reply)
  sending.value = true
  await nextTick()
  listEl.value?.scrollTo({ top: listEl.value.scrollHeight })

  try {
    const history = messages.value
      .filter((m) => m.content)
      .slice(0, -1)
      .map((m) => ({ role: m.role, content: m.content }))
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        messages: [{ role: 'system', content: '你是一个友好、简洁的 AI 助手。' }, ...history],
        model: model.value || undefined,
      }),
    })
    if (!res.ok || !res.body) throw new Error((await res.json().catch(() => null))?.detail || `HTTP ${res.status}`)
    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buf = ''
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buf += decoder.decode(value, { stream: true })
      const lines = buf.split('\n\n')
      buf = lines.pop() ?? ''
      for (const line of lines) {
        const data = line.replace(/^data: /, '')
        if (data === '[DONE]') continue
        reply.content += JSON.parse(data).content
        listEl.value?.scrollTo({ top: listEl.value.scrollHeight })
      }
    }
  } catch (e) {
    reply.content = `请求失败：${e}`
  } finally {
    sending.value = false
  }
}
</script>

<template>
  <div class="mx-auto flex h-screen max-w-3xl flex-col p-4">
    <div class="mb-2 flex items-center justify-between">
      <h1 class="text-xl font-bold text-gray-800">AI 聊天</h1>
      <div class="flex items-center gap-2">
        <select
          v-model="model"
          class="rounded-full border bg-white px-3 py-1.5 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-400"
        >
          <option v-for="m in models" :key="m" :value="m">{{ m }}</option>
          <option v-if="!models.length" :value="model">{{ model }}</option>
        </select>
        <button
          class="rounded-full border px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-100"
          @click="showSettings = !showSettings"
        >设置</button>
      </div>
    </div>

    <!-- 设置面板 -->
    <div v-if="showSettings" class="mb-3 space-y-3 rounded-lg border bg-white p-4 shadow-sm">
      <div class="flex items-center gap-3">
        <label class="w-24 shrink-0 text-sm text-gray-600">API Key</label>
        <input
          v-model="apiKeyInput"
          type="password"
          class="flex-1 rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
          :placeholder="keyMasked ? `已保存（${keyMasked}），留空则不修改` : '输入 API Key'"
          autocomplete="off"
        />
      </div>
      <div class="flex items-center gap-3">
        <label class="w-24 shrink-0 text-sm text-gray-600">Base URL</label>
        <input
          v-model="baseUrl"
          class="flex-1 rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
          placeholder="https://... /v1"
        />
      </div>
      <div class="flex items-center gap-3">
        <label class="w-24 shrink-0 text-sm text-gray-600">模型</label>
        <select
          v-model="model"
          class="flex-1 rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
          :disabled="loadingModels"
        >
          <option v-if="loadingModels" value="">加载模型列表中…</option>
          <option v-for="m in models" :key="m" :value="m">{{ m }}</option>
          <option v-if="!models.length && !loadingModels" :value="model">{{ model }}</option>
        </select>
      </div>
      <div class="flex items-center justify-end gap-3">
        <span v-if="settingsMsg" class="text-sm text-gray-500">{{ settingsMsg }}</span>
        <button
          class="rounded-full bg-blue-500 px-5 py-2 text-sm text-white disabled:opacity-50"
          :disabled="saving"
          @click="saveSettings"
        >{{ saving ? '保存中…' : '保存' }}</button>
      </div>
    </div>

    <div ref="listEl" class="flex-1 space-y-3 overflow-y-auto rounded-lg bg-gray-50 p-4">
      <div
        v-for="(m, i) in messages"
        :key="i"
        class="flex"
        :class="m.role === 'user' ? 'justify-end' : 'justify-start'"
      >
        <div
          class="max-w-[80%] whitespace-pre-wrap rounded-2xl px-4 py-2 text-sm leading-6"
          :class="m.role === 'user' ? 'bg-blue-500 text-white' : 'bg-white text-gray-800 shadow'"
        >{{ m.content }}</div>
      </div>
    </div>
    <form class="mt-3 flex gap-2" @submit.prevent="send">
      <input
        v-model="input"
        class="flex-1 rounded-full border px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
        placeholder="输入消息，回车发送"
        :disabled="sending"
      />
      <button
        type="submit"
        class="rounded-full bg-blue-500 px-5 py-2 text-sm text-white disabled:opacity-50"
        :disabled="sending || !input.trim()"
      >发送</button>
    </form>
  </div>
</template>
