import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from data_manager import (
    load_subscriptions,
    add_subscription,
    edit_subscription,
    delete_subscription,
    monthly_equivalent,
    CATEGORIES,
)
from fuzzy_engine import (
    evaluate_subscription,
    cost,
    usage,
    importance,
    alternatives,
    cancellation_fee,
    retention,
)
from baseline import evaluate_baseline


# ============================================================
# 1. Page configuration and styling
# ============================================================

st.set_page_config(
    page_title="SUBSIGHT | Subscription Advisor",
    page_icon="S",
    layout="wide",
)

st.markdown(
    """
    <style>
    /* Main sidebar */
    section[data-testid="stSidebar"] {
        background: #101828;
        border-right: 1px solid #263449;
    }

    section[data-testid="stSidebar"] > div {
        padding: 2rem 1rem 1rem 1rem;
    }

    /* Sidebar text */
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] span {
        color: #D0D5DD;
    }

    /* Brand */
    .subsight-brand {
        padding: 12px 8px 24px 8px;
    }

    .subsight-logo {
        background: #2563EB;
        color: white;
        width: 44px;
        height: 44px;
        border-radius: 13px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 23px;
        font-weight: 800;
        margin-bottom: 15px;
    }

    .subsight-title {
        color: #FFFFFF;
        font-size: 27px;
        font-weight: 750;
        letter-spacing: 1px;
    }

    .subsight-subtitle {
        color: #98A2B3;
        font-size: 13px;
        margin-top: 6px;
        line-height: 1.6;
    }

    .sidebar-section {
        color: #667085;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 1.5px;
        padding: 12px 8px 8px 8px;
        text-transform: uppercase;
    }

    .sidebar-footer {
        border-top: 1px solid #263449;
        margin-top: 30px;
        padding: 20px 8px 0 8px;
        color: #98A2B3;
        font-size: 12px;
        line-height: 1.8;
    }

    /* Navigation options */
    section[data-testid="stSidebar"]
    div[data-testid="stRadio"] > div {
        gap: 7px;
    }

    section[data-testid="stSidebar"]
    div[data-testid="stRadio"] label {
        background: transparent;
        border: 1px solid transparent;
        border-radius: 9px;
        padding: 10px 12px;
        transition: background 0.2s ease;
    }

    section[data-testid="stSidebar"]
    div[data-testid="stRadio"] label:hover {
        background: #1D2939;
        border-color: #344054;
    }

    section[data-testid="stSidebar"]
    div[data-testid="stRadio"] label:has(input:checked) {
        background: #1D355B;
        border: 1px solid #315A91;
    }

    section[data-testid="stSidebar"]
    div[data-testid="stRadio"] label:has(input:checked) p,
    section[data-testid="stSidebar"]
    div[data-testid="stRadio"] label:has(input:checked) span {
        color: #FFFFFF !important;
        font-weight: 650;
    }

    /* Hide radio circles for a cleaner navigation */
    section[data-testid="stSidebar"]
    div[data-testid="stRadio"] label > div:first-child {
        display: none;
    }

    /* Main content spacing */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    div[data-testid="stMetric"] {
        background: rgba(128, 128, 128, 0.08);
        padding: 15px;
        border-radius: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# 2. Helper functions
# ============================================================

def format_rupees(value):
    return f"₹{float(value):,.2f}"


def prepare_recommendations(df):
    """Run both decision methods for each saved subscription."""
    records = []

    for _, row in df.iterrows():
        monthly_cost = monthly_equivalent(
            row["price"], row["billing_cycle"]
        )

        common_inputs = {
            "monthly_cost": monthly_cost,
            "usage_days": int(row["usage_days"]),
            "importance_rating": float(row["importance"]),
            "alternative_rating": float(row["alternatives"]),
            "cancellation_fee_amount": float(row["cancellation_fee"]),
        }

        if monthly_cost > 2000:
            fuzzy_result = {
                "score": None,
                "action": "Out of range",
                "explanation": (
                    "Monthly-equivalent cost is above the fuzzy engine's "
                    "current maximum of ₹2,000. Expand and test the input "
                    "universe before using this recommendation."
                ),
            }
            baseline_result = {"score": None, "action": "Out of range"}
        else:
            try:
                fuzzy_result = evaluate_subscription(**common_inputs)
                baseline_result = evaluate_baseline(**common_inputs)
            except (ValueError, RuntimeError) as exc:
                fuzzy_result = {
                    "score": None,
                    "action": "Error",
                    "explanation": str(exc),
                }
                baseline_result = {"score": None, "action": "Error"}

        records.append({
            "id": row["id"],
            "name": row["name"],
            "category": row["category"],
            "billing_cycle": row["billing_cycle"],
            "price": float(row["price"]),
            "monthly_cost": float(monthly_cost),
            "usage_days": int(row["usage_days"]),
            "importance": float(row["importance"]),
            "alternatives": float(row["alternatives"]),
            "cancellation_fee": float(row["cancellation_fee"]),
            "fuzzy_score": fuzzy_result["score"],
            "fuzzy_action": fuzzy_result["action"],
            "baseline_score": baseline_result["score"],
            "baseline_action": baseline_result["action"],
            "explanation": fuzzy_result["explanation"],
        })

    return pd.DataFrame(records)


def run_test_scenarios(test_df):
    """Evaluate both systems on the same test scenarios."""
    results = []

    for _, row in test_df.iterrows():
        inputs = {
            "monthly_cost": float(row["monthly_cost"]),
            "usage_days": int(row["usage_days"]),
            "importance_rating": float(row["importance"]),
            "alternative_rating": float(row["alternatives"]),
            "cancellation_fee_amount": float(row["cancellation_fee"]),
        }

        try:
            fuzzy_result = evaluate_subscription(**inputs)
            baseline_result = evaluate_baseline(**inputs)

            results.append({
                "Scenario": row["scenario_id"],
                "Expected action": row["expected_action"],
                "Fuzzy score": fuzzy_result["score"],
                "Fuzzy action": fuzzy_result["action"],
                "Baseline score": baseline_result["score"],
                "Baseline action": baseline_result["action"],
                "Fuzzy matches expectation": (
                    fuzzy_result["action"] == row["expected_action"]
                ),
                "Baseline matches expectation": (
                    baseline_result["action"] == row["expected_action"]
                ),
            })
        except (ValueError, RuntimeError) as exc:
            results.append({
                "Scenario": row["scenario_id"],
                "Expected action": row["expected_action"],
                "Fuzzy score": None,
                "Fuzzy action": "Error",
                "Baseline score": None,
                "Baseline action": "Error",
                "Fuzzy matches expectation": False,
                "Baseline matches expectation": False,
                "Error": str(exc),
            })

    return pd.DataFrame(results)




# Advanced dashboard helpers
ACTIONS = ["Keep", "Review", "Downgrade", "Cancel"]
COLORS = {
    "Keep": "#10B981",
    "Review": "#F59E0B",
    "Downgrade": "#3B82F6",
    "Cancel": "#EF4444",
}


def inject_pro_css():
    st.markdown(
        """
        <style>
        .block-container {padding-top: 1.2rem; padding-bottom: 2rem;}
        .kpi {
            background: linear-gradient(135deg, rgba(99,102,241,.12), rgba(128,128,128,.06));
            border-radius: 14px; padding: 16px 18px; height: 100%;
            transition: transform .15s ease, box-shadow .15s ease;
        }
        .kpi:hover {transform: translateY(-3px); box-shadow: 0 8px 20px rgba(0,0,0,.15);}
        .kpi-label {font-size: .78rem; letter-spacing: .06em; text-transform: uppercase; opacity: .7;}
        .kpi-value {font-size: 1.8rem; font-weight: 700; line-height: 1.25;}
        .kpi-sub {font-size: .8rem; opacity: .75;}
        .hero {
            padding: 20px 24px; border-radius: 16px; margin-bottom: 18px;
            background: linear-gradient(120deg, #4F46E5 0%, #7C3AED 55%, #DB2777 100%);
            color: white;
        }
        .hero h1 {margin: 0; font-size: 1.9rem; color: white;}
        .hero p {margin: 4px 0 0; opacity: .9;}
        .pill {
            display:inline-block; padding: 2px 10px; border-radius: 999px;
            font-size: .75rem; font-weight: 600; color: white;
        }
        div[data-baseweb="tab-list"] {gap: 6px;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _inr(v):
    return f"₹{float(v):,.0f}"


def _kpi(col, label, value, sub="", accent="#6366F1"):
    col.markdown(
        f"""<div class="kpi" style="border-left:4px solid {accent}">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-sub">{sub}</div></div>""",
        unsafe_allow_html=True,
    )


def _style(fig, height=380):
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=50, b=10),
        legend=dict(orientation="h", y=-0.15),
        font=dict(size=13),
    )
    return fig


def render_dashboard(rec: pd.DataFrame):
    st.markdown(
        """<div class="hero"><h1>Subscription Command Center</h1>
        <p>Spending, value-for-money and savings opportunities, powered by fuzzy inference.</p></div>""",
        unsafe_allow_html=True,
    )

    if rec.empty:
        st.info("No subscriptions saved yet. Open Manage Subscriptions to add one.")
        return

    st.sidebar.divider()
    st.sidebar.subheader("Dashboard filters")
    cats = sorted(rec["category"].unique())
    sel_cats = st.sidebar.multiselect("Categories", cats, default=cats)
    sel_cycles = st.sidebar.multiselect(
        "Billing cycle",
        sorted(rec["billing_cycle"].unique()),
        default=sorted(rec["billing_cycle"].unique()),
    )
    total_all = float(rec["monthly_cost"].sum())
    budget = st.sidebar.number_input(
        "Monthly budget (₹)",
        min_value=100.0,
        value=float(max(500, round(total_all * 0.8, -2))),
        step=100.0,
    )

    df = rec[rec["category"].isin(sel_cats) & rec["billing_cycle"].isin(sel_cycles)].copy()
    if df.empty:
        st.warning("No subscriptions match the current filters.")
        return

    df["cost_per_use"] = df["monthly_cost"] / df["usage_days"].clip(lower=1)
    df["wasted_spend"] = df["monthly_cost"] * (1 - df["usage_days"] / 30)
    valid = df[df["fuzzy_action"].isin(ACTIONS)].copy()

    total = df["monthly_cost"].sum()
    annual = total * 12
    wasted = df["wasted_spend"].sum()
    cancel_df = valid[valid["fuzzy_action"] == "Cancel"]
    cancel_save = cancel_df["monthly_cost"].sum()
    avg_cpu = df["cost_per_use"].mean()

    if valid.empty or valid["monthly_cost"].sum() == 0:
        health = float("nan")
    else:
        health = (valid["fuzzy_score"] * valid["monthly_cost"]).sum() / valid["monthly_cost"].sum()

    over = total - budget
    k1, k2, k3, k4, k5 = st.columns(5)
    _kpi(k1, "Monthly spend", _inr(total),
         f"{'▲' if over > 0 else '▼'} {_inr(abs(over))} {'over' if over > 0 else 'under'} budget",
         "#EF4444" if over > 0 else "#10B981")
    _kpi(k2, "Annual cost", _inr(annual), f"{len(df)} active subscriptions", "#6366F1")
    _kpi(k3, "Avg cost / use-day", _inr(avg_cpu), "lower is better", "#3B82F6")
    _kpi(k4, "Under-used spend", _inr(wasted), f"{wasted / total * 100:.0f}% of monthly spend", "#F59E0B")
    _kpi(k5, "Portfolio health",
         "N/A" if pd.isna(health) else f"{health:.0f}/100",
         f"{len(cancel_df)} cancel candidate(s)", "#10B981")

    st.write("")

    tab_over, tab_value, tab_save, tab_cmp, tab_data = st.tabs(
        ["Overview", "Value analysis", "Savings planner", "Fuzzy vs baseline", "Data & export"]
    )

    with tab_over:
        g1, g2 = st.columns([1, 1.4])

        with g1:
            fig = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=total,
                number={"prefix": "₹", "valueformat": ",.0f"},
                delta={"reference": budget, "increasing": {"color": "#EF4444"},
                       "decreasing": {"color": "#10B981"}},
                title={"text": "Budget utilisation"},
                gauge={
                    "axis": {"range": [0, max(budget, total) * 1.3]},
                    "bar": {"color": "#6366F1"},
                    "steps": [
                        {"range": [0, budget * 0.8], "color": "rgba(16,185,129,.25)"},
                        {"range": [budget * 0.8, budget], "color": "rgba(245,158,11,.25)"},
                        {"range": [budget, max(budget, total) * 1.3], "color": "rgba(239,68,68,.25)"},
                    ],
                    "threshold": {"line": {"color": "#EF4444", "width": 4}, "value": budget},
                },
            ))
            st.plotly_chart(_style(fig, 340), use_container_width=True)

        with g2:
            if valid.empty:
                st.info("No valid fuzzy results to display.")
            else:
                fig = px.treemap(
                    valid,
                    path=[px.Constant("All"), "category", "name"],
                    values="monthly_cost",
                    color="fuzzy_action",
                    color_discrete_map={**COLORS, "(?)": "#64748B"},
                    title="Spend map: size = cost, colour = recommendation",
                )
                st.plotly_chart(_style(fig, 340), use_container_width=True)

        o1, o2 = st.columns(2)
        with o1:
            cat = df.groupby("category", as_index=False)["monthly_cost"].sum()
            fig = px.pie(cat, names="category", values="monthly_cost", hole=0.55,
                         title="Spending by category")
            fig.update_traces(textinfo="percent+label")
            st.plotly_chart(_style(fig), use_container_width=True)
        with o2:
            top = df.nlargest(8, "monthly_cost").sort_values("monthly_cost")
            fig = px.bar(top, x="monthly_cost", y="name", orientation="h",
                         color="fuzzy_action", color_discrete_map=COLORS,
                         title="Top spenders", labels={"monthly_cost": "₹ / month", "name": ""})
            st.plotly_chart(_style(fig), use_container_width=True)

    with tab_value:
        v1, v2 = st.columns(2)
        with v1:
            fig = px.scatter(
                df, x="usage_days", y="monthly_cost", size="importance",
                color="fuzzy_action", color_discrete_map=COLORS, hover_name="name",
                title="Usage vs cost (bubble = importance)",
                labels={"usage_days": "Usage days / month", "monthly_cost": "₹ / month"},
            )
            fig.add_vline(x=10, line_dash="dot", opacity=.4)
            fig.add_hline(y=df["monthly_cost"].median(), line_dash="dot", opacity=.4)
            fig.add_annotation(x=2, y=df["monthly_cost"].max(), text="High cost, low use",
                               showarrow=False, font=dict(color="#EF4444"))
            st.plotly_chart(_style(fig), use_container_width=True)
        with v2:
            cpu = df.sort_values("cost_per_use", ascending=False).head(10)
            fig = px.bar(cpu, x="name", y="cost_per_use", color="fuzzy_action",
                         color_discrete_map=COLORS, title="Cost per usage-day (worst first)",
                         labels={"cost_per_use": "₹ per day used", "name": ""})
            st.plotly_chart(_style(fig), use_container_width=True)

        r1, r2 = st.columns(2)
        with r1:
            pick = st.selectbox("Radar profile for", df["name"].tolist())
            row = df[df["name"] == pick].iloc[0]
            axes = ["Usage", "Importance", "Alternatives", "Cost", "Exit fee"]
            vals = [
                row["usage_days"] / 30 * 10,
                row["importance"],
                row["alternatives"],
                min(row["monthly_cost"] / 2000 * 10, 10),
                min(row["cancellation_fee"] / 1000 * 10, 10),
            ]
            fig = go.Figure(go.Scatterpolar(r=vals + vals[:1], theta=axes + axes[:1],
                                            fill="toself", line_color="#7C3AED"))
            fig.update_layout(polar=dict(radialaxis=dict(range=[0, 10])),
                              title=f"Profile: {pick} (all axes scaled 0-10)")
            st.plotly_chart(_style(fig, 360), use_container_width=True)
        with r2:
            if not valid.empty:
                heat = pd.crosstab(valid["category"], valid["fuzzy_action"]).reindex(
                    columns=ACTIONS, fill_value=0)
                fig = px.imshow(heat, text_auto=True, aspect="auto",
                                color_continuous_scale="Purples",
                                title="Category × recommendation heatmap")
                st.plotly_chart(_style(fig, 360), use_container_width=True)

    with tab_save:
        st.write("Pick subscriptions you are willing to cancel and see the projected impact.")
        default = cancel_df["name"].tolist()
        chosen = st.multiselect("Subscriptions to cancel", df["name"].tolist(), default=default)
        sel = df[df["name"].isin(chosen)]
        save_m = sel["monthly_cost"].sum()
        fees = sel["cancellation_fee"].sum()
        net_year = save_m * 12 - fees
        breakeven = (fees / save_m) if save_m > 0 and fees > 0 else 0

        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Monthly savings", _inr(save_m))
        s2.metric("One-time fees", _inr(fees))
        s3.metric("First-year net", _inr(net_year))
        s4.metric("Break-even", f"{breakeven:.1f} mo" if breakeven else "Immediate")

        w1, w2 = st.columns(2)
        with w1:
            fig = go.Figure(go.Waterfall(
                x=["Current annual", "Avoided charges", "Cancellation fees", "Projected annual"],
                measure=["absolute", "relative", "relative", "total"],
                y=[annual, -save_m * 12, fees, 0],
                connector={"line": {"color": "rgba(128,128,128,.5)"}},
                increasing={"marker": {"color": "#EF4444"}},
                decreasing={"marker": {"color": "#10B981"}},
                totals={"marker": {"color": "#6366F1"}},
            ))
            fig.update_layout(title="Annual cost bridge")
            st.plotly_chart(_style(fig), use_container_width=True)
        with w2:
            months = list(range(0, 13))
            keep_line = [total * m for m in months]
            after_line = [(total - save_m) * m + (fees if m > 0 else 0) for m in months]
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=months, y=keep_line, name="Keep everything",
                                     line=dict(color="#EF4444")))
            fig.add_trace(go.Scatter(x=months, y=after_line, name="After cancelling",
                                     line=dict(color="#10B981"), fill="tonexty",
                                     fillcolor="rgba(16,185,129,.15)"))
            fig.update_layout(title="Cumulative spend, next 12 months",
                              xaxis_title="Month", yaxis_title="₹")
            st.plotly_chart(_style(fig), use_container_width=True)

        st.caption("Estimates only. Billing dates, refunds and contract terms may change the result.")

    with tab_cmp:
        both = df[df["fuzzy_score"].notna() & df["baseline_score"].notna()]
        if both.empty:
            st.info("No comparable results available.")
        else:
            agree = (both["fuzzy_action"] == both["baseline_action"]).mean() * 100
            corr = both["fuzzy_score"].corr(both["baseline_score"])
            m1, m2, m3 = st.columns(3)
            m1.metric("Action agreement", f"{agree:.0f}%")
            m2.metric("Score correlation", "n/a" if pd.isna(corr) else f"{corr:.2f}")
            m3.metric("Avg score gap",
                      f"{(both['fuzzy_score'] - both['baseline_score']).abs().mean():.1f} pts")

            fig = px.scatter(both, x="baseline_score", y="fuzzy_score", color="fuzzy_action",
                             color_discrete_map=COLORS, hover_name="name",
                             title="Fuzzy score vs weighted baseline",
                             labels={"baseline_score": "Baseline", "fuzzy_score": "Fuzzy"})
            fig.add_shape(type="line", x0=0, y0=0, x1=100, y1=100,
                          line=dict(dash="dash", color="gray"))
            st.plotly_chart(_style(fig, 420), use_container_width=True)

            diff = both[both["fuzzy_action"] != both["baseline_action"]]
            st.subheader("Where the methods disagree")
            if diff.empty:
                st.success("Both methods agree on every subscription.")
            else:
                st.dataframe(
                    diff[["name", "fuzzy_score", "fuzzy_action", "baseline_score", "baseline_action"]],
                    use_container_width=True, hide_index=True)

    with tab_data:
        action_pick = st.multiselect("Recommendation", ACTIONS + ["Out of range", "Error"],
                                     default=ACTIONS + ["Out of range", "Error"])
        table = df[df["fuzzy_action"].isin(action_pick)][[
            "name", "category", "billing_cycle", "monthly_cost", "usage_days",
            "cost_per_use", "importance", "fuzzy_score", "fuzzy_action", "baseline_action",
        ]]
        st.dataframe(
            table,
            use_container_width=True,
            hide_index=True,
            column_config={
                "monthly_cost": st.column_config.NumberColumn("Monthly ₹", format="₹%.0f"),
                "cost_per_use": st.column_config.NumberColumn("₹ / use-day", format="₹%.1f"),
                "usage_days": st.column_config.ProgressColumn("Usage days", min_value=0, max_value=30, format="%d"),
                "importance": st.column_config.ProgressColumn("Importance", min_value=0, max_value=10, format="%.1f"),
                "fuzzy_score": st.column_config.ProgressColumn("Fuzzy score", min_value=0, max_value=100, format="%.0f"),
            },
        )
        st.download_button(
            "Download report (CSV)",
            table.to_csv(index=False).encode("utf-8"),
            file_name="subsight_report.csv",
            mime="text/csv",
            type="primary",
        )

