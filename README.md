# Personal Finance for Newbies (PFN)

## Table of Contents

- [What is it?](#what-is-it)

- [How can I run it?](#how-can-i-run-it)

- [How can I use my own data?](#how-can-i-use-my-own-data)

- [How can I help?](#how-can-i-help)

## What is it?
**Personal Finance for Newbies** (or **PFN**) is a web app that – from buy/sell financial asset transactions – provides easy-to-use, near-real-time statistics (*i.e.*, updated to the last closing) on your investment portfolio.
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

## How can I run it?

### Streamlit
Install **dependencies** via [poetry](https://python-poetry.org/docs/) with

- `poetry install`

Launch the **web app** via

- `streamlit run ./src/0_🏠_Home.py`

### Docker
To build the app's Docker image

- `docker build -t personal-finance-for-newbies .`

To run the Docker image and expose it on a preferred port (for example 8080)

- `docker run --rm -p 8080:8501 personal-finance-for-newbies`

To run the Docker image using the host's network (which will make the app accessible on port 8501)

- `docker run --rm --network host personal-finance-for-newbies`

Alternatively, on Windows you simply launch

- `scripts/run-web-app.ps1`

### Docker-compose
To build and run the app's Docker image:

- `docker compose up streamlit`

You can choose, by editing the `.env` file in the project root, whether to install dependencies via `poetry` or via `uv` (a library written in RUST that greatly speeds up the installation of python libraries)

## How can I use my own data?
To load and use your data, download and fill in the template with your accumulation plan's buy/sell transactions and upload it. Make sure you fill it in correctly. The fields to be entered are:

- **Exchange**: name of the market (according to Yahoo Finance) [list of exchange suffixes](https://help.yahoo.com/kb/SLN2310.html);
- **Ticker**: symbol to identify a publicly traded security;
- **Transaction Date**: date of transaction in DD/MM/YYYY format;
- **Shares**: number of purchased/sold shares; please, include a minus sign to indicate selling;
- **Price**: price of a single share;
- **Fees**: transaction fees, if any.

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
