import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import copy

def evaluate(df, cfg):
  balance_init = cfg["balance_init"]
  year_start = cfg["year_start"]
  year_end = cfg["year_end"]
  year_end_complete = cfg["year_end_complete"]
  
  #plot stratgey comparison 
  fig = plt.figure(figsize=(16,9))
  ax = fig.add_subplot(111)
  daily = df[["date", "benchmark_portf", "strat_portf"]]
  line = pd.DataFrame({"date": "-", "benchmark_portf": balance_init, "strat_portf": balance_init}, index=[0])
  daily.append(line, ignore_index=False)
  ax.plot(daily.index, daily.benchmark_portf)
  ax.plot(daily.index, daily.strat_portf)
  plt.legend(['buy and hold SPY', 'max sharpe'], loc='best')
  ax.set_xlabel('Trading Day')
  ax.set_ylabel("Value ($)")
  plt.title('Daily Portfolio Value (init=$10000)')
  plt.show()      
        
  monthly = df[df.monthend==1][["date", "benchmark_portf", "strat_portf"]]
  monthly = monthly.reset_index(drop=True)
  #plot stratgey comparison 
  fig = plt.figure(figsize=(16,9))
  ax = fig.add_subplot(111)
  ax.plot(monthly.index, monthly.benchmark_portf)
  ax.plot(monthly.index, monthly.strat_portf, marker=".")
  plt.legend(['buy and hold SPY', 'max sharpe'], loc='best')
  ax.set_xlabel('Trading Month')
  ax.set_ylabel("Value ($)")
  plt.title('Monthly Portfolio Value (init=$10000)')
  plt.show()
  
  if year_start < year_end_complete:
    
    yearly = df[df.yearend==1][["date", "benchmark_portf", "strat_portf", "value"]]
    yearly_cp = copy.deepcopy(yearly).drop("value", axis=1)
    
    fig = plt.figure(figsize=(16,9))
    ax = fig.add_subplot(111)
    ax.plot(yearly.date, yearly.benchmark_portf)
    ax.plot(yearly.date, yearly.strat_portf)
    plt.legend(['buy and hold SPY', 'max sharpe'], loc='best')
    plt.xticks(rotation=45)
    ax.set_xlabel('Date')
    ax.set_ylabel("Value ($)")
    plt.title('Yearly Portfolio Value (init=$10000)')
    plt.show()
    
    monthly_cp = copy.deepcopy(monthly)
    line = pd.DataFrame({"date": "-", "benchmark_portf": balance_init, "strat_portf": balance_init}, index=[0])
    yearly_cp = yearly_cp.append(line, ignore_index=False)
    yearly_cp = yearly_cp.sort_index().reset_index(drop=True)
    yearly_pct_change = yearly_cp[["benchmark_portf", "strat_portf"]].pct_change().iloc[1:,:].reset_index(drop=True)
    years=np.array(range(year_start, year_end_complete+1))
    yearly_pct_change.insert(0, "year", years)
    cumulative_benchmark = (monthly_cp.iloc[-1, 1] - balance_init) / balance_init
    cumulative_strat = (monthly_cp.iloc[-1, 2] - balance_init) / balance_init
    
    #calculate sharpe ratio
    yearendindx = df.index[df['yearend'] == 1].tolist()
    indx = [0] + yearendindx
    daily_pct_change = daily[["benchmark_portf", "strat_portf"]].pct_change().iloc[1:,:].reset_index(drop=True)
    r = df.value
    sig = np.array([np.std(daily_pct_change["strat_portf"][indx[i]:indx[i+1]]-r[i+1]/100) for i in range(len(indx)-1)])
    #bench_sig = np.array([np.std(daily_pct_change["benchmark_portf"][indx[i]:indx[i+1]]-r[i+1]/100) for i in range(len(indx)-1)])
    ret = yearly_pct_change.strat_portf
    #bench_ret = yearly_pct_change.benchmark_portf
    r = yearly.value.reset_index(drop=True)
    sharpe = (ret - r/100) / sig
    #benchmark_sharpe = (bench_ret - r/100) / bench_sig
    
    #yearly_pct_change.insert(yearly_pct_change.shape[1], "benchmark_sharpe", benchmark_sharpe)
    yearly_pct_change.insert(yearly_pct_change.shape[1], "risk_free", r/100)
    yearly_pct_change.insert(yearly_pct_change.shape[1], "strat_sharpe", sharpe)
    yearly_pct_change.insert(yearly_pct_change.shape[1], "strat_sigma", sig)
    yearly_pct_change= yearly_pct_change.rename(columns={"benchmark_portf": "benchmark_ret", "strat_portf": "strat_ret"})
    
    
    print("\n########## Cumulative Return since Year ", year_start, "##########\n")
    print('benchmark_portf:    {:.2%}'.format(cumulative_benchmark))
    print('strat_portf:        {:.2%}'.format(cumulative_strat))
    print("\n########## Cumulative Return since Year ", year_start, "##########\n")
    
    print("\n#################### Detailed Annual Return####################\n")
    print(yearly_pct_change)
    print("\n#################### Detailed Annual Return####################\n")
          
# =============================================================================
#     print("########## Average Annual Return##########")
#     print(yearly_pct_change.iloc[1:].mean(axis=0).iloc[1:])
#     print("########## Average Annual Return##########\n")
# =============================================================================
  
  else:
    months = np.array(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])
    monthly_cp = copy.deepcopy(monthly)
    line = pd.DataFrame({"date": "-", "benchmark_portf": balance_init, "strat_portf": balance_init}, index=[0])
    monthly_cp = monthly_cp.append(line, ignore_index=False)
    monthly_cp = monthly_cp.sort_index().reset_index(drop=True)
    monthly_pct_change = monthly_cp[["benchmark_portf", "strat_portf"]].pct_change().iloc[1:,:].reset_index(drop=True)
    monthly_pct_change.insert(0, "month", months[0:monthly_pct_change.shape[0]])
    YTD_benchmark = (monthly_cp.iloc[-1, 1] - balance_init) / balance_init
    YTD_strat = (monthly_cp.iloc[-1, 2] - balance_init) / balance_init
    
    print("\n########## Detailed Monthly Return of Year ", year_start, "##########\n")
    print(monthly_pct_change)
    print("\n########## Detailed Monthly Return of Year ", year_start, "##########\n")
          
    print("\n########## YTD Return since Year ", year_start, "##########\n")
    print('benchmark_portf:    {:.2%}'.format(YTD_benchmark))
    print('strat_portf:        {:.2%}'.format(YTD_strat))
    print("\n########## YTD Return since Year ", year_start, "##########\n")
    
# =============================================================================
#     print("########## Average Monthly Return of Year ", year_start, "##########")
#     print(monthly_pct_change.iloc[1:].mean(axis=0))
#     print("########## Average Monthly Return of Year ", year_start, "##########\n")
# =============================================================================
    