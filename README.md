# Personal Finance for Newbies (PFN)

## Table of Contents

- [What is it?](#what-is-it)

- [Key features](#key-features)

- [How can I run it?](#how-can-i-run-it)

- [How can I help?](#how-can-i-help)

## What is it?
**Personal Finance for Newbies** (or **PFN**) is aweb application designed to provide near-real-time analytics and insights into your investment portfolio. By centralising your transaction history, PFN eliminates messy spreadsheets and provides a high-fidelity view of your wealth evolution.
<br><br>
PFN allows you to analyse your portfolio from **multiple perspectives**: from **higher-level metrics** (profit & loss, asset class weights) to those allowing you to study **risk** and **returns** in depth, especially over time. To use the app, you don't need to create an account! You just need to set up your buy/sell transactions: PFN takes care of downloading historical prices from [Yahoo Finance](https://finance.yahoo.com/) and analysing them for you!
<br><br>
<center><sub><sup>
We do not collect or store any data. We provide no guarantee, explicit or implicit, as to the accuracy of the results displayed, which are intended for educational and informational purposes only.
</sup></sub></center>
<br>

| ![PFN at play amidst a vivid dawn](images/cover_2.jpeg) | 
|:--:| 
| *Generated image of PFN at play amidst a vivid dawn* |

## Key Features

- Cloud-Native Persistence: Powered by **MongoDB Atlas** for secure and scalable storage of transactions and asset registries.

- Automated Market Data: Seamless integration with **Yahoo Finance** to fetch the latest closing prices automatically.

- Multi-Dimensional Analytics:

    - Asset Allocation & PnL.

    - Return Analysis: Explore correlations and return distributions.

    - Risk Management: Monitor drawdowns and calculate Relative Risk Contributions.

- Data Integrity: Built with **Pydantic** models to enforce data validation and consistency.

## How can I run it?

### Docker (Recommended)

The easiest way to run PFN is via Docker.

1. Clone the repository
    
    ```bash
    git clone https://github.com/viventriglia/personal-finance-for-newbies.git
    cd personal-finance-for-newbies
    ```

2. Configure your environment
    
    Create a `.env` file in the root directory:
    ```bash
    STREAMLIT_MONGO__URI="your_mongodb_atlas_uri"
    ```

3. Launch the app
    
    ```bash
    docker compose up --build
    ```

    Access the dashboard at `http://localhost:8501`.

### Local Development

If you prefer running without Docker:

- Ensure you have [poetry](https://python-poetry.org/docs/) installed.

- After cloning the repository, run `poetry install`.

- Launch the app with `streamlit run src/0_🏠_Home.py`.


<!-- The fields to be entered are:

- **Exchange**: name of the market (according to Yahoo Finance) [list of exchange suffixes](https://help.yahoo.com/kb/SLN2310.html);
- **Ticker**: symbol to identify a publicly traded security;
- **Transaction Date**: date of transaction in DD/MM/YYYY format;
- **Shares**: number of purchased/sold shares; please, include a minus sign to indicate selling;
- **Price**: price of a single share;
- **Fees**: transaction fees, if any. -->

## How can I help?

Contributions are what make the open source community an amazing place to learn, inspire, and create. Any contribution you make is **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature_amazing_feature`)
3. Commit your Changes (`git commit -m 'Add some amazing stuff'`)
4. Push to the Branch (`git push origin feature_amazing_feature`)
5. Open a Pull Request

Here's an hopefully up-to-date **list of things to build**:
- Improve Sharpe Ratio calculation, to take into account a time-varying:
    - risk-free rate
    - asset allocation
- Rolling Sharpe ratio chart
- Sortino and Calmar ratios
