from gpiozero import DigitalOutputDevice

class NegativeLogicRelay(DigitalOutputDevice):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, initial_value=True,  **kwargs)
    
    @property
    def value(self):
        return not super().value

    @value.setter
    def value(self, value):
        super().value = not value

    def on(self):
        super().off()

    def off(self):
        super().on()
