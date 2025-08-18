import streamlit_authenticator as stauth

# Create hashed passwords
hashed_passwords = stauth.Hasher(['TGDrugs@123','TGDrugs@321']).generate()

print(hashed_passwords)