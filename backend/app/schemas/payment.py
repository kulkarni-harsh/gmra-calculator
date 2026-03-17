from pydantic import BaseModel, EmailStr

from app.types.alphasophia import Provider


class CreatePaymentIntentRequest(BaseModel):
    customer_email: EmailStr
    provider_name: str
    specialty_name: str
    client_provider: Provider
    miles_radius: int
