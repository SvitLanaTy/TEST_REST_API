from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks, Request, Response
from fastapi.security import OAuth2PasswordRequestForm, HTTPAuthorizationCredentials, HTTPBearer
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.conf import messages
from src.database.db import get_db
from src.repository import users as repositories_users
from src.schemas.user import UserSchema, TokenSchema, UserResponse, RequestEmail, PasswordChangeRequest
from src.services.auth import auth_service
from src.services.email import send_email, send_email_password


router = APIRouter(prefix='/auth', tags=['auth'])
get_refresh_token = HTTPBearer()


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(body: UserSchema, bt: BackgroundTasks, request: Request, db: AsyncSession =            Depends(get_db)):
    """
    The signup function creates a new user in the database.
    
    :param body: UserSchema: Validate the request body
    :param bt: BackgroundTasks: Add a task to the background tasks queue
    :param request: Request: Get the base_url of the request
    :param db: AsyncSession: Get the database connection
    :return: A userschema object, but when i try to access the user
    :doc-author: Trelent
    """
    exist_user = await repositories_users.get_user_by_email(body.email, db)
    if exist_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=messages.ACCOUNT_EXIST)
    body.password = auth_service.get_password_hash(body.password)
    new_user = await repositories_users.create_user(body, db)
    bt.add_task(send_email, new_user.email, new_user.username, str(request.base_url))
    return new_user


