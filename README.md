MonteFi

MonteFi is a full-stack web application for simulating future portfolio performance using Monte Carlo methods.

Users can fetch real-time stock prices, construct a weighted portfolio, and run large-scale simulations to evaluate expected returns, portfolio risk, and best- and worst-case outcomes over a chosen time horizon.

The system uses historical daily stock data (≈15–20 years) to estimate the stock  return behavior and correlations. These statistics are used to generate thousands of simulated future market scenarios via a multivariate normal model. 

The frontend, built with React, allows interactive portfolio configuration and visualization of simulation results. The backend, powered by FastAPI, handles data ingestion, validation, pricing APIs, and simulation logic.


Tech Stack

React, FastAPI, Python, NumPy, Pandas, Monte Carlo Simulation, TwelveData API
