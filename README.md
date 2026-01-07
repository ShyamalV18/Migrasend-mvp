# MigraSend – Instant Low-Cost Remittances on XRPL

**NUS FinTech Summit 2026 – Ripple Challenge + BGA Bounty**

## Problem
Migrant workers in Southeast Asia pay 6–10% fees and wait days to send money home.

## Solution
A trustless remittance app using:
- **XRP escrow** as collateral (conditional release)
- **Issued currency** simulating RLUSD stablecoin
- Instant, near-zero fee transfers on XRPL

## Features
- One-click trust line setup
- Time-locked XRP escrow for safety
- Automatic USD transfer after claim
- Full transaction transparency via XRPL explorer

## Tech
- Python + xrpl-py
- Streamlit frontend
- XRPL Testnet

## How to Run
```bash
pip install -r requirements.txt
streamlit run app.py
