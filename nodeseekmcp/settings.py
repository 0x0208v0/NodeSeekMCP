from __future__ import annotations

import os
from pprint import pprint

from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        extra='ignore',
        env_file=os.getenv('NODESEEKMCP_ENV', '.env'),
    )

    LOGGING_LEVEL: str = 'DEBUG'
    LOGGING_FORMAT: str = '[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s'

    SQLALCHEMY_ECHO: bool = False
    SQLALCHEMY_DATABASE_URI: str = 'sqlite+aiosqlite:///db.sqlite3'

    SECRET_KEY: str = 'NODESEEKMCP'
    PERMANENT_SESSION_LIFETIME_MINUTES: int = 10
    ALGORITHM: str = 'HS256'


settings = Settings()

if __name__ == '__main__':
    print(f'{os.getcwd()=}\n')

    pprint(settings.model_dump(), width=120)
