from typing import Optional
from ninja import Schema

from pydantic import ConfigDict, Field

class _FlexibleSchema(Schema):
    """Izinkan field tambahan (agar payload gaya GET DASA tetap terbaca)."""
    model_config = ConfigDict(extra='allow')

class ApiMessage(Schema):
    status: str = 'success'
    message: str
    data: Optional[dict] = None
