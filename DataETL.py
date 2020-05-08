import numpy as np
import pandas as pd
from os import listdir
from os.path import isfile, join
import re
from functools import reduce
import json
from datetime import datetime, timedelta
import time
import requests, pandas, lxml
from calendar import timegm
import urllib
import bs4 as bs

def _getEpoch(date_str):
  utc_time = time.strptime(date_str+"T00:00:00", "%Y-%m-%dT%H:%M:%S")
  epoch_time = timegm(utc_time)

  return epoch_time

def _crawlPriceHist(symbol, epoch_1, epoch_2):
  #dfObj = pd.DataFrame()
  lst = []
  url = "https://ca.finance.yahoo.com/quote/{}/history?period1={}&period2={}&interval=1d&filter=history&frequency=1d".format(symbol, epoch_1, epoch_2)
  print(url)
  sauce = urllib.request.urlopen(url).read()
  soup = bs.BeautifulSoup(sauce, 'lxml')
  body = soup.body
  table = body.find(lambda tag: tag.name=='table' and tag.has_attr('data-test') and tag['data-test']=="historical-prices")
  rows = table.findAll(lambda tag: tag.name=='tr')
  rows = rows[1:-1]

  if len(rows) == 2:

    rows.pop()

  for row in rows:

    spans = row.findAll(lambda tag: tag.name=='span')
    dateStr = spans[0].text
    closeStr = spans[-2].text
    dateStr = dateStr.replace(".", "")
    date_time_obj = datetime.strptime(dateStr, '%b %d, %Y')
    dateStr = date_time_obj.date()
    if closeStr.replace('.','',1).isdigit():
      lst.append([dateStr, closeStr])

  dfObj = pd.DataFrame(lst, columns =['date', symbol])
  dfObj = dfObj.drop_duplicates()

  return dfObj


#print(_getEpoch("2020-05-07"))
#get price history of 5/7
#_crawlPriceHist("ibm", str(_getEpoch("2020-05-07")), str(_getEpoch("2020-05-08")))



def extractData(symbols, date_start, date_end, write_mode="write"):

  filedir = "data_raw/raw.csv"
  epoch_1 = _getEpoch(date_start)
  epoch_2 = _getEpoch(date_end) + 86400
  df_list = []

  for symbol in symbols:
    print("\n getting price history of {}...".format(symbol))
    price_df = _crawlPriceHist(symbol, str(epoch_1), str(epoch_2))
    df_list.append(price_df)
    time.sleep(5)

  df = reduce(lambda left,right: left.merge(right, how='outer', on=['date'], suffixes=(False, False)), df_list)
  df = df.sort_index(axis = 0, ascending = False).reset_index(drop=True)

  if write_mode == "append":
    curr = pd.read_csv(filedir)
    df = curr.append(df)

  df.to_csv(filedir, index=False)
  return df


# =============================================================================
# extractData(['aapl', 'ibm'], "2004-01-01", "2020-05-06", write_mode="write")
# extractData(['aapl', 'ibm'], "2020-05-07", "2020-05-07", write_mode="append")
# =============================================================================

def transformData():

  return

def load():

  return

###############################################################################################################

def _merge(raw_dir, file_names):

  df_list = []

  #read in all raw data iteratively and choose date and adj close
  for file_name in file_names:
    dataFile = join(raw_dir, file_name)
    df = pd.read_csv(dataFile)
    close = df[["Date", "Adj Close"]]
    col_name = re.findall("[A-Z]+",file_name)
    close = close.rename(columns={"Adj Close": col_name[0]})
    close = close.rename(str.lower, axis='columns')
    df_list.append(close)

  #join
  df = reduce(lambda left,right: left.merge(right, how='outer', on=['date'], suffixes=(False, False)), df_list)

  return df

def _createNewData(raw_dir, raw_suffixes, processed_dir, processed_suffixes, write_mode=False):

  #use raw_suffixes to filter data files to be merged
  targetFiles =  [f for f in listdir(raw_dir) if (isfile(join(raw_dir, f)) and raw_suffixes in join(raw_dir, f))]

  #call _merge() to merge colume-wise
  merged = _merge(raw_dir, targetFiles)

  #save merged if write_mode is set as True
  if write_mode:
    merged.to_csv(processed_dir+"processed"+processed_suffixes+".csv",index=False)

  return merged

