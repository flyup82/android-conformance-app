package io.github.flyup82.androidconformance;

import java.util.Arrays;
import java.util.Collections;
import java.util.List;

final class SeedCatalog {
    static final List<Seed> ALL = Collections.unmodifiableList(Arrays.asList(
            new Seed("A-D-001", "lifecycle_state_loss", "lifecycle", "recreate_activity"),
            new Seed("A-D-002", "back_deep_link", "navigation", "back_from_detail"),
            new Seed("A-D-003", "permission_denial", "permission", "deny_camera_permission"),
            new Seed("A-D-004", "network_recovery", "network", "retry_embedded_transport"),
            new Seed("A-D-005", "accessibility_semantics", "accessibility", "inspect_star_action"),
            new Seed("A-D-006", "adaptive_localization", "adaptive", "inspect_long_localized_text"),
            new Seed("A-D-007", "runtime_stability", "stability", "trigger_controlled_failure"),
            new Seed("A-D-008", "persistence", "persistence", "recreate_after_increment"),
            new Seed("A-D-009", "intent_platform_boundary", "intent", "send_untrusted_local_route"),
            new Seed("A-D-010", "webview_native_boundary", "webview", "activate_local_recovery_link")
    ));

    private SeedCatalog() {}

    static final class Seed {
        private final String id;
        private final String family;
        private final String route;
        private final String triggerId;

        Seed(String id, String family, String route, String triggerId) {
            this.id = id;
            this.family = family;
            this.route = route;
            this.triggerId = triggerId;
        }

        String id() {
            return id;
        }

        String family() {
            return family;
        }

        String route() {
            return route;
        }

        String triggerId() {
            return triggerId;
        }
    }
}
