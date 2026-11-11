import type { Register } from 'claude-code'

const DEFAULT_THRESHOLD = 85

/** The configured percent, 1 to 100; anything else means the default. */
export const parseThreshold = (raw: unknown): number => {
  const n = typeof raw === 'number' ? raw : Number(String(raw ?? '').trim())
  return Number.isFinite(n) && n >= 1 && n <= 100 ? n : DEFAULT_THRESHOLD
}

type Limit = { kind: string; percentUsed: number; resetsAt?: string }

/** The 5-hour window, if the session reports one (a subscription does; an API key does not). */
export const fiveHour = (limits: readonly Limit[] | undefined): Limit | undefined =>
  limits?.find(l => l.kind === 'five_hour')

const clock = (iso?: string): string => {
  if (!iso) return 'later'
  const d = new Date(iso)
  return Number.isNaN(d.getTime())
    ? 'later'
    : d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

export const refusal = (limit: Limit, threshold: number): string =>
  `quota-guard: the 5-hour window is at ${Math.round(limit.percentUsed)}% ` +
  `(limit ${threshold}%), resets ${clock(limit.resetsAt)}. ` +
  `No new subagent will start until then. Stop, report to the person, and wait.`

export const register: Register = (on, options) => {
  const threshold = parseThreshold(options?.threshold)
  let isWarned = false

  // Judge before calling next. Deliberately no .catch handler: if this hook throws or the figure is
  // missing, the call goes on (fail open). A broken guard must not stop the person's work.
  on('tool.call', { tool: 'Agent' }, async ($, e, next) => {
    const limit = fiveHour((await $.session.usage()).rateLimits)
    if (limit && limit.percentUsed >= threshold) return { deny: refusal(limit, threshold) }
    return next(e)
  })

  // Pushed whenever a window moves a whole point: toast once on the way up, re-arm on the way down.
  on('session.measure', ($, e, next) => {
    const limit = fiveHour(e.rateLimits)
    if (limit && limit.percentUsed >= threshold && !isWarned) {
      isWarned = true
      $.ui.toast(`quota-guard: 5-hour window at ${Math.round(limit.percentUsed)}%, subagents blocked until ${clock(limit.resetsAt)}`)
    } else if (!limit || limit.percentUsed < threshold) {
      isWarned = false
    }
    return next(e)
  })
}