def _appendNewData(raw_dir, raw_suffixes, processed_dir, processed_suffixes, write_mode=False):

  #use raw_suffixes to filter data files to be merged
  targetFiles =  [f for f in listdir(raw_dir) if (isfile(join(raw_dir, f)) and raw_suffixes in join(raw_dir, f))]

  #call _merge() to merge colume-wise
  merged = _merge(raw_dir, targetFiles)

  #read the saved processed data
  dir = processed_dir+"processed"+processed_suffixes+".csv"
  curr = pd.read_csv(dir)

  #append new data to the existing data
  df = curr.append(merged)

  #saved appended if write_mode is set as True
  if write_mode:
    suffix_start = re.findall("\d{4}",processed_suffixes)
    suffix_end = re.findall("_\d{4}",raw_suffixes)
    print(suffix_start[0] + suffix_end[0])
    df.to_csv(processed_dir+"processed_"+suffix_start[0] + suffix_end[0]+".csv",index=False)
  return df

def _addNewAssets(raw_dir, raw_suffixes, processed_dir, processed_suffixes, write_mode=False):
  return

def _convert_date_to_array(datestr):
    temp = [int(x) for x in datestr.split('-')]
    return [temp[0], temp[1], temp[2]]

def _addPeriodEndFlag(df):

  bimonthflags = np.zeros(shape=[df.shape[0]])
  monthflags = np.zeros(shape=[df.shape[0]])
  yearflags = np.zeros(shape=[df.shape[0]])

  def convert_date_to_array(datestr):
    temp = [int(x) for x in datestr.split('-')]
    return [temp[0], temp[1], temp[2]]

  dates_array = np.array(list(df['date'].apply(convert_date_to_array)))

  for i in range(df.shape[0]-1):
    if dates_array[i][0] != dates_array[i+1][0]:
      yearflags[i] = 1
    if dates_array[i][1] != dates_array[i+1][1]:
      monthflags[i] = 1
    if dates_array[i][1] != dates_array[i+1][1] and dates_array[i][1] % 2 != 0:
      bimonthflags[i] = 1

  if dates_array[-1][1] == 12:
    yearflags[-1] =1
  if dates_array[-1][1] % 2 != 0:
    bimonthflags[i] = 1
  monthflags[-1]=1

  df.insert(1, "bimonthend", bimonthflags)
  df.insert(1, "monthend", monthflags)
  df.insert(1, "yearend", yearflags)

  return df

def addRiskFreeRate(df, raw_dir, file_name):

  rate_df = pd.read_csv(raw_dir+file_name)
  rate_df['date'] = pd.to_datetime(rate_df['date'], format="%m/%d/%Y").astype(str)
  df = df.merge(rate_df, on="date", how="left")

  return df

def loadData(cfg_fileName):

  cfg_dir = "config/"+cfg_fileName
  raw_dir = "data_raw/"
  processed_dir = "data_processed/"
  with open(cfg_dir) as json_data_file:
    cfg = json.load(json_data_file)

  raw_suffixes = cfg["raw_suffixes"]
  processed_suffixes = cfg["processed_suffixes"]
  append_suffixes = cfg["append_suffixes"]
  year_start = cfg["year_start"]
  year_end = cfg["year_end"]

  #read data or generate new
  dir = processed_dir+"processed"+processed_suffixes+".csv"
  if (isfile(dir)):
    df = pd.read_csv(dir)
    print("data file is loaded\n")
  else:
    df = _createNewData(raw_dir, raw_suffixes, processed_dir, processed_suffixes, write_mode=True)

  if append_suffixes != "":
    df = _appendNewData(raw_dir, append_suffixes, processed_dir, processed_suffixes, write_mode=True)

  df = _addPeriodEndFlag(df)
  df= addRiskFreeRate(df, raw_dir, "Rate.csv")

  #try filter on date
  df = df[(df['date'] >= str(year_start)+'-01-01') & (df['date'] <= str(year_end)+'-12-31')].reset_index(drop=True)


  return df, cfg
