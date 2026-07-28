package io.github.flyup82.androidconformance;

import java.util.Arrays;
import java.util.Collections;
import java.util.HashSet;
import java.util.LinkedHashSet;
import java.util.Set;
import java.util.stream.Collectors;

final class FixtureComposition {
    private static final Set<String> CATALOG = Collections.unmodifiableSet(SeedCatalog.ALL.stream()
            .map(SeedCatalog.Seed::id)
            .collect(Collectors.toCollection(HashSet::new)));

    private final String kind;
    private final Set<String> activeSeeds;

    private FixtureComposition(String kind, Set<String> activeSeeds) {
        this.kind = kind;
        this.activeSeeds = Collections.unmodifiableSet(new LinkedHashSet<>(activeSeeds));
        validate();
    }

    static FixtureComposition current() {
        Set<String> seeds = Arrays.stream(BuildConfig.AQ_ACTIVE_SEEDS.split(",", -1))
                .filter(value -> !value.isEmpty())
                .collect(Collectors.toCollection(LinkedHashSet::new));
        return new FixtureComposition(BuildConfig.AQ_COMPOSITION, seeds);
    }

    String kind() {
        return kind;
    }

    boolean isActive(String seedId) {
        return activeSeeds.contains(seedId);
    }

    private void validate() {
        if (!CATALOG.containsAll(activeSeeds)) {
            throw new IllegalStateException("unknown public seed");
        }
        if ("clean".equals(kind) || "normal_twin".equals(kind)) {
            requireSeedCount(0);
        } else if ("single_seed".equals(kind)) {
            requireSeedCount(1);
        } else if ("all_seeds".equals(kind)) {
            if (!activeSeeds.equals(CATALOG)) {
                throw new IllegalStateException("all_seeds must activate the complete catalog");
            }
        } else {
            throw new IllegalStateException("unknown composition");
        }
    }

    private void requireSeedCount(int count) {
        if (activeSeeds.size() != count) {
            throw new IllegalStateException(kind + " has invalid seed count");
        }
    }
}
