'''
    Machine Class 

    The purpose of this class is to handle everything there is
    to do with a machine, including how to handle opening and
    writing from and to the machine.

    Machines have a function: receive

    The purpose of this function is to receive gcode from
    an emitter class and  to write it to the machine, that
    includes managing any buffering etc.
'''
class Machine:
    def __init__(self, name="", path=""):
        self.path = path
        self.name = name
        ''' 
            [ btype, diameter, distance, currentdistance ]
            The third element is for tracking our current distance
            from the original distance, for if we start a 5mm from
            the material, and we move 6mm (1mm below the surface) this
            is so that we can reverse the bit and put it back, or advance
            etc as we please.
        '''
        self.bit = ["flat", 6, 0, 0]
        
    '''
    mat: wood_hard, wood_soft which helps to decide the speed.
    w,h,d: width, height, depthe in mm
    '''
    def material(mat=False,w=False,h=False,d=False):
        if not mat and not w and not h and not d:
            return self.material
        else:
            if mat: 
                self.material[0] = mat
            if w:
                self.material[1] = w
            if h:
                self.material[2] = h
            if d:
                self.material[3] = d
                    
    def receive(self,txt):
        fd = os.open(self.path,os.O_WRONLY | os.O_CREAT)
        os.write(fd, txt + "\n")
        os.fsync(fd)
        os.close(fd)
        
    '''
        Bit btypes are: flat round v20 v90 etc
        Bit size is always in mm diameter
        Bit dist is the distance from the tippy tip of the bit to the top of
        the material to be routed.
    '''
    def bit(size=False, btype=False, dist=False):
        if not size and not btype and not dist:
            return self.bit
        else:
            if btype:
                    self.bit[0] = btype
            if size:
                    self.bit[1] = size
            if dist:
                    self.bit[2] = dist