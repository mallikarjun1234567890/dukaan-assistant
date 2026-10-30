import assert from 'node:assert/strict'
import { createRazorpayCheckoutSession } from './razorpaySession.ts'
import { test } from 'node:test'

test('a failed card attempt does not block a later success handler', () => {
  const session = createRazorpayCheckoutSession()
  const notices: string[] = []
  session.noteFailedAttempt((message) => notices.push(message), 'International cards are not supported')
  assert.equal(notices.length, 1)
  assert.equal(session.beginHandler(), true)
  session.finishSuccess()
  session.noteDismiss((message) => notices.push(message), 'Checkout was cancelled. Your trial is unchanged.')
  assert.deepEqual(notices, ['International cards are not supported'])
})

test('dismiss during verification does not cancel a successful payment', () => {
  const session = createRazorpayCheckoutSession()
  const notices: string[] = []
  assert.equal(session.beginHandler(), true)
  session.noteDismiss((message) => notices.push(message), 'Checkout was cancelled. Your trial is unchanged.')
  session.finishSuccess()
  assert.deepEqual(notices, [])
})

test('dismiss without a handler is treated as cancel', () => {
  const session = createRazorpayCheckoutSession()
  const notices: string[] = []
  session.noteDismiss((message) => notices.push(message), 'Checkout was cancelled. Your trial is unchanged.')
  assert.equal(notices[0], 'Checkout was cancelled. Your trial is unchanged.')
  assert.equal(session.beginHandler(), true)
})
