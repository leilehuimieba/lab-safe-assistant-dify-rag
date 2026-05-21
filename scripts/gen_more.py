import csv
from datetime import datetime
records = []
def add(t,c,q,a,h,s,o,u,r):
  records.append({'title':t,'category':c,'question':q,'answer':a,'hazard_types':h,'steps':s,'source_org':o,'source_url':u,'risk_level':r})

