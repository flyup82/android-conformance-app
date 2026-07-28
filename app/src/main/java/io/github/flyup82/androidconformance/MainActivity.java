package io.github.flyup82.androidconformance;

import android.Manifest;
import android.app.Activity;
import android.content.Intent;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.view.View;
import android.view.ViewGroup;
import android.webkit.WebResourceRequest;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

/**
 * Synthetic, deterministic Android fixture.
 *
 * <p>Every scenario is local to this package. It performs no real network,
 * account, payment, message, upload, or third-party action.
 */
public final class MainActivity extends Activity {
    private static final String EXTRA_ROUTE = "aq_fixture_route";
    private static final String STATE_ROUTE = "aq_state_route";
    private static final String STATE_LIFECYCLE_COUNTER = "aq_lifecycle_counter";
    private static final int REQUEST_CAMERA_PERMISSION = 401;
    private static final String PREFS = "aq_fixture_state";
    private static final String PREF_PERSISTENCE_COUNT = "persistence_count";

    private FixtureComposition composition;
    private LinearLayout content;
    private String currentRoute = SeedBehavior.ROUTE_HOME;
    private int lifecycleCounter;
    private int processLocalPersistenceCount;
    private boolean permissionDenied;
    private boolean transportFailedOnce;
    private int committedOperations;
    private String scenarioMessage;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        composition = FixtureComposition.current();
        if (savedInstanceState != null) {
            currentRoute = savedInstanceState.getString(
                    STATE_ROUTE,
                    SeedBehavior.ROUTE_HOME
            );
        }
        currentRoute = resolveIntentRoute(getIntent(), currentRoute);
        Integer savedCounter = savedInstanceState == null
                ? null
                : savedInstanceState.getInt(STATE_LIFECYCLE_COUNTER, 0);
        lifecycleCounter = SeedBehavior.restoreLifecycleCounter(
                savedCounter,
                active("A-D-001")
        );
        render();
    }

    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        setIntent(intent);
        currentRoute = resolveIntentRoute(intent, currentRoute);
        render();
    }

    @Override
    protected void onSaveInstanceState(Bundle outState) {
        super.onSaveInstanceState(outState);
        outState.putString(STATE_ROUTE, currentRoute);
        if (!active("A-D-001")) {
            outState.putInt(STATE_LIFECYCLE_COUNTER, lifecycleCounter);
        }
    }

    @Override
    public void onBackPressed() {
        if (SeedBehavior.ROUTE_NAVIGATION_DETAIL.equals(currentRoute)) {
            currentRoute = SeedBehavior.backRouteFromNavigationDetail(active("A-D-002"));
            scenarioMessage = active("A-D-002")
                    ? "Detail context was discarded."
                    : "Returned to the navigation fixture.";
            render();
            return;
        }
        if (!SeedBehavior.ROUTE_HOME.equals(currentRoute)) {
            currentRoute = SeedBehavior.ROUTE_HOME;
            scenarioMessage = null;
            render();
            return;
        }
        super.onBackPressed();
    }

    @Override
    public void onRequestPermissionsResult(
            int requestCode,
            String[] permissions,
            int[] grantResults
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == REQUEST_CAMERA_PERMISSION) {
            permissionDenied = grantResults.length == 0 || grantResults[0] != 0;
            scenarioMessage = permissionDenied
                    ? "Camera permission denied. No camera access was attempted."
                    : "Camera permission granted. No camera access will be attempted.";
            currentRoute = "permission";
            render();
        }
    }

    private void render() {
        content = new LinearLayout(this);
        content.setOrientation(LinearLayout.VERTICAL);
        content.setPadding(dp(20), dp(20), dp(20), dp(20));
        content.setBackgroundColor(Color.WHITE);

        addText("Android Conformance", 24, Color.BLACK);
        addText(
                "fixture=" + BuildConfig.AQ_FIXTURE_REVISION
                        + "\ncomposition=" + composition.kind()
                        + "\nroute=" + currentRoute,
                14,
                Color.DKGRAY
        );

        switch (currentRoute) {
            case "lifecycle":
                renderLifecycle();
                break;
            case "navigation":
                renderNavigation();
                break;
            case SeedBehavior.ROUTE_NAVIGATION_DETAIL:
                renderNavigationDetail();
                break;
            case "permission":
                renderPermission();
                break;
            case "network":
                renderNetwork();
                break;
            case "accessibility":
                renderAccessibility();
                break;
            case "adaptive":
                renderAdaptive();
                break;
            case "stability":
                renderStability();
                break;
            case "persistence":
                renderPersistence();
                break;
            case "intent":
                renderIntent();
                break;
            case SeedBehavior.ROUTE_INTENT_PREVIEW:
                renderIntentPreview();
                break;
            case "webview":
                renderWebView();
                break;
            case SeedBehavior.ROUTE_WEBVIEW_RECOVERY:
                renderWebViewRecovery();
                break;
            default:
                renderHome();
                break;
        }

        if (scenarioMessage != null) {
            TextView status = addText(scenarioMessage, 15, Color.rgb(80, 45, 0));
            status.setContentDescription("fixture status: " + scenarioMessage);
        }
        if (!SeedBehavior.ROUTE_HOME.equals(currentRoute)) {
            addButton("Return to fixture index", "return_to_fixture_index", view -> {
                currentRoute = SeedBehavior.ROUTE_HOME;
                scenarioMessage = null;
                render();
            });
        }

        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        scroll.addView(
                content,
                new ScrollView.LayoutParams(
                        ViewGroup.LayoutParams.MATCH_PARENT,
                        ViewGroup.LayoutParams.WRAP_CONTENT
                )
        );
        setContentView(scroll);
    }

    private void renderHome() {
        addText(
                "Public deterministic scenarios. A seed changes only its matching route.",
                16,
                Color.DKGRAY
        );
        for (SeedCatalog.Seed seed : SeedCatalog.ALL) {
            String state = active(seed.id()) ? "active" : "normal";
            addButton(
                    seed.id() + " · " + seed.family() + " · " + state,
                    "route_" + seed.route(),
                    view -> {
                        currentRoute = seed.route();
                        scenarioMessage = null;
                        render();
                    }
            ).setTag(seed.triggerId());
        }
        addText(
                "Source behavior only. Build, APK, device, and conformance claims remain closed.",
                14,
                Color.RED
        );
    }

    private void renderLifecycle() {
        addScenarioHeading("A-D-001 · lifecycle state");
        addText("Counter: " + lifecycleCounter, 20, Color.BLACK);
        addButton("Increment counter", "increment_lifecycle_counter", view -> {
            lifecycleCounter += 1;
            scenarioMessage = "Counter incremented.";
            render();
        });
        addButton("Recreate activity", "recreate_activity", view -> recreate());
    }

    private void renderNavigation() {
        addScenarioHeading("A-D-002 · back and deep-link context");
        addText("Navigation root", 18, Color.BLACK);
        addButton("Open local detail", "open_navigation_detail", view -> {
            currentRoute = SeedBehavior.ROUTE_NAVIGATION_DETAIL;
            scenarioMessage = null;
            render();
        });
        addText(
                "Equivalent local deep link: aqconformance://fixture/navigation/detail",
                13,
                Color.DKGRAY
        );
    }

    private void renderNavigationDetail() {
        addScenarioHeading("A-D-002 · navigation detail");
        addText("Detail item: deterministic-42", 18, Color.BLACK);
        TextView backInstruction = addText(
                "Use Android Back to evaluate the previous context.",
                14,
                Color.DKGRAY
        );
        backInstruction.setContentDescription("back_from_detail");
    }

    private void renderPermission() {
        addScenarioHeading("A-D-003 · permission denial recovery");
        addText(
                "The fixture requests CAMERA permission but never opens or reads the camera.",
                14,
                Color.DKGRAY
        );
        boolean retryAvailable = SeedBehavior.permissionRetryAvailable(
                permissionDenied,
                active("A-D-003")
        );
        Button request = addButton(
                permissionDenied ? "Retry camera permission" : "Request camera permission",
                "deny_camera_permission",
                view -> requestPermissions(
                        new String[]{Manifest.permission.CAMERA},
                        REQUEST_CAMERA_PERMISSION
                )
        );
        request.setEnabled(retryAvailable);
        if (permissionDenied && !retryAvailable) {
            addText("Permission-dependent flow is blocked.", 16, Color.RED);
        }
    }

    private void renderNetwork() {
        addScenarioHeading("A-D-004 · embedded transport retry");
        addText(
                "No external network is used. The first local transport attempt always fails.",
                14,
                Color.DKGRAY
        );
        addText("Committed operations: " + committedOperations, 18, Color.BLACK);
        addButton(
                transportFailedOnce ? "Retry embedded request" : "Start embedded request",
                "retry_embedded_transport",
                view -> {
                    if (!transportFailedOnce) {
                        transportFailedOnce = true;
                        scenarioMessage = "Deterministic transient failure.";
                    } else {
                        committedOperations = SeedBehavior.committedOperationsAfterRetry(
                                active("A-D-004")
                        );
                        scenarioMessage = "Embedded retry completed.";
                    }
                    render();
                }
        );
    }

    private void renderAccessibility() {
        addScenarioHeading("A-D-005 · accessibility semantics");
        addText("Inspect the semantics of the symbol action below.", 14, Color.DKGRAY);
        Button symbol = addButton("★", "inspect_star_action", view -> {
            scenarioMessage = "Deterministic fixture detail opened.";
            render();
        });
        symbol.setContentDescription(
                SeedBehavior.accessibilityDescription(active("A-D-005"))
        );
    }

    private void renderAdaptive() {
        addScenarioHeading("A-D-006 · adaptive localized content");
        TextView localized = addText(
                "Long localized fixture text: Configuration changes and larger fonts must keep this complete action reachable.",
                18,
                Color.BLACK
        );
        boolean singleLine = SeedBehavior.adaptiveContentIsSingleLine(active("A-D-006"));
        localized.setSingleLine(singleLine);
        if (singleLine) {
            localized.setWidth(dp(160));
        } else {
            localized.setLayoutParams(new LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT,
                    ViewGroup.LayoutParams.WRAP_CONTENT
            ));
        }
        localized.setContentDescription("inspect_long_localized_text");
        addButton("Complete adaptive action", "complete_adaptive_action", view -> {
            scenarioMessage = "Adaptive action remains reachable.";
            render();
        });
    }

    private void renderStability() {
        addScenarioHeading("A-D-007 · controlled runtime stability");
        addText(
                "The trigger has no external side effect. In the matching seed it terminates this app process.",
                14,
                Color.DKGRAY
        );
        addButton("Trigger controlled action", "trigger_controlled_failure", view -> {
            if (SeedBehavior.shouldTriggerControlledFailure(active("A-D-007"))) {
                throw new IllegalStateException("A-D-007 controlled local failure");
            }
            scenarioMessage = "Controlled action completed without failure.";
            render();
        });
    }

    private void renderPersistence() {
        addScenarioHeading("A-D-008 · local persistence");
        SharedPreferences preferences = getSharedPreferences(PREFS, MODE_PRIVATE);
        int displayed = SeedBehavior.displayedPersistentCount(
                processLocalPersistenceCount,
                preferences.getInt(PREF_PERSISTENCE_COUNT, 0),
                active("A-D-008")
        );
        addText("Saved count: " + displayed, 20, Color.BLACK);
        addButton("Increment saved count", "increment_persistent_count", view -> {
            if (active("A-D-008")) {
                processLocalPersistenceCount += 1;
            } else {
                preferences.edit()
                        .putInt(PREF_PERSISTENCE_COUNT, displayed + 1)
                        .apply();
            }
            scenarioMessage = "Local count incremented.";
            render();
        });
        addButton("Recreate after increment", "recreate_after_increment", view -> recreate());
    }

    private void renderIntent() {
        addScenarioHeading("A-D-009 · local intent boundary");
        addText(
                "The trigger sends an explicit intent back to this exact activity with an untrusted local route.",
                14,
                Color.DKGRAY
        );
        addButton("Send untrusted local route", "send_untrusted_local_route", view -> {
            Intent intent = new Intent(this, MainActivity.class);
            intent.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP);
            intent.putExtra(EXTRA_ROUTE, "untrusted_fixture_preview");
            startActivity(intent);
        });
        if ("untrusted route rejected".equals(scenarioMessage)) {
            addText("Untrusted route rejected.", 16, Color.rgb(0, 100, 0));
        }
    }

    private void renderIntentPreview() {
        addScenarioHeading("A-D-009 · synthetic preview");
        addText(
                "Synthetic account preview was reached from an untrusted local route.",
                18,
                Color.RED
        );
        addText("No real account or protected data exists in this fixture.", 14, Color.DKGRAY);
    }

    private void renderWebView() {
        addScenarioHeading("A-D-010 · WebView/native recovery");
        addText(
                "Embedded HTML only. JavaScript, file access, content access, and external navigation are disabled.",
                14,
                Color.DKGRAY
        );
        WebView webView = new WebView(this);
        webView.getSettings().setJavaScriptEnabled(false);
        webView.getSettings().setAllowFileAccess(false);
        webView.getSettings().setAllowContentAccess(false);
        webView.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                return handleEmbeddedRecovery(request.getUrl());
            }

            @SuppressWarnings("deprecation")
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, String url) {
                return handleEmbeddedRecovery(Uri.parse(url));
            }
        });
        webView.loadDataWithBaseURL(
                null,
                "<html><body><h2>Embedded fixture error</h2>"
                        + "<a id=\"activate_local_recovery_link\""
                        + " aria-label=\"activate_local_recovery_link\""
                        + " href=\"aq-local://recover\">Return to native recovery</a>"
                        + "</body></html>",
                "text/html",
                "UTF-8",
                null
        );
        content.addView(
                webView,
                new LinearLayout.LayoutParams(
                        ViewGroup.LayoutParams.MATCH_PARENT,
                        dp(220)
                )
        );
    }

    private void renderWebViewRecovery() {
        addScenarioHeading("A-D-010 · native recovery");
        addText("Native recovery surface reached.", 18, Color.rgb(0, 100, 0));
    }

    private boolean handleEmbeddedRecovery(Uri uri) {
        if (!"aq-local".equals(uri.getScheme()) || !"recover".equals(uri.getHost())) {
            scenarioMessage = "External navigation blocked.";
            render();
            return true;
        }
        if (SeedBehavior.webViewRecoveryAvailable(active("A-D-010"))) {
            currentRoute = SeedBehavior.ROUTE_WEBVIEW_RECOVERY;
            scenarioMessage = null;
        } else {
            currentRoute = "webview";
            scenarioMessage = "Embedded error remains trapped.";
        }
        render();
        return true;
    }

    private String resolveIntentRoute(Intent intent, String fallback) {
        if (intent == null) {
            return fallback;
        }
        String requested = intent.getStringExtra(EXTRA_ROUTE);
        Uri data = intent.getData();
        if (
                data != null
                        && "aqconformance".equals(data.getScheme())
                        && "fixture".equals(data.getHost())
                        && "/navigation/detail".equals(data.getPath())
        ) {
            requested = SeedBehavior.ROUTE_NAVIGATION_DETAIL;
        }
        if (requested == null) {
            return fallback;
        }
        String resolved = SeedBehavior.resolveIncomingRoute(
                requested,
                active("A-D-009")
        );
        if (
                SeedBehavior.ROUTE_INTENT.equals(resolved)
                        && !SeedBehavior.ROUTE_INTENT.equals(requested)
        ) {
            scenarioMessage = "untrusted route rejected";
        }
        return resolved;
    }

    private boolean active(String seedId) {
        return composition.isActive(seedId);
    }

    private void addScenarioHeading(String title) {
        addText(title, 21, Color.BLACK);
    }

    private TextView addText(String value, int sizeSp, int color) {
        TextView view = new TextView(this);
        view.setText(value);
        view.setTextSize(sizeSp);
        view.setTextColor(color);
        view.setPadding(0, 0, 0, dp(12));
        content.addView(view);
        return view;
    }

    private Button addButton(String label, String contentDescription, View.OnClickListener action) {
        Button button = new Button(this);
        button.setText(label);
        button.setContentDescription(contentDescription);
        button.setOnClickListener(action);
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT
        );
        params.setMargins(0, 0, 0, dp(8));
        content.addView(button, params);
        return button;
    }

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }
}
