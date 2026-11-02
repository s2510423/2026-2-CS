import microbit
import radio
import time
if not hasattr(time, "sleep_us"):
    time.sleep_us = lambda us: time.sleep(us / 1000000.0)

nah = None
M_LUT = [
    nah,' ','E','T','I',
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
    256 : True  ,
} 
for i in M_etc.keys(): 
    M_LUT[i] = M_etc[i]
Morse = tuple(M_LUT)
del M_LUT, M_etc, nah

def handshake(send:bool=True): 
    wave = ((9,8,7,8,9),(8,7,6,7,8),(7,6,5,6,7),(8,7,6,7,8),(9,8,7,8,9))
    while True:
        for a in range(0,10):
            result = str()
            for i in wave: 
                for j in i: result += str((j+a+(-1*int(send)))%10)
                result += ':'
            microbit.display.show(microbit.Image(result))
            microbit.sleep(15)

class Radio:    
    def __init__(self):
        self.group = 0
    def config(self, plusminus:bool = True):
        self.group = self.group-1+2*(plusminus)
        if self.group < 0 : self.group = 255
        elif self.group > 255 : self.group = 0
        radio.config(group=self.group, channel=81)
        return self.group
    def send(self,data: bytearray): 
        radio.send_bytes(data)
    def receive(self): 
        digits = radio.receive_bytes()
        return digits
class Display: #으흐흐흐 출처불명입니다 히히히
    BK      = 0b1000
    # backLight
    EN      = 0b0100
    # enable
    DT      = 0b0001
    # data
    CLEAR   = bytes([0b0000,0b0001]) # Requires 2ms(2000 us) of Delay.
    # clearDisplay
    FUNC    = bytes([0b0010,0b1000])
    # functionInitializetaion: 4-bit, 2-line, 5*8dot-font
    ENTRY   = bytes([0b0000,0b0110])
    # entryModeSet: left to right
    CURSOR_W= bytes([0b0000,0b1111])
    # displayAndCursorSet: display-on, cursor-on,  cursor-block-blink-on
    CURSOR_R= bytes([0b0000,0b1100])
    # displayAndCursorSet: display-on, cursor-off, cursor-block-blink-off
    LINE1   = bytes([0b1000,0b0000])
    # moveToLine1
    LINE2   = bytes([0b1100,0b0000])
    # moveToLine2
    SPACE   = bytes([0b0001,0b0100])
    # goToNextColon
    BACK    = bytes([0b0001,0b0000])
    # goToPreviousColon
    INIT    = (CLEAR, ENTRY, FUNC)
    
    def __init__(self):
        self.buffer = bytearray()
        self.digit = 0b1
        microbit.i2c.init(sda=microbit.pin0,scl=microbit.pin1)
        self.addr = microbit.i2c.scan()[0]
        self.init()        
    def error(self): microbit.display.show(microbit.Image.SAD)
    def write(self,char: int,is_data:bool=True,wait:int=5):
        if char < 0 or char > 128: raise ValueError
        byte = (
            char & 0b11110000,
            (char & 0b1111) << 4
            )
        if is_data: nbl = self.BK|self.DT
        else: nbl = self.BK
        for nibble in byte:
            microbit.i2c.write(self.addr,bytes([nibble|nbl|self.EN]))
            time.sleep_us(1)
            microbit.i2c.write(self.addr,bytes([nibble|nbl]))
            time.sleep_us(wait)
    def init(self): 
        self.write(self.INIT[0],False,2000)
        for cmd in self.INIT[1:]: self.write(cmd,False)
    def cursor(self,RW:bool=True):
        self.init()
        if RW: self.write(self.CURSOR_R,False) 
        else : self.write(self.CURSOR_W,False)
    def print(self,string: str | bytearray | bytes,RW:bool=True):
        self.cursor(RW)
        if type(string) == str: 
            tmpstring = string
            string = bytearray()
            for char in tmpstring: string.append(ord(char))
        for count, char in enumerate(string): 
            if count == 16: self.write(self.LINE2,False)
            self.write(char)
class Buffer:
    def __init__(self): 
        self.digit = 0b1
        self.string = bytearray()
    def add(self,bit:bool): 
        if self.digit <= 128:
            self.digit = (self.digit << 1) | int(bit)
        else: raise ValueError('Digit Size Overflow')
        return self.digit
    def newDigit(self):
        digit = Morse[self.digit]
        if digit == True: self.string.pop()
        elif digit: self.string.append(self.digit)
        self.digit = 0b1
    def send(self): 
        string = self.string
        self.string = bytes()
        return string
    def receive(self, string: bytearray):
        return bytes([Morse[digit] for digit in string])

class Button: 
    NOPE =  0b00
    SHRT =  0b01
    LONG =  0b11
    cmd = [NOPE,LONG,SHRT,LONG]
    def __init__(self,func=microbit.button_a.is_pressed,thres:int=2000):
        self.state = [None,None]
        self.pressedTime = 0
        self.clockTime = microbit.running_time()
        self.func = func
        self.thres = thres
    def update(self):
        state = self.func()
        if self.thres <= 0: raise ValueError
        currentTime = microbit.running_time()
        if state: self.pressedTime += currentTime - self.clockTime
        else: self.pressedTime = 0
        self.clockTime = currentTime
        self.state[1] = self.state[0]
        self.state[0] = self.cmd[(state<<1)|(self.pressedTime>=self.thres)]
        return self.state
    def getstate(self):
        state = self.update()
        if self.state[0] == self.LONG: return self.LONG
        elif self.state == [self.NOPE,self.SHRT]: return self.SHRT
        else: return self.NOPE
class Controller:
    N = 0b000
    B = 0b010
    A = 0b100
    S =   0b0
    L =   0b1
    """
    __________________________
    | ab | binary | n  | CMD |
    |____|________|____|_____|
    |    |        |    |     |
    | nn | 0b0000 | 0  |  NO |
    | ns | 0b0001 | 1  |  SB |
    | nl | 0b0011 | 3  |  LB |
    | sn | 0b0100 | 4  |  SA |
    | ss | 0b0101 | 5  |  NO |
    | sl | 0b0111 | 7  |  AB |
    | ln | 0b1100 | 12 |  LA |
    | ls | 0b1101 | 13 |  AB |
    | ll | 0b1111 | 15 |  AB |
    |____|________|____|_____|
    """
    LUT_RAW = (
        N,      #00
        S|B,    #01
        N,      #02
        L|B,    #03
        S|A,    #04
        N,      #05
        N,      #06
        L|A|B,  #07
        N,      #08
        N,      #09
        N,      #10
        N,      #11
        L|A,    #12
        L|A|B,  #13
        N,      #14
        L|A|B   #15
    )
    def __init__(self):
        self.a, self.b = Button(),Button(microbit.button_b.is_pressed)
        self.lut(0,1,2,3,4,5)
    def lut(self,N,SB,LB,SA,LA,AB):
        self.N  = N
        self.SB = SB
        self.LB = LB
        self.SA = SA
        self.LA = LA
        self.AB = AB
        self.LUT = [self.N,self.N,self.SB,self.LB,self.SA,self.LA,self.N,self.AB]
    def update(self): # 0b(A: {Long:11}/{Short:01}/{No:00})(B: sameAsA) -> self.LUT_RAW
        val = (self.a.getstate()<<2)|(self.b.getstate())
        return self.LUT_RAW[val]
    def getstate(self): # 0b(A)(B)(L/S) -> [N,N,SB,LB,SA,LA,N,AB] -> self.LUT
        return self.LUT[self.update()]
        
def setup():
    radio.on()

def loop(): 
    pass