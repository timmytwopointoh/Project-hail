package dev.projecthail.visionprobe;

import android.app.Activity;
import android.os.Bundle;
import android.graphics.Color;
import android.view.Gravity;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

public final class MainActivity extends Activity {
    private int presses = 0;

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        LinearLayout column = new LinearLayout(this);
        column.setOrientation(LinearLayout.VERTICAL);
        column.setPadding(36, 60, 36, 36);
        column.setGravity(Gravity.CENTER);
        column.setBackgroundColor(Color.rgb(18, 27, 43));

        TextView title = new TextView(this);
        title.setText("VISION PROBE READY");
        title.setTextSize(26);
        title.setTextColor(Color.WHITE);
        title.setGravity(Gravity.CENTER);

        TextView state = new TextView(this);
        state.setText("TAPPED 0 TIMES");
        state.setTextSize(20);
        state.setTextColor(Color.rgb(116, 231, 204));
        state.setGravity(Gravity.CENTER);

        Button button = new Button(this);
        button.setText("TAP TO TEST");
        button.setOnClickListener(view -> {
            presses++;
            state.setText("TAPPED " + presses + (presses == 1 ? " TIME" : " TIMES"));
        });

        LinearLayout.LayoutParams wrap = new LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        wrap.setMargins(0, 12, 0, 12);
        column.addView(title, wrap);
        column.addView(state, wrap);
        column.addView(button, wrap);
        setContentView(column);
    }
}
