import datetime #시간을 다루기위한 라이브러리
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt #시각화를 위한 라이브러리
import seaborn as sns #matplotlib을 좀 더 이쁘게 만들어주는 라이브러리
sns.set() #seaborn으로 처음부터 사용하겠다는 의미

import QuantExt as qe
import xlwings as xw

#원화 스왑금리커브의 데이터 형태와 달러 스왑금리커브의 데이터 형태가 다르기 때문에 이를 따로 구분하여 데이터를 받아와야한다.
# Get Quote from Excel File
def GET_QUOTE(today, ticker):
    
    xw.App(visible=False)
    wb=xw.Book(r'./FX_CURVE.xlsx')
    
    if ticker =='USD':
        sht=wb.sheets('USDIRS')
        curve=sht.range('A1:D25').options(pd.DataFrame).value
        
    elif ticker=='KRW':
        sht=wb.sheets('KRWCCS')
        curve=sht.range('A1:D15').options(pd.DataFrame).value
    
    wb.close()
    
    #우리에게 필요한 것은 오늘부터 만기시점까지의 잔존일수 즉 오늘부터 내년 1월 9일까지 몇일 남았는지 데이터가 필요하다.
    curve['DaysToMaturity']=np.nan # 잔존일수 열을 추가할 것이다.
                                   # 처음에는 아무것도 들어가 있으면 안되기 때문에 np.nan를 써준다.
    curve['Maturity']= pd.to_datetime(curve['Maturity']).dt.date # Maturity라는 값이 실제데이터로 찍히기 위해서  
                                                                 # pd.to_datetime(curve['Maturity']).dt.date는 기존의 Maturity데이터를 실제 pandas데이터 형식으로 바꿔준다.           
    
    #오늘부터 만기까지의 차이이기 때문에 for문을 통해 curve의 인덱스 별로 하나하나 돌아가면서 DaysToMaturity(잔존일수) 구해준다.   
    for tenor in curve.index:
        curve.loc[tenor,'DaysToMaturity']= (curve.loc[tenor,'Maturity']-today).days # days는 일수로 바꿔준다.
                                                      
    return curve


