import QuantLib as ql
from UST_Curve import GET_DATE, GET_QUOTE, TREASURY_CURVE

# Basic Setup
eval_date=GET_DATE()
quote=GET_QUOTE(eval_date)
curve=TREASURY_CURVE(eval_date,quote)

# Handle, Engine
curveHandle=ql.YieldTermStructureHandle(curve) # Yield Term Structure는 UST_Curve의 curve와 같다.
bondEngine=ql.DiscountingBondEngine(curveHandle) # 채권 프라이싱을 진행 하는 엔진
                                                #우리가 평가를 수학적으로 어떻게 진행하냐라는 고려를 전혀 할 필요가 없이 bondEngine에서 다해준다.

# Treasury Bond Information 채권의 성질이 필요함
issueDate=ql.Date(13,11,2019) # 채권의 발행일자
maturityDate=ql.Date(13,11,2029) # 채권의 만기일자
tenor=ql.Period(ql.Semiannual)# 이 채권이 얼마주기로 이자를 지급하냐
calendar=ql.UnitedStates() # 사용달력
convention=ql.ModifiedFollowing # 시장관행
dateGeneration=ql.DateGeneration.Backward # 이자일수를 어떻게 생성할 것인가
endOfMonth=False #월말 기준
schedule=ql.Schedule(issueDate,
                     maturityDate,
                     tenor,
                     calendar,
                     convention,
                     convention,
                     dateGeneration,
                     endOfMonth)
                    

settlementDays=1 # 어떤한 채권 거래를 했다. 실제 거래 대금을 언제 주고 받을 것인가 
                 # 그리고 그 상품이 언제 인수도(?)가 될것인가
                 # 시장 관행에 맞게 입력 (settlementDays=1라는 것은 만약 내가 채권을 오늘 구매를 했으면 내일 대금이 빠져나가면서 채권이 들어온다.) 
faceAmount=100 # (미국의 face value는 100이다.)
coupon=[0.0175]# 지금 내가 어떤 10년 만기 국고채를 구매햇는데 이것이 6개월 마다. 금리를 얼마 지급하냐
dayCount=ql.ActualActual()



# Fixed-rate Bond
fixedRateBond=ql.FixedRateBond(settlementDays,
                               faceAmount,
                               schedule,
                               coupon,
                               dayCount)

# 필요한 것이 2가지 파트가 이다. 
# 1. 시장 금리(시장 데이터) : 시장데이터가 바뀌면서 가지고 있는 자산가격에도 변동이 있기 때문에
# 2. 상품에 대한 정보 
# 이 2파트를 합치면 평가가 완료된다.

# Conduct Pricing
fixedRateBond.setPricingEngine(bondEngine)


# 예를 들어서 내가 채권을 삿는데 이날이 거래일이다. 
# 2년 만기채권이 있고 6개월 마다 이자를 지급하는 채권이 잇는데 요날이 발행일이고 근데 내가 채권을 매수한 날이 이날이다. 
# 그러면은 내가 요거의 이자는 내 것이 아니다. 
# 왜냐하면은 내가 소유하고 있지 않으니깐 
# 그러면은 결국 내가 받아야 하는 이자는 이 이자, 이 이자, 이자 인데, 이 이자는 완벽히 내 것이다.
# 근데 이 이자는 이 기간동안 요만큼만 나의 것이고 나머지 이자는 원래 들고 있던 상대방 것이다.
# 그렇기 때문에 실제 대금을 거래 할때 이 이자를 빼서 계산을 해줘야한다. 
# 그래서 요것을 경과이자라고 한다. 이미 시간이 경과해서 내가 가질수없는 이자를 말한다.
# 경과이자를 뺀 이만큼의 value를 우리는 clean price라고 부른다. 시장에서 실제로 가격을 주고 받을 때는 clean price 기준으로 한다.
# clean price와 경과이자 합쳐서 dirty price라고 한다.
# 요 "경과이자", "clean price", "dirty price" 3개의 개념을 이해하여야한다.

#결국 시장에서 이야기하는 채권가격은 얼마다 하는 것은 clean price기준으로 말하면 된다.

# Print Pricing Result
clean_price=fixedRateBond.cleanPrice()
accrued_interest=fixedRateBond.accruedAmount()
dirty_price=fixedRateBond.dirtyPrice()
ytm=fixedRateBond.bondYield(dayCount, ql.Compounded,ql.Semiannual) # 만기 수익률

print("Clean Price={}".format(clean_price))
print("Accrued Interest={}".format(accrued_interest))
print("Dirty Price={}".format(dirty_price))
print("Yield To Maturity={}".format(ytm))

#출력후

# 출력된 Clean Price의 값은 해당채권의 현재 가격이다.
# 2019/11/13에 이 채권을 미국이 100에 발행을 했는데
# Clean price의 값과 다르다.
# 그 이유는 쿠폰의 퍼센트에 영향을 변화된 것이다.
# 만약 시장 금리가 낮아지면 채권의 가격이 올라가기 때문에 채권 매수자 입장에서는 좋다.

# Generate Cashflow Table
for cashflow in fixedRateBond.cashflows():
    print(cashflow.date(),cashflow.amount())
    
#이 채권이 가지고있는 진짜 cash flow 이자지급 스케줄을 우리가 궁금하다.
# ex) May 13th, 2020 0.8708604685979449 : 2020년 5월 13일이  0.8708604685979449 이자지급 
# ex) November 13th, 2020 0.8797814207650356 : 2020년 11월 13일 0.8797814207650356 이자지급 
# 6개월 마다 이자를 지급한다.
# 만기일에는 원급을 받는다.
# ex) November 13th, 2029 100.0 : 2029년 11월 13일 원금을 받는다.    
    
    
    
#Calculate YTM 
new_ytm=ql.InterestRate(fixedRateBond.bondYield(dayCount,
                                                ql.Compounded,
                                                ql.Semiannual),
                        dayCount,
                        ql.Compounded,
                        ql.Semiannual)

# Duration & Convexity
duration=ql.BondFunctions.duration(fixedRateBond,new_ytm) # 금리의 방향성 / 상승하냐 하락하냐에 따른 채권의 가격의 얼마나 변하는지 
                                                          # ex) Duration=7.71441160428433
                                                              # 금리와 채권의 가격은 반대이기 때문이다
                                                              # => 금리가 1%인데 +1%상승하여 2%가 되었다. 그러면은 내 채권의 가격이 -7.71441160428433 감소한다는 소리이다. 
                                                              # => 금리가 1%인데 -1%하락하여 0%가 되었다. 그러면은 내 채권의 가격이 +7.71441160428433 증가한다는 소리이다.
                                                         #만약 Duration이 작으면 금리의 영향력이 작아져 채권의 변동성은 작을 것이다. 
                                                         #만약 Duration이 크면 금리의 영향력이 강해져 채권의 변동성은 클 것이다. 
                                                         # 채권쟁이들이 금리가 인상을 예상 -> 위험 부담이 큰 Duration(변동성)이 큰 채권을 팔고 안전한 Duration(변동성)이 작은 채권을 찾는다.
                                                         # 채권쟁이들이 금리가 인하를 예상 -> Duration(변동성)이 큰 채권을 구매하여 금리 인하에 따른 채권의 가격상승을 통해 이득을 봄
                                                         
convexity=ql.BondFunctions.convexity(fixedRateBond,new_ytm) # 금리의 변동성에 대한 민감도 /

print("Duration={}".format(duration))
print("Convexity={}".format(convexity))



