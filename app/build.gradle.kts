plugins {
    id("com.android.application")
}

val releaseSigningEnvironment = mapOf(
    "storeFile" to providers.environmentVariable("AQ_SIGNING_KEYSTORE").orNull,
    "storePassword" to providers.environmentVariable("AQ_SIGNING_STORE_PASSWORD").orNull,
    "keyAlias" to providers.environmentVariable("AQ_SIGNING_KEY_ALIAS").orNull,
    "keyPassword" to providers.environmentVariable("AQ_SIGNING_KEY_PASSWORD").orNull,
)
val releaseSigningRequested = releaseSigningEnvironment.values.any { !it.isNullOrBlank() }
val releaseSigningReady = releaseSigningEnvironment.values.all { !it.isNullOrBlank() }

if (releaseSigningRequested && !releaseSigningReady) {
    throw GradleException("external release signing configuration is incomplete")
}

val seedIds = listOf(
    "A-D-001",
    "A-D-002",
    "A-D-003",
    "A-D-004",
    "A-D-005",
    "A-D-006",
    "A-D-007",
    "A-D-008",
    "A-D-009",
    "A-D-010",
)

android {
    namespace = "io.github.flyup82.androidconformance"
    compileSdk = 36

    defaultConfig {
        applicationId = "io.github.flyup82.androidconformance"
        minSdk = 28
        targetSdk = 36
        versionCode = 1
        versionName = "0.1.0-dev.2"

        buildConfigField("String", "AQ_FIXTURE_REVISION", "\"android-conformance-r2\"")
    }

    buildFeatures {
        buildConfig = true
    }

    flavorDimensions += "fixture"
    productFlavors {
        create("clean") {
            dimension = "fixture"
            buildConfigField("String", "AQ_COMPOSITION", "\"clean\"")
            buildConfigField("String", "AQ_ACTIVE_SEEDS", "\"\"")
        }
        create("normalTwin") {
            dimension = "fixture"
            buildConfigField("String", "AQ_COMPOSITION", "\"normal_twin\"")
            buildConfigField("String", "AQ_ACTIVE_SEEDS", "\"\"")
        }
        seedIds.forEachIndexed { index, seedId ->
            create("seed%03d".format(index + 1)) {
                dimension = "fixture"
                buildConfigField("String", "AQ_COMPOSITION", "\"single_seed\"")
                buildConfigField("String", "AQ_ACTIVE_SEEDS", "\"$seedId\"")
            }
        }
        create("allSeeds") {
            dimension = "fixture"
            buildConfigField("String", "AQ_COMPOSITION", "\"all_seeds\"")
            buildConfigField("String", "AQ_ACTIVE_SEEDS", "\"${seedIds.joinToString(",")}\"")
        }
    }

    signingConfigs {
        if (releaseSigningReady) {
            create("externalRelease") {
                storeFile = file(requireNotNull(releaseSigningEnvironment["storeFile"]))
                storePassword = requireNotNull(releaseSigningEnvironment["storePassword"])
                keyAlias = requireNotNull(releaseSigningEnvironment["keyAlias"])
                keyPassword = requireNotNull(releaseSigningEnvironment["keyPassword"])
            }
        }
    }

    buildTypes {
        debug {
            isDebuggable = true
        }
        release {
            isMinifyEnabled = false
            // Release signing is intentionally external and USER-owned.
            // Never add a keystore or password to this repository.
            if (releaseSigningReady) {
                signingConfig = signingConfigs.getByName("externalRelease")
            }
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}
