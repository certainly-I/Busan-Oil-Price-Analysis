# class에서 show 불러와서 실행
import sys
from PyQt5 import uic
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from urllib.parse import quote
import urllib.request  # URL openAPI 검색위해
import json  # 검색결과를 json 타입으로 받음
import webbrowser # 웹브라우저 열기위한 패키지
import pandas as pd


# 클래스 OOP
class qTemplate(QWidget):
    start = 1 # api호출할 때 시작하는 데이터 번호
    max_display = 100 # 한페이지에 나올 데이터 수 지정
    saveResult = [] # 저장할 때 담을 데이터 (딕셔너리 리스트) -> DataFrame
    prevSearch = ''

    # 생성자
    def __init__(self) -> None: # class는 함수 자신을 지정해야한다. exec -> 생성자는 보통 return 값이 없다. None / str이면 return을 str로 해야한다.
        super().__init__() # QWidget에 있는걸 호출
        uic.loadUi('./navernews_2.ui',self)
        self.initUI()
    
    def initUI(self) -> None:
        self.addControls()
        self.show()

    def addControls(self) -> None: # 위젯 정의, 이벤트(시그널) 처리
        self.btnSearch.clicked.connect(self.btnSearchClicked) # 시그널 연결
        self.txtSearch.returnPressed.connect(self.btnSearchClicked) # 다시 검색하면 리셋하고 나타내줌
        self.tblResult.itemSelectionChanged.connect(self.tblResultSelected) # 결과창에 클릭해서 웹페이지 나타나게 해줌
        # 22.08.18 이전 소스에서 추가한 버튼 이벤트(시그널) 확장
        self.btnNext.clicked.connect(self.btnNextClicked)
        self.btnSave.clicked.connect(self.btnSaveClicked)
    
    def btnNextClicked(self) -> None: # 다음페이지로 넘기기
        self.start = self.start + self.max_display
        self.btnSearchClicked()

    def btnSaveClicked(self) -> None:
        if len(self.saveResult) > 0:
            df = pd.DataFrame(self.saveResult)
            df.to_csv(f'./data/{self.txtSearch.text()}_뉴스검색결과.csv', encoding='utf-8', index=True)
        
        QMessageBox.information(self, '저장', '저장완료!')
        # 저장 후 모든 변수 초기화(초기화를 잘해줘야.. 안하면 다 섞임)
        self.saveResult = []
        self.start = 1
        self.txtSearch.setText('')
        self.lblStatus.setText('Data : ')
        self.lblStatus2.setText('저장할 데이터 > 0개')
        self.tblResult.setRowCount(0)
        self.btnNext.setEnabled(True) # 여기까지 ------> 결과창 초기화
    
    def tblResultSelected(self) -> None:
        selected = self.tblResult.currentRow() # 현재 선택된 열의 인덱스
        link = self.tblResult.item(selected, 1).text()
        webbrowser.open(link)

    def btnSearchClicked(self)-> None: # 슬롯(이벤트핸들러) 
        jsonResult = [ ]
        totalResult = [ ]
        keyword = 'news'
        search_word = self.txtSearch.text( )
        # display_count = 50
       

        # QMessageBox.information(self, '결과', search_word)
        jsonResult = self.getNaverSearch(keyword, search_word, self.start, self.max_display)
        # print(jsonResult)

        for post in jsonResult['items']:
            totalResult.append(self.getPostData(post))
        
        # print(totalResult)
        self.makeTable(totalResult) # 앱의 창으로 불러들임

        # saveResult 값 할당, lblStatus /2 상태값을 표시
        total = jsonResult['total']
        curr = self.start + self.max_display - 1

        self.lblStatus.setText(f'Data : {curr} / {total}')

        # saveResult 변수에 저장할 데이터를 복사
        for post in totalResult:
            self.saveResult.append(post[0])

        self.lblStatus2.setText(f'저장할데이터 > {len(self.saveResult)}개')

        if curr >= 1000 :
            self.btnNext.setDisabled(True) # 다음버튼 비활성화
        else:
            self.btnNext.setEnabled(True) # 다음버튼 활성화

    def makeTable(self, result):
        self.tblResult.setSelectionMode(QAbstractItemView.SingleSelection) # qtdesigner 에서 수정가능
        self.tblResult.setColumnCount(3)
        self.tblResult.setRowCount(len(result)) # displayCount에 따라서 변경, 현재는 50
        self.tblResult.setHorizontalHeaderLabels(['기사제목','뉴스링크','기사날짜'])
        self.tblResult.setColumnWidth(0, 350)
        self.tblResult.setColumnWidth(1, 100)
        self.tblResult.setColumnWidth(2, 100)
        self.tblResult.setEditTriggers(QAbstractItemView.NoEditTriggers) # readonly

        i = 0
        for item in result:
            title = self.strip_tag(item[0]['title'])
            link = item[0]['originallink']
            pubDate = item[0]['pubDate']
            self.tblResult.setItem(i, 0, QTableWidgetItem(title))
            self.tblResult.setItem(i, 1, QTableWidgetItem(link))
            self.tblResult.setItem(i, 2, QTableWidgetItem(pubDate))
            i += 1

    def strip_tag(self, title): # html 태그를 없애주는 함수
        ret = title.replace('&lt;', '<')
        ret = ret.replace('&gt;', '>')
        ret = ret.replace('&quot;', '"')
        ret = ret.replace('&apos;', "'")
        ret = ret.replace('&amp;', '&')
        ret = ret.replace('<b>', '')
        ret = ret.replace('</b>', '')
        return ret
    
    def getPostData(self, post):
        temp = []
        title = self.strip_tag(post['title'])
        description = self.strip_tag(post['description'])
        originallink = post['originallink']
        link = post['link']
        pubDate = post['pubDate']

        temp.append({'title':title, 'description':description, 'originallink':originallink, 'link':link, 'pubDate':pubDate})

        return temp

    #네이버 API 크롤링 함수
    def getNaverSearch(self, keyword, search, start, display): # 돌려주는 값 json
        url = f'https://openapi.naver.com/v1/search/{keyword}.json' \
              f'?query={quote(search)}&start={start}&display={display}&sort=sim'
              
        print(url)
        req = urllib.request.Request(url)
        # 네이버 인증 추가
        req.add_header('X-Naver-Client-Id', 'JqpkgFJJbXWXTzhAEa4i')
        req.add_header('X-Naver-Client-Secret', 'tSLsq0RhsE')

        res = urllib.request.urlopen(req) # request 대한 response
        if res.getcode() == 200:
            print('URL request success')
        else:
            print('URL request failed')

        ret = res.read().decode('utf-8') # return
        if ret == None:
            return None
        else:
            return json.loads(ret)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ins = qTemplate()
    app.exec_()

