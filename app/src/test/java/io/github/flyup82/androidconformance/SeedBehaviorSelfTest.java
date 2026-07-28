package io.github.flyup82.androidconformance;

/** Plain-JDK behavior checks; this test does not invoke Android tooling. */
public final class SeedBehaviorSelfTest {
    private SeedBehaviorSelfTest() {}

    public static void main(String[] args) {
        lifecycleStateLossIsIndependent();
        backContextDeltaIsIndependent();
        permissionRecoveryDeltaIsIndependent();
        retryDeltaIsIndependent();
        accessibilityDeltaIsIndependent();
        adaptiveDeltaIsIndependent();
        stabilityDeltaIsIndependent();
        persistenceDeltaIsIndependent();
        intentBoundaryDeltaIsIndependent();
        webViewRecoveryDeltaIsIndependent();
    }

    private static void lifecycleStateLossIsIndependent() {
        require(SeedBehavior.restoreLifecycleCounter(3, false) == 3);
        require(SeedBehavior.restoreLifecycleCounter(3, true) == 0);
    }

    private static void backContextDeltaIsIndependent() {
        require("navigation".equals(
                SeedBehavior.backRouteFromNavigationDetail(false)
        ));
        require(SeedBehavior.ROUTE_HOME.equals(
                SeedBehavior.backRouteFromNavigationDetail(true)
        ));
    }

    private static void permissionRecoveryDeltaIsIndependent() {
        require(SeedBehavior.permissionRetryAvailable(true, false));
        require(!SeedBehavior.permissionRetryAvailable(true, true));
    }

    private static void retryDeltaIsIndependent() {
        require(SeedBehavior.committedOperationsAfterRetry(false) == 1);
        require(SeedBehavior.committedOperationsAfterRetry(true) == 2);
    }

    private static void accessibilityDeltaIsIndependent() {
        require(SeedBehavior.accessibilityDescription(false) != null);
        require(SeedBehavior.accessibilityDescription(true) == null);
    }

    private static void adaptiveDeltaIsIndependent() {
        require(!SeedBehavior.adaptiveContentIsSingleLine(false));
        require(SeedBehavior.adaptiveContentIsSingleLine(true));
    }

    private static void stabilityDeltaIsIndependent() {
        require(!SeedBehavior.shouldTriggerControlledFailure(false));
        require(SeedBehavior.shouldTriggerControlledFailure(true));
    }

    private static void persistenceDeltaIsIndependent() {
        require(SeedBehavior.displayedPersistentCount(1, 4, false) == 4);
        require(SeedBehavior.displayedPersistentCount(1, 4, true) == 1);
    }

    private static void intentBoundaryDeltaIsIndependent() {
        require(SeedBehavior.ROUTE_INTENT.equals(
                SeedBehavior.resolveIncomingRoute("untrusted", false)
        ));
        require(SeedBehavior.ROUTE_INTENT_PREVIEW.equals(
                SeedBehavior.resolveIncomingRoute("untrusted", true)
        ));
    }

    private static void webViewRecoveryDeltaIsIndependent() {
        require(SeedBehavior.webViewRecoveryAvailable(false));
        require(!SeedBehavior.webViewRecoveryAvailable(true));
    }

    private static void require(boolean condition) {
        if (!condition) {
            throw new AssertionError("public behavior contract failed");
        }
    }
}
