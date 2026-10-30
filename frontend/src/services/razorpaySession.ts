/** Checkout session flags. payment.failed must not block a later Success in the same modal. */

export type CheckoutNotice = (message: string) => void

export function createRazorpayCheckoutSession() {
  let verifying = false
  let completed = false

  return {
    noteFailedAttempt(notify: CheckoutNotice, message: string) {
      if (completed || verifying) return
      notify(message)
    },
    noteDismiss(notify: CheckoutNotice, message: string) {
      if (completed || verifying) return
      notify(message)
    },
    beginHandler(): boolean {
      if (completed) return false
      verifying = true
      return true
    },
    finishSuccess() {
      completed = true
      verifying = false
    },
    finishFailure() {
      completed = true
      verifying = false
    },
  }
}
