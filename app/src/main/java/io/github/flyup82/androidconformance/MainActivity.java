package io.github.flyup82.androidconformance;

import android.app.Activity;
import android.graphics.Color;
import android.os.Bundle;
import android.view.ViewGroup;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

public final class MainActivity extends Activity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        FixtureComposition composition = FixtureComposition.current();
        LinearLayout content = new LinearLayout(this);
        content.setOrientation(LinearLayout.VERTICAL);
        int padding = Math.round(20 * getResources().getDisplayMetrics().density);
        content.setPadding(padding, padding, padding, padding);

        content.addView(text("Android Conformance", 24, Color.BLACK));
        content.addView(text(
                "fixture=" + BuildConfig.AQ_FIXTURE_REVISION
                        + "\ncomposition=" + composition.kind(),
                15,
                Color.DKGRAY
        ));

        for (SeedCatalog.Seed seed : SeedCatalog.ALL) {
            String state = composition.isActive(seed.id()) ? "active" : "normal";
            TextView row = text(seed.id() + " · " + seed.family() + " · " + state, 16, Color.BLACK);
            row.setContentDescription(
                    "seed " + seed.id() + ", route " + seed.route() + ", state " + state
            );
            content.addView(row);
        }

        TextView boundary = text(
                "Source scaffold only. Seed behavior and device execution are not yet admitted.",
                14,
                Color.RED
        );
        content.addView(boundary);

        ScrollView scroll = new ScrollView(this);
        scroll.addView(
                content,
                new ScrollView.LayoutParams(
                        ViewGroup.LayoutParams.MATCH_PARENT,
                        ViewGroup.LayoutParams.WRAP_CONTENT
                )
        );
        setContentView(scroll);
    }

    private TextView text(String value, int sizeSp, int color) {
        TextView view = new TextView(this);
        view.setText(value);
        view.setTextSize(sizeSp);
        view.setTextColor(color);
        view.setPadding(0, 0, 0, Math.round(12 * getResources().getDisplayMetrics().density));
        return view;
    }
}
