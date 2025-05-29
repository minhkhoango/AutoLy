import streamlit as st

# ─── ONE-TIME inits ──────────────────────────────────────────
for key, default in {
    'step': 0,
    'full_name_mre': '',
    'dob_mre': None,
    'address_mre': '',
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ─── NAVIGATION CALLBACKS ────────────────────────────────────
def go_next():
    st.session_state.step += 1

def go_back():
    st.session_state.step -= 1

# ─── UI ──────────────────────────────────────────────────────
st.title("Multi-Step Wizard (No Forms)")

if st.session_state.step == 0:
    st.header("Step 1: Personal Info")
    st.text_input("Họ và tên (IN HOA)", key="full_name_mre")
    st.date_input("Ngày sinh", key="dob_mre")
    st.button("→ Next", on_click=go_next)

elif st.session_state.step == 1:
    st.header("Step 2: Address")
    st.text_input("Địa chỉ", key="address_mre")
    c1, c2 = st.columns(2)
    c1.button("← Back", on_click=go_back)
    c2.button("Finish", on_click=lambda: st.success("All done!"))

# ─── DEBUG ───────────────────────────────────────────────────
st.write("Session state:", dict(st.session_state))