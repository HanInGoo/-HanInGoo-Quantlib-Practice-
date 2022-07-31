#데이터 분석 및 데이터 시각화를 위해 필요한 라이브러리
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
###############################
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
        headers=['maturitys','days','price','coupon']  # 제목 리스트
        df.columns=headers # 각각의 열들의 제목을 붙여준다.
        df.set_index('maturitys',inplace=True) #maturities을 축으로 사용한다. 그러면 'days','price','coupons'는 값이 되지만 maturities는 인덱스가 된다.
        
        return df
       




def TREASURY_CURVE(eval_date,rate_table):
    
       # Divide Quotes 무이표채금리와 이표채 금리를 나눈다.
       tbill=rate_table[0:4] # 단기 채권 4개를 가져옴
       tbond=rate_table[4:] # 중장기 채권 6개를가져옴
    
       # Set Evaluation Date 오늘의 평가일자가 얼마인가를 퀀트립 자체에서 지정을 해줘야한다.
       eval_date=ql.Date(eval_date.day, eval_date.month,eval_date.year) # 함수 인자로 받은 eval_date는 사실 QuotelibDate 형식이 아니고 DateTime 형식이기 때문에 이 것을 다시 QuotelibDate 형식으로 바꿔야한다.
   
       # 퀀트립에서는 평가를 할때 항상 그 전역변수를 설정을 해서 아 오늘의 평가 일이 이 것이다라고 지정을 해줘야한다. 
       # 이것의 문법을 따로 불리해야한다.
       ql.Settings.instance().evaluationDate= eval_date # => 이 모듈은 오늘 이 순간 평가를 함에 있어서 평가일자의 기준을 이것으로 맞춰야 겠다는 것을 인지를 받게 된고
                                                         #    모든 평가와 모듈에는 이와 같이 첫머리에 평가일자를 설정해주는 작업이 필요하다.
                                                    
       # 평가일자를 지정해 주었고 평가 일자를 지정해준 다음에는
       # 실제 필요한 커브를 만드어야 한다.
       # 결국 DepositRateHelper와 FizedRateBondHelper가 필요한데 각각의 문법 구조가 복잡하다.
   
       # Set Market Convention 시장 관행을 설정(미국국채 시장 관행)
       calendar=ql.UnitedStates() #미국 달력을 설정해준다.
       convention=ql.ModifiedFollowing # 영업일 수의 휴일 처리
       dayCounter=ql.ActualActual() #이자일수를 어떤게 계산하는가
       endOfMonth=False # 거래일이 월말일 때 나중에 발생하는 이자 지급 일을 월말로 맞춰줄 것인가 아닌가 (맞춤:True/안맞춤:False)
       fixingDays= 1 # 다음이자 지급구간에 적용되는 금리가 오늘 설정할 것인가. 예를 들어서 오늘부터 6개월 동안에 이자지급구간을 설정 할때 거기에서 이제 해당하는 이자 금리 설정할때 
                     # 오늘에 fixing 되는 이자 금리를 쓸것인가 아니면은 하루전에 미리 fixing을 할 것인가 이틀전에 미리 fixing을 할 것인가 이것을 fixingdays라고 한다.
                     # (미국 시장관행은 하루이다.)
       faceAmount=100 # 우리나라의 국채 같은 경우는 표면가격이 만단위 이다. 미국 같은 경우는 표면가격이 100달러 단위이다.
       frequency= ql.Period(ql.Semiannual)  # 이자 지금주기 이 채권이 3개월 마다 이자를 지급하냐 6개월 마다 이자를 지급하냐
                                            # (미국은 6개월마다 이자를 지급한다.)
       dateGeneration=ql.DateGeneration.Backward #이자일수를 어떻게 생성할 것인가                                    
    
     
        
       # Construct Treasury Bill Helper 
       # 쿠폰값이 0인 4개의 데이터를 묶어서 금리커브를 만들기 위한 준비를 해준다.
       bill_helpers=[ql.DepositRateHelper(ql.QuoteHandle(ql.SimpleQuote(price/100.0)), #100을 나눠주는 이유는 price데이터는 %가 아닌 소수점으로 표기 되었기 때문에 이것을 %로 만들기 위해서다.
                                             ql.Period(maturity,ql.Days), #단기금리의 채권의 만기가 언제이냐~
                                             fixingDays,
                                             calendar,
                                             convention,
                                             endOfMonth,
                                             dayCounter)
      
                      for price,maturity in zip(tbill['price'],tbill['days'])] # zip은 어떤 일련의 데이터 세트들이 있을때 거기서 순서대로 하나하나씩 가지고 오는 것이다.
        
       # Construct Treasury Bond Helpers
       bond_helpers=[]
       for price,coupon,maturity in zip(tbond['price'], tbond['coupon'], tbond['days']):   
           maturity_date = eval_date + ql.Period(maturity,ql.Days) # 만기일자 생성    
           schedule= ql.Schedule(  # schedule 구현
                                 eval_date,      
                                 maturity_date,
                                 frequency,
                                 calendar,
                                 convention, # 이자 발생일수의 convention 어떻게 설정할 것인가
                                 convention, # 원금이 상환되는 원금상환 일의 convention은 어떻게 될것이가
                                 dateGeneration,
                                 endOfMonth)
           bond_helper=ql.FixedRateBondHelper(ql.QuoteHandle(ql.SimpleQuote(price)),
                                              fixingDays,
                                              faceAmount,
                                              schedule,
                                              [coupon/100.0], # 여기에서는 100을 나눠주지 않는 이유는 price데이터가 여기서는 100단위로 있기 때문에 할 필요가 없다. 
                                              dayCounter,
                                              convention)
           bond_helpers.append(bond_helper)
           
       # Bind Helper 헬퍼들을 함친다.
       rate_helper = bill_helpers + bond_helpers
       curve=ql.PiecewiseLinearZero(eval_date,
                                    rate_helper,
                                    dayCounter)
       
       return curve
   
#커브가 제대로 만들어 졌는지 확인한다.
def DISCOUNT_FACTOR(date,curve): # 할인계수
    date=ql.Date(date.day,date.month,date.year) # DateTime -> QuoteDate로 변경해준다.
    discount_factor=curve.discount(date) # cuvrve의 함수중에 discount를 이용
    return discount_factor

def ZERO_RATE(date,curve):
    date=ql.Date(date.day,date.month,date.year) # DateTime -> QuoteDate로 변경해준다.
    dayCount=ql.ActualActual()
    compounding=ql.Compounded # 복리방식을 어떻게 할것인가?(일반적인 복리방식을 사용)
    frequency=ql.Continuous # 이자 지급주기(연속복리 사용)
    zero_rate=curve.zeroRate(date,dayCount, compounding,frequency).rate() 

    return zero_rate

# 채권의 이론적 가치가 얼마가 될것인가
    
if __name__=="__main__": 
    eval_date=GET_DATE()
    rate_table=GET_QUOTE(eval_date)
    curve=TREASURY_CURVE(eval_date,rate_table)
    
    
    # 제일 궁금한거 각각의 채권들이 가지고 있는 할인계수 특정만기 시점의 할인계수와 특정만기 시점의 스팟금리가 궁금해서 할인계수와 스팟금리를 연결해서 선으로 나태내면 커브가 된다.
    # 여기서는 테이블을 만들어 시각화를 할것이다.
    rate_table['discount factor']=np.nan # np.nan는 테이블을 비워준다.
    rate_table['zero rate']=np.nan # np.nan는 테이블을 비워준다.
    
    for date in rate_table.index:
        rate_table.loc[date, 'discount factor']=DISCOUNT_FACTOR(date,curve) # loc는 로케이션을 뜻한다.
                                                                            # 해당 date(행)가 품고있는 discount factor의 열을 찾아라 
                                                                            # 이 값은 DISCOUNT_FACTOR함수를 이용하여  반복하여 각각에 만기에 맞는 할인계수들이 세로운 discount factor라는 열에 추가가 된다.
        rate_table.loc[date, 'zero rate']=ZERO_RATE(date, curve) # loc는 로케이션을 뜻한다.
                                                                 # 해당 date(행)가 품고있는 zero rate의 열을 찾아라 
                                                                 # 이 값은 ZERO_RATE함수를 이용하여  반복하여 각각에 만기에 맞는 zero rate들이 세로운 zero rate라는 열에 추가가 된다.
    
    ## Visualization 그래프 그리기
    # Zero Curve 그래프
    plt.figure(figsize=(10,8)) # 그래프의 사이즈
    plt.plot(rate_table['zero rate'],'b.-') # 직접이 데이터를 넣어줘서 plot을 하여라 
                                          # b는 색깔이고
                                          # -는 그래프의 타입이다.
    plt.title('Zero Curve',loc='center') # 그래프 제목 설정
                                         # 제목 Zero Rate
                                         # 위치는 가운데 (=center)
    plt.xlabel('Maturity') # x좌표 이름
    plt.ylabel('Zero Rate') # y좌표 이름


    # Discount Curve 그래프
    plt.figure(figsize=(10,8)) # 그래프의 사이즈
    plt.plot(rate_table['discount factor'],'r.-') # 직접이 데이터를 넣어줘서 plot을 하여라 
                                          # r는 색깔이고
                                          # -는 그래프의 타입이다.
    plt.title('Discount Curve',loc='center') # 그래프 제목 설정
                                         # 제목 Discount Curve
                                         # 위치는 가운데 (=center)
    plt.xlabel('Maturity') # x좌표 이름
    plt.ylabel('Discount Factor') # y좌표 이름     
    
    