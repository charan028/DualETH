import firebase_admin
from firebase_admin import credentials, auth

# Initialize Firebase Admin SDK
cred = credentials.Certificate("private_cred.json")  # Ensure this file is correct
firebase_admin.initialize_app(cred)

def verify_user(email, password):
    try:
        user = auth.get_user_by_email(email)
        return user.uid
    except:
        return None
