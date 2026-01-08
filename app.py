import streamlit as st
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.models.transactions import EscrowCreate, EscrowFinish, TrustSet, Payment
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.transaction import submit_and_wait, autofill
from xrpl.utils import datetime_to_ripple_time
from datetime import datetime, timedelta
from xrpl.models.requests import AccountInfo, AccountLines

# === CONFIG ===
client = JsonRpcClient("https://s.altnet.rippletest.net:51234/")

SENDER_SEED = "sEdTtf2p1yjodpvYqhUvnCiTGQa4a4o"
RECEIVER_SEED = "sEd7j5Lbj7jyZqotFBz8Cj7RBPMyfMS"

sender_wallet = Wallet.from_seed(SENDER_SEED)
receiver_wallet = Wallet.from_seed(RECEIVER_SEED)

CURRENCY_CODE = "USD"
ISSUER = sender_wallet.classic_address

# Session state init
if "usd_amount" not in st.session_state:
    st.session_state["usd_amount"] = 50.0
if "escrow_seq" not in st.session_state:
    st.session_state["escrow_seq"] = 0

# === HELPERS ===
def receiver_has_usd_trustline():
    try:
        lines = client.request(AccountLines(account=receiver_wallet.classic_address)).result.get("lines", [])
        for line in lines:
            if line["currency"] == CURRENCY_CODE and line["account"] == ISSUER:
                return True
    except:
        return False
    return False

# === SETUP ===
def enable_usd_wallet():
    try:
        trust = TrustSet(
            account=receiver_wallet.classic_address,
            limit_amount=IssuedCurrencyAmount(currency=CURRENCY_CODE, issuer=ISSUER, value="10000")
        )
        filled = autofill(trust, client)
        response = submit_and_wait(filled, client, receiver_wallet)
        hash_tx = response.result["hash"]
        st.success("Receiver USD wallet enabled!")
        st.markdown(f"[View TrustSet on Explorer](https://testnet.xrpl.org/transactions/{hash_tx})")
    except Exception as e:
        st.error(f"Failed: {str(e)}")

# === ESCROW ===
def create_xrp_escrow():
    try:
        info = client.request(AccountInfo(account=sender_wallet.classic_address, ledger_index="validated"))
        seq = info.result["account_data"]["Sequence"]

        finish_after = datetime.now() + timedelta(seconds=30)  # Longer for reliable demo

        escrow = EscrowCreate(
            account=sender_wallet.classic_address,
            destination=receiver_wallet.classic_address,
            amount="1000000",  # 1 XRP
            finish_after=datetime_to_ripple_time(finish_after)
        )

        filled = autofill(escrow, client)
        response = submit_and_wait(filled, client, sender_wallet)
        hash_tx = response.result["hash"]

        st.success("XRP Escrow locked as collateral!")
        st.markdown(f"[View EscrowCreate on Explorer](https://testnet.xrpl.org/transactions/{hash_tx})")
        st.info(f"Sequence Number for Claim: **{seq}** (save this!)")
        return seq
    except Exception as e:
        st.error(f"Escrow failed: {str(e)}")
        return None

def finish_escrow(owner, seq):
    try:
        finish = EscrowFinish(
            account=receiver_wallet.classic_address,
            owner=owner,
            offer_sequence=seq
        )
        filled = autofill(finish, client)
        response = submit_and_wait(filled, client, receiver_wallet)
        result = response.result["meta"]["TransactionResult"]

        if result != "tesSUCCESS":
            raise Exception(result)

        hash_tx = response.result["hash"]
        st.success("Escrow released successfully!")
        st.markdown(f"[View EscrowFinish on Explorer](https://testnet.xrpl.org/transactions/{hash_tx})")
        return True
    except Exception as e:
        st.warning("Escrow not ready yet — wait longer or check sequence.")
        return False

# === USD PAYMENT ===
def send_usd(amount):
    if not receiver_has_usd_trustline():
        st.error("Receiver USD wallet not enabled! Go to Setup tab first.")
        return

    try:
        usd = IssuedCurrencyAmount(currency=CURRENCY_CODE, issuer=ISSUER, value=str(amount))
        payment = Payment(
            account=sender_wallet.classic_address,
            destination=receiver_wallet.classic_address,
            amount=usd
        )
        filled = autofill(payment, client)
        response = submit_and_wait(filled, client, sender_wallet)
        hash_tx = response.result["hash"]

        st.success(f"{amount} USD sent instantly!")
        st.markdown(f"[View Payment on Explorer](https://testnet.xrpl.org/transactions/{hash_tx})")
    except Exception as e:
        st.error(f"Payment failed: {str(e)}")

# === UI ===
st.set_page_config(page_title="MigraSend", page_icon="🌍")
st.title("🌍 MigraSend – Low-Cost Remittance on XRPL")

st.markdown("""
**For migrant workers in Southeast Asia** — send money home instantly with near-zero fees using XRPL escrow + stable token.
""")

st.info("**Demo Note**: Sender issues USD token (simulates RLUSD). In production: trusted issuer like Ripple.")

tab1, tab2, tab3, tab4 = st.tabs(["Setup", "Send", "Claim", "Balances"])

with tab1:
    st.header("Setup: Enable Receiver USD Wallet")
    if receiver_has_usd_trustline():
        st.success("✅ Receiver USD wallet already enabled.")
    else:
        if st.button("Enable Receiver USD Wallet"):
            enable_usd_wallet()

with tab2:
    st.header("Sender: Lock Remittance")
    amount = st.number_input("USD Amount to Send", min_value=1.0, value=50.0)
    if st.button("🔒 Lock XRP Escrow (Collateral)"):
        st.session_state["usd_amount"] = amount
        seq = create_xrp_escrow()
        if seq:
            st.session_state["escrow_seq"] = seq
            st.success(f"Ready to send {amount} USD after claim!")

with tab3:
    st.header("Receiver: Claim Funds")
    seq = st.number_input("Escrow Sequence Number", value=st.session_state.get("escrow_seq", 1))
    amount = st.session_state.get("usd_amount", 50.0)
    st.write(f"**Amount to receive:** {amount} USD")

    if st.button("✅ Claim & Receive USD"):
        if finish_escrow(sender_wallet.classic_address, int(seq)):
            send_usd(amount)

with tab4:
    st.header("Live Balances (Refresh page to update)")
    try:
        # XRP
        info = client.request(AccountInfo(account=receiver_wallet.classic_address, ledger_index="validated"))
        xrp = int(info.result["account_data"]["Balance"]) / 1_000_000
        st.metric("Receiver XRP Balance", f"{xrp:.6f} XRP")

        # USD
        lines = client.request(AccountLines(account=receiver_wallet.classic_address)).result.get("lines", [])
        usd_balance = 0.0
        for line in lines:
            if line["currency"] == "USD":
                usd_balance += float(line["balance"])
        st.metric("Receiver USD Balance", f"{usd_balance:.2f} USD")
    except Exception as e:
        st.error("Balance fetch failed — try again.")
