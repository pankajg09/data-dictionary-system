from sqlalchemy import Column, String, DateTime, func
from core.database import Base

class Configuration(Base):
    __tablename__ = 'configurations'

    key = Column(String, primary_key=True)
    value = Column(String, nullable=False)
    description = Column(String)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Configuration(key='{self.key}', value='***')>"

    @classmethod
    def get_value(cls, session, key: str, default=None):
        config = session.query(cls).filter(cls.key == key).first()
        return config.value if config else default

    @classmethod
    def set_value(cls, session, key: str, value: str, description: str = None):
        config = session.query(cls).filter(cls.key == key).first()
        if config:
            config.value = value
            config.updated_at = func.now()
            if description:
                config.description = description
        else:
            config = cls(key=key, value=value, description=description)
            session.add(config)
        session.commit()
        return config 