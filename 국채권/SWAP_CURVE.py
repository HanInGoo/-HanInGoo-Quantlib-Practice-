import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
#데이터 분석 및 데이터 시각화를 위해 필요한 라이브러리
import datetime #날짜 관련된 라이브러리
                #실제계산은 퀀트립이 해주지만 나중에 엑셀로 빼주거나 다른 날짜 연산 할때 필요하다.
import QuantLib as ql
from bs4 import BeautifulSoup 
from selenium import webdriver
options=webdriver.ChromeOptions()#웹 드라이버에서 크롬을 사용하겠다는 것을 알려줌/ 크롬의 일반적인 옵션들을 가져옴
options.add_argument('headless')
#여기까지가 기본적으로 필요한 도구들이다.

def GET_DATE():
    date=ql.Date().todaysDate() # today's date
    one_day=ql.Period(1, ql.Days) # one day
    last_bday=date-one_day # 전날의 장을 알아봐야하기 때문에 오늘 날짜에서 하루를 뺀다.
    
    us=ql.UnitedStates() # 미국의 휴일을 제외한 영업일을 자동적으로 계산하기 위해
    
    while us.isBusinessDay(last_bday)==False: # 위에서의 last_bday가 휴일이면 영업일이 나올 때 까지 계속 하루를 반복적으로 빼주다가 영업일이 나와 True값이 되면 반복을 멈추고 last_bday에 나온 영업날짜를 대입한다.
        last_bday-=one_day
        
    date=datetime.date(last_bday.year(),        #퀀트립에서는 일, 월, 년 / datetime 함수에서는 년, 월, 일
                       last_bday.month(),
                       last_bday.dayOfMonth())
    return date

def GET_QUOTE(eval_date): #금리를 가져오는 함수
                          # eval_date는 월스트리저널에서 금리를 가져오는데 사용하는 것은 아니고 어떤 테이블을 만들때 특정시점의 금리가 만기가 몇일 남았냐를 계산해주기 위해서 평가 일(eval_date)이 필요한 것이다.
        driver=webdriver.Chrome('C:\chromedriver',options=options) # 크롬으로 부터 데이터를 가져올 준비
        tenors=['01M','03M','06M','01Y','02Y','03Y','05Y','07Y','10Y','30Y']
        
        # Create Empty Lists 받은 정보들을 이쁘게 담을 그릇
        maturities=[] # 만기별 데이터를 가져온다.
        days=[] # 이 채권의 만기가 몇일 남았냐
        prices=[] # 가격들
        coupons=[] # 각각 채권들이 가지고 있는 채권금리

        #Get Market Information 실제 데이터를 가져오는 것
        for i, tenor in enumerate(tenors): # enumerate을 사용하면 i에는 인덱스 값이 들어가게 되고 tenor에는 인덱스 안에 담긴 값(ex. 01M, 03M등)을 가져온다.
                driver.get("https://www.wsj.com/market-data/quotes/bond/BX/TMUBMUSD" + tenor + "?mod=md_bond_overview_quote")# 해당 사이트에 접속한다.
                html=driver.page_source # Source code 해당페이지 소스를 전부 가져온다.
                soup=BeautifulSoup(html) # 위에서의 from bs4 import BeautifulSoup를 한 이유는 page 소스를 그냥 출력하면 너무 난잡하게 출력된다. 하지만 BeautifulSoop를 사용하면 이쁘게 나온다.
                                        
                # Price 가격
                if i<=3: # 리스트에서 우리가 고려 할것은 coupon이 없는 1년이하 채권 부터이다. 그러므로 1년에 해당하는 인덱스 3을 기준으로 한다.
                    data_src=soup.find("span",id="quote_val") # coupon이 없는 채권의 Yield에 밑에있는 %값에 해당하는 소스코드에 있는 값을 가져온다.
                    # 하지만 가져온 %값은 숫자가 아니고 텍스트이기 때문에 우리는 이를 숫자로 바꿔준다.
                    price=data_src.text # (값)% 텍스트 이다. ex) 0.094% >> text no number
                    price=float(price[:-1]) # (값)% 실수 이다. ex) 0.94>> number
                else:# 여기에서는 우리가 고려 할것은 coupon이 있는 2년이상 채권 부터이다.  
                    data_src=soup.find("span", id="price_quote_val")
                    price=data_src.text # ex) 100 0/32
                    price=price.split() # ex) ["100", "0/32"]
                    price1=float(price[0]) # ex) 100 >> number
                    price= price[1].split('/') # ex) ["0","32"]     price를 다시 초기하 
                    price2=float(price[0]) # ex) 0 >> number
                    price3=float(price[1]) # ex) 32 >> number
                    price=price1+price2/price3 # ex) 100 + 0/32    price를 다시 초기화
                    
                # Coupon 쿠폰
                data_src2=soup.find_all("span", class_="data_data") # data_data 클래스가 페이지 소스코드에 정말많이 존재한다. find_all는 이를 모두 찾아온다.
                
                coupon=data_src2[2].text # 그 모두 찾아온 data_data 클래스중에 3번째 것을 가져온다 (3번째를 인덱스로하면 2이다.)
                if coupon !='': # coupon이 존재하는 2년 이상
                    coupon=float(coupon[:-1]) # 텍스트 값을 숫자 값으로 변경해준다. ex) 0.125 >> number
                else: # coupon이 존재하지 않는 1년 이하 
                    coupon=0.0
                
                # Maturity Date 만기일자
                maturity=data_src2[3].text # 그 모두 찾아온 data_data 클래스중에 4번째 것을 가져온다 (4번째를 인덱스로하면 3이다.)
                maturity=datetime.datetime.strptime(maturity, '%m/%d/%y').date() # strptime는 해당 텍스트의 형식을 날짜에 맞게하여 저장을 해준다. 년도가 2자리이면 소문자 y, 년도가 4자리이면 대문자 Y를 쓴다.
                
                
                # Spand to Lists 
                days.append((maturity-eval_date).days) # 이 채권의 만기가 몇일 남았냐를 리스트에 입력
                prices.append(price)
                coupons.append(coupon)
                maturities.append(maturity)
        
        #Create DateFrame : 4가지를 모두 합쳐서 데이터 프레임을 만들어 줄 것이다.
        df=pd.DataFrame([maturities,days,prices,coupons ] ).transpose() #transpose는 maturities,days,price,coupons 90도로 회전 시켜준다.
        headers=['maturities','days','price','coupons']  # 제목 리스트
        df.columns=headers # 각각의 열들의 제목을 붙여준다.
        df.set_index('maturities',inplace=True) #maturities을 축으로 사용한다. 그러면 'days','price','coupons'는 값이 되지만 maturities는 인덱스가 된다.
        
        return df
        
        
        
        
                
if __name__=="__main__": 
    eval_date=GET_DATE()
    rate_table=GET_QUOTE(eval_date)
    
    
    