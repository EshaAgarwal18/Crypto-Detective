import streamlit as st
import requests
import pandas as pd
import plotly.express as px


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Crypto Detective",
    page_icon="🕵️",
    layout="wide"
)


# =========================================================
# TITLE
# =========================================================

st.title("🕵️ Crypto Detective")

st.markdown(
    "### Investigate cryptocurrency market conditions using live data."
)

st.info(
    "This application uses real market data and simple rule-based "
    "analysis. It does not predict prices or provide financial advice."
)


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.header("🔎 Investigation")

coins = {
    "Bitcoin": "bitcoin",
    "Ethereum": "ethereum",
    "Solana": "solana",
    "XRP": "ripple",
    "Dogecoin": "dogecoin"
}

selected_coin = st.sidebar.selectbox(
    "Choose a cryptocurrency",
    list(coins.keys())
)

coin_id = coins[selected_coin]

days = st.sidebar.selectbox(
    "Price history",
    [7, 14, 30]
)

analyze = st.sidebar.button("🕵️ Investigate")


# =========================================================
# GET CURRENT CRYPTO DATA
# =========================================================

@st.cache_data(ttl=60)
def get_crypto_data(coin_id):

    url = "https://api.coingecko.com/api/v3/coins/markets"

    params = {
        "vs_currency": "usd",
        "ids": coin_id,
        "price_change_percentage": "24h,7d"
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        if response.status_code == 429:

            return {
                "error": "RATE_LIMIT"
            }

        if response.status_code != 200:

            return {
                "error": f"API_ERROR_{response.status_code}"
            }

        data = response.json()

        if not data:

            return {
                "error": "NO_DATA"
            }

        return data[0]

    except requests.exceptions.RequestException as e:

        return {
            "error": str(e)
        }


# =========================================================
# GET HISTORICAL DATA
# =========================================================

@st.cache_data(ttl=300)
def get_history(coin_id, days):

    url = (
        f"https://api.coingecko.com/api/v3/"
        f"coins/{coin_id}/market_chart"
    )

    params = {
        "vs_currency": "usd",
        "days": days
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        if response.status_code == 429:
            return None

        if response.status_code != 200:
            return None

        data = response.json()

        prices = data.get("prices", [])

        if not prices:
            return None

        df = pd.DataFrame(
            prices,
            columns=["timestamp", "price"]
        )

        df["date"] = pd.to_datetime(
            df["timestamp"],
            unit="ms"
        )

        return df

    except:

        return None


# =========================================================
# GET COMPARISON DATA
# =========================================================

@st.cache_data(ttl=60)
def get_comparison_data():

    url = "https://api.coingecko.com/api/v3/coins/markets"

    params = {
        "vs_currency": "usd",
        "ids": ",".join(coins.values()),
        "price_change_percentage": "24h,7d"
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        if response.status_code != 200:
            return None

        data = response.json()

        if not data:
            return None

        rows = []

        name_lookup = {
            value: key
            for key, value in coins.items()
        }

        for coin in data:

            rows.append({
                "Crypto": name_lookup.get(
                    coin.get("id"),
                    coin.get("name")
                ),

                "Price": coin.get(
                    "current_price",
                    0
                ),

                "24H Change (%)": coin.get(
                    "price_change_percentage_24h",
                    0
                ),

                "7D Change (%)": coin.get(
                    "price_change_percentage_7d_in_currency",
                    0
                ),

                "Market Cap ($B)": (
                    coin.get("market_cap", 0) /
                    1_000_000_000
                ),

                "Volume ($B)": (
                    coin.get("total_volume", 0) /
                    1_000_000_000
                )
            })

        return pd.DataFrame(rows)

    except:

        return None


# =========================================================
# GET DATA WHEN BUTTON IS PRESSED
# =========================================================

if analyze:

    with st.spinner("🔍 Investigating the market..."):

        coin = get_crypto_data(
            coin_id
        )

    if isinstance(coin, dict) and "error" in coin:

        if coin["error"] == "RATE_LIMIT":

            st.error(
                "⚠️ CoinGecko API rate limit reached. "
                "Please wait 30–60 seconds and try again."
            )

        else:

            st.error(
                f"Unable to get cryptocurrency data: "
                f"{coin['error']}"
            )

        st.stop()

else:

    st.info(
        "👈 Select a cryptocurrency and click **Investigate**."
    )

    st.stop()


# =========================================================
# EXTRACT DATA
# =========================================================

price = coin.get(
    "current_price",
    0
)

change_24h = coin.get(
    "price_change_percentage_24h",
    0
) or 0

change_7d = coin.get(
    "price_change_percentage_7d_in_currency",
    0
) or 0

market_cap = coin.get(
    "market_cap",
    0
)

volume = coin.get(
    "total_volume",
    0
)


# =========================================================
# MAIN PRICE DISPLAY
# =========================================================

st.subheader(
    f"💰 {selected_coin}"
)

col1, col2, col3, col4 = st.columns(4)

with col1:

    st.metric(
        "Current Price",
        f"${price:,.2f}"
    )

with col2:

    st.metric(
        "24H Change",
        f"{change_24h:.2f}%"
    )

with col3:

    st.metric(
        "7D Change",
        f"{change_7d:.2f}%"
    )

with col4:

    st.metric(
        "24H Volume",
        f"${volume / 1_000_000_000:.2f}B"
    )


# =========================================================
# PRICE HISTORY
# =========================================================

st.divider()

with st.spinner(
    "Loading price history..."
):

    history = get_history(
        coin_id,
        days
    )


# =========================================================
# PRICE CHART
# =========================================================

st.subheader(
    f"📈 {selected_coin} Price History"
)

if history is not None:

    fig = px.line(
        history,
        x="date",
        y="price",
        title=(
            f"{selected_coin} — "
            f"Last {days} Days"
        ),
        labels={
            "date": "Date",
            "price": "Price (USD)"
        }
    )

    fig.update_layout(
        hovermode="x unified"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

else:

    st.warning(
        "Unable to load historical price data."
    )


# =========================================================
# CRYPTO COMPARISON
# =========================================================

st.divider()

st.subheader(
    "⚖️ Crypto Comparison"
)

st.caption(
    "Compare the major cryptocurrencies using current market data."
)

with st.spinner(
    "Loading cryptocurrency comparison..."
):

    comparison_df = get_comparison_data()


if comparison_df is not None:

    st.dataframe(
        comparison_df.style.format(
            {
                "Price": "${:,.2f}",
                "24H Change (%)": "{:+.2f}%",
                "7D Change (%)": "{:+.2f}%",
                "Market Cap ($B)": "${:,.2f}B",
                "Volume ($B)": "${:,.2f}B"
            }
        ),
        use_container_width=True,
        hide_index=True
    )


    # =====================================================
    # BEST / WORST 24H PERFORMER
    # =====================================================

    best_coin = comparison_df.loc[
        comparison_df["24H Change (%)"].idxmax()
    ]

    worst_coin = comparison_df.loc[
        comparison_df["24H Change (%)"].idxmin()
    ]

    comp1, comp2, comp3 = st.columns(3)

    with comp1:

        st.metric(
            "Selected Crypto",
            selected_coin
        )

    with comp2:

        st.metric(
            "Best 24H Performer",
            best_coin["Crypto"],
            f"{best_coin['24H Change (%)']:+.2f}%"
        )

    with comp3:

        st.metric(
            "Worst 24H Performer",
            worst_coin["Crypto"],
            f"{worst_coin['24H Change (%)']:+.2f}%"
        )


    # =====================================================
    # PERFORMANCE CHART
    # =====================================================

    st.write(
        "### 📊 24H Performance Comparison"
    )

    comparison_chart = px.bar(
        comparison_df,
        x="Crypto",
        y="24H Change (%)",
        title="24H Cryptocurrency Performance",
        labels={
            "24H Change (%)": "24H Change (%)"
        }
    )

    comparison_chart.add_hline(
        y=0,
        line_width=1
    )

    st.plotly_chart(
        comparison_chart,
        use_container_width=True
    )

else:

    st.warning(
        "Unable to load comparison data right now."
    )


# =========================================================
# MARKET MOOD
# =========================================================

st.divider()

st.subheader(
    "📊 Market Mood"
)

if change_24h >= 3:

    market_mood = "🟢 BULLISH"

elif change_24h <= -3:

    market_mood = "🔴 BEARISH"

else:

    market_mood = "🟡 NEUTRAL"


mood_col1, mood_col2 = st.columns(2)

with mood_col1:

    st.metric(
        "Market Mood",
        market_mood
    )

with mood_col2:

    st.metric(
        "24H Movement",
        f"{change_24h:+.2f}%"
    )


# =========================================================
# MARKET INTERPRETATION
# =========================================================

if market_mood == "🟢 BULLISH":

    st.success(
        """
        🟢 **BULLISH MARKET**

        The cryptocurrency has increased by at least 3%
        in the last 24 hours.

        The current market movement shows positive momentum.
        """
    )

elif market_mood == "🔴 BEARISH":

    st.error(
        """
        🔴 **BEARISH MARKET**

        The cryptocurrency has decreased by at least 3%
        in the last 24 hours.

        The current market movement shows negative momentum.
        """
    )

else:

    st.info(
        """
        🟡 **NEUTRAL MARKET**

        The cryptocurrency has moved less than 3%
        in either direction during the last 24 hours.

        There is no strong market movement at the moment.
        """
    )


# =========================================================
# DETECTIVE VERDICT
# =========================================================

st.divider()

st.subheader(
    "🕵️ Detective Verdict"
)


if market_mood == "🔴 BEARISH":

    st.warning(
        f"""
        ### ⚠️ NEGATIVE SIGNAL

        **{selected_coin}** is showing a bearish movement.

        **24H Movement:** {change_24h:+.2f}%

        **Market Mood:** {market_mood}

        🕵️ The market data currently shows weakness.
        """
    )


elif market_mood == "🟢 BULLISH":

    st.success(
        f"""
        ### 🟢 POSITIVE SIGNAL

        **{selected_coin}** is showing a bullish movement.

        **24H Movement:** {change_24h:+.2f}%

        **Market Mood:** {market_mood}

        🕵️ The market data currently shows positive momentum.
        """
    )


else:

    st.info(
        f"""
        ### 🟡 MIXED / NEUTRAL SIGNAL

        **{selected_coin}** does not currently show
        a strong market movement.

        **24H Movement:** {change_24h:+.2f}%

        **Market Mood:** {market_mood}

        🕵️ The market movement is relatively stable.
        """
    )


# =========================================================
# MARKET INFORMATION
# =========================================================

st.divider()

st.subheader(
    "📊 Market Information"
)

info1, info2 = st.columns(2)

with info1:

    st.write(
        f"**Market Capitalization:** "
        f"${market_cap / 1_000_000_000:.2f}B"
    )

with info2:

    if market_cap > 0:

        volume_ratio = volume / market_cap

        st.write(
            f"**Volume / Market Cap:** "
            f"{volume_ratio:.2%}"
        )

    else:

        st.write(
            "**Volume / Market Cap:** N/A"
        )


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "🕵️ Crypto Detective | Educational Project | "
    "Not Financial Advice"
)