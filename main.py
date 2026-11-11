import microbit
import radio
import time

def center(self,length):
    return ((length-len(self))//2)*' ' + self + ((length-len(self))-(length-len(self))//2)*' '
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


class Radio:    
    def __init__(self):
        
        self.group = 0
    def config(self, plusminus:bool = True):
        radio.off()
        self.group = self.group-1+2*(plusminus)
        if self.group < 0 : self.group = 255
        elif self.group > 255 : self.group = 0
        radio.config(group=self.group, channel=81)
        radio.on()
        return self.group
    def send(self,data): 
        radio.send_bytes(data)
    def receive(self): 
        return radio.receive_bytes()
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
        self.offset = 0
        self.buffer = bytearray()
        self.digit = 0b1
        microbit.i2c.init(sda=microbit.pin19,scl=microbit.pin20)
        self.a=0
        while len(microbit.i2c.scan()) is not 1: microbit.sleep(100)
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
        self.buffer = bytearray()
        self.write(self.INIT[0],False,2000)
        for cmd in self.INIT[1:]: self.write(cmd,False)
    def cursor(self,RW:bool=True):
        self.init()
        if RW: self.write(self.CURSOR_R,False) 
        else : self.write(self.CURSOR_W,False)
    def print(self,string: str | bytearray | bytes, RW=True):
        self.cursor(RW)
        if isinstance(string,str):self.buffer = bytearray(string.encode("utf-8"))
        else: self.buffer = bytearray([Morse[digit].encode("utf-8") for digit in string])
        for i,digit in enumerate(self.buffer):
            if i<self.offset: continue
            if i==16+self.offset: self.write(self.LINE2,False)
            self.write(digit)
    def move(self,toRight=True,RW=True):
        self.offset += (-1+(2*toRight))*16
        if self.offset<0: self.offset += 16
        if self.offset*16>len(self.buffer): self.offset -= 16
        self.print(self.buffer,RW)
    def handshake(self,send:bool=True): 
        wave = ((9,8,7,8,9),(8,7,6,7,8),(7,6,5,6,7),(8,7,6,7,8),(9,8,7,8,9))
        result = str()
        for i in wave: 
            for j in i: result += str((j+self.a+(-1*int(send)))%10)
            result += ':'
        microbit.display.show(microbit.Image(result))
        microbit.sleep(15)
        self.a=(self.a+1)%10
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
    def receive(self, string:bytearray):
        return bytes([Morse[digit] for digit in string])
class Button: 
    NOPE =  0b00
    SHRT =  0b01
    LONG =  0b11
    cmd = [NOPE,LONG,SHRT,LONG]
    def __init__(self,func=microbit.button_a.is_pressed,thres:int=2000):
        self.state = [None,None]
        self.pressedTime = 0
        self.clockTime = time.ticks_ms()
        self.func = func
        self.thres = thres
    def update(self):
        state = self.func()
        if self.thres <= 0: raise ValueError 
        currentTime = time.ticks_ms()
        if state: self.pressedTime += time.ticks_diff(self.clockTime,currentTime)
        else: self.pressedTime = 0
        self.clockTime = currentTime
        self.state[1] = self.state[0]
        self.state[0] = self.cmd[(state<<1)|(self.pressedTime>=self.thres)]
        return self.state
    def __call__(self):
        self.update()
        if   self.state == [self.LONG,self.SHRT]:   return self.LONG
        elif self.state == [self.NOPE,self.SHRT]:   return self.SHRT
        else:                                       return self.NOPE
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
        val = (self.a()<<2)|(self.b())
        return self.LUT_RAW[val]
    def __call__(self): # 0b(A)(B)(L/S) -> [N,N,SB,LB,SA,LA,N,AB] -> self.LUT
        return self.LUT[self.update()]
class Status:
    def __init__(self,machine:Machine,controller:Controller, buffer:Buffer, display:Display, radio:Radio):
        self.activated = False
        self.reset = False
        self.clockTime, self.currentTime = time.ticks_ms()
        self.timer = 0
        self.machine, self.controller, self.buffer, self.display, self.radio = machine, controller, buffer, display, radio
    def wait(self,waitingTime):
        self.currentTime = time.ticks_ms()
        if time.ticks_diff(self.clockTime,self.currentTime)>=waitingTime: 
            self.clockTime = self.currentTime
            return True
        return False
    def toWait(self): 
        self.reset = True
        self.clockTime = time.ticks_ms()
    def n (self):               #대기
        if self.reset and self.wait(3000): 
            self.display.init()
            return True
    def __call__(self,prev:Status,n,sb,lb,sa,la,ab):
        if not self.activated:
            self.controller.lut(n,sb,lb,sa,la,ab)
            prev.activated = False
            self.activated = True
            self.display.init()
        self.controller()()
class Idle      (Status):
    def n (self):               #수신 대기
        super().n()
        if self.radio.receive() == bytes([self.machine.REQ]): self.machine.getRequest(self)
    sb_string = center("Radio Group +1",16)
    def sb(self):               #주파수 올리기
        self.radio.config(True)
        string = self.sb_string + center(("Current Group: "+str(self.radio.group)),16)
        self.display.print(string)
        self.toWait()
    def lb(self):               #발신시작
        self.display.init()
        return self.machine.send
    sa_string = center("Radio Group -1",16)
    def sa(self):               #주파수 내리기
        self.radio.config(False)
        string = self.sa_string + center(("Current Group: "+str(self.radio.group)),16)
        self.display.print(string)
        self.toWait()
    def la(self):               #발신시작
        return self.lb()
    def ab(self):               #발신시작
        return self.lb()
    def __call__(self,prev:Status):
        return super().__call__(prev,self.n,self.sb,self.lb,self.sa,self.la,self.ab)
class GetRequest(Status):
    def n (self):               #알림벨 노출 #TODO
        self.display.handshake(False)
        if super().n(): return self.machine.idle
    sb_string = center("[Rejected]",16)
    def sb(self):               #거절
        self.radio.send(bytes([self.machine.NACK]))
        self.display.print(self.sb_string)
        self.toWait()
    def lb(self):               #거절
        return self.sb()
    def sa(self):               #수신
        self.radio.send(bytes([self.machine.ACK]))
        return self.machine.receive
    def la(self):               #수신
        return self.sa()
    def ab(self):               #알림벨 노출
        return self.n()
    def __call__(self,prev:Status):
        return super().__call__(prev,self.n,self.sb,self.lb,self.sa,self.la,self.ab)
class Receive   (Status):
    def sb(self):               #다음 줄
        self.display.move(True)
    def lb(self):               #종료
        self.radio.send(self.machine.DONE)
        return self.machine.idle 
    def sa(self):               #이전 줄
        self.display.move(False)
    def la(self):               #종료
        return self.lb()
    def ab(self):               #종료
        return self.lb()
    def __call__(self,prev:Status):
        digits = self.radio.receive()
        self.display.print(digits)
        return super().__call__(prev,self.n,self.sb,self.lb,self.sa,self.la,self.ab)
class Send      (Status):
    def sb(self):               #선 입력
        self.buffer.add(True)
    def lb(self):               #다음 글자
        self.buffer.newDigit()
        self.display.print(self.buffer.string,False)
        lines = len(self.buffer.string)//16
        for _ in range(lines-1): self.display.move(True,False)
    def sa(self):               #점 입력
        self.buffer.add(False)
    def la(self):               #다음 글자
        return self.lb()
    def ab(self):               #작성 완료 및 발신
        self.lb()
        self.radio.send([self.machine.REQ])
        self.radio.send(self.buffer.send())
        self.display.print("Receiver is Reading Message...")
        while True: 
            self.display.handshake()
            if self.radio.receive() == self.machine.DONE: return self.machine.idle
    def __call__(self,prev:Status):
        return super().__call__(prev,self.n,self.sb,self.lb,self.sa,self.la,self.ab)
class Machine: 
    REQ = 19 #Early-Middle 1900's: The Age of You-Know-Where
    ACK = 33 #1933: The Arise
    NACK= 45 #1945: The Downfall
    DONE= 49 #1949: The Division
    def setup(self):
        self.controller = Controller(                                                           )
        self.buffer     = Buffer    (                                                           )
        self.display    = Display   (                                                           )
        self.radio      = Radio     (                                                           )
        self.idle       = Idle      ( self, self.controller,self.buffer,self.display,self.radio )
        self.getRequest = GetRequest( self, self.controller,self.buffer,self.display,self.radio )
        self.receive    = Receive   ( self, self.controller,self.buffer,self.display,self.radio )
        self.send       = Send      ( self, self.controller,self.buffer,self.display,self.radio )
        self.state = [self.idle, self.idle, self.idle]
    def loop(self):
        while True: 
            self.state[0] = self.state[1](self.state[2])
            self.state[2] = self.state[1]
            self.state[1] = self.state[0]
machine = Machine()
machine.setup()
machine.loop() 