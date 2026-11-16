import type { Register } from 'claude-code'

const DEFAULT_THRESHOLD = 85

/** The configured percent, 1 to 100; anything else means the default. */
export const parseThreshold = (raw: unknown): number => {
  const n = typeof raw === 'number' ? raw : Number(String(raw ?? '').trim())
  return Number.isFinite(n) && n >= 1 && n <= 100 ? n : DEFAULT_THRESHOLD
}

export type OnLimit = 'ask' | 'block'

/** What to do at the threshold: "block" refuses at once; anything else asks the person. */
export const parseOnLimit = (raw: unknown): OnLimit =>
  String(raw ?? '').trim().toLowerCase() === 'block' ? 'block' : 'ask'

export const ALLOW_ONCE = 'Allow this one'
export const ALLOW_WINDOW = 'Allow until the window resets'
export const KEEP_BLOCKING = 'Keep blocking'

/** The dialog answer that lets the call through. Anything else, "Other" text included, keeps the block. */
export const isAllowed = (answer: string): boolean => answer === ALLOW_ONCE || answer === ALLOW_WINDOW

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

export const askText = (limit: Limit, threshold: number): string =>
  `The 5-hour window is at ${Math.round(limit.percentUsed)}% (limit ${threshold}%), resets ${clock(limit.resetsAt)}. ` +
  `Start this subagent anyway?`

export const register: Register = (on, options) => {
  const threshold = parseThreshold(options?.threshold)
  const onLimit = parseOnLimit(options?.onLimit)
  let isWarned = false
  // "Allow until the window resets" is remembered by the window's reset time; a new window asks again.
  let allowedWindow: string | undefined
  // Parallel Agent calls share one dialog instead of opening one each.
  let pending: Promise<string> | undefined

  // Judge before calling next. Deliberately no .catch handler: if this hook throws or the figure is
  // missing, the call goes on (fail open). A broken guard must not stop the person's work.
  on('tool.call', { tool: 'Agent' }, async ($, e, next) => {
    const limit = fiveHour((await $.session.usage()).rateLimits)
    if (!limit || limit.percentUsed < threshold) return next(e)
    if (onLimit === 'block') return { deny: refusal(limit, threshold) }

    const windowKey = limit.resetsAt ?? 'unknown'
    if (allowedWindow === windowKey) return next(e)

    // Ask. If nobody can answer (a -p run) or the dialog is dismissed, the block stands.
    pending ??= $.ui.ask(askText(limit, threshold), {
      options: [ALLOW_ONCE, ALLOW_WINDOW, KEEP_BLOCKING],
      header: 'Quota',
    }).finally(() => { pending = undefined })
    let answer: string
    try {
      answer = await pending
    } catch {
      return { deny: refusal(limit, threshold) }
    }
    if (!isAllowed(answer)) return { deny: refusal(limit, threshold) }
    if (answer === ALLOW_WINDOW) allowedWindow = windowKey
    return next(e)
  })

  // Pushed whenever a window moves a whole point: toast once on the way up, re-arm on the way down.
  on('session.measure', ($, e, next) => {
    const limit = fiveHour(e.rateLimits)
    if (limit && limit.percentUsed >= threshold && !isWarned) {
      isWarned = true
      $.ui.toast(`quota-guard: 5-hour window at ${Math.round(limit.percentUsed)}%, subagents ${onLimit === 'ask' ? 'need your OK' : 'blocked'} until ${clock(limit.resetsAt)}`)
    } else if (!limit || limit.percentUsed < threshold) {
      isWarned = false
    }
    return next(e)
  })
}
