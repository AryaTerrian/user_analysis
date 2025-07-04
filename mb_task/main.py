"""
This script includes:
1) Computes average customer-lifetime value (mean `total_deposit`)
2) Flags churned users (no login in the last 30 days)
3) Splits customers into quartiles by `total_games_played`
   and reports average deposit per quartile
"""

from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd

brand_palette   = ["#FF2E9E", "#FDA549", "#8DC63F", "#22A9E1"]
BRAND_PINK = "#FF2E9E"


def read_data_and_prepare(file_path: Path) -> pd.DataFrame:
    """read file into dataframe and prepare for calculations"""
    df = pd.read_excel(
        file_path,
    )
    df['date_joined'] = pd.to_datetime(df['date_joined'])
    df['last_login_date']= pd.to_datetime(df['last_login_date'])
    df['cust_lifetime_days'] =  (df['last_login_date'] - df['date_joined']).dt.days
    df['cust_lifetime_months'] = df['cust_lifetime_days'] / 30
    df['monthly_revenue'] = df['total_deposit'] / df['cust_lifetime_months']
    return df


def calculate_avg_clv(df: pd.DataFrame) -> int:
    """Average CLV = Avg Monthly Revenue per Customer×Avg Customer Lifetime"""
    return (df['monthly_revenue'] * df['cust_lifetime_months']).mean()


def identify_churn_users(df: pd.DataFrame, cutoff_days: int) -> pd.DataFrame:
    cutoff_date = pd.Timestamp.today() - pd.Timedelta(days=cutoff_days)
    df['churned'] = df['last_login_date'] < cutoff_date
    return df


def user_segmentation(df: pd.DataFrame) -> pd.DataFrame:
    """ Segment users into quartiles by games played"""
    df['games_played_quartile'] = pd.qcut(df['total_games_played'],
                                          q=4,
                                          labels=['Q1', 'Q2', 'Q3', 'Q4'])

    return df.groupby("games_played_quartile")["total_deposit"].mean().reset_index()


def plot_join_date_distribution(df: pd.DataFrame, bins: int = 6) -> None:
    """One-off histogram of when players joined."""
    plt.figure()
    plt.hist(df["date_joined"], bins=bins, color=BRAND_PINK)
    plt.gcf().autofmt_xdate()
    plt.xlabel("Date joined")
    plt.ylabel("Number of players")
    plt.title("Player sign-ups over time")
    plt.tight_layout()
    plt.show()


def plot_quartile_deposits(quartile_summary: pd.DataFrame):
    plt.figure(figsize=(8, 5))
    plt.bar(
        quartile_summary["games_played_quartile"],
        quartile_summary["total_deposit"],
        color=brand_palette
    )
    plt.title("Engagement vs. Spend")
    plt.xlabel("Games Played Quartile")
    plt.ylabel("Average Total Deposit (£)")

    plt.tight_layout()
    plt.show()



def summarise_fields(df: pd.DataFrame) -> pd.DataFrame:
    """
    Thin wrapper around df.describe() that tidies the output.
    """
    summary = df.describe(include="all").T
    # Drop unwieldy scientific format for easier reading
    return summary.round(2)


def present(avg_clv, num_churned, churn_rate, df: pd.DataFrame):
    print("------------------------------------------------------------")
    print(f"Average CLV (mean total deposit): £{avg_clv:,.2f}")
    print(
        f"Churned users (>30 days inactive): "
        f"{num_churned} of {len(df)} ({churn_rate:.1%})"
    )



def main():
    file_path = Path(r"C:\Users\AryaZhao\Downloads\match_bingo_user_data_sample.xlsx")
    df = read_data_and_prepare(file_path)
    avg_clv = calculate_avg_clv(df)
    df = identify_churn_users(df, cutoff_days=30)
    num_churned = df["churned"].sum()
    churn_rate = num_churned / len(df)
    df_avg_deposit_by_segment = user_segmentation(df)

    plot_join_date_distribution(df)
    plot_quartile_deposits(df_avg_deposit_by_segment)
    print(summarise_fields(df).to_markdown())
    present(avg_clv, num_churned, churn_rate, df)

if __name__ == "__main__":
    main()