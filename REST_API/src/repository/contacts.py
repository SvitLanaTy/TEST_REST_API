from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import Contact, User
from src.schemas.contact import ContactSchema


async def get_contacts(limit: int, offset: int, db: AsyncSession, user: User):
    """
    The get_contacts function returns a list of contacts for the given user.
    
    :param limit: int: Limit the number of contacts returned
    :param offset: int: Specify the offset of the query
    :param db: AsyncSession: Pass in the database session
    :param user: User: Filter the contacts by user
    :return: A list of contacts
    :doc-author: Trelent
    """
    stmt = select(Contact).filter_by(user=user).offset(offset).limit(limit)
    contacts = await db.execute(stmt)
    return contacts.scalars().all()


async def get_contact(contact_id: int, db: AsyncSession, user: User):
    """
    The get_contact function returns a contact object from the database.
        Args:
            contact_id (int): The id of the contact to be retrieved.
            db (AsyncSession): An async session for interacting with the database.
            user (User): The user who owns this contact.
    
    :param contact_id: int: Filter the database query by id
    :param db: AsyncSession: Pass the database connection to the function
    :param user: User: Check if the user is allowed to see the contact
    :return: A contact object or none
    :doc-author: Trelent
    """
    stmt = select(Contact).filter_by(id=contact_id, user=user)
    res = await db.execute(stmt)
    contact = res.scalar_one_or_none()
    if contact:
        return contact
    else:
        return None


async def create_contact(body: ContactSchema, db: AsyncSession, user: User):
    """
    The create_contact function creates a new contact in the database.
    
    :param body: ContactSchema: Validate the data that is passed in
    :param db: AsyncSession: Pass the database session to the function
    :param user: User: Get the user from the database
    :return: A contact object
    :doc-author: Trelent
    """
    contact = Contact(**body.model_dump(exclude_unset=True), user=user)
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return contact


async def update_contact(body: ContactSchema, contact_id: int, db: AsyncSession, user: User):
    """
    The update_contact function updates a contact in the database.
    
    :param body: ContactSchema: Validate the request body
    :param contact_id: int: Find the contact in the database
    :param db: AsyncSession: Pass in the database session
    :param user: User: Ensure that the user is only able to update their own contacts
    :return: A contact object
    :doc-author: Trelent
    """
    stmt = select(Contact).filter_by(id=contact_id, user=user)
    result = await db.execute(stmt)
    contact = result.scalar_one_or_none()

    if contact:
        contact.first_name = body.first_name
        contact.last_name = body.last_name
        contact.email = body.email
        contact.phone_number = body.phone_number
        contact.birthday = body.birthday
        contact.extra_data = body.extra_data
        await db.commit()
        await db.refresh(contact)
    return contact


async def delete_contact(contact_id: int, db: AsyncSession, user: User):
    """
    The delete_contact function deletes a contact from the database.
    
    :param contact_id: int: Specify the id of the contact to be deleted
    :param db: AsyncSession: Pass the database session to the function
    :param user: User: Ensure that the user is only deleting their own contacts
    :return: A contact object or none
    :doc-author: Trelent
    """
    stmt = select(Contact).filter_by(id=contact_id, user=user)
    res = await db.execute(stmt)
    contact = res.scalar_one_or_none()
    if contact:
        await db.delete(contact)
        await db.commit()
        return contact
    else:
        return None
    

async def search_contacts(first_name: str, last_name: str, email: str, db: AsyncSession, user: User):   
    """
    The search_contacts function searches the database for contacts that match the given search criteria.
        Args:
            first_name (str): The first name of a contact to search for.
            last_name (str): The last name of a contact to search for.
            email (str): The email address of a contact to search for.
    
    :param first_name: str: Filter the contacts by first name
    :param last_name: str: Filter the contacts by last name
    :param email: str: Search for contacts by email
    :param db: AsyncSession: Pass the database connection to the function
    :param user: User: Ensure that the user is only able to search for contacts they have created
    :return: A list of contacts
    :doc-author: Trelent
    """
    stmt = None
    if first_name:
        stmt = select(Contact).filter(Contact.first_name.ilike(f"%{first_name}%"), Contact.user == user)
    if last_name:
        stmt = select(Contact).filter(Contact.last_name.ilike(f"%{last_name}%"), Contact.user == user)
    if email:
        stmt = select(Contact).filter(Contact.email.ilike(f"%{email}%"), Contact.user == user)

    contacts = await db.execute(stmt)
    return contacts.scalars().all()


def days_to_birthday(self):
    """
    The days_to_birthday function returns the number of days until a person's next birthday.
    
    :param self: Refer to the current instance of a class
    :return: The number of days until the next birthday
    :doc-author: Trelent
    """
    today = date.today()
    year = today.year if today <= self.replace(year=today.year) else today.year + 1
    end_birthday = self.replace(year=year)
    return (end_birthday - today).days


async def get_upcoming_birthdays(limit: int, offset: int, db: AsyncSession, user: User):
    """
    The get_upcoming_birthdays function returns a list of contacts with birthdays in the next 7 days.
        
    
    :param limit: int: Limit the number of contacts returned
    :param offset: int: Specify how many records to skip
    :param db: AsyncSession: Pass in the database session to be used for querying
    :param user: User: Filter the contacts by user
    :return: A list of contacts with birthdays in the next 7 days
    :doc-author: Trelent
    """
    stmt = select(Contact).filter_by(user=user).offset(offset).limit(limit)
    contacts = await db.execute(stmt)
    results = list(contacts.scalars().all())

    return [contact for contact in results if days_to_birthday(contact.birthday) <= 7]