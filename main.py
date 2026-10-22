import microbit
import radio
nah = None
M_LUT = [
    nah,nah,'E','T','I',
    'A','N','M','S','U',
    'R','W','D','K','G',
    'O','H','V','F',nah,
    'L',nah,'P','J','B',
    'X','C','Y','Z','Q'
] + [nah]*228
M_etc = {
    32  : '5'   ,
    33  : '4'   ,
    35  : '3'   ,
    39  : '2'   ,
    47  : '1'   ,
    48  : '6'   ,
    50  : '/'   ,
    54  : '('   ,
    56  : '7'   ,
    60  : '8'   ,
    62  : '9'   ,
    63  : '0'   ,
    76  : '?'   ,
    85  : '.'   ,
    95  : "'"   ,
    96  : '-'   ,
    109 : ')'   ,
    115 : ','   ,
    120 : ':'   ,
    256 : False
}
for i in M_etc.keys(): 
    M_LUT[i] = M_etc[i]
Morse = tuple(M_LUT)
del M_LUT, M_etc, nah


class Radio:    
    def __init__(self):
        self.group = 0
    def config(self, plusminus:bool = True):
        self.group = self.group+1-2*(plusminus)
        if self.group < 0 : self.group = 255
        elif self.group > 255 : self.group = 0
        radio.config(group=self.group, channel=81)
    def send(self,data: bytearray): 
        radio.send_bytes(data)
    def receive(self): 
        digits = radio.receive_bytes()
        if digits is not None: return digits
class Display:
    def error(self): microbit.display.show(microbit.Image.SAD)
    def show(self,digit): microbit.display.show(Morse[digit])
class Buffer:
    def __init__(self): 
        self.digit = 0b1
        self.string = bytearray()
    def add(self,bit:bool): 
        if self.digit < 256:
            self.digit = (self.digit << 1) | int(bit)
        else: raise ValueError('Digit Size Overflow')
        if Morse[self.digit] is not None: return self.digit

def setup():
    radio.on()

def loop(): 
    pass