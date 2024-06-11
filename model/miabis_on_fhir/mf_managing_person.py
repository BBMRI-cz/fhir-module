from fhirclient.models.address import Address
from fhirclient.models.contactpoint import ContactPoint
from fhirclient.models.humanname import HumanName
from fhirclient.models.practitioner import Practitioner


class MFManagingPerson:
    def __init__(self, given_name: str, family_name: str, email: str, city: str,
                 country: str, postal_code: str, street_name_and_number: str):
        self._given_name = given_name
        self._family_name = family_name
        self._email = email
        self._city = city
        self._country = country
        self._postal_code = postal_code
        self._street_name_and_number = street_name_and_number

    @property
    def given_name(self) -> str:
        return self._given_name

    @given_name.setter
    def given_name(self, given_name: str):
        self._given_name = given_name

    @property
    def family_name(self) -> str:
        return self._family_name

    @family_name.setter
    def family_name(self, family_name: str):
        self._family_name = family_name

    @property
    def email(self) -> str:
        return self._email

    @email.setter
    def email(self, email: str):
        self._email = email

    @property
    def city(self) -> str:
        return self._city

    @city.setter
    def city(self, city: str):
        self._city = city

    @property
    def country(self) -> str:
        return self._country

    @country.setter
    def country(self, country: str):
        self._country = country

    @property
    def postal_code(self) -> str:
        return self._postal_code

    @postal_code.setter
    def postal_code(self, postal_code: str):
        self._postal_code = postal_code

    @property
    def street_name_and_number(self) -> str:
        return self._street_name_and_number

    @street_name_and_number.setter
    def street_name_and_number(self, street_name_and_number: str):
        self._street_name_and_number = street_name_and_number

    def to_fhir(self) -> Practitioner:
        managing_person = Practitioner()
        managing_person.name = [HumanName()]
        managing_person.name[0].given = self.given_name
        managing_person.name[0].family = self.family_name
        managing_person.telecom = [ContactPoint()]
        managing_person.telecom[0].system = "email"
        managing_person.telecom[0].value = self.email
        managing_person.address = [Address()]
        managing_person.address[0].city = self.city
        managing_person.address[0].country = self.country
        managing_person.address[0].postalCode = self.postal_code
        managing_person.address[0].line = self.street_name_and_number
        return managing_person