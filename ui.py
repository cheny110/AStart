from typing import Optional
from PySide6.QtGui import QGuiApplication,QPainter,QPaintEvent,QBrush,QPen,QColor,QMouseEvent
from PySide6.QtWidgets import QPushButton,QLabel,QWidget,QMainWindow
from PySide6.QtCore import Qt,QRectF
import numpy as np
from a_point import Point
from numba import jit

class ChessWindow(QMainWindow):
    SetObstacle=1
    SetStartPoint=2
    SetEndPoint=3
    def __init__(self, parent: QWidget=None ) -> None:
        super().__init__(parent)
        self.setFixedSize(800,640)
        self.pen=QPen()
        self.pen.setWidth(1)
        self.pen.setColor("#000000") #black
        self.pen.setCapStyle(Qt.PenCapStyle.FlatCap)
        #self.map=np.zeros((30,30),np.int8)
        self.map:np.ndarray=np.load("./map.npy")

        self.mode=self.SetObstacle

        self.pushButtonSave=QPushButton(self)
        self.pushButtonSave.setGeometry(700,40,80,40)
        self.pushButtonSave.setText("Save Map")
        self.pushButtonCal=QPushButton(self)
        self.pushButtonCal.setGeometry(700,100,80,40)
        self.pushButtonCal.setText("Calculate")
        self.pushButtonSave.clicked.connect(self.saveMap)
        self.pushButtonSetStart=QPushButton(self)
        self.pushButtonSetStart.setGeometry(700,160,80,40)
        self.pushButtonSetStart.setText("Set Start")
        self.pushButtonSetEnd=QPushButton(self)
        self.pushButtonSetObstacle=QPushButton(self)
        self.pushButtonSetEnd.setGeometry(700,220,80,40)
        self.pushButtonSetObstacle.setGeometry(700,280,80,40)
        self.pushButtonSetEnd.setText("Set End")
        self.pushButtonSetObstacle.setText("Set Obstacle")
        self.pushButtonSetStart.clicked.connect(self.changeMode)
        self.pushButtonSetEnd.clicked.connect(self.changeMode)
        self.pushButtonSetObstacle.clicked.connect(self.changeMode)
        self.pushButtonCal.clicked.connect(self.calPath)
        self.startPoint=None
        self.endPoint=None
        self.openList=[]
        self.closeList=[]
        self.initPointFromMap()


    def initPointFromMap(self):
        for i in range(self.map.shape[0]):
            for j in range(self.map.shape[1]):
                if self.map[i][j]==self.SetStartPoint:
                    self.startPoint=Point(i,j,None)
                elif self.map[i][j]==self.SetEndPoint:
                    self.endPoint=Point(i,j,None)
                elif self.map[i][j]==4:
                    self.map[i][j]=0 #reset path to nuknown


        
    def paintEvent(self, a: QPaintEvent) -> None:
        padding=20
        cells=30
        painter=QPainter(self)
        self.borderLength=borderLength= self.width()-padding*2 if self.width()<self.height() else self.height()-padding*2
        painter.setPen(self.pen)
        for i in range(0,cells):
            for j in range(0,cells):
                if self.map[i][j]==0:   #empty
                    color=QColor(169,169,169)
                elif self.map[i][j]==1: #obstacle
                    color=QColor(128,128,0)
                elif self.map[i][j]==2:
                    color=QColor(0,255,255)
                elif self.map[i][j]==3:
                    color=QColor(138,43,226)
                elif self.map[i][j]==4:
                    color=QColor(34,139,34)

                painter.fillRect(QRectF(i*(borderLength//cells)+padding,j*(borderLength//cells)+padding,(borderLength//cells),(borderLength//cells)),color)
        for i in range(padding,borderLength+padding,borderLength//cells):
            painter.drawLine(padding,i,borderLength+padding,i)
            painter.drawLine(i,padding,i,borderLength+padding)
        painter.end()
        self.update()
    
    def mousePressEvent(self, event: QMouseEvent) -> None:
        padding=20
        cells=30
        x,y=event.x(),event.y()
        m=(x-padding)//(self.borderLength//cells)
        n=(y-padding)//(self.borderLength//cells)
        if event.button()==Qt.MouseButton.LeftButton:
            if self.mode==self.SetObstacle :
                self.map[m,n]=1
            elif self.mode==self.SetStartPoint:
                self.map[m,n]=2
                if self.startPoint is not None:
                    self.map[self.startPoint.x,self.startPoint.y]=0
                self.startPoint=Point(m,n,None)
                    
            elif self.mode==self.SetEndPoint:
                self.map[m,n]=3
                if self.endPoint is not None:
                    self.map[self.endPoint.x,self.endPoint.y]=0
                self.endPoint=Point(m,n,None)

        elif event.button() == Qt.MouseButton.RightButton:
            self.map[m,n]=0
            if self.startPoint.x==m and self.startPoint.y==0:
                self.startPoint=None
            elif self.endPoint.x==m and self.endPoint.y==0:
                self.endPoint=None

    def saveMap(self):
        np.save("./map",self.map)

    def changeMode(self):
        sender:QPushButton=self.sender()
        if sender.text()=="Set Start":
            self.mode=self.SetStartPoint
        elif sender.text()=="Set End":
            self.mode=self.SetEndPoint
        elif sender.text()=="Set Obstacle":
            self.mode=self.SetObstacle

    @jit
    def calPath(self):
        assert(self.startPoint is not None and self.endPoint is not None)
        self.closeList.clear()
        self.openList.clear()
        self.clearPathFromMap()
        self.openList.append(self.startPoint)
        while len(self.openList)!=0:
            # end loop condition
            if self.closeList.count(self.endPoint)>0:
                break
            curPoint= self.getLeastFPoint()
            self.closeList.append(curPoint)
            self.openList.remove(curPoint)
            surrounds=self.getSurroundingPoint(curPoint)
            
            for pt in surrounds:
                if not self.isInOpenList(pt):
                    pt.parent=curPoint
                    pt.calF(self.endPoint)
                    self.openList.append(pt)
                else:
                    if curPoint.calF(pt)<pt.g:
                        pt.parent=curPoint
                        pt._g=curPoint.f
                        pt.f=pt.g+pt.calH(self.endPoint)
        self.drawPath()
    
    def drawPath(self):
        for p in self.closeList:
            if p==self.endPoint:
                mPoint=p
                break
        prePoint=mPoint.parent
        while prePoint != self.startPoint:
            self.map[prePoint.x,prePoint.y]=4
            mPoint=prePoint
            prePoint=mPoint.parent


    
    @jit
    def getSurroundingPoint(self,curPoint, ignoreCorner=False)->list[Point]:
        surrounds=[]
        for i in range(curPoint.x-1,curPoint.x+2):
            for j in range(curPoint.y-1,curPoint.y+2):
                if self.canSearch(Point(i,j),curPoint,ignoreCorner):
                    surrounds.append(Point(i,j,curPoint))
        return surrounds

    def canSearch(self,point:Point,curPoint,ignoreCorner:bool=True)->bool:
        if point.x<0 or point.y<0:
            return False
        elif point.x>29 or point.y>29:
            return False
        if self.closeList.count(point)!=0:
            return False
        if curPoint==point:
            return False
        
        #strip obstacle points
        if self.map[point.x,point.y]==self.SetObstacle:
            return False

        
        if abs(point.x-curPoint.x)+abs(point.y-curPoint.y) ==1:
            return True
        elif abs(point.x-curPoint.x)+abs(point.y-curPoint.y) ==2:
            return  ignoreCorner
        
    @jit
    def getLeastFPoint(self):
        targetP:Point=self.openList[0]
        targetP.calF(self.endPoint)
        for p in self.openList:
            if p.f<targetP.f:
                targetP=p
        return targetP
    
    @jit
    def clearPathFromMap(self):
        for i in range(self.map.shape[0]):
            for j in range(self.map.shape[1]):
                if self.map[i][j]==4:
                    self.map[i][j]=0
    
    @jit
    def isInOpenList(self,pt:Point):
        for op in self.openList:
            if op==pt:
                return True
        return False
