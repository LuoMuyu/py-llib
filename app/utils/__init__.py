# -*- coding: utf-8 -*-
from dotenv import load_dotenv

load_dotenv(override=True)

from .mysql import DatabaseManager
from .redis import Redis

db_manager = DatabaseManager()
r = Redis()
