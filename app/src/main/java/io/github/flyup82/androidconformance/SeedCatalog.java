package io.github.flyup82.androidconformance;

import java.util.Arrays;
import java.util.Collections;
import java.util.List;

final class SeedCatalog {
    static final List<Seed> ALL = Collections.unmodifiableList(Arrays.asList(
            new Seed("A-D-001", "lifecycle_state_loss", "lifecycle"),
            new Seed("A-D-002", "back_deep_link", "navigation"),
            new Seed("A-D-003", "permission_denial", "permission"),
            new Seed("A-D-004", "network_recovery", "network"),
            new Seed("A-D-005", "accessibility_semantics", "accessibility"),
            new Seed("A-D-006", "adaptive_localization", "adaptive"),
            new Seed("A-D-007", "runtime_stability", "stability"),
            new Seed("A-D-008", "persistence", "persistence"),
            new Seed("A-D-009", "intent_platform_boundary", "intent"),
            new Seed("A-D-010", "webview_native_boundary", "webview")
    ));

    private SeedCatalog() {}

    static final class Seed {
        private final String id;
        private final String family;
        private final String route;

        Seed(String id, String family, String route) {
            this.id = id;
            this.family = family;
            this.route = route;
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
    }
}
