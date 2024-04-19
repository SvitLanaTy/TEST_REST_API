from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from libgravatar import Gravatar

from src.database.db import get_db
from src.entity.models import User
from src.schemas.user import UserSchema


async def get_user_by_email(email: str, db: AsyncSession = Depends(get_db)):
    """
    The get_user_by_email function returns a user object from the database based on the email address provided.
        If no user is found, None is returned.
    
    :param email: str: Pass the email of the user to be fetched
    :param db: AsyncSession: Pass in the database session
    :return: A user object or none if no user is found
    :doc-author: Trelent
    """
    stmt = select(User).filter_by(email=email)
    user = await db.execute(stmt)
    user = user.scalar_one_or_none()
    return user


async def create_user(body: UserSchema, db: AsyncSession = Depends(get_db)):
    """
    The create_user function creates a new user in the database.
        It takes a UserSchema object as input and returns the newly created user.
    
    :param body: UserSchema: Validate the request body
    :param db: AsyncSession: Pass in the database session
    :return: The new user object
    :doc-author: Trelent
    """
    avatar = None
    try:
        g = Gravatar(body.email)
        avatar = g.get_image()
    except Exception as err:
        print(err)

    new_user = User(**body.model_dump(), avatar=avatar)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


async def update_token(user: User, token: str | None, db: AsyncSession):
    """
    The update_token function updates the user's refresh token in the database.
    
    :param user: User: Specify the user that is being updated
    :param token: str | None: Set the refresh_token field of the user object
    :param db: AsyncSession: Pass the database session to the function
    :return: The user object
    :doc-author: Trelent
    """
    user.refresh_token = token
    await db.commit()
    
    
async def confirmed_email(email: str, db: AsyncSession) -> None:    
    """
    The confirmed_email function marks a user as confirmed in the database.
    
    :param email: str: Specify the email of the user that we want to confirm
    :param db: AsyncSession: Pass in the database session
    :return: None
    :doc-author: Trelent
    """
    user = await get_user_by_email(email, db)
    user.confirmed = True
    await db.commit()


async def update_avatar_url(email: str, url: str | None, db: AsyncSession) -> User:
    """
    The update_avatar_url function updates the avatar url of a user.
    
    :param email: str: Identify the user
    :param url: str | None: Specify that the url parameter can either be a string or none
    :param db: AsyncSession: Pass the database session to the function
    :return: The updated user object
    :doc-author: Trelent
    """
    user = await get_user_by_email(email, db)
    user.avatar = url
    await db.commit()
    await db.refresh(user)
    return user


async def change_password(user: User, password: str, db: AsyncSession):
    """
    The change_password function changes the password of a user.
    
    
    :param user: User: Pass the user object to the function
    :param password: str: Pass in the new password
    :param db: AsyncSession: Pass the database session to the function
    :return: The user object
    :doc-author: Trelent
    """
    user.password = password
    await db.commit()
    await db.refresh(user)
    return user