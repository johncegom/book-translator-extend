import { expect, test } from 'claude-code/testing'

import { fiveHour, parseThreshold, refusal } from '../hooks/register'

test('threshold: numbers 1 to 100 are kept, anything else is 85', () => {
  expect(parseThreshold('85')).toBe(85)
  expect(parseThreshold(' 70 ')).toBe(70)
  expect(parseThreshold(100)).toBe(100)
  for (const bad of ['', 'abc', '0', '101', '-5', undefined, null, NaN]) {
    expect(parseThreshold(bad)).toBe(85)
  }
})

test('fiveHour picks the five_hour window and ignores others', () => {
  expect(fiveHour(undefined)).toBeUndefined()
  expect(fiveHour([])).toBeUndefined()
  expect(fiveHour([{ kind: 'seven_day', percentUsed: 99 }])).toBeUndefined()
  expect(fiveHour([{ kind: 'seven_day', percentUsed: 99 }, { kind: 'five_hour', percentUsed: 10 }])?.percentUsed).toBe(10)
})

test('the refusal names the percent, the limit and tells the model to stop', () => {
  const text = refusal({ kind: 'five_hour', percentUsed: 87.4, resetsAt: '2026-11-12T15:40:00Z' }, 85)
  expect(text).toMatch(/at 87%/)
  expect(text).toMatch(/limit 85%/)
  expect(text).toMatch(/Stop/)
})

test('an Agent call is refused at the threshold and allowed below it', async ($, on) => {
  let percent = 90
  on('session.usage', () => ({ value: { startedAt: 0, context: {}, rateLimits: [{ kind: 'five_hour', percentUsed: percent, resetsAt: '2026-11-12T15:40:00Z' }], cost: undefined } }))
  on('tool.call', () => ({ result: {} }))

  const blocked = await $.tool.call({ tool: 'Agent', prompt: 'x', description: 'x', subagent_type: 'general-purpose' })
  expect(JSON.stringify(blocked)).toMatch(/quota-guard/)

  percent = 40
  const allowed = await $.tool.call({ tool: 'Agent', prompt: 'x', description: 'x', subagent_type: 'general-purpose' })
  expect(JSON.stringify(allowed)).not.toMatch(/quota-guard/)
})

test('other tools are never touched, whatever the usage', async ($, on) => {
  on('session.usage', () => ({ value: { startedAt: 0, context: {}, rateLimits: [{ kind: 'five_hour', percentUsed: 99 }], cost: undefined } }))
  on('tool.call', () => ({ result: {} }))
  const res = await $.tool.call({ tool: 'Bash', command: 'ls' })
  expect(JSON.stringify(res)).not.toMatch(/quota-guard/)
})

test('no five-hour figure (API key) fails open', async ($, on) => {
  on('session.usage', () => ({ value: { startedAt: 0, context: {}, rateLimits: [], cost: undefined } }))
  on('tool.call', () => ({ result: {} }))
  const res = await $.tool.call({ tool: 'Agent', prompt: 'x', description: 'x', subagent_type: 'general-purpose' })
  expect(JSON.stringify(res)).not.toMatch(/quota-guard/)
})
