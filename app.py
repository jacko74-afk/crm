import pandas as pd
import plotly.express as px
import streamlit as st

from utils.data_loader import (
    filter_activities,
    filter_customers,
    filter_sales,
    format_currency,
    format_percent,
    get_filter_options,
    load_all_data,
)

st.set_page_config(page_title="영업 대시보드", page_icon="📊", layout="wide")

st.title("📊 영업 대시보드")
st.caption("매출 · 거래처 · 영업활동 통합 분석")

sales_raw, customers_raw, activities_raw = load_all_data()
options = get_filter_options(sales_raw, customers_raw, activities_raw)

with st.sidebar:
    st.header("필터")
    selected_years = st.multiselect("연도", options["years"], default=options["years"])
    selected_quarters = st.multiselect("분기", options["quarters"], default=options["quarters"])
    selected_regions = st.multiselect("지역", options["regions"], default=options["regions"])
    selected_types = st.multiselect(
        "거래처유형", options["customer_types"], default=options["customer_types"]
    )
    selected_reps = st.multiselect(
        "담당영업", options["sales_reps"], default=options["sales_reps"]
    )
    selected_statuses = st.multiselect(
        "수주상태", options["order_statuses"], default=options["order_statuses"]
    )

sales = filter_sales(
    sales_raw,
    years=selected_years or None,
    quarters=selected_quarters or None,
    regions=selected_regions or None,
    customer_types=selected_types or None,
    sales_reps=selected_reps or None,
    order_statuses=selected_statuses or None,
)
customers = filter_customers(
    customers_raw,
    regions=selected_regions or None,
    customer_types=selected_types or None,
)
activities = filter_activities(
    activities_raw,
    years=selected_years or None,
    sales_reps=selected_reps or None,
)

tab_overview, tab_sales, tab_customers, tab_activities, tab_raw = st.tabs(
    ["종합 개요", "매출 분석", "거래처 분석", "영업 활동", "데이터 탐색"]
)


def render_kpi_row(metrics: list[tuple[str, str]]) -> None:
    cols = st.columns(len(metrics))
    for col, (label, value) in zip(cols, metrics):
        col.metric(label, value)


with tab_overview:
    st.subheader("종합 개요")

    total_revenue = sales["매출금액"].sum()
    total_orders = sales["수주금액"].sum()
    total_receivable = sales["미수금"].sum()
    txn_count = len(sales)
    completion_rate = (
        (sales["수주상태"] == "완료").sum() / txn_count * 100 if txn_count else 0
    )
    customer_count = len(customers)
    activity_count = len(activities)
    positive_rate = (
        (activities["활동결과"] == "긍정").sum() / activity_count * 100
        if activity_count
        else 0
    )

    render_kpi_row(
        [
            ("총 매출금액", format_currency(total_revenue)),
            ("총 수주금액", format_currency(total_orders)),
            ("미수금 합계", format_currency(total_receivable)),
            ("거래 건수", f"{txn_count:,}건"),
            ("완료율", format_percent(completion_rate)),
            ("거래처 수", f"{customer_count:,}곳"),
            ("영업활동", f"{activity_count:,}건"),
            ("긍정 활동 비율", format_percent(positive_rate)),
        ]
    )

    st.divider()
    col1, col2, col3 = st.columns(3)

    with col1:
        quarter_sales = (
            sales.groupby("분기", as_index=False)["매출금액"]
            .sum()
            .sort_values("분기")
        )
        fig = px.bar(
            quarter_sales,
            x="분기",
            y="매출금액",
            title="분기별 매출 추이",
            labels={"분기": "분기", "매출금액": "매출금액"},
            text_auto=",.0f",
        )
        fig.update_layout(yaxis_tickformat=",.0f")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        region_sales = (
            sales.groupby("지역", as_index=False)["매출금액"]
            .sum()
            .sort_values("매출금액", ascending=True)
        )
        fig = px.bar(
            region_sales,
            x="매출금액",
            y="지역",
            orientation="h",
            title="지역별 매출",
            labels={"지역": "지역", "매출금액": "매출금액"},
            text_auto=",.0f",
        )
        fig.update_layout(xaxis_tickformat=",.0f")
        st.plotly_chart(fig, use_container_width=True)

    with col3:
        status_counts = sales["수주상태"].value_counts().reset_index()
        status_counts.columns = ["수주상태", "건수"]
        fig = px.pie(
            status_counts,
            names="수주상태",
            values="건수",
            title="수주상태 분포",
            hole=0.4,
        )
        st.plotly_chart(fig, use_container_width=True)


with tab_sales:
    st.subheader("매출 분석")

    col1, col2 = st.columns(2)

    with col1:
        product_sales = (
            sales.groupby("제품군", as_index=False)
            .agg(매출금액=("매출금액", "sum"), 건수=("거래ID", "count"))
            .sort_values("매출금액", ascending=False)
        )
        fig = px.bar(
            product_sales,
            x="제품군",
            y="매출금액",
            title="제품군별 매출",
            labels={"제품군": "제품군", "매출금액": "매출금액"},
            text_auto=",.0f",
        )
        fig.update_layout(yaxis_tickformat=",.0f")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        rep_sales = (
            sales.groupby("담당영업", as_index=False)
            .agg(매출금액=("매출금액", "sum"), 건수=("거래ID", "count"))
            .sort_values("매출금액", ascending=False)
        )
        fig = px.bar(
            rep_sales,
            x="담당영업",
            y="매출금액",
            title="담당영업별 실적",
            labels={"담당영업": "담당영업", "매출금액": "매출금액"},
            text_auto=",.0f",
        )
        fig.update_layout(yaxis_tickformat=",.0f")
        st.plotly_chart(fig, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        type_sales = (
            sales.groupby("거래처유형", as_index=False)["매출금액"]
            .sum()
            .sort_values("매출금액", ascending=False)
        )
        fig = px.bar(
            type_sales,
            x="거래처유형",
            y="매출금액",
            title="거래처유형별 매출",
            labels={"거래처유형": "거래처유형", "매출금액": "매출금액"},
            text_auto=",.0f",
        )
        fig.update_layout(yaxis_tickformat=",.0f")
        st.plotly_chart(fig, use_container_width=True)

    with col4:
        receivable_top = (
            sales[sales["미수금"] > 0]
            .sort_values("미수금", ascending=False)
            .head(10)[["거래처명", "거래ID", "미수금", "수주상태"]]
        )
        st.markdown("**미수금 Top 10**")
        if receivable_top.empty:
            st.info("미수금이 있는 거래가 없습니다.")
        else:
            display = receivable_top.copy()
            display["미수금"] = display["미수금"].apply(format_currency)
            st.dataframe(display, use_container_width=True, hide_index=True)

    st.markdown("**상세 거래 목록**")
    sales_display = sales.copy()
    sales_display["수주일"] = sales_display["수주일"].dt.strftime("%Y-%m-%d")
    sales_display["납품일"] = sales_display["납품일"].dt.strftime("%Y-%m-%d")
    st.dataframe(sales_display, use_container_width=True, hide_index=True)


with tab_customers:
    st.subheader("거래처 분석")

    col1, col2 = st.columns(2)

    with col1:
        grade_counts = customers["등급"].value_counts().reset_index()
        grade_counts.columns = ["등급", "건수"]
        fig = px.pie(
            grade_counts,
            names="등급",
            values="건수",
            title="거래처 등급 분포",
            hole=0.4,
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        type_revenue = (
            customers.groupby("거래처유형", as_index=False)["누적매출"]
            .sum()
            .sort_values("누적매출", ascending=False)
        )
        fig = px.bar(
            type_revenue,
            x="거래처유형",
            y="누적매출",
            title="거래처유형별 누적매출",
            labels={"거래처유형": "거래처유형", "누적매출": "누적매출"},
            text_auto=",.0f",
        )
        fig.update_layout(yaxis_tickformat=",.0f")
        st.plotly_chart(fig, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        region_revenue = (
            customers.groupby("지역", as_index=False)["누적매출"]
            .sum()
            .sort_values("누적매출", ascending=True)
        )
        fig = px.bar(
            region_revenue,
            x="누적매출",
            y="지역",
            orientation="h",
            title="지역별 누적매출",
            labels={"지역": "지역", "누적매출": "누적매출"},
            text_auto=",.0f",
        )
        fig.update_layout(xaxis_tickformat=",.0f")
        st.plotly_chart(fig, use_container_width=True)

    with col4:
        top_customers = (
            customers.sort_values("누적매출", ascending=False)
            .head(10)[["거래처명", "거래처유형", "등급", "지역", "누적매출"]]
        )
        st.markdown("**누적매출 Top 10**")
        display = top_customers.copy()
        display["누적매출"] = display["누적매출"].apply(format_currency)
        st.dataframe(display, use_container_width=True, hide_index=True)

    st.markdown("**연도별 신규 거래처 유입**")
    new_customers = customers.copy()
    new_customers["유입연도"] = new_customers["첫거래일"].dt.year
    yearly_new = (
        new_customers.groupby("유입연도", as_index=False)
        .size()
        .rename(columns={"size": "거래처수"})
        .sort_values("유입연도")
    )
    fig = px.line(
        yearly_new,
        x="유입연도",
        y="거래처수",
        markers=True,
        title="첫거래일 기준 연도별 신규 거래처",
        labels={"유입연도": "연도", "거래처수": "거래처 수"},
    )
    st.plotly_chart(fig, use_container_width=True)


with tab_activities:
    st.subheader("영업 활동")

    col1, col2 = st.columns(2)

    with col1:
        type_counts = activities["활동유형"].value_counts().reset_index()
        type_counts.columns = ["활동유형", "건수"]
        fig = px.bar(
            type_counts,
            x="활동유형",
            y="건수",
            title="활동유형별 건수",
            labels={"활동유형": "활동유형", "건수": "건수"},
            text_auto=True,
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        result_counts = activities["활동결과"].value_counts().reset_index()
        result_counts.columns = ["활동결과", "건수"]
        fig = px.pie(
            result_counts,
            names="활동결과",
            values="건수",
            title="활동결과 비율",
            hole=0.4,
        )
        st.plotly_chart(fig, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        rep_stats = (
            activities.groupby("담당영업", as_index=False)
            .agg(
                활동건수=("활동ID", "count"),
                긍정건수=("활동결과", lambda s: (s == "긍정").sum()),
            )
        )
        rep_stats["긍정률"] = (
            rep_stats["긍정건수"] / rep_stats["활동건수"] * 100
        ).round(1)
        fig = px.bar(
            rep_stats.sort_values("활동건수", ascending=False),
            x="담당영업",
            y="활동건수",
            title="담당영업별 활동 건수",
            labels={"담당영업": "담당영업", "활동건수": "활동 건수"},
            text_auto=True,
        )
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(
            rep_stats.sort_values("긍정률", ascending=False),
            use_container_width=True,
            hide_index=True,
        )

    with col4:
        monthly = activities.copy()
        monthly["월"] = monthly["활동일"].dt.to_period("M").astype(str)
        monthly_counts = (
            monthly.groupby("월", as_index=False)
            .size()
            .rename(columns={"size": "건수"})
            .sort_values("월")
        )
        fig = px.line(
            monthly_counts,
            x="월",
            y="건수",
            markers=True,
            title="월별 활동 추이",
            labels={"월": "월", "건수": "활동 건수"},
        )
        fig.update_xaxes(tickangle=45)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("**상세 활동 목록**")
    activity_display = activities.copy()
    activity_display["활동일"] = activity_display["활동일"].dt.strftime("%Y-%m-%d")
    st.dataframe(activity_display, use_container_width=True, hide_index=True)


with tab_raw:
    st.subheader("데이터 탐색")

    raw_tab1, raw_tab2, raw_tab3 = st.tabs(["매출 데이터", "거래처 데이터", "활동 데이터"])

    def download_button(df: pd.DataFrame, label: str, filename: str) -> None:
        csv = df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(label=label, data=csv, file_name=filename, mime="text/csv")

    with raw_tab1:
        st.caption(f"필터 적용 결과: {len(sales):,}건")
        download_button(sales, "매출 CSV 다운로드", "sales_filtered.csv")
        st.dataframe(sales, use_container_width=True, hide_index=True)

    with raw_tab2:
        st.caption(f"필터 적용 결과: {len(customers):,}건")
        download_button(customers, "거래처 CSV 다운로드", "customers_filtered.csv")
        st.dataframe(customers, use_container_width=True, hide_index=True)

    with raw_tab3:
        st.caption(f"필터 적용 결과: {len(activities):,}건")
        download_button(activities, "활동 CSV 다운로드", "activities_filtered.csv")
        st.dataframe(activities, use_container_width=True, hide_index=True)
