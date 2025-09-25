# streamlit_app.py
import os
import time
import uuid
import pandas as pd
import streamlit as st

# Import your domain logic / data stores
# Make sure core.py sits next to this file at the repo root.
import core as bb


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
    requester = bb.users_db[st.session_state.current_user_id]

    from_identifier = st.text_input("From (App ID, phone, or email)")
    req_amount = st.number_input("Amount to request", min_value=0.0, step=1.0, key="req_amount")
    simulate_auto_approve = st.checkbox("Simulate recipient auto-approve (demo)", value=True)

    if st.button("Send request"):
        payer = get_user_by_identifier(from_identifier.strip()) if from_identifier else None
        if not payer:
            st.error("Payer not found.")
        elif req_amount <= 0:
            st.error("Enter a positive amount.")
        else:
            if simulate_auto_approve:
                if payer.balance >= req_amount:
                    payer.balance -= req_amount
                    requester.balance += req_amount
                    st.success(f"Request approved. Received ${req_amount:.2f} from **{payer.app_id or payer.user_id}**.")
                else:
                    st.warning("Payer has insufficient funds (simulated).")
            else:
                rid = str(uuid.uuid4())
                link = f"https://breakbread.app/request/{rid}"
                st.info(f"Share this link with the payer: {link}")

# ----------------------------
# Tab 3: Invest
# ----------------------------
with tab3:
    st.subheader("Invest")
    investor = bb.users_db[st.session_state.current_user_id]

    # Show available assets & prices
    st.caption("Available assets & prices")
    assets_view = []
    for k, v in bb.investment_assets.items():
        fee_pct = v.get("fee_percent", 0.0) * 100
        label = price_label(k)
        assets_view.append({"Asset": k.replace("_", " ").title(), "Price": label, "Fee %": f"{fee_pct:.2f}%"})
    st.dataframe(pd.DataFrame(assets_view), use_container_width=True, hide_index=True)

    # Choose asset and invest
    asset_keys = list(bb.investment_assets.keys())
    sel_asset_key = st.selectbox("Choose asset", options=asset_keys,
                                 format_func=lambda k: k.replace("_", " ").title())
    invest_amt = st.number_input("Investment amount ($)", min_value=0.0, step=10.0)
    pwd_inv = st.text_input("Password (to confirm)", type="password", key="pwd_inv")

    if st.button("Execute trade", type="primary"):
        if invest_amt <= 0:
            st.error("Enter a positive investment amount.")
        elif not bb.verify_password(investor.password_hash, pwd_inv):
            st.error("Authorization failed: wrong password.")
        else:
            asset = bb.investment_assets[sel_asset_key]
            price_key = "price_per_ounce" if "price_per_ounce" in asset else "price_per_unit"
            units = invest_amt / asset[price_key]
            commission = round(invest_amt * asset["fee_percent"], 2)

            total_cost = invest_amt + commission
            if investor.balance < total_cost:
                st.error(f"Insufficient balance. Need ${total_cost:.2f}.")
            else:
                # Deduct & update portfolio
                investor.balance -= total_cost
                if investor.user_id not in bb.user_portfolios:
                    bb.user_portfolios[investor.user_id] = {}
                bb.user_portfolios[investor.user_id][sel_asset_key] = \
                    bb.user_portfolios[investor.user_id].get(sel_asset_key, 0.0) + units

                # Add to fund
                bb.break_bread_fund += commission

                # Record investment (optional object)
                inv = bb.Investment(investor.user_id, sel_asset_key, float(invest_amt), float(units), float(commission))
                # You could keep a separate investments_db if desired

                st.success(
                    f"Bought **{units:.4f}** units of **{sel_asset_key.replace('_', ' ').title()}** "
                    f"for ${invest_amt:.2f}. Commission ${commission:.2f}. "
                    f"New balance: ${investor.balance:.2f}"
                )

# ----------------------------
# Tab 4: Portfolio
# ----------------------------
with tab4:
    st.subheader("Your portfolio")
    u = bb.users_db[st.session_state.current_user_id]
    port = bb.user_portfolios.get(u.user_id, {})
    if not port:
        st.info("No holdings yet.")
    else:
        rows = []
        for k, units in port.items():
            a = bb.investment_assets.get(k, {})
            price = a.get("price_per_ounce") or a.get("price_per_unit") or 0.0
            value = units * price
            rows.append({
                "Asset": k.replace("_", " ").title(),
                "Units": round(units, 6),
                "Price": price_label(k) if a else "$0",
                "Est. Value ($)": f"{value:,.2f}"
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

# ----------------------------
# Tab 5: Admin / Logs
# ----------------------------
with tab5:
    st.subheader("Admin & Logs")
    colA, colB = st.columns(2)
    with colA:
        st.metric("Break Bread Fund", f"${bb.break_bread_fund:,.2f}")
        if st.button("Allocate Fund (simulate quarter close)"):
            # Same allocation rules from your PRD (40/35/25)
            total = bb.break_bread_fund
            if total <= 0:
                st.info("No funds to allocate.")
            else:
                community = total * 0.40
                rnd = total * 0.35
                emergency = total * 0.25
                bb.break_bread_fund = 0.0
                st.success(
                    f"Allocated: Community ${community:,.2f} | R&D ${rnd:,.2f} | Emergency ${emergency:,.2f}"
                )
    with colB:
        st.caption("Security events")
        if bb.security_logs:
            logs = [{
                "time": e["timestamp"].isoformat(timespec="seconds"),
                "event": e["event"],
                "transaction_id": e["transaction_id"],
                "details": e["details"],
            } for e in bb.security_logs]
            st.dataframe(pd.DataFrame(logs), use_container_width=True, hide_index=True)
        else:
            st.write("No security events recorded.")

    st.divider()
    st.caption("Users snapshot")
    if bb.users_db:
        users_df = pd.DataFrame([u.to_dict() | {"created_at": u.created_at.isoformat(timespec="seconds")}
                                 for u in bb.users_db.values()])
        st.dataframe(users_df, use_container_width=True, hide_index=True)

# Footer
st.caption("⚠️ Demo only — in-memory data resets on redeploy. Not financial advice.")
