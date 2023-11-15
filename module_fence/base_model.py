from pydantic import BaseModel

from system.event_handler import EventHandlerConfig
from system.plc_controller import PLCControllerConfig

class LogicConfig(BaseModel):
    event_handler_config: EventHandlerConfig = None
    plc_controller_config: PLCControllerConfig = None