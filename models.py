from sqlalchemy import Column, Integer, String
from database import Base


class InstallationRequest(Base):

    __tablename__ = "requests"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(100), nullable=False)

    phone = Column(String(15), nullable=False)

    email = Column(String(100), nullable=True)

    place = Column(String(100), nullable=False)

    purpose = Column(String(200), nullable=False)

    users = Column(String(50), nullable=False)

    message = Column(String(500), nullable=True)

    status = Column(
        String(20),
        default="Pending"
    )