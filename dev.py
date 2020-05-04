import numpy as np
import math
import pandas as pd
from DataETL import loadData
from PortfolioCore import rebalance
from PortfolioEvaluation import evaluate

config = "config1.json"
df, cfg = loadData(config)

#benchmark portoflio: buy and hold SPY 
balance_init = cfg["balance_init"]
benchmark_x_init = math.floor(balance_init / df.spy[0])
benchmark_cash_init = balance_init - benchmark_x_init * df.spy[0]
benchmark_portf_val = benchmark_cash_init + df.spy * benchmark_x_init

#split df into multiples
r=df.iloc[:,-1]
prices = df.iloc[:, 4:-1].drop(["spy", "vix"], axis=1)
asset_names = list(prices.columns) 
prices = prices.to_numpy()
vix = df.iloc[:,-2]
N_asset = prices.shape[1]
N_day = prices.shape[0]

#construct equal weight portfolio for cold-start
w = np.array([1/N_asset]*N_asset)
equity_init = balance_init * w
strat_x_init = np.floor(equity_init/prices[0])
strat_cash_init = balance_init - np.dot(strat_x_init, prices[0])

curr_x = strat_x_init
curr_cash = strat_cash_init
strat_portf_val = []

day_ind_start = cfg["day_ind_start"]
check_start = cfg["check_start"]
check_end = cfg["check_end"]
increment = check_end - check_start

#back-testing
for i in range(N_day):
  
  #per 20-day strategy:
  #1) if past 20 day's return is higher than 12%, take all profits
  #2) if past 20 day's loss is higher than 3%, take all losses
  
  if i >= check_end:
    
    if (np.sum(curr_x) != 0) and (strat_portf_val[check_end-1] /strat_portf_val[check_start] >= 1.12 or strat_portf_val[check_end-1] /strat_portf_val[check_start] <= 0.95):
      
      print("#############################################################################")
      print("####################rebalancing####################")
      print("rebalanced on date", df.date[i], ": sellout - take profit/loss")
      portf = np.dot(curr_x, prices[i]) + curr_cash  
      x_optimal = np.zeros(prices.shape[1])
      transactionFees = np.sum(curr_x) * 0.005
      cash_optimal = portf - np.dot(prices[i], x_optimal)- transactionFees 
      curr_x = x_optimal
      curr_cash = cash_optimal
      check_start += increment
      check_end += increment
      
    else:
      
      check_start = i
      check_end= i + increment
      
  #bi-monthly strategy:
  #1) sellout if vix spikes
  #2) if 1) is not satisfied, execute maxsharpe optimization 
  #3) if last period has 0 holdings and stratigy issues 0 holdings signal again, force equal-weight  
  
  if df.iloc[i, 3] == 1:
    day_ind_end = i
    prices_i = prices[i]
    print("####################rebalancing####################")
    print("vix range:", vix[day_ind_start], "-", vix[day_ind_end])            
    curr_x, curr_cash = rebalance(df, r, i, curr_x, curr_cash, prices, vix, day_ind_start, day_ind_end)
    day_ind_start = i
    
  curr_portf_val = np.dot(curr_x, prices[i]) + curr_cash  
  strat_portf_val.append(curr_portf_val)
  
  if curr_cash < 0:
    print("infeasible")
    break
  
df["benchmark_portf"] = benchmark_portf_val
df["strat_portf"] = np.array(strat_portf_val)
evaluate(df, cfg)

print("\n####################Current Holdings####################\n")
print(pd.DataFrame(list(zip(asset_names, curr_x)), columns =['Asset', 'Quantity']))
print("\n####################Current Holdings####################\n")