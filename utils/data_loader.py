from pathlib import Path

import pandas as pd
import streamlit as st

DATA_DIR = Path(__file__).resolve().parent.parent


@st.cache_data
def load_all_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    sales = pd.read_csv(DATA_DIR / "sales_data.csv")
    customers = pd.read_csv(DATA_DIR / "customer_data.csv")
    activities = pd.read_csv(DATA_DIR / "activity_data.csv")

    sales["수주일"] = pd.to_datetime(sales["수주일"])
    sales["납품일"] = pd.to_datetime(sales["납품일"])
    for col in ["수주금액", "매출금액", "미수금"]:
        sales[col] = pd.to_numeric(sales[col], errors="coerce").fillna(0)

    customers["첫거래일"] = pd.to_datetime(customers["첫거래일"])
    customers["누적매출"] = pd.to_numeric(customers["누적매출"], errors="coerce").fillna(0)

    activities["활동일"] = pd.to_datetime(activities["활동일"])

    return sales, customers, activities


def get_filter_options(
    sales: pd.DataFrame,
    customers: pd.DataFrame,
    activities: pd.DataFrame,
) -> dict:
    years = sorted(sales["수주일"].dt.year.dropna().unique().tolist())
    quarters = sorted(sales["분기"].dropna().unique().tolist())
    regions = sorted(
        set(sales["지역"].dropna().unique())
        | set(customers["지역"].dropna().unique())
    )
    customer_types = sorted(
        set(sales["거래처유형"].dropna().unique())
        | set(customers["거래처유형"].dropna().unique())
    )
    sales_reps = sorted(
        set(sales["담당영업"].dropna().unique())
        | set(activities["담당영업"].dropna().unique())
    )
    order_statuses = sorted(sales["수주상태"].dropna().unique().tolist())

    return {
        "years": years,
        "quarters": quarters,
        "regions": regions,
        "customer_types": customer_types,
        "sales_reps": sales_reps,
        "order_statuses": order_statuses,
    }


def filter_sales(
    sales: pd.DataFrame,
    years: list | None = None,
    quarters: list | None = None,
    regions: list | None = None,
    customer_types: list | None = None,
    sales_reps: list | None = None,
    order_statuses: list | None = None,
) -> pd.DataFrame:
    df = sales.copy()
    if years:
        df = df[df["수주일"].dt.year.isin(years)]
    if quarters:
        df = df[df["분기"].isin(quarters)]
    if regions:
        df = df[df["지역"].isin(regions)]
    if customer_types:
        df = df[df["거래처유형"].isin(customer_types)]
    if sales_reps:
        df = df[df["담당영업"].isin(sales_reps)]
    if order_statuses:
        df = df[df["수주상태"].isin(order_statuses)]
    return df


def filter_customers(
    customers: pd.DataFrame,
    regions: list | None = None,
    customer_types: list | None = None,
) -> pd.DataFrame:
    df = customers.copy()
    if regions:
        df = df[df["지역"].isin(regions)]
    if customer_types:
        df = df[df["거래처유형"].isin(customer_types)]
    return df


def filter_activities(
    activities: pd.DataFrame,
    years: list | None = None,
    sales_reps: list | None = None,
) -> pd.DataFrame:
    df = activities.copy()
    if years:
        df = df[df["활동일"].dt.year.isin(years)]
    if sales_reps:
        df = df[df["담당영업"].isin(sales_reps)]
    return df


def format_currency(value: float) -> str:
    return f"₩{value:,.0f}"


def format_percent(value: float) -> str:
    return f"{value:.1f}%"
