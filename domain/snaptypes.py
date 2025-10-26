from enum import Enum

# Enumeration to hold the type desription of the snapshot as a global variable
class SnapType(Enum):
    EMPTY = ("UNKNOWN", "Unknown Snapshot Type")
    ECU_V1 = ("ECU_V1", "Bobcat V1 Engine (Delphi ECU)")
    DCU_V1 = ("DCU_V1", "Bobcat V1 Engine SCR System (Bosch DCU)")
    EUD_V1 = ("EUD_V1", "Bobcat V1 Engine Use Data")
    ECU_V2 = ("ECU_V2", "Bobcat V2 Engine (Bosch ECU)")
    EUD_V2 = ("EUD_V2", "Bobcat V2 Engine Use Data")

    def __init__(self, type: str, description: str):
        # Initialize the enumeration with a tuple
        # type of snap and plain word description for labels
        self.type = type
        self.description = description

    def __str__(self):
        '''Return a description as string'''
        #Overrides the string type
        # when I call the string of this enumeration
        # I'll get the description from the tuple
        return self.description