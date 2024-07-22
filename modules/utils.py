# utils.py
from modules.rest_modules.rest_utils.resource_manager import ResourceManager, resource_manager

async def get_resource_manager() -> ResourceManager:
    return resource_manager
