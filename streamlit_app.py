# streamlit_app.py
import os
import time
import uuid
import pandas as pd
import streamlit as st

# Import your domain logic / data stores
# Make sure core.py sits next to this file at the repo root.
import core as bb  # exposes users_db, transactions_db, investment_assets, helpers, models


# ----------------------------
# Helpers for UI <-> core glue
# ----------------------------
def get_user_by_identifier(identifier: str):
    """Find a user by app_id, phone or email."""
    for u in bb.users_db.values():
        if identifier in {u.app_id, u.phone, u.email}:
            return u
    return None


def ensure_demo_users():
    """Seed a couple of demo users once per session."""
    if getattr(st.session_state, "_seeded", False):
        return
    if "test_user_1" not in bb.users_db:
        u1 = bb.User("test_user_1", phone="+1234567890", app_id="johndoe",
                     password_hash=bb.hash_password("password123"))
        u1.balance = 1000.0
        u1.verified = True
        bb.users_db[u1.user_id] = u1
    if "test_user_2" not in bb.users_db:
        u2 = bb.User("test_user_2", email="jane@example.com", app_id="janedoe",
                     password_hash=bb.hash_password("password123"))
        u2.balance = 500.0
        u2.verified = True
        bb.users_db[u2.user_id] = u2
    st.session_state._seeded = True


def price_label(asset_key: str) -> str:
    a = bb.investment_assets[asset_key]
    if "price_per_ounce" in a:
        return f"${a['price_per_ounce']}/oz"
    return f"${a.get('price_per_unit', 0)}/unit"


# ----------------------------
# Streamlit App
# ----------------------------
st.set_page_config(page_title="Break Bread", page_icon="🍞", layout="centered")
st.title("🍞 Break Bread")
st.caption("A peer-to-peer payments & simple investing demo (in-memory)")

# Seed demo data
ensure_demo_users()

# Sidebar: current user / quick actions
with st.sidebar:
    st.header("Account")
    # Login / switch
    all_users = sorted([(u.app_id or u.user_id, u.user_id) for u in bb.users_db.values()])
    user_id_default = st.session_state.get("current_user_id") or (all_users[0][1] if all_users else None)
    current_user_id = st.selectbox("Signed in as", options=[uid for _, uid in all_users],
                                   format_func=lambda uid: bb.users_db[uid].app_id or uid,
                                   index=([uid for _, uid in all_users].index(user_id_default)
                                          if user_id_default in [uid for _, uid in all_users] else 0)
                                   if all_users else 0)
    st.session_state.current_user_id = current_user_id

    # Create new user
    with st.expander("Create new user"):
        new_app_id = st.text_input("App ID (username)", key="new_app_id")
        new_email = st.text_input("Email (optional)", key="new_email")
        new_phone = st.text_input("Phone (optional)", key="new_phone")
        new_pwd = st.text_input("Password", type="password", key="new_pwd")
        if st.button("Create user", use_container_width=True):
            if not new_app_id or not new_pwd:
                st.error("App ID and Password are required.")
            elif any(u.app_id == new_app_id for u in bb.users_db.values()):
                st.error("That App ID is taken. Choose another.")
            else:
                uid = str(uuid.uuid4())
                user = bb.User(
                    user_id=uid,
                    phone=new_phone or None,
                    email=new_email or None,
                    app_id=new_app_id,
                    password_hash=bb.hash_password(new_pwd)
                )
                user.verified = True  # KYC simulated as approved for demo
                bb.users_db[uid] = user
                st.success(f"User created: {new_app_id}")
                st.session_state.current_user_id = uid
                st.rerun()

    # Demo top-ups
    with st.expander("Add funds (demo)"):
        amt = st.number_input("Amount", min_value=0.0, step=10.0, value=100.0, key="topup_amt")
        if st.button("Add to balance", use_container_width=True):
            u = bb.users_db[st.session_state.current_user_id]
            u.balance += float(amt)
            st.success(f"Added ${amt:.2f}. New balance: ${u.balance:.2f}")

    # Quick info
    if current_user_id:
        u = bb.users_db[current_user_id]
        st.metric("Balance", f"${u.balance:,.2f}")
        st.write(f"**User ID**: `{u.user_id}`")
        st.write(f"**Verified**: {'✅' if u.verified else '❌'}")
        st.write(f"**Limit**: ${u.transaction_limit:,.2f}")

st.divider()

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["Send (P2P)", "Request", "Invest", "Portfolio", "Admin / Logs"]
)

# ----------------------------
# Tab 1: P2P Send
# ----------------------------
with tab1:
    st.subheader("Send money")
    u = bb.users_db[st.session_state.current_user_id]

    recipient_identifier = st.text_input("Recipient (App ID, phone, or email)")
    amount = st.number_input("Amount", min_value=0.0, step=1.0)
    note = st.text_input("Note (optional)")
    password = st.text_input("Your password (to authorize)", type="password")

    if st.button("Send", type="primary"):
        r = get_user_by_identifier(recipient_identifier.strip()) if recipient_identifier else None
        if not r:
            st.error("Recipient not found.")
        elif amount <= 0:
            st.error("Enter a positive amount.")
        elif not bb.verify_password(u.password_hash, password):
            st.error("Authorization failed: wrong password.")
        else:
            fee = round(amount * 0.015, 2)
            if u.balance < amount + fee:
                st.error("Insufficient balance including fee.")
            else:
                t = bb.Transaction(u.user_id, r.user_id, float(amount), float(fee), note or "")
                if not bb.security_check(t):
                    t.status = "flagged"
                    bb.transactions_db.append(t)
                    st.warning("Transaction flagged by security. Not sent.")
                else:
                    # Execute
                    u.balance -= (amount + fee)
                    r.balance += amount
                    t.status = "completed"
                    bb.break_bread_fund += fee
                    bb.transactions_db.append(t)
                    st.success(f"Sent ${amount:.2f} to **{r.app_id or r.user_id}**. "
                               f"Fee ${fee:.2f}. New balance: ${u.balance:.2f}")

    if bb.transactions_db:
        st.caption("Recent transactions (most recent first)")
        df = pd.DataFrame([t.to_dict() for t in sorted(bb.transactions_db, key=lambda x: x.timestamp, reverse=True)])
        st.dataframe(df, use_container_width=True, hide_index=True)

# ----------------------------
# Tab 2: Request Money (simple)
# ----------------------------
with tab2:
    st.subheader("Request money")

