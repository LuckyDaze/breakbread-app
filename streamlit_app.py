# streamlit_app.py
import uuid
import streamlit as st
import core as bb  # your logic (User/Transaction/models/prices/etc.)

st.set_page_config(page_title="Break Bread", page_icon="🍞", layout="centered")
st.title("🍞 Break Bread")

# --- seed demo users once per process ---
if "seeded" not in st.session_state:
    st.session_state.seeded = True
    bb.users_db.clear()
    u1 = bb.User("test_user_1", phone="+1234567890", app_id="johndoe", password_hash=bb.hash_password("password123"))
    u1.balance = 20000.0; u1.verified = True; bb.users_db[u1.user_id] = u1
    u2 = bb.User("test_user_2", email="jane@example.com", app_id="janedoe", password_hash=bb.hash_password("password123"))
    u2.balance = 15000.0; u2.verified = True; bb.users_db[u2.user_id] = u2

tab_users, tab_p2p, tab_invest, tab_fund = st.tabs(["Users", "P2P", "Invest", "Fund"])

# ---------- Users ----------
with tab_users:
    st.subheader("Register (demo)")
    contact = st.text_input("Phone or Email")
    app_id = st.text_input("App ID (username)")
    pw = st.text_input("Password", type="password")
    if st.button("Register"):
        if not contact or not app_id or not pw:
            st.error("Please fill all fields.")
        elif any(u.app_id == app_id for u in bb.users_db.values()):
            st.error("App ID already taken.")
        else:
            uid = str(uuid.uuid4())
            email = contact if "@" in contact else None
            phone = None if email else contact
            u = bb.User(uid, phone=phone, email=email, app_id=app_id, password_hash=bb.hash_password(pw))
            u.verified = True
            bb.users_db[uid] = u
            st.success(f"Registered! User ID: {uid}")

    st.subheader("Users & Balances")
    if bb.users_db:
        for uid, u in bb.users_db.items():
            st.write(f"**{u.app_id}** — ${u.balance:,.2f}  |  Verified: {u.verified}")
    else:
        st.info("No users yet.")

# ---------- P2P ----------
with tab_p2p:
    st.subheader("Send Money")
    if not bb.users_db:
        st.info("No users to transact.")
    else:
        sender_id = st.selectbox(
            "Sender",
            options=list(bb.users_db.keys()),
            format_func=lambda k: f"{bb.users_db[k].app_id} ({k})"
        )
        recip_id_input = st.text_input("Recipient (App ID / phone / email)")
        amt = st.number_input("Amount (USD)", min_value=0.0, step=10.0)
        note = st.text_input("Note", "")

        if st.button("Send"):
            # find recipient
            recip = next(
                (u for u in bb.users_db.values()
                 if u.app_id == recip_id_input or u.phone == recip_id_input or u.email == recip_id_input),
                None
            )
            if not recip:
                st.error("Recipient not found.")
            elif amt <= 0:
                st.error("Amount must be greater than 0.")
            else:
                sender = bb.users_db[sender_id]
                fee = round(amt * 0.015, 2)
                if sender.balance < (amt + fee):
                    st.error("Insufficient balance (includes fee).")
                else:
                    # Build a transaction and run the same checks as core
                    t = bb.Transaction(sender_id, recip.user_id, amt, fee, note)
                    if not bb.security_check(t):
                        t.status = "flagged"; bb.transactions_db.append(t)
                        st.warning("Transaction flagged for security review.")
                    else:
                        sender.balance -= (amt + fee)
                        recip.balance += amt
                        t.status = "completed"; bb.transactions_db.append(t)
                        bb.break_bread_fund += fee
                        st.success(f"Sent ${amt:,.2f} to {recip.app_id}. Fee: ${fee:,.2f}")

    if bb.transactions_db:
        st.caption("Recent Transactions (latest 10)")
        for t in bb.transactions_db[-10:][::-1]:
            st.write(f"- {t.timestamp:%Y-%m-%d %H:%M} | {t.status} | "
                     f"{t.sender_id} → {t.recipient_id} | ${t.amount:,.2f} (fee ${t.fee:,.2f}) | {t.note}")

# ---------- Invest ----------
with tab_invest:
    st.subheader("Invest")
    if not bb.users_db:
        st.info("No users to invest.")
    else:
        uid = st.selectbox(
            "User",
            options=list(bb.users_db.keys()),
            format_func=lambda k: bb.users_db[k].app_id
        )
        asset_label = st.selectbox("Asset", ["Gold", "Silver", "Platinum", "Treasury Bonds"])
        asset_key = {"Gold": "gold", "Silver": "silver", "Platinum": "platinum", "Treasury Bonds": "treasury_bonds"}[asset_label]
        asset = bb.investment_assets[asset_key]
        price_key = "price_per_ounce" if asset_key in ["gold", "silver", "platinum"] else "price_per_unit"

        st.write(f"**Current price**: ${asset[price_key]:,.6f}")
        st.write(f"**Fee**: {asset['fee_percent']*100:.2f}%")

        inv_amt = st.number_input("Investment Amount (USD)", min_value=0.0, step=50.0)
        password = st.text_input("Password (confirm investment)", type="password")

        if st.button("Execute Investment"):
            if inv_amt <= 0:
                st.error("Amount must be greater than 0.")
            else:
                user = bb.users_db[uid]
                units = inv_amt / asset[price_key] if asset[price_key] else 0.0
                commission = round(inv_amt * asset["fee_percent"], 2)
                if user.balance < inv_amt + commission:
                    st.error("Insufficient balance (includes fee).")
                elif not bb.verify_password(user.password_hash, password):
                    st.error("Authentication failed.")
                else:
                    user.balance -= (inv_amt + commission)
                    if uid not in bb.user_portfolios:
                        bb.user_portfolios[uid] = {}
                    bb.user_portfolios[uid][asset_key] = bb.user_portfolios[uid].get(asset_key, 0.0) + units
                    bb.break_bread_fund += commission
                    st.success(f"Bought {units:,.6f} units of {asset_label}. Fee ${commission:,.2f}. New balance ${user.balance:,.2f}")
                    st.write("**Portfolio**:", bb.user_portfolios[uid])

# ---------- Fund ----------
with tab_fund:
    st.subheader("Break Bread Fund")
    st.write(f"Current fund: **${bb.break_bread_fund:,.2f}**")
    if st.button("Allocate (demo)"):
        if bb.break_bread_fund <= 0:
            st.info("No funds to allocate.")
        else:
            community = bb.break_bread_fund * 0.40
            rnd = bb.break_bread_fund * 0.35
            emergency = bb.break_bread_fund * 0.25
            st.write(f"- Community Outreach: ${community:,.2f}")
            st.write(f"- R&D: ${rnd:,.2f}")
            st.write(f"- Emergency Assistance: ${emergency:,.2f}")
            bb.break_bread_fund = 0.0
            st.success("Allocated and reset fund.")
