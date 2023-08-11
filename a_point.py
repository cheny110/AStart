

class Point:
    def __init__(self,x=0,y=0,parent=None,explored=False) -> None:
        self.x=x
        self.y=y
        self.parent=parent
        self.explored=explored
        self._g=0
        self._h=0
        self.f=0

    @property
    def g(self):
        return self._g

    def calF(self,point):
        self.f=self.calH(point)+self.calG()
        return self.f

    def calG(self):
        if self.parent is not None:
            if (abs(self.x-self.parent.x)+abs(self.y-self.parent.y)) ==2:
                gExtra=14
            else:
                gExtra=10
            self._g=+self.parent.g+gExtra
        else:
            self._g=0
        return self._g
    
    def calH(self,target):
        self._h=abs(self.x-target.x)*10+abs(self.y-target.y)*10
        return self._h
    
    def __eq__(self, __value: object) -> bool:
        return self.x==__value.x and self.y==__value.y  
        
    def __repr__(self) -> str:
        return f"x:{self.x},y:{self.y}"