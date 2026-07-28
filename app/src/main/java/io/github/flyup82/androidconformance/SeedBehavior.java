package io.github.flyup82.androidconformance;

import java.util.Arrays;
import java.util.Collections;
import java.util.HashSet;
import java.util.Set;

/**
 * Deterministic, app-local behavior deltas for the public conformance fixture.
 *
 * <p>This class contains no evaluator answer, device control, network access, or
 * external side effect. Every delta is enabled only by its exact public seed.
 */
final class SeedBehavior {
    static final String ROUTE_HOME = "home";
    static final String ROUTE_INTENT = "intent";
    static final String ROUTE_INTENT_PREVIEW = "intent_preview";
    static final String ROUTE_NAVIGATION_DETAIL = "navigation_detail";
    static final String ROUTE_WEBVIEW_RECOVERY = "webview_recovery";

    private static final Set<String> ALLOWED_ROUTES = Collections.unmodifiableSet(
            new HashSet<>(Arrays.asList(
                    ROUTE_HOME,
                    "lifecycle",
                    "navigation",
                    ROUTE_NAVIGATION_DETAIL,
                    "permission",
                    "network",
                    "accessibility",
                    "adaptive",
                    "stability",
                    "persistence",
                    ROUTE_INTENT,
                    "webview",
                    ROUTE_WEBVIEW_RECOVERY
            ))
    );

    private SeedBehavior() {}

    static int restoreLifecycleCounter(Integer savedCounter, boolean seedActive) {
        if (seedActive || savedCounter == null) {
            return 0;
        }
        return savedCounter;
    }

    static String backRouteFromNavigationDetail(boolean seedActive) {
        return seedActive ? ROUTE_HOME : "navigation";
    }

    static boolean permissionRetryAvailable(boolean denied, boolean seedActive) {
        return !denied || !seedActive;
    }

    static int committedOperationsAfterRetry(boolean seedActive) {
        return seedActive ? 2 : 1;
    }

    static String accessibilityDescription(boolean seedActive) {
        return seedActive ? null : "Open deterministic fixture details";
    }

    static boolean adaptiveContentIsSingleLine(boolean seedActive) {
        return seedActive;
    }

    static boolean shouldTriggerControlledFailure(boolean seedActive) {
        return seedActive;
    }

    static int displayedPersistentCount(
            int processLocalCount,
            int storedCount,
            boolean seedActive
    ) {
        return seedActive ? processLocalCount : storedCount;
    }

    static String resolveIncomingRoute(String requestedRoute, boolean seedActive) {
        if (requestedRoute == null || requestedRoute.isEmpty()) {
            return ROUTE_HOME;
        }
        if (ALLOWED_ROUTES.contains(requestedRoute)) {
            return requestedRoute;
        }
        return seedActive ? ROUTE_INTENT_PREVIEW : ROUTE_INTENT;
    }

    static boolean webViewRecoveryAvailable(boolean seedActive) {
        return !seedActive;
    }
}
