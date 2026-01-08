# 🌍 MigraSend – Low-Cost Remittance on XRPL

**NUS FinTech Summit 2026 – Ripple Challenge + BGA Bounty**


## Problem Statement
Migrant workers in Southeast Asia send billions home every year, but traditional services charge **6–10% fees** and take **days** to deliver. This hurts families who depend on every dollar.

## Solution
**MigraSend** is a trustless remittance prototype that uses the XRP Ledger (XRPL) to deliver money **instantly** with **near-zero fees**.

Key innovations:
- **XRP escrow** as collateral — proves sender intent and adds conditional security
- **Issued currency** simulating a USD stablecoin (RLUSD-like) — stable value transfer
- **Full transparency** — every step visible on the public XRPL Testnet explorer

Real-world impact: Cuts remittance costs from ~7% to almost nothing while providing trust and speed.

## Features
- One-click trust line setup for the receiver
- Time-locked XRP escrow (collateral) for safety
- Automatic USD token transfer after successful claim
- Live balance display (XRP + USD)
- Direct links to XRPL Testnet explorer for every transaction
- Clean, intuitive Streamlit interface with separate Sender/Receiver views

## Tech Stack
- **Backend**: Python + `xrpl-py` library
- **Frontend**: Streamlit (responsive web app)
- **Blockchain**: XRP Ledger Testnet
- **Features used**: EscrowCreate/EscrowFinish, TrustSet, Payment (issued currency), AccountLines, AccountInfo

## How to Run Locally
```bash
# Clone the repo
git clone https://github.com/YOUR-USERNAME/migrasend-mvp.git
cd migrasend-mvp

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
