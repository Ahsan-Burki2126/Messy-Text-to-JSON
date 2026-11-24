from pydantic import BaseModel

class Extracted(BaseModel):

    event_name : str
    event_date : str | None = None
    event_time : str | None = None
    event_venue : str | None = None
    event_city : str | None = None
    event_price : str | None = None
    registration_required : bool | None = None
    