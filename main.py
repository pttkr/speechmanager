from PyQt5 import QtWidgets
from PyQt5.QtGui import QIcon, QPainter
import pyqtgraph as pg
import sys

from PyQt5.QtCore import QThread, QObject, pyqtSignal, Qt
from pyqtgraph.functions import disconnect
import AudioProcessing #音声処理用
import TextProcessing # テキスト処理用
import TextTime # テキスト表示管理

class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setWindowTitle('Speech Manager 0.0.1')
        self.setGeometry(100, 100, 1000, 1000)
        self.initUI()

        ### 音声処理スレッド　###
        # 外部スレッドからグラフを更新(graph.update(y))する
        self.audioThread = QThread()
        self.audioProcessing = AudioProcessing.AudioProcessingClass(self)
        self.audioProcessing.moveToThread(self.audioThread)

        self.audioThread.started.connect(self.audioProcessing.run)
        self.audioProcessing.updateSignal.connect(self.graph.update)
        self.audioProcessing.updateSignal.connect(self.realtime.update)
        self.audioProcessing.updateSignal_ave.connect(self.average.update)
        self.audioProcessing.updateSignal_ave.connect(self.graph.update_ave)

        # 外部スレッドからテキスト更新を行う
        self.textThread = QThread()
        self.textTime = TextTime.TextReplace(self)
        self.textTime.moveToThread(self.textThread)
        self.textThread.started.connect(self.textTime.run)
        self.textTime.updateSignal.connect(self.text.update)

        # テキスト上のどこを読むべきかを計算
        self.textnowThread = QThread()
        self.nowposition = TextTime.moveRect(self)
        self.nowposition.moveToThread(self.textnowThread)
        self.textnowThread.started.connect(self.nowposition.run)
        self.nowposition.updateSignal.connect(self.movepoint.update)

        self.audioThread.start()
        # self.textThread.start()
        # self.textnowThread.start()

    def initUI(self):
        # メニューバーのアイコン設定
        self.openFile = QtWidgets.QAction(QIcon('computer_folder.png'), 'Open', self)
        # ショートカット設定
        self.openFile.setShortcut('Ctrl+O')
        # ステータスバー設定
        self.openFile.setStatusTip('Open new File')
        self.openFile.triggered.connect(self.loadText)

        # メニューバー作成
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(self.openFile)   
        
        
        self.graph = graphWindow(self)
        self.graph.setGeometry(40, 40, 500, 300)
        self.realtime = nowWindow(self)
        self.realtime.setGeometry(600,20,100,300)
        self.average = averageNum(self)
        self.average.setGeometry(20,330,500,50)
        # 自分の声を聞くかどうか
        self.loopBackCheckBox = QtWidgets.QCheckBox("自分の声を聞く", self)
        def toggleLoopback():
            self.audioProcessing.loopback = not self.audioProcessing.loopback
        self.loopBackCheckBox.stateChanged.connect(toggleLoopback)
        self.loopBackCheckBox.setGeometry(20, 400, 500, 50)
        self.text = TextTime.textWindow(self)
        self.text.setGeometry(20, 500, 500, 50)

        # 動くバー
        self.movepoint = movePoint(self)
        self.movepoint.setGeometry(20, 530, 500, 50)


    def loadText(self):
        # 第二引数はダイアログのタイトル、第三引数は表示するパス
        fname = QtWidgets.QFileDialog.getOpenFileName(self, 'Open file', '/home')
        self.text.loadTextFromFile(fname)
        self.textTime.start = True
        self.nowposition.start = True


class graphWindow(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.graphWidget = pg.PlotWidget(self)
        self.graphWidget.setGeometry(0, 0, 500, 300)
        self.graphWidget.setYRange(0,7)

        self.x = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        self.y = [30, 32, 34, 32, 33, 31, 29, 32, 35, 45]
        self.initHorizontal = [0]*10

        # plot data: x, y values
        self.line = self.graphWidget.plot(self.x, self.y)
        self.horizontal = self.graphWidget.plot(self.x, self.initHorizontal)

    # 描画更新関数
    def update(self, x, y):
        print("update graph")
        print(x, y)
        self.line.setData(x,y)
    
    def update_ave(self, newAverage):
        print("update average graph")
        print(newAverage)
        self.horizontal.setData(self.x,[newAverage]*10)

class averageNum(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.label = QtWidgets.QLabel(f'<h3>average:{0.0}[mora/sec]</h3>', self)
        self.label.setGeometry(0, 0, 500, 50)


    # 描画更新関数
    def update(self, newAverage):
        print("update average")
        print(newAverage)
        self.label.setText(f'<h3>average:{round(newAverage,3)}[mora/sec]</h3>')

class nowWindow(QtWidgets.QWidget):
    def __init__(self,parent=None):
        super().__init__(parent)
        self.graphWidget = pg.PlotWidget(self)
        self.graphWidget.setGeometry(0, 0, 500, 300)
        x = [0]
        y = [5]
        self.bg = pg.BarGraphItem(x=x,height=y,width=0.5,brush='r')
        self.graphWidget.addItem(self.bg)
        self.graphWidget.setXRange(0,1)
        self.graphWidget.setYRange(0,7)
        self.graphWidget.setBackground("#ffff")
    
    def update(self, x, y):
        if y[-1]<4:
            self.bg.setOpts(height=[y[-1]],brush='g')
        else:
            self.bg.setOpts(height=[y[-1]],brush='r') 

class movePoint(QtWidgets.QWidget):
    def __init__(self,parent=None):
        super().__init__(parent)
        self.label = QtWidgets.QLabel('<h3>.</h3>', self)
        self.label.setGeometry(0, 0, 500, 50)
    def update(self,time:float):
        # self.painter.drawRect(10,10,10,10)
        print("------debug----time-------"+str(time))
        self.label.setGeometry(int(float(500/3)*time), 0,
                               500-int(float(500/3)*time), 50)
    def init_position(self):
        self.label.setGeometry(0, 0, 500, 50)
def main():
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())





if __name__ == '__main__':
    main()