@router.post("/login",  response_model=TokenSchema)
async def login(body: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    """
    The login function is used to authenticate a user.
    It takes the username and password as input, verifies them against the database, and returns an access token if successful.
    
    
    :param body: OAuth2PasswordRequestForm: Pass the username and password to the login function
    :param db: AsyncSession: Get the database session
    :return: A dictionary with the access_token, refresh_token and token_type
    :doc-author: Trelent
    """
    user = await repositories_users.get_user_by_email(body.username, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No such user")
    if not user.confirmed:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email not confirmed")
    if not auth_service.verify_password(body.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect credentials")
    # Generate JWT
    access_token = await auth_service.create_access_token(data={"sub": user.email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": user.email})
    await repositories_users.update_token(user, refresh_token, db)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.get('/refresh_token',  response_model=TokenSchema)
async def refresh_token(credentials: HTTPAuthorizationCredentials = Depends(get_refresh_token),
                        db: AsyncSession = Depends(get_db)):
    """
    The refresh_token function is used to refresh the access token.
    It takes in a refresh token and returns an access_token, a new refresh_token, and the type of token (bearer).
    
    
    :param credentials: HTTPAuthorizationCredentials: Get the refresh token from the request header
    :param db: AsyncSession: Access the database
    :return: A dictionary with the access_token, refresh_token and token_type
    :doc-author: Trelent
    """
    token = credentials.credentials
    email = await auth_service.decode_refresh_token(token)
    user = await repositories_users.get_user_by_email(email, db)
    if user.refresh_token != token:
        await repositories_users.update_token(user, None, db)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    access_token = await auth_service.create_access_token(data={"sub": email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": email})
    await repositories_users.update_token(user, refresh_token, db)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.get('/confirmed_email/{token}')
async def confirmed_email(token: str, db: AsyncSession = Depends(get_db)):    
    """
    The confirmed_email function is used to confirm a user's email address.
    It takes the token from the URL and uses it to get the user's email address.
    Then, it checks if that user exists in our database, and if they do not exist, 
    we return an error message saying "Verification error". If they do exist in our database, 
    we check whether or not their account has already been confirmed. If their account has already been confirmed, 
    then we return a message saying "Your email is already confirmed". Otherwise (if their account hasn't yet been confirmed), 
    
    :param token: str: Get the token from the url
    :param db: AsyncSession: Get the database connection
    :return: A dictionary with a message
    :doc-author: Trelent
    """
    email = await auth_service.get_email_from_token(token)
    user = await repositories_users.get_user_by_email(email, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error")
    if user.confirmed:
        return {"message": "Your email is already confirmed"}
    await repositories_users.confirmed_email(email, db)
    return {"message": "Email confirmed"}



@router.post('/request_email')
async def request_email(body: RequestEmail, background_tasks: BackgroundTasks, request: Request,
                        db: AsyncSession = Depends(get_db)):
    """
    The request_email function is used to send an email to the user with a link that will allow them
    to confirm their email address. The function takes in a RequestEmail object, which contains the 
    email of the user who wants to confirm their account. It then checks if there is already a confirmed 
    user with that email address, and if so returns an error message saying as much. If not, it sends an 
    email containing a confirmation link.
    
    :param body: RequestEmail: Get the email from the request body
    :param background_tasks: BackgroundTasks: Add a task to the background tasks queue
    :param request: Request: Get the base url of the application
    :param db: AsyncSession: Get the database session from the dependency injection container
    :return: {&quot;message&quot;: &quot;your email is already confirmed&quot;}
    :doc-author: Trelent
    """
    user = await repositories_users.get_user_by_email(body.email, db)

    if user.confirmed:
        return {"message": "Your email is already confirmed"}
    if user:
        background_tasks.add_task(send_email, user.email, user.username, str(request.base_url))
    return {"message": "Check your email for confirmation."}


@router.get('/{username}')
async def request_email(username: str, response: Response, db: AsyncSession = Depends(get_db)):
    """
    The request_email function is called when a user opens an email.
    It saves the fact that the user opened the email in our database, and returns a 1x2 pixel image to display in their browser.
    
    :param username: str: Get the username of the user who opened the email
    :param response: Response: Send a response to the client
    :param db: AsyncSession: Get the database connection
    :return: A fileresponse object
    :doc-author: Trelent
    """
    print('--------------------------------')
    print(f'{username} зберігаємо що він відкрив email в БД')
    print('--------------------------------')
    return FileResponse("src/static/open_check.png", media_type="image/png", content_disposition_type="inline")


@router.post("/reset_password")
async def reset_password(body: RequestEmail, background_tasks: BackgroundTasks, request: Request,
                         db: AsyncSession = Depends(get_db)):
    """
    The reset_password function is used to reset a user's password.
        It takes in the email of the user and sends an email with a link to reset their password.
        The function returns a message that tells the user to check their email for further instructions.
    
    :param body: RequestEmail: Get the email from the request body
    :param background_tasks: BackgroundTasks: Add a task to the background tasks queue
    :param request: Request: Get the base url of the server
    :param db: AsyncSession: Get the database session
    :return: A dictionary with the message
    :doc-author: Trelent
    """
    user = await repositories_users.get_user_by_email(body.email, db)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Not found user email"
        )
    
    if user:
        background_tasks.add_task(send_email_password, user.email, user.username, str(request.base_url))
    return {"message": "Check your email for reset password. "}


@router.get("/change_password/{token}")
async def change_password(token: str, password_change: PasswordChangeRequest, 
                          db: AsyncSession = Depends(get_db)):
  
    """
    The change_password function allows a user to change their password.
        The function takes in the token of the user and a PasswordChangeRequest object, which contains 
        two fields: password and confirm_password. If these two fields are equal, then the function will 
        hash the new password using Argon2 hashing algorithm (which is considered one of the most secure) 
        and update it in our database.
    
    :param token: str: Get the email of the user who wants to change his password
    :param password_change: PasswordChangeRequest: Get the password and confirm_password from the request body
    :param db: AsyncSession: Get the database session from the dependency injection
    :return: A dict with a message
    :doc-author: Trelent
    """
    email = await auth_service.get_email_from_token(token)
    user = await repositories_users.get_user_by_email(email, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Password change error"
        )
    if password_change.password != password_change.confirm_password:
        return {"message": "Different passwords"}
    hashed_password = auth_service.get_password_hash(password_change.password)
    print(hashed_password)
    await repositories_users.change_password(user, hashed_password, db)
    return {"message": "Password change done"}