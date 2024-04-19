import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, AsyncMock

from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import Contact, User
from src.repository.contacts import (
    get_contacts,
    get_contact,
    create_contact,
    update_contact,
    delete_contact,
    search_contacts,
    days_to_birthday,
    get_upcoming_birthdays
)
from src.schemas.contact import ContactSchema


class TestAsyncContacts(unittest.IsolatedAsyncioTestCase):
    
    def setUp(self) -> None:
        self.user = User(id=1, username='test_user', email="test_user@gmail.com", password="password", confirmed=True)
        self.session = AsyncMock(spec=AsyncSession)
        
        

    async def test_get_contact(self):
        contact = Contact(id=1, first_name="test1", last_name="test2", email="test@gmail.com", phone_number="+380123456789", birthday=datetime.now().date(), extra_data="test_extra")
        mocked_contact = MagicMock()
        mocked_contact.scalar_one_or_none.return_value = contact
        self.session.execute.return_value = mocked_contact
        result = await get_contact(1, self.session, self.user)
        self.assertEqual(result, contact)

    async def test_get_contacts(self):
        limit = 10
        offset = 0
        contacts = [
            Contact(id=1, first_name="test1", last_name="test2", email="test@gmail.com", phone_number="+380123456789", birthday=datetime.now().date(), extra_data="test_extra"),
            Contact(id=2, first_name="test1", last_name="test2", email="test@gmail.com", phone_number="+380123456789", birthday=datetime.now().date(), extra_data="test_extra")]
        mocked_contacts = MagicMock()
        mocked_contacts.scalars.return_value.all.return_value = contacts
        self.session.execute.return_value = mocked_contacts
        result = await get_contacts(limit, offset, self.session, self.user)
        self.assertEqual(result, contacts)

    
