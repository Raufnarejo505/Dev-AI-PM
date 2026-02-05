import asyncio
import sys
import os

# Ensure backend directory is in python path
sys.path.append(os.getcwd())

from app.db.session import AsyncSessionLocal
from app.services import user_service
from app.schemas.user import UserCreate

async def main():
    email = "tanirajsingh@itx-solution.com"
    password = "tanirajsingh1122"
    
    print(f"Checking for user: {email}")
    async with AsyncSessionLocal() as session:
        user = await user_service.get_user_by_email(session, email)
        if user:
            print(f"User {email} already exists.")
        else:
            print(f"Creating user {email}...")
            try:
                await user_service.create_user(
                    session, 
                    UserCreate(email=email, password=password, full_name="Taniraj Singh", role="admin")
                )
                print("User created successfully.")
            except Exception as e:
                print(f"Error creating user: {e}")

if __name__ == "__main__":
    asyncio.run(main())