# ============================================================
# 3. Sidebar navigation
# ============================================================

# ============================================================
# 3. SUBSIGHT Sidebar Navigation
# ============================================================

with st.sidebar:
    st.markdown(
        """
        <div class="subsight-brand">
            <div class="subsight-logo">S</div>
            <div class="subsight-title">SUBSIGHT</div>
            <div class="subsight-subtitle">
                Smart Subscription<br>
                Decision Advisor
            </div>
        </div>
        <div class="sidebar-section">Workspace</div>
        """,
        unsafe_allow_html=True,
    )

    page = st.radio(
        "Navigation",
        [
            "Dashboard",
            "Manage Subscriptions",
            "Recommendations",
            "What-If Simulator",
            "Fuzzy Logic Explorer",
            "Experiment Results",
            "About the Project",
        ],
        format_func=lambda item: {
            "Dashboard": "▦   Dashboard",
            "Manage Subscriptions": "▤   Manage Subscriptions",
            "Recommendations": "✧   Recommendations",
            "What-If Simulator": "⇄   What-If Simulator",
            "Fuzzy Logic Explorer": "◈   Fuzzy Logic Explorer",
            "Experiment Results": "▥   Experiment Results",
            "About the Project": "ⓘ   About the Project",
        }[item],
        label_visibility="collapsed",
    )

    st.markdown(
        """
        <div class="sidebar-footer">
            <b style="color:#D0D5DD;">SUBSIGHT v1.0</b><br>
            Soft Computing Project<br>
            B.Tech CSE · AI/ML
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# 4. Load subscription records
# ============================================================

try:
    subscriptions = load_subscriptions()
except Exception as exc:
    st.error(f"Could not load subscription data: {exc}")
    st.stop()

if subscriptions.empty:
    recommendations = pd.DataFrame()
else:
    recommendations = prepare_recommendations(subscriptions)


# ============================================================
# 5. Dashboard
# ============================================================

if page == "Dashboard":
    inject_pro_css()
    render_dashboard(recommendations)


# ============================================================
# 6. Manage subscriptions
# ============================================================

# ============================================================
# Manage Subscriptions — Management Center
# ============================================================

elif page == "Manage Subscriptions":
    st.title("Subscription Management Center")
    st.caption("SUBSIGHT / Workspace / Subscription records")

    st.write(
        "Manage recurring services, review billing details, "
        "and keep your subscription records organized."
    )

    current = load_subscriptions()

    # Summary metrics
    total_subscriptions = len(current)

    total_monthly = (
        sum(
            monthly_equivalent(row["price"], row["billing_cycle"])
            for _, row in current.iterrows()
        )
        if not current.empty else 0
    )

    annual_billing = (
        int((current["billing_cycle"] == "Annual").sum())
        if not current.empty else 0
    )

    monthly_billing = (
        int((current["billing_cycle"] == "Monthly").sum())
        if not current.empty else 0
    )

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total subscriptions", total_subscriptions)
    m2.metric("Monthly-equivalent cost", format_rupees(total_monthly))
    m3.metric("Monthly billing", monthly_billing)
    m4.metric("Annual billing", annual_billing)

    st.divider()

    # Add, edit and delete workspace
    tab_add, tab_edit, tab_delete = st.tabs(
        ["＋ Add subscription", "✎ Edit subscription", "⌫ Delete subscription"]
    )

    with tab_add:
        st.subheader("Add a new subscription")
        st.caption("Enter the service details and billing information.")

        with st.form("add_subscription_form", clear_on_submit=True):
            left, right = st.columns(2, gap="large")

            with left:
                name = st.text_input(
                    "Subscription name",
                    placeholder="e.g. Netflix",
                )
                category = st.selectbox("Category", CATEGORIES)
                cycle = st.selectbox(
                    "Billing cycle", ["Monthly", "Annual"]
                )
                price = st.number_input(
                    "Price for selected billing cycle (₹)",
                    min_value=1.0,
                    max_value=24000.0,
                    value=199.0,
                    step=1.0,
                )

            with right:
                usage_days = st.slider(
                    "Usage days per month", 0, 30, 10
                )
                importance_rating = st.slider(
                    "Importance (0–10)", 0.0, 10.0, 5.0, 0.5
                )
                alternative_rating = st.slider(
                    "Cheaper alternatives (0–10)",
                    0.0, 10.0, 5.0, 0.5,
                )
                fee = st.number_input(
                    "One-time cancellation fee (₹)",
                    min_value=0.0,
                    max_value=1000.0,
                    value=0.0,
                    step=50.0,
                )

            if cycle == "Annual":
                st.info(
                    f"Monthly-equivalent cost: {format_rupees(price / 12)}"
                )
            else:
                st.info(
                    f"Monthly-equivalent cost: {format_rupees(price)}"
                )

            submitted = st.form_submit_button(
                "Add subscription",
                type="primary",
                use_container_width=True,
            )

        if submitted:
            if not name.strip():
                st.error("Please enter a subscription name.")
            else:
                try:
                    new_id = add_subscription({
                        "name": name.strip(),
                        "category": category,
                        "billing_cycle": cycle,
                        "price": price,
                        "usage_days": usage_days,
                        "importance": importance_rating,
                        "alternatives": alternative_rating,
                        "cancellation_fee": fee,
                    })
                    st.success(f"Subscription added successfully: {new_id}")
                    st.rerun()
                except (ValueError, OSError) as exc:
                    st.error(str(exc))

    with tab_edit:
        st.subheader("Update subscription details")

        if current.empty:
            st.info("There are no subscriptions to edit.")
        else:
            selected_id = st.selectbox(
                "Select subscription",
                current["id"].tolist(),
                format_func=lambda item_id: (
                    f"{current.loc[current['id'] == item_id, 'name'].iloc[0]}"
                    f" · {item_id}"
                ),
                key="management_edit_id",
            )

            selected = current[
                current["id"] == selected_id
            ].iloc[0]

            with st.form("management_edit_form"):
                left, right = st.columns(2, gap="large")

                with left:
                    edit_name = st.text_input(
                        "Name", value=str(selected["name"])
                    )
                    edit_category = st.selectbox(
                        "Category",
                        CATEGORIES,
                        index=CATEGORIES.index(selected["category"]),
                    )
                    edit_cycle = st.selectbox(
                        "Billing cycle",
                        ["Monthly", "Annual"],
                        index=["Monthly", "Annual"].index(
                            selected["billing_cycle"]
                        ),
                    )
                    edit_price = st.number_input(
                        "Price (₹)",
                        min_value=1.0,
                        max_value=24000.0,
                        value=float(selected["price"]),
                        step=1.0,
                    )

                with right:
                    edit_usage = st.slider(
                        "Usage days per month",
                        0, 30, int(selected["usage_days"]),
                        key="management_edit_usage",
                    )
                    edit_importance = st.slider(
                        "Importance (0–10)",
                        0.0, 10.0, float(selected["importance"]), 0.5,
                        key="management_edit_importance",
                    )
                    edit_alternatives = st.slider(
                        "Cheaper alternatives (0–10)",
                        0.0, 10.0,
                        float(selected["alternatives"]), 0.5,
                        key="management_edit_alternatives",
                    )
                    edit_fee = st.number_input(
                        "Cancellation fee (₹)",
                        min_value=0.0,
                        max_value=1000.0,
                        value=float(selected["cancellation_fee"]),
                        step=50.0,
                        key="management_edit_fee",
                    )

                update_clicked = st.form_submit_button(
                    "Save changes",
                    type="primary",
                    use_container_width=True,
                )

            if update_clicked:
                if not edit_name.strip():
                    st.error("Subscription name cannot be empty.")
                else:
                    try:
                        edit_subscription(selected_id, {
                            "name": edit_name.strip(),
                            "category": edit_category,
                            "billing_cycle": edit_cycle,
                            "price": edit_price,
                            "usage_days": edit_usage,
                            "importance": edit_importance,
                            "alternatives": edit_alternatives,
                            "cancellation_fee": edit_fee,
                        })
                        st.success("Subscription updated successfully.")
                        st.rerun()
                    except (ValueError, OSError) as exc:
                        st.error(str(exc))

    with tab_delete:
        st.subheader("Remove a subscription")

        if current.empty:
            st.info("There are no subscriptions to delete.")
        else:
            delete_id = st.selectbox(
                "Select subscription to remove",
                current["id"].tolist(),
                format_func=lambda item_id: (
                    f"{current.loc[current['id'] == item_id, 'name'].iloc[0]}"
                    f" · {item_id}"
                ),
                key="management_delete_id",
            )

            delete_name = current.loc[
                current["id"] == delete_id, "name"
            ].iloc[0]

            st.warning(
                f"You are about to remove **{delete_name}** "
                f"({delete_id}) from your saved records."
            )

            confirmed = st.checkbox(
                "I understand this will delete the saved record.",
                key="management_delete_confirm",
            )

            if st.button(
                "Delete selected subscription",
                type="primary",
                disabled=not confirmed,
            ):
                try:
                    delete_subscription(delete_id)
                    st.success("Subscription deleted.")
                    st.rerun()
                except (ValueError, OSError) as exc:
                    st.error(str(exc))

    # Saved records
    st.divider()
    st.subheader("Your subscriptions")

    current = load_subscriptions()

    if current.empty:
        st.info("No subscriptions have been saved yet.")
    else:
        search = st.text_input(
            "Search saved records",
            placeholder="Search by name or category...",
            key="management_search",
        )

        display = current.copy()

        if search.strip():
            mask = (
                display["name"].astype(str).str.contains(
                    search.strip(), case=False, na=False
                )
                | display["category"].astype(str).str.contains(
                    search.strip(), case=False, na=False
                )
            )
            display = display[mask]

        display["Monthly-equivalent cost"] = display.apply(
            lambda row: monthly_equivalent(
                row["price"], row["billing_cycle"]
            ),
            axis=1,
        )

        table = display[
            [
                "id", "name", "category", "billing_cycle",
                "price", "Monthly-equivalent cost",
                "usage_days", "importance",
            ]
        ].copy()

        table.columns = [
            "ID", "Subscription", "Category", "Billing cycle",
            "Listed price (₹)", "Monthly cost (₹)",
            "Usage days", "Importance",
        ]

        st.caption(f"{len(display)} subscription records")

        st.dataframe(
            table,
            use_container_width=True,
            hide_index=True,
            height=400,
            column_config={
                "Listed price (₹)": st.column_config.NumberColumn(
                    format="₹%.2f"
                ),
                "Monthly cost (₹)": st.column_config.NumberColumn(
                    format="₹%.2f"
                ),
                "Usage days": st.column_config.NumberColumn(
                    format="%d days"
                ),
                "Importance": st.column_config.NumberColumn(
                    format="%.1f / 10"
                ),
            },
        )

        st.download_button(
            "Export subscription records (CSV)",
            data=table.to_csv(index=False).encode("utf-8-sig"),
            file_name="subsight_subscriptions.csv",
            mime="text/csv",
        )


# ============================================================
# 7. Recommendations
# ============================================================

# ============================================================
# Recommendations — Decision Center
# ============================================================

elif page == "Recommendations":
    st.title("Subscription Decision Center")
    st.caption(
        "SUBSIGHT / Intelligent recommendations / Decision analysis"
    )

    st.write(
        "Review recurring expenses, compare decision methods, "
        "and identify subscriptions that deserve attention."
    )

    if recommendations.empty:
        st.info(
            "No subscription records are available. "
            "Add subscriptions from Manage Subscriptions."
        )
        st.stop()

    # --------------------------------------------------------
    # Summary metrics
    # --------------------------------------------------------

    valid_actions = ["Keep", "Review", "Downgrade", "Cancel"]
    valid_df = recommendations[
        recommendations["fuzzy_action"].isin(valid_actions)
    ].copy()

    total = len(recommendations)
    cancel_count = int(
        (valid_df["fuzzy_action"] == "Cancel").sum()
    )
    review_count = int(
        (valid_df["fuzzy_action"] == "Review").sum()
    )
    disagreement_count = int(
        (
            valid_df["fuzzy_action"]
            != valid_df["baseline_action"]
        ).sum()
    )

    m1, m2, m3, m4 = st.columns(4)

    m1.metric("Subscriptions analysed", total)
    m2.metric("Cancellation candidates", cancel_count)
    m3.metric("Need review", review_count)
    m4.metric("Methods disagree", disagreement_count)

    st.divider()

    # --------------------------------------------------------
    # Filters
    # --------------------------------------------------------

    st.subheader("Explore recommendations")

    f1, f2, f3 = st.columns([1.2, 1, 1])

    with f1:
        search_text = st.text_input(
            "Search subscription",
            placeholder="e.g. Netflix, Spotify...",
            key="recommendation_search",
        )

    with f2:
        selected_actions = st.multiselect(
            "Fuzzy recommendation",
            valid_actions,
            default=valid_actions,
            key="recommendation_actions",
        )

    with f3:
        categories = sorted(
            recommendations["category"].dropna().unique().tolist()
        )
        selected_categories = st.multiselect(
            "Category",
            categories,
            default=categories,
            key="recommendation_categories",
        )

    filtered = recommendations[
        recommendations["fuzzy_action"].isin(selected_actions)
        & recommendations["category"].isin(selected_categories)
    ].copy()

    if search_text.strip():
        filtered = filtered[
            filtered["name"].astype(str).str.contains(
                search_text.strip(),
                case=False,
                na=False,
            )
        ]

    st.caption(f"Showing {len(filtered)} of {total} subscriptions")

    # --------------------------------------------------------
    # Main recommendation table
    # --------------------------------------------------------

    st.subheader("Recommendation overview")

    if filtered.empty:
        st.info("No subscriptions match the selected filters.")
    else:
        table_df = filtered[
            [
                "name",
                "category",
                "monthly_cost",
                "usage_days",
                "fuzzy_score",
                "fuzzy_action",
                "baseline_score",
                "baseline_action",
            ]
        ].copy()

        table_df.columns = [
            "Subscription",
            "Category",
            "Monthly cost (₹)",
            "Usage days",
            "Fuzzy score",
            "Fuzzy decision",
            "Baseline score",
            "Baseline decision",
        ]

        st.dataframe(
            table_df,
            use_container_width=True,
            hide_index=True,
            height=390,
            column_config={
                "Monthly cost (₹)": st.column_config.NumberColumn(
                    format="₹%.2f"
                ),
                "Fuzzy score": st.column_config.NumberColumn(
                    format="%.2f / 100"
                ),
                "Baseline score": st.column_config.NumberColumn(
                    format="%.2f / 100"
                ),
                "Usage days": st.column_config.NumberColumn(
                    format="%d days"
                ),
            },
        )

        csv_data = table_df.to_csv(index=False).encode("utf-8-sig")

        st.download_button(
            "Download filtered recommendations (CSV)",
            data=csv_data,
            file_name="subsight_recommendations.csv",
            mime="text/csv",
        )

    st.divider()

    # --------------------------------------------------------
    # Individual decision analysis
    # --------------------------------------------------------

    st.subheader("Individual decision analysis")

    if filtered.empty:
        st.info("Select filters that include at least one subscription.")
    else:
        selected_id = st.selectbox(
            "Choose a subscription to analyse",
            filtered["id"].tolist(),
            format_func=lambda item_id: (
                f"{filtered.loc[filtered['id'] == item_id, 'name'].iloc[0]}"
                f" — {item_id}"
            ),
            key="recommendation_detail_id",
        )

        item = filtered[
            filtered["id"] == selected_id
        ].iloc[0]

        st.markdown(f"### {item['name']}")
        st.caption(
            f"{item['category']} · "
            f"{item['usage_days']} usage days per month · "
            f"Monthly-equivalent cost: ₹{item['monthly_cost']:,.2f}"
        )

        fuzzy_score = item["fuzzy_score"]
        baseline_score = item["baseline_score"]

        left, right = st.columns(2, gap="large")

        with left:
            with st.container(border=True):
                st.caption("MAMDANI FUZZY INFERENCE")
                st.metric(
                    "Retention suitability",
                    (
                        "Unavailable"
                        if pd.isna(fuzzy_score)
                        else f"{float(fuzzy_score):.2f}/100"
                    ),
                )

                action = item["fuzzy_action"]
                st.markdown(f"## {action}")

                if action == "Keep":
                    st.write("The system suggests retaining this subscription.")
                elif action == "Review":
                    st.write("Review the cost and actual value before deciding.")
                elif action == "Downgrade":
                    st.write("Consider a lower-cost plan if it meets your needs.")
                elif action == "Cancel":
                    st.write("Consider cancellation after checking contract terms.")
                else:
                    st.write("The fuzzy system could not produce a valid decision.")

                st.caption(str(item["explanation"]))

        with right:
            with st.container(border=True):
                st.caption("WEIGHTED-SCORE BASELINE")
                st.metric(
                    "Baseline score",
                    (
                        "Unavailable"
                        if pd.isna(baseline_score)
                        else f"{float(baseline_score):.2f}/100"
                    ),
                )

                st.markdown(f"## {item['baseline_action']}")
                st.write(
                    "This decision is calculated independently using "
                    "the project's weighted-score baseline."
                )

                if item["fuzzy_action"] == item["baseline_action"]:
                    st.success("Both methods agree on the recommendation.")
                else:
                    st.warning(
                        "The methods disagree. Review the inputs and "
                        "decision rules before acting."
                    )

        # ----------------------------------------------------
        # Visual score comparison
        # ----------------------------------------------------

        st.subheader("Score comparison")

        score_records = []

        if not pd.isna(fuzzy_score):
            score_records.append({
                "Method": "Mamdani fuzzy logic",
                "Score": float(fuzzy_score),
            })

        if not pd.isna(baseline_score):
            score_records.append({
                "Method": "Weighted-score baseline",
                "Score": float(baseline_score),
            })

        if score_records:
            score_df = pd.DataFrame(score_records)

            fig = px.bar(
                score_df,
                x="Method",
                y="Score",
                text="Score",
                range_y=[0, 110],
                title="Retention suitability by method",
            )

            fig.update_traces(
                texttemplate="%{text:.2f}",
                textposition="outside",
            )

            fig.update_layout(
                template="plotly_white",
                showlegend=False,
                yaxis_title="Score out of 100",
                xaxis_title="",
                height=350,
            )

            st.plotly_chart(fig, use_container_width=True)

        # ----------------------------------------------------
        # Input profile
        # ----------------------------------------------------

        st.subheader("Factors used in the decision")

        a, b, c, d = st.columns(4)

        a.metric(
            "Monthly cost",
            f"₹{item['monthly_cost']:,.2f}",
        )
        b.metric(
            "Usage",
            f"{item['usage_days']} days",
        )
        c.metric(
            "Importance",
            f"{item['importance']:.1f}/10",
        )
        d.metric(
            "Cheaper alternatives",
            f"{item['alternatives']:.1f}/10",
        )

        st.caption(
            "Recommendations are decision-support suggestions. "
            "SUBSIGHT does not cancel subscriptions or verify "
            "provider contracts automatically."
        )


# ============================================================
# 8. What-if simulator
# ============================================================

# ============================================================
# What-If Simulator — Enhanced UI
# ============================================================

elif page == "What-If Simulator":
    import plotly.graph_objects as go

    st.title("What-If Simulator")
    st.caption(
        "SUBSIGHT / Decision Lab / Scenario Analysis"
    )

    st.markdown(
        """
        Explore how changes in subscription usage, cost and importance
        affect the recommendations generated by both decision systems.
        """
    )

    current = load_subscriptions()

    if current.empty:
        st.info("Add a subscription in Manage Subscriptions to begin.")
        st.stop()

    selected_id = st.selectbox(
        "Select a subscription to simulate",
        current["id"].tolist(),
        format_func=lambda item_id: (
            f"{item_id} — "
            f"{current.loc[current['id'] == item_id, 'name'].iloc[0]}"
        ),
    )

    row = current[current["id"] == selected_id].iloc[0]
    original_cost = float(
        monthly_equivalent(row["price"], row["billing_cycle"])
    )

    st.divider()

    left, right = st.columns([1.05, 1.4], gap="large")

    with left:
        st.subheader("Scenario inputs")
        st.caption("Adjust the values and evaluate your scenario.")

        with st.container(border=True):
            st.markdown("**Monthly-equivalent cost**")
            sim_cost = st.number_input(
                "Monthly cost (₹)",
                min_value=0.0,
                max_value=2000.0,
                value=float(min(original_cost, 2000)),
                step=25.0,
                key="sim_cost_enhanced",
            )

            sim_usage = st.slider(
                "Usage days per month",
                0, 30, int(row["usage_days"]),
                key="sim_usage_enhanced",
            )

            sim_importance = st.slider(
                "Importance",
                0.0, 10.0, float(row["importance"]), 0.5,
                key="sim_importance_enhanced",
            )

            sim_alternatives = st.slider(
                "Cheaper alternatives",
                0.0, 10.0, float(row["alternatives"]), 0.5,
                key="sim_alternatives_enhanced",
            )

            sim_fee = st.number_input(
                "Cancellation fee (₹)",
                min_value=0.0,
                max_value=1000.0,
                value=float(row["cancellation_fee"]),
                step=50.0,
                key="sim_fee_enhanced",
            )

            simulate = st.button(
                "Evaluate scenario",
                type="primary",
                use_container_width=True,
            )

        st.caption(
            "Changes are temporary. Your saved subscription is not modified."
        )

    with right:
        st.subheader("Scenario overview")

        m1, m2 = st.columns(2)
        m1.metric(
            "Saved monthly cost",
            f"₹{original_cost:,.2f}",
        )
        m2.metric(
            "Simulated monthly cost",
            f"₹{sim_cost:,.2f}",
            delta=f"₹{sim_cost - original_cost:+,.2f}",
        )

        m3, m4 = st.columns(2)
        m3.metric(
            "Usage",
            f"{sim_usage} days/month",
        )
        m4.metric(
            "Importance",
            f"{sim_importance:.1f}/10",
        )

        st.markdown("**What the system evaluates**")

        st.markdown(
            """
            - Monthly-equivalent subscription cost
            - Usage frequency
            - Personal importance
            - Availability of cheaper alternatives
            - Cancellation fee
            """
        )

        st.info(
            "The simulator compares two decision methods using the same "
            "scenario inputs."
        )

    if simulate:
        st.session_state["subsight_sim_result"] = {
            "id": selected_id,
            "cost": sim_cost,
            "usage": sim_usage,
            "importance": sim_importance,
            "alternatives": sim_alternatives,
            "fee": sim_fee,
        }

    saved = st.session_state.get("subsight_sim_result")

    if saved is not None and saved["id"] == selected_id:
        try:
            fuzzy_result = evaluate_subscription(
                saved["cost"],
                saved["usage"],
                saved["importance"],
                saved["alternatives"],
                saved["fee"],
            )

            baseline_result = evaluate_baseline(
                saved["cost"],
                saved["usage"],
                saved["importance"],
                saved["alternatives"],
                saved["fee"],
            )

            st.divider()
            st.subheader("Decision results")

            fcol, bcol = st.columns(2, gap="large")

            with fcol:
                st.markdown("**Mamdani fuzzy logic**")
                with st.container(border=True):
                    st.metric(
                        "Retention suitability",
                        f"{fuzzy_result['score']:.2f}/100",
                    )
                    st.markdown(
                        f"### {fuzzy_result['action']}"
                    )
                    st.caption(fuzzy_result["explanation"])

            with bcol:
                st.markdown("**Weighted-score baseline**")
                with st.container(border=True):
                    st.metric(
                        "Retention suitability",
                        f"{baseline_result['score']:.2f}/100",
                    )
                    st.markdown(
                        f"### {baseline_result['action']}"
                    )
                    st.caption(
                        "Calculated using the existing weighted-score method."
                    )

            st.subheader("Score comparison")

            fig = go.Figure()

            fig.add_trace(go.Bar(
                x=["Fuzzy logic", "Weighted-score baseline"],
                y=[fuzzy_result["score"], baseline_result["score"]],
                text=[
                    f"{fuzzy_result['score']:.2f}",
                    f"{baseline_result['score']:.2f}",
                ],
                textposition="outside",
                name="Retention score",
            ))

            fig.update_layout(
                yaxis_title="Retention suitability",
                yaxis_range=[0, 110],
                template="plotly_white",
                showlegend=False,
                height=360,
            )

            st.plotly_chart(fig, use_container_width=True)

            st.subheader("Potential savings estimate")

            fuzzy_action = fuzzy_result["action"]
            baseline_action = baseline_result["action"]

            if fuzzy_action == "Cancel":
                gross_monthly = saved["cost"]
                gross_yearly = saved["cost"] * 12
                first_year_net = gross_yearly - saved["fee"]

                s1, s2, s3 = st.columns(3)
                s1.metric(
                    "Gross monthly opportunity",
                    f"₹{gross_monthly:,.2f}",
                )
                s2.metric(
                    "Gross yearly opportunity",
                    f"₹{gross_yearly:,.2f}",
                )
                s3.metric(
                    "First-year estimate",
                    f"₹{first_year_net:,.2f}",
                )

                st.caption(
                    "Illustrative estimate only. It assumes 12 months of "
                    "avoided charges and subtracts the one-time cancellation "
                    "fee. It is not a confirmed saving."
                )
            else:
                st.info(
                    f"The fuzzy system recommends **{fuzzy_action}**. "
                    "Cancellation savings are not counted unless cancellation "
                    "is recommended. Downgrade savings require a known cheaper "
                    "plan price."
                )

            if fuzzy_action != baseline_action:
                st.warning(
                    f"The methods disagree: fuzzy logic recommends "
                    f"'{fuzzy_action}', while the baseline recommends "
                    f"'{baseline_action}'. Review the inputs and rules."
                )
            else:
                st.success(
                    f"Both methods recommend: {fuzzy_action}."
                )

        except (ValueError, RuntimeError, KeyError) as exc:
            st.error(f"Could not evaluate this scenario: {exc}")

    else:
        st.info(
            "Adjust the inputs and select **Evaluate scenario** to see the "
            "decision scores, recommendations and comparison chart."
        )

# ============================================================
# 9. Fuzzy Logic Explorer
# ============================================================

elif page == "Fuzzy Logic Explorer":
    st.title("Fuzzy Logic Explorer")
    st.write(
        "Explore the membership functions used by the Mamdani fuzzy inference system."
    )

    variables = {
        "Monthly cost": cost,
        "Usage days": usage,
        "Importance": importance,
        "Cheaper alternatives": alternatives,
        "Cancellation fee": cancellation_fee,
        "Retention suitability": retention,
    }
    selected_variable = st.selectbox("Select a fuzzy variable", list(variables.keys()))
    variable = variables[selected_variable]

    fig = go.Figure()
    for term_name, membership in variable.terms.items():
        fig.add_trace(go.Scatter(
            x=variable.universe,
            y=membership.mf,
            mode="lines",
            name=term_name.replace("_", " ").title(),
        ))

    fig.update_layout(
        title=f"Membership Functions: {selected_variable}",
        xaxis_title=selected_variable,
        yaxis_title="Membership degree",
        yaxis_range=[0, 1.05],
        template="plotly_white",
        legend_title="Fuzzy categories",
    )
    st.plotly_chart(fig, use_container_width=True)

    st.info(
        "Membership degrees range from 0 to 1. Overlapping functions allow a "
        "value to belong partially to more than one linguistic category."
    )

    st.subheader("Test a sample input")
    with st.form("fuzzy_explorer_form"):
        sample_cost = st.slider("Monthly cost (₹)", 0, 2000, 649, step=25)
        sample_usage = st.slider("Usage days", 0, 30, 12)
        sample_importance = st.slider("Importance", 0.0, 10.0, 8.0, 0.5)
        sample_alternatives = st.slider("Cheaper alternatives", 0.0, 10.0, 7.0, 0.5)
        sample_fee = st.slider("Cancellation fee (₹)", 0, 1000, 0, step=50)
        run_sample = st.form_submit_button("Run fuzzy inference", type="primary")

    if run_sample:
        try:
            sample_result = evaluate_subscription(
                sample_cost, sample_usage, sample_importance,
                sample_alternatives, sample_fee,
            )
            x1, x2 = st.columns(2)
            x1.metric("Retention suitability", f"{sample_result['score']:.2f}/100")
            x2.metric("Recommendation", sample_result["action"])
            st.write(sample_result["explanation"])
        except (ValueError, RuntimeError) as exc:
            st.error(f"Could not calculate fuzzy output: {exc}")


# ============================================================
# 10. Experiment Results
# ============================================================

elif page == "Experiment Results":
    from pathlib import Path

    st.title("Experiment Results")
    st.write(
        "Evaluate both methods on identical, predefined test scenarios. "
        "Agreement with expected actions is a design check, not real-world accuracy."
    )

    test_file = Path(__file__).resolve().parent / "data" / "test_scenarios.csv"
    if not test_file.exists():
        st.error("Test scenarios CSV was not found. Run python generate_dataset.py.")
        st.stop()

    try:
        test_df = pd.read_csv(test_file)
        result_df = run_test_scenarios(test_df)
    except Exception as exc:
        st.error(f"Could not run the experiment: {exc}")
        st.stop()

    valid_results = result_df[
        (result_df["Fuzzy action"] != "Error")
        & (result_df["Baseline action"] != "Error")
    ].copy()

    if valid_results.empty:
        st.error("No scenarios could be evaluated successfully.")
        st.stop()

    total = len(valid_results)
    fuzzy_matches = int(valid_results["Fuzzy matches expectation"].sum())
    baseline_matches = int(valid_results["Baseline matches expectation"].sum())
    method_agreement = (
        valid_results["Fuzzy action"] == valid_results["Baseline action"]
    ).mean() * 100

    c1, c2, c3 = st.columns(3)
    c1.metric(
        "Fuzzy expectation agreement",
        f"{fuzzy_matches}/{total} ({fuzzy_matches / total * 100:.1f}%)",
    )
    c2.metric(
        "Baseline expectation agreement",
        f"{baseline_matches}/{total} ({baseline_matches / total * 100:.1f}%)",
    )
    c3.metric("Agreement between methods", f"{method_agreement:.1f}%")

    st.caption(
        "Expected actions are predefined design expectations. These percentages "
        "do not measure real-world predictive accuracy."
    )

    st.subheader("Scenario-by-scenario results")
    st.dataframe(result_df, use_container_width=True, hide_index=True)

    st.subheader("Recommendation comparison")
    comparison = pd.crosstab(
        valid_results["Fuzzy action"],
        valid_results["Baseline action"],
        rownames=["Fuzzy logic"],
        colnames=["Weighted-score baseline"],
    )
    fig = px.imshow(
        comparison,
        text_auto=True,
        aspect="auto",
        title="Recommendation agreement matrix",
        labels={
            "x": "Weighted-score baseline",
            "y": "Fuzzy logic",
            "color": "Scenario count",
        },
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Retention score comparison")
    score_df = valid_results.melt(
        id_vars="Scenario",
        value_vars=["Fuzzy score", "Baseline score"],
        var_name="Method",
        value_name="Score",
    )
    fig = px.line(
        score_df,
        x="Scenario",
        y="Score",
        color="Method",
        markers=True,
        title="Scores for identical scenarios",
    )
    fig.update_yaxes(range=[0, 100])
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Recommendation counts")
    counts_df = pd.concat([
        valid_results["Fuzzy action"].value_counts().rename("Fuzzy logic"),
        valid_results["Baseline action"].value_counts().rename("Baseline"),
    ], axis=1).fillna(0).astype(int).rename_axis("Action").reset_index()
    counts_long = counts_df.melt(
        id_vars="Action", var_name="Method", value_name="Count"
    )
    fig = px.bar(
        counts_long,
        x="Action",
        y="Count",
        color="Method",
        barmode="group",
        title="Action counts by method",
    )
    st.plotly_chart(fig, use_container_width=True)


# ============================================================
# 11. About the project
# ============================================================

elif page == "About the Project":
    import plotly.graph_objects as go

    st.markdown(
        """
        <style>
        .about-hero {
            padding: 34px;
            border-radius: 18px;
            background: linear-gradient(120deg, #101828, #1D355B);
            color: white;
            margin-bottom: 24px;
        }
        .about-hero h1 {
            color: white;
            font-size: 36px;
            margin: 8px 0 12px 0;
        }
        .about-hero p {
            color: #D0D5DD;
            font-size: 15px;
            line-height: 1.8;
        }
        .about-eyebrow {
            color: #93C5FD;
            text-transform: uppercase;
            letter-spacing: 2px;
            font-size: 11px;
            font-weight: 700;
        }
        .about-step {
            border: 1px solid #D0D5DD;
            border-radius: 13px;
            padding: 17px;
            min-height: 155px;
            background: rgba(128,128,128,0.035);
        }
        .about-step-number {
            color: #3B82F6;
            font-size: 12px;
            font-weight: 800;
            letter-spacing: 1px;
        }
        .about-step h4 {
            margin: 12px 0 7px 0;
            font-size: 16px;
        }
        .about-step p {
            font-size: 13px;
            color: #98A2B3;
            line-height: 1.6;
        }
        .tech-chip {
            display: inline-block;
            padding: 8px 12px;
            margin: 4px 5px 4px 0;
            border: 1px solid #D0D5DD;
            border-radius: 9px;
            font-size: 12px;
            font-weight: 600;
        }
        .about-section-label {
            color: #3B82F6;
            font-size: 11px;
            font-weight: 800;
            letter-spacing: 1.6px;
            text-transform: uppercase;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="about-hero">
            <div class="about-eyebrow">SOFT COMPUTING · PROJECT OVERVIEW</div>
            <h1>Inside SUBSIGHT</h1>
            <p>
                A fuzzy-logic decision-support system that helps users
                evaluate recurring subscriptions, compare decision methods,
                and identify services that may deserve attention.
            </p>
            <p>
                <b>Decision intelligence, not automatic cancellation.</b>
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Overview metrics
    metric_cols = st.columns(4)

    overview = [
        ("01", "Decision engines", "Fuzzy + weighted baseline"),
        ("02", "Inference", "Mamdani"),
        ("03", "Defuzzification", "Centroid"),
        ("04", "Test scenarios", "20 predefined cases"),
    ]

    for col, (number, heading, value) in zip(metric_cols, overview):
        with col:
            with st.container(border=True):
                st.caption(number)
                st.markdown(f"**{heading}**")
                st.markdown(f"### {value}")

    st.divider()

    # Visual workflow
    st.markdown(
        '<div class="about-section-label">01 / System workflow</div>',
        unsafe_allow_html=True,
    )
    st.subheader("From subscription data to a decision")

    workflow = [
        (
            "01",
            "Collect",
            "Cost, billing cycle, usage, importance and alternatives.",
        ),
        (
            "02",
            "Fuzzify",
            "Represent input values using membership functions.",
        ),
        (
            "03",
            "Infer",
            "Apply the configured Mamdani fuzzy rules.",
        ),
        (
            "04",
            "Compare",
            "Evaluate the weighted-score baseline independently.",
        ),
        (
            "05",
            "Recommend",
            "Map scores to Keep, Review, Downgrade or Cancel.",
        ),
    ]

    columns = st.columns(5)

    for col, (number, heading, description) in zip(columns, workflow):
        with col:
            st.markdown(
                f"""
                <div class="about-step">
                    <div class="about-step-number">{number}</div>
                    <h4>{heading}</h4>
                    <p>{description}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.divider()

    # Methodology
    st.markdown(
        '<div class="about-section-label">02 / Decision methodology</div>',
        unsafe_allow_html=True,
    )
    st.subheader("Two methods. One comparison framework.")

    fuzzy_tab, baseline_tab, evaluation_tab = st.tabs(
        ["Fuzzy inference", "Weighted baseline", "Evaluation"]
    )

    with fuzzy_tab:
        left, right = st.columns([1.15, 1])

        with left:
            st.markdown("#### Mamdani fuzzy inference")
            st.write(
                "Fuzzy membership functions represent inputs through "
                "linguistic categories. The configured rules combine these "
                "inputs, and centroid defuzzification produces a numerical "
                "retention-suitability score."
            )

            st.info(
                "The output depends on the actual membership functions, "
                "rule base and action thresholds implemented in the project."
            )

        with right:
            st.markdown("#### Decision pipeline")

            pipeline = go.Figure(
                go.Sankey(
                    arrangement="snap",
                    node=dict(
                        label=[
                            "Input variables",
                            "Membership functions",
                            "Fuzzy rules",
                            "Centroid output",
                            "Recommendation",
                        ],
                        pad=18,
                        thickness=18,
                    ),
                    link=dict(
                        source=[0, 1, 2, 3],
                        target=[1, 2, 3, 4],
                        value=[1, 1, 1, 1],
                    ),
                )
            )

            pipeline.update_layout(
                height=340,
                margin=dict(l=10, r=10, t=20, b=10),
                font_size=11,
            )

            st.plotly_chart(pipeline, use_container_width=True)

    with baseline_tab:
        st.markdown("#### Traditional weighted-score baseline")
        st.write(
            "The baseline combines input factors using predefined weights "
            "to produce a retention score. It provides a comparison against "
            "the fuzzy system on the same scenarios."
        )

        st.warning(
            "The baseline is a comparison method, not ground-truth financial "
            "advice. Its performance depends on the chosen weights."
        )

    with evaluation_tab:
        e1, e2, e3 = st.columns(3)

        e1.metric("Fuzzy expectation agreement", "80%")
        e2.metric("Baseline expectation agreement", "75%")
        e3.metric("Agreement between methods", "85%")

        st.caption(
            "These are the current recorded results for 20 predefined "
            "scenarios. They measure agreement with design expectations "
            "and between methods, not real-world predictive accuracy."
        )

    st.divider()

    # Capabilities and limitations
    st.markdown(
        '<div class="about-section-label">03 / Project capabilities</div>',
        unsafe_allow_html=True,
    )
    st.subheader("What the application provides")

    capability_cols = st.columns(3)

    capabilities = [
        (
            "Subscription analysis",
            "Review recurring costs, billing cycles and usage patterns.",
        ),
        (
            "Scenario simulation",
            "Explore how changing inputs affects both decision methods.",
        ),
        (
            "Savings estimates",
            "Estimate potential savings using explicit assumptions.",
        ),
    ]

    for col, (heading, description) in zip(
        capability_cols, capabilities
    ):
        with col:
            with st.container(border=True):
                st.markdown(f"#### {heading}")
                st.write(description)

    with st.expander("Limitations and assumptions"):
        st.markdown(
            """
            - Sample subscription records are fictional.
            - Membership functions, rules and weights are design choices.
            - Recommendations require human review.
            - Savings estimates depend on billing terms and cancellation fees.
            - Local CSV changes may not persist across cloud redeployments.
            """
        )

    st.divider()

    # Technology stack
    st.markdown(
        '<div class="about-section-label">04 / Technology stack</div>',
        unsafe_allow_html=True,
    )
    st.subheader("Built with Python tools")

    st.markdown(
        """
        <div>
            <span class="tech-chip">Python</span>
            <span class="tech-chip">Streamlit</span>
            <span class="tech-chip">scikit-fuzzy</span>
            <span class="tech-chip">NumPy</span>
            <span class="tech-chip">Pandas</span>
            <span class="tech-chip">Plotly</span>
            <span class="tech-chip">Pytest</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("")
    st.caption(
        "SUBSIGHT · Smart Subscription Decision Advisor · "
        "B.Tech CSE (AI/ML) · Soft Computing"
    )
