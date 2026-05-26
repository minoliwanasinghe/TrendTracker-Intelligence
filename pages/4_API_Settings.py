import streamlit as st

st.title("🔗 Instagram API Connection")

st.info("Connect your Instagram Business Account to fetch real-time data.")

if st.button("Connect Instagram"):
    # This is where the OAuth URL would go
    st.write("Redirecting to Meta Login...")
    st.markdown("[Login with Facebook](https://www.facebook.com/v19.0/dialog/oauth?client_id=YOUR_ID...)")

st.subheader("API Status")
st.code("Access Token: [NOT CONNECTED]\nAccount ID: [NONE]")