def USDIRS_CURVE(today,quote) : # 시장금리와 퀀트립을 이용해서 금리커브를 만든다.
# 퀀트립에서 기간금리구조를 만들때 크게 여러가지 helper function들을 사용해서 각각의 다른 상품에 대해서 그것을 구분을 해서 금리커브를 만든다고 했었다.
# 여기서 Inst Type에서 CASH, FUTURE, SWAP등을 구분을 해줘야한다.(각각에서 처리하는 방법이 다르기 때문)

    #구분을 해주는 코드
    #Divide DataFrame into 3 Parts
    depo=quote[quote['InstType']=='CASH']
    futures=quote[quote['InstType']=='FUTURE']
    swap=quote[quote['InstType']=='SWAP']
    
    # 평가일자를 선언해준다.
    # Set Evalution Date
    todays_date=qe.Date(today.day, today.month, today.year) # 날짜의 형태가 퀀트립형태의 날짜로 바뀐다.
    qe.Settings.instance().evaluationDate=todays_date # "전역적으로 todays_date를 평가일자로 쓰겠다."라는 것을 이 평가 모듈에 알려준다.
    
    # 시장관행을 맞춰준다.
    # 여기에서는 예시로 미국관행으로 맞춰준다.
    # Market conventions
    calendar=qe.UnitedStates()
    dayCounter= qe.Actual360() # 미국은 Actual360으로 맞춰준다. / 1년을 360일로 보겠다./ 실제이자가 발생한 날짜를 실제 일짜로 계산해 주겠다. 예를 들어 한달이 31일이더라도 30일로 계산하지 않고 31일로 계산해준다.
    convention=qe.ModifiedFollowing # 휴알처리방식 / 어떤 이자 발생일자가 휴일이면 그 다음날 영업일을 실제이자의 정산일로 보고 만약에 그 다음날자가 월이 넘어간다면 휴일의 전날 영업일을 실제이자발생일로 하겠다.
    settlementDays=2 # 미국스왑금리커브 같은 경우 정산일자가 이틀이다 / 예를 들어서 어떤 스왑거래를 하면 그 거래일로 부터 이틀 뒤에 효력이 발생한다.
    frequancy=qe.Semiannual # 이자를 얼마나자주 지금할 것 인가? / 여기에서는 6개월에 한번씩이다.
    
    # 실제로 커브를 만드는 helper function들을 정의해주는 것이다.
    # Build Rate Helpers
    # 1. Deposit Rate Helper / 초단기부분의 금리데이터를 처리를 해준다.
    depositHelpers=[qe.DepositRateHelper(qe.QuoteHandle(qe.SimpleQuote(rate/100)), 
                                         qe.Period(int(day),qe.Days),
                                         settlementDays,
                                         calendar,
                                         convention,
                                         False,
                                         dayCounter)
                    for day, rate in zip(depo['DaysToMaturity'],depo['Market.Mid'])]
    
    # 2. Futures Rate Helper
    futuresHelpers=[]
    for i, price in enumerate(futures['Market.Mid']):
        iborStartDate=qe.Date(futures['Maturity'][i].day,
                              futures['Maturity'][i].month,
                              futures['Maturity'][i].year)
        
        futuresHelper=qe.FuturesRateHelper(price,
                                           iborStartDate,
                                           3,
                                           calendar,
                                           convention,
                                           False,
                                           dayCounter)
        futuresHelpers.append(futuresHelper)
    
    # 3. Swap Rate Helper
    swapHelpers=[qe.SwapRateHelper(qe.QuoteHandle(qe.SimpleQuote(rate/100)),
                                   qe.Period(int(day),qe.Days),
                                   calendar,
                                   frequancy,
                                   convention,
                                   dayCounter,
                                   qe.Euribor3M())
                 for day, rate in zip(swap['DaysToMaturity'],swap['Market.Mid'])]

    # Curvce Construction
    helpers=depositHelpers+futuresHelpers+swapHelpers
    depoFuturesSwapCurve=qe.PiecewiseLinearZero(todays_date,helpers,dayCounter)    
    
    return depoFuturesSwapCurve    

def KRWCCS_CURVE(today,quote): # 시장금리와 퀀트립을 이용해서 금리커브를 만든다.
# 퀀트립에서 기간금리구조를 만들때 크게 여러가지 helper function들을 사용해서 각각의 다른 상품에 대해서 그것을 구분을 해서 금리커브를 만든다고 했었다.
# 여기서 Inst Type에서 CASH, SWAP등을 구분을 해줘야한다.(각각에서 처리하는 방법이 다르기 때문)
    
    #구분을 해주는 코드
    #Divide DataFrame into 3 Parts
    depo=quote[quote['InstType']=='CASH']
    swap=quote[quote['InstType']=='SWAP']
    
    # 평가일자를 선언해준다.
    # Set Evalution Date
    todays_date=qe.Date(today.day, today.month, today.year) # 날짜의 형태가 퀀트립형태의 날짜로 바뀐다.
    qe.Settings.instance().evaluationDate=todays_date # "전역적으로 todays_date를 평가일자로 쓰겠다."라는 것을 이 평가 모듈에 알려준다.
    
    # 시장관행을 맞춰준다.
    # 여기에서는 예시로 미국관행으로 맞춰준다.
    # Market conventions
    calendar=qe.SouthKorea()
    dayCounter= qe.Actual365Fixed() # 한국은 Actual360으로 맞춰준다. / 1년을 365일로 보겠다.
    convention=qe.ModifiedFollowing # 휴알처리방식 / 어떤 이자 발생일자가 휴일이면 그 다음날 영업일을 실제이자의 정산일로 보고 만약에 그 다음날자가 월이 넘어간다면 휴일의 전날 영업일을 실제이자발생일로 하겠다.
    settlementDays=1 # 원화스왑금리커브 같은 경우 정산일자가 하루이다 / 예를 들어서 어떤 스왑거래를 하면 그 거래일로 부터 하루 뒤에 효력이 발생한다.
    frequancy=qe.Semiannual # 이자를 얼마나자주 지금할 것 인가? / 여기에서는 6개월에 한번씩이다.
    
    # 실제로 커브를 만드는 helper function들을 정의해주는 것이다.
    # Build Rate Helpers
    # 1. Deposit Rate Helper / 초단기부분의 금리데이터를 처리를 해준다.
    depositHelpers=[qe.DepositRateHelper(qe.QuoteHandle(qe.SimpleQuote(rate/100)), 
                                         qe.Period(int(day),qe.Days),
                                         settlementDays,
                                         calendar,
                                         convention,
                                         False,
                                         dayCounter)
                    for day, rate in zip(depo['DaysToMaturity'],depo['Market.Mid'])]
    
    
    
    # 2. Swap Rate Helper
    swapHelpers=[qe.SwapRateHelper(qe.QuoteHandle(qe.SimpleQuote(rate/100)),
                                   qe.Period(int(day),qe.Days),
                                   calendar,
                                   frequancy,
                                   convention,
                                   dayCounter,
                                   qe.Euribor3M())
                 for day, rate in zip(swap['DaysToMaturity'],swap['Market.Mid'])]
    
    # Curvce Construction
    helpers=depositHelpers+swapHelpers
    depoFuturesSwapCurve=qe.PiecewiseLinearZero(todays_date,helpers,dayCounter)    
    
    return depoFuturesSwapCurve

def DISCOUNT_FACTOR(date, curve): # 할인계수 계산해주는 함수
    date=qe.Date(date.day, date.month, date.year) # date형식의 날짜를 퀀트립 형식의 날짜로 바꿔준다.
    return curve.discount(date) #커브상에서 퀀트립 construction라는 클래스는 여러가지 하부 메소드를 가지고 있는데 construction클래스 중에 dicount()라는 메소드를 이용한다.
                                # discount()는 커브에서 특정날짜를 입력을 하면은 그 특정날짜(date)의 할인계수 바로 계산해서 출력해주는 하부 메소드이다.

def ZERO_RATE(date, curve): #제로금리를 계산해주는 함수
    date=qe.Date(date.day, date.month, date.year) # date형식의 날짜를 퀀트립 형식의 날짜로 바꿔준다.
 
    dayCounter= qe.Actual360() # 미국은 Actual360으로 맞춰준다. / 1년을 360일로 보겠다./ 실제이자가 발생한 날짜를 실제 일짜로 계산해 주겠다. 예를 들어 한달이 31일이더라도 30일로 계산하지 않고 31일로 계산해준다.
    compounding=qe.Compounded # 복리를 사용한다.
    frequency=qe.Continuous # 연속복리 / 실제복리가 이루어지고 있는 지급주기는 연속적이어야 한다.
    
    zero_rate=curve.zeroRate(date, # 제로금리를 계산해준다.
                             dayCounter,
                             compounding,
                             frequency).rate() # zeroRate()같은 경우는 실제금리 값이 아니라 zero_rate라는 하나의 어떤 변수를 만들어주는 것 뿐이다. 그래서 rate()라는 것을 지정을 해줘야 zeroRate()에서 계산한 실제 금리값을 zero_rate라는 변수에 할당해 주겠다는 의미가 된다. 
    
    return zero_rate


def FORWARD_RATE(date, curve): # 선도금리 계산
    date=qe.Date(date.day, date.month, date.year) # date형식의 날짜를 퀀트립 형식의 날짜로 바꿔준다.
    
    dayCounter= qe.Actual360() # 미국은 Actual360으로 맞춰준다. / 1년을 360일로 보겠다./ 실제이자가 발생한 날짜를 실제 일짜로 계산해 주겠다. 예를 들어 한달이 31일이더라도 30일로 계산하지 않고 31일로 계산해준다.
    compounding=qe.Compounded # 복리를 사용한다.
    frequency=qe.Continuous # 연속복리 / 실제복리가 이루어지고 있는 지급주기는 연속적이어야 한다.

    #미래 어떤구간의 선도금리 구하기 위해서는 시작일자(t1)와 끝일자(t2)를 지정해줘야한다.
    #하지만 여기에서는 시작일자(t1)와 끝일자(t2)를 같다고 가정을 한다면 현재로부터 1년뒤의 선도금리를 근사값을 계산을 해주게 된다.
    #여기서는 금융공학적인 이론에 일관성을 위해서 시작날자(date)와 끝날자(date)를 같다고 지정을 한다.(=여기서는 어떤 연속복리를 가정하고 있고 그 다음에 금융공학의 모델을 쫌 더 이쁘게 만들어 주기 위해서 시작일자와 끝일자를 같다고 가정을 하였다.)
    forward_rate=curve.forwardRate(date, # 시작 일자
                                   date, #끝 일자
                                   dayCounter,
                                   compounding,
                                   frequency).rate() # forwardRate()같은 경우는 실제금리 값이 아니라 forward_rate라는 하나의 어떤 변수를 만들어주는 것 뿐이다. 그래서 rate()라는 것을 지정을 해줘야 forwardRate()에서 계산한 실제 금리값을 forward_rate라는 변수에 할당해 주겠다는 의미가 된다.
    return forward_rate

if __name__=="__main__":
    date=datetime.date(2020,10,9)
    ticker1='USD'
    ticker2='KRW'
    
    quote1= GET_QUOTE(date, ticker1)
    quote2=GET_QUOTE(date,ticker2)
    
    usd_curve=USDIRS_CURVE(date, quote1)
    krw_curve=KRWCCS_CURVE(date, quote2)
    
    # plot the result
    quote1['discount factor']=np.nan
    quote1['zero rate']=np.nan
    quote1['forward rate']=np.nan

    for tenor, date in zip(quote1.index, quote1['Maturity']):
        quote1.loc[tenor, 'discount factor']=DISCOUNT_FACTOR(date, usd_curve)
        quote1.loc[tenor, 'zero rate']=ZERO_RATE(date,usd_curve)
        quote1.loc[tenor, 'forward rate']=FORWARD_RATE(date,usd_curve)
        
    # Print result
    print(quote1)

    #Plot the result
    plt.figure(figsize=(16,8))
    plt.plot(quote1['discount factor'],'r.-', label='Discount Curve')
    plt.title('Discount Curve', loc='center')
    plt.legend()
    plt.xlabel('Maturity')
    plt.ylabel('Discount Facotr')
    
    plt.figure(figsize=(16,8))
    plt.plot(quote1['zero rate'],'b.-',label='Zero Curve')
    plt.plot(quote1['forward rate'],'g.-',label='Forward Curve')
    plt.title('Zero & Forward Curve', loc='center')
    plt.legend()
    plt.xlabel('Maturity')
    plt.ylabel('Interest Rate')
    
    # plot the result
    quote2['discount factor']=np.nan
    quote2['zero rate']=np.nan
    quote2['forward rate']=np.nan

    for tenor, date in zip(quote2.index, quote2['Maturity']):
        quote2.loc[tenor, 'discount factor']=DISCOUNT_FACTOR(date, krw_curve)
        quote2.loc[tenor, 'zero rate']=ZERO_RATE(date,krw_curve)
        quote2.loc[tenor, 'forward rate']=FORWARD_RATE(date,krw_curve)
        
    # Print result
    print(quote2)

    #Plot the result
    plt.figure(figsize=(16,8))
    plt.plot(quote2['discount factor'],'r.-', label='Discount Curve')
    plt.title('Discount Curve', loc='center')
    plt.legend()
    plt.xlabel('Maturity')
    plt.ylabel('Discount Facotr')
    
    plt.figure(figsize=(16,8))
    plt.plot(quote2['zero rate'],'b.-',label='Zero Curve')
    plt.plot(quote2['forward rate'],'g.-',label='Forward Curve')
    plt.title('Zero & Forward Curve', loc='center')
    plt.legend()
    plt.xlabel('Maturity')
    plt.ylabel('Interest Rate')
    
    