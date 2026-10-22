import microbit
import radio
radioChannel = 0
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

def radioConfig(plusminus:bool = True):
    global radioChannel
    radioChannel = radioChannel+1-2*(plusminus)
    if radioChannel < 0 : radioChannel = 255
    elif radioChannel > 255 : radioChannel = 0
    radio.config(group=23)
def read(digit): microbit.display.show(Morse[digit])
def send(data: bytearray): radio.send_bytes(data)
def receive(digits: bytearray):return [Morse[i] for i in digits]
def setup():
    radio.on()
def loop(): 
    pass