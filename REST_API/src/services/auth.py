import pickle
from datetime import datetime, timedelta
from typing import Optional

import redis
from fastapi import Depends, HTTPException, status
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt

from src.database.db import get_db
from src.repository import users as repository_users
from src.conf.config import config


class Auth:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")    
    SECRET_KEY = config.SECRET_KEY_JWT
    ALGORITHM = config.ALGORITHM
    cache = redis.Redis(
        host=config.REDIS_DOMAIN,
        port=config.REDIS_PORT,
        db=0,
        password=config.REDIS_PASSWORD,
    )

    def verify_password(self, plain_password, hashed_password):
        """
        The verify_password function takes a plain-text password and the hashed version of that password,
            and returns True if they match, False otherwise. This is used to verify that the user's login
            credentials are correct.
        
        :param self: Represent the instance of the class
        :param plain_password: Store the password entered by the user
        :param hashed_password: Compare the password that is being passed in with the hashed version of it
        :return: True or false depending on whether the password is correct
        :doc-author: Trelent
        """
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str):
        """
        The get_password_hash function takes a password as input and returns the hash of that password.
            The function uses the pwd_context object to generate a hash from the given password.
        
        :param self: Represent the instance of the class
        :param password: str: Pass the password to be hashed into the function
        :return: A hashed password
        :doc-author: Trelent
        """
        return self.pwd_context.hash(password)

    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

    # define a function to generate a new access token
    async def create_access_token(
        self, data: dict, expires_delta: Optional[float] = None
    ):
        """
        The create_access_token function creates a new access token for the user.   
                
        
        :param self: Represent the instance of the class
        :param data: dict: Pass the data to be encoded in the jwt
        :param expires_delta: Optional[float]: Set the expiration time of the token
        :return: A jwt token with the following claims:
        :doc-author: Trelent
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + timedelta(seconds=expires_delta)
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update(
            {"iat": datetime.utcnow(), "exp": expire, "scope": "access_token"}
        )
        encoded_access_token = jwt.encode(
            to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM
        )
        return encoded_access_token
    

    # define a function to generate a new refresh token
    async def create_refresh_token(
        self, data: dict, expires_delta: Optional[float] = None
    ):
        """
        The create_refresh_token function creates a refresh token for the user.
            Args:
                data (dict): The data to be encoded in the JWT. This should include at least a username and an email address, but can also include other information such as roles or permissions.
                expires_delta (Optional[float]): The number of seconds until this token expires, defaults to 7 days if not specified.
        
        :param self: Represent the instance of the class
        :param data: dict: Store the user's id and username
        :param expires_delta: Optional[float]: Set the expiration time of the refresh token
        :return: A jwt token
        :doc-author: Trelent
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + timedelta(seconds=expires_delta)
        else:
            expire = datetime.utcnow() + timedelta(days=7)
        to_encode.update(
            {"iat": datetime.utcnow(), "exp": expire, "scope": "refresh_token"}
        )
        encoded_refresh_token = jwt.encode(
            to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM
        )
        return encoded_refresh_token
    

    async def decode_refresh_token(self, refresh_token: str):
        """
        The decode_refresh_token function is used to decode the refresh token.
            The function will raise an HTTPException if the token is invalid or has expired.
            If the token is valid, it will return a string with the email address of 
            user who owns that refresh_token.
        
        :param self: Represent the instance of a class
        :param refresh_token: str: Pass the refresh token to the function
        :return: The email address of the user who requested a new token
        :doc-author: Trelent
        """
        try:
            payload = jwt.decode(
                refresh_token, self.SECRET_KEY, algorithms=[self.ALGORITHM]
            )
            if payload["scope"] == "refresh_token":
                email = payload["sub"]
                return email
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid scope for token",
            )
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )
            

    async def get_current_user(
        self, token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
    ):
        """
        The get_current_user function is a dependency that will be used in the
            protected endpoints. It takes a token as an argument and returns the user
            if it's valid, otherwise raises an HTTPException with status code 401.
        
        :param self: Represent the instance of the class
        :param token: str: Get the token from the request header
        :param db: AsyncSession: Get the database session
        :return: The user object which is used to authorize the endpoint
        :doc-author: Trelent
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            # Decode JWT
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            if payload["scope"] == "access_token":
                email = payload["sub"]
                if email is None:
                    raise credentials_exception
            else:
                raise credentials_exception
        except JWTError as e:
            raise credentials_exception

        user_hash = str(email)

        user = self.cache.get(user_hash)

        if user is None:
            print("User from database")
            user = await repository_users.get_user_by_email(email, db)
            if user is None:
                raise credentials_exception
            self.cache.set(user_hash, pickle.dumps(user))
            self.cache.expire(user_hash, 300)
        else:
            print("User from cache")
            user = pickle.loads(user)
        return user


    def create_email_token(self, data: dict):
        """
        The create_email_token function takes a dictionary of data and returns a JWT token.
            The token is encoded with the SECRET_KEY and ALGORITHM defined in the class.
            The expiration date is set to 1 day from now.
        
        :param self: Represent the instance of the class
        :param data: dict: Pass in the data to be encoded
        :return: A token
        :doc-author: Trelent
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=1)
        to_encode.update({"iat": datetime.utcnow(), "exp": expire})
        token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return token
    

    async def get_email_from_token(self, token: str):
        """
        The get_email_from_token function takes a token as an argument and returns the email address associated with that token.
        The function uses the jwt library to decode the token, which is then used to return the email address.
        
        :param self: Represent the instance of the class
        :param token: str: Pass the token to the function
        :return: The email address of the user who is trying to log in
        :doc-author: Trelent
        """
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            email = payload["sub"]
            return email
        except JWTError as e:
            print(e)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid token for email verification",
            )


auth_service = Auth()
