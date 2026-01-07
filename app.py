import streamlit as st
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.models.transactions import EscrowCreate, EscrowFinish, TrustSet, Payment
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.transaction import submit_and_wait, autofill
from xrpl.utils import datetime_to_ripple_time
from datetime import datetime, timedelta
from xrpl.models.requests import AccountInfo


# === CONFIG ===
client = JsonRpcClient("https://s.altnet.rippletest.net:51234/")

SENDER_SEED = "sEdTtf2p1yjodpvYqhUvnCiTGQa4a4o"
RECEIVER_SEED = "sEd7j5Lbj7jyZqotFBz8Cj7RBPMyfMS"

sender_wallet = Wallet.from_seed(SENDER_SEED)
receiver_wallet = Wallet.from_seed(RECEIVER_SEED)

CURRENCY_CODE = "USD"
ISSUER = sender_wallet.classic_address

# === SET TRUST LINE ===
def enable_usd_wallet():
    trust = TrustSet(
        account=receiver_wallet.classic_address,
        limit_amount=IssuedCurrencyAmount(
            currency=CURRENCY_CODE,
            issuer=ISSUER,
            value="10000"
        )
    )
    trust = autofill(trust, client)
    submit_and_wait(trust, client, receiver_wallet)
    st.success("Receiver wallet is now enabled for USD.")

# === ESCROW XRP COLLATERAL ===
def create_xrp_escrow():
    # Step 1 – get current account sequence
    info = client.request(AccountInfo(account=sender_wallet.classic_address, ledger_index="validated"))
    current_seq = info.result["account_data"]["Sequence"]

    finish_after = datetime.now() + timedelta(seconds=10)

    escrow = EscrowCreate(
        account=sender_wallet.classic_address,
        destination=receiver_wallet.classic_address,
        amount="1000000",  # 1 XRP collateral
        finish_after=datetime_to_ripple_time(finish_after),
        sequence=current_seq
    )

    escrow = autofill(escrow, client)
    res = submit_and_wait(escrow, client, sender_wallet)

    st.success("XRP Escrow created.")
    st.info(f"Escrow Sequence Number: {current_seq}")
    return current_seq

# === FINISH ESCROW ===
def finish_escrow(owner, seq):
    finish = EscrowFinish(
        account=receiver_wallet.classic_address,
        owner=owner,
        offer_sequence=seq
    )
    finish = autofill(finish, client)
    submit_and_wait(finish, client, receiver_wallet)
    st.success("Escrow unlocked!")

# === SEND RLUSD AFTER CLAIM ===
def send_usd(amount):
    usd = IssuedCurrencyAmount(
        currency=CURRENCY_CODE,
        issuer=ISSUER,
        value=str(amount)
    )
    payment = Payment(
        account=sender_wallet.classic_address,
        destination=receiver_wallet.classic_address,
        amount=usd
    )
    payment = autofill(payment, client)
    submit_and_wait(payment, client, sender_wallet)
    st.success("USD successfully transferred!")

# === STREAMLIT UI ===
st.set_page_config("MigraSend", "🌍")
st.title("🌍 MigraSend – Low Cost Remittance")

tab1, tab2, tab3 = st.tabs(["Setup", "Send", "Claim"])

with tab1:
    if st.button("Enable Receiver USD Wallet"):
        enable_usd_wallet()

with tab2:
    st.header("Sender")
    amount = st.number_input("USD Amount", value=50.0)
    if st.button("Lock XRP Escrow"):
        seq = create_xrp_escrow()
        st.session_state["escrow_seq"] = seq

with tab3:
    st.header("Receiver")
    owner = st.text_input("Sender Address", value=sender_wallet.classic_address)
    seq = st.number_input("Escrow Sequence", value=st.session_state.get("escrow_seq", 1))
    amount = st.number_input("USD to Claim", value=50.0)
    if st.button("Claim Funds"):
        finish_escrow(owner, int(seq))
        send_usd(amount)
