import redis.asyncio as redis
from fastapi import APIRouter, HTTPException, Depends, status, Path, Query
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.repository import contacts as repositories_contacts
from src.schemas.contact import ContactSchema, ContactResponse
from src.entity.models import User
from src.services.auth import auth_service


router = APIRouter(prefix='/contacts', tags=['contacts'])


@router.get("/", response_model=list[ContactResponse],
    dependencies=[Depends(RateLimiter(times=1, seconds=10))])
async def get_contacts(limit: int = Query(10, ge=10, le=500), offset: int = Query(0, ge=0),
                    db: AsyncSession = Depends(get_db), user: User = Depends(auth_service.get_current_user)):
    """
    The get_contacts function returns a list of contacts for the current user.
        The limit and offset parameters are used to paginate the results.
    
    
    :param limit: int: Limit the number of contacts returned
    :param ge: Specify a minimum value for the limit parameter
    :param le: Limit the number of contacts returned to 500
    :param offset: int: Skip the first n contacts in the database
    :param ge: Specify the minimum value for a parameter
    :param db: AsyncSession: Pass the database session to the function
    :param user: User: Get the current user
    :return: A list of contacts
    :doc-author: Trelent
    """
    contacts = await repositories_contacts.get_contacts(limit, offset, db, user)    
    return contacts


@router.get("/{contact_id}", response_model=ContactResponse,
    dependencies=[Depends(RateLimiter(times=1, seconds=10))])
async def get_contact(contact_id: int = Path(ge=1), db: AsyncSession = Depends(get_db), user: User = Depends(auth_service.get_current_user)):
    """
    The get_contact function returns a contact by id.
        Args:
            contact_id (int): The id of the contact to return.
            db (AsyncSession): A database connection object.
            user (User): The current logged in user, if any.
    
    :param contact_id: int: Get the contact id from the path
    :param db: AsyncSession: Pass the database session to the function
    :param user: User: Get the current user from the auth service
    :return: A contact object
    :doc-author: Trelent
    """
    contact = await repositories_contacts.get_contact(contact_id, db, user)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NOT FOUND")
    return contact


@router.post("/", response_model=ContactResponse, status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RateLimiter(times=1, seconds=20))])
async def create_contact(body: ContactSchema, db: AsyncSession = Depends(get_db), user: User = Depends(auth_service.get_current_user)):
    """
    The create_contact function creates a new contact in the database.
        The function takes a ContactSchema object as input, and returns the newly created contact.
    
    :param body: ContactSchema: Validate the request body
    :param db: AsyncSession: Get the database session
    :param user: User: Get the current user
    :return: A contactschema object
    :doc-author: Trelent
    """
    contact = await repositories_contacts.create_contact(body, db, user)
    return contact


@router.put("/{contact_id}")
async def update_contact(body: ContactSchema, contact_id: int = Path(ge=1), db: AsyncSession = Depends(get_db), user: User = Depends(auth_service.get_current_user)):
    """
    The update_contact function updates a contact in the database.
        Args:
            body (ContactSchema): The ContactSchema object to be updated.
            contact_id (int): The id of the ContactSchema object to be updated.
            db (AsyncSession): An AsyncSession instance for interacting with the database.
            user (User): A User instance representing an authenticated user making this request, if any exists.
    
    :param body: ContactSchema: Validate the data sent in the request body
    :param contact_id: int: Identify the contact that is to be deleted
    :param db: AsyncSession: Pass the database connection to the function
    :param user: User: Get the current user from the auth_service
    :return: A contactschema object
    :doc-author: Trelent
    """
    contact = await repositories_contacts.update_contact(body, contact_id, db, user)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NOT FOUND")    
    return contact


@router.delete("/{contact_id}")
async def delete_contact(contact_id: int = Path(ge=1), db: AsyncSession = Depends(get_db), user: User = Depends(auth_service.get_current_user)):
    """
    The delete_contact function deletes a contact from the database.
        Args:
            contact_id (int): The id of the contact to delete.
            db (AsyncSession): An async session for interacting with the database.
            user (User): The current user, as determined by auth_service's get_current_user function.
    
    :param contact_id: int: Specify the contact id
    :param db: AsyncSession: Pass the database connection to the function
    :param user: User: Get the current user
    :return: A contact object
    :doc-author: Trelent
    """
    contact = await repositories_contacts.delete_contact(contact_id, db, user)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_204_NO_CONTENT, detail="NO CONTENT")
    return contact
    


@router.get("/search/", response_model=list[ContactResponse])
async def search_contacts(first_name: str = Query(None), last_name: str = Query(None), email: str = Query(None), db: AsyncSession = Depends(get_db), user: User = Depends(auth_service.get_current_user)):
    """
    The search_contacts function searches for contacts in the database.
        Args:
            first_name (str): The contact's first name.
            last_name (str): The contact's last name.
            email (str): The contact's email address.
    
    :param first_name: str: Search for a contact by first name
    :param last_name: str: Search for a contact by last name
    :param email: str: Search for a contact by email
    :param db: AsyncSession: Get the database connection
    :param user: User: Get the current user from the auth_service
    :return: A list of contacts
    :doc-author: Trelent
    """
    contact = await repositories_contacts.search_contacts(first_name, last_name, email, db, user)
    return contact
    

@router.get("/birthdays/", response_model=list[ContactResponse],
    dependencies=[Depends(RateLimiter(times=1, seconds=10))])
async def get_upcoming_birthdays(limit: int = Query(10, ge=10, le=200), offset: int = Query(0, ge=0),
                                db: AsyncSession = Depends(get_db), user: User = Depends(auth_service.get_current_user)):
    """
    The get_upcoming_birthdays function returns a list of contacts with upcoming birthdays.
        The limit parameter specifies the maximum number of contacts to return, and the offset parameter specifies how many
        contacts to skip before returning results. For example, if you want to get all upcoming birthdays starting from
        contact #10, set limit=200 and offset=10.
    
    :param limit: int: Limit the number of contacts returned
    :param ge: Specify a minimum value for the parameter
    :param le: Limit the number of results returned
    :param offset: int: Specify the number of records to skip
    :param ge: Specify a minimum value for the parameter
    :param db: AsyncSession: Get the database session from the dependency injection
    :param user: User: Get the current user
    :return: A list of contacts
    :doc-author: Trelent
    """
    contacts = await repositories_contacts.get_upcoming_birthdays(limit, offset, db, user)
    if contacts is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NOT FOUND")
    return contacts
