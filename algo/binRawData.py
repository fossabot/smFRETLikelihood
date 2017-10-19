try:
    import algo.BurstSearch as BurstSearch
    import algo.BGrate as BGrate
except ImportError:
    import BurstSearch
    import BGrate
import sqlite3
import numpy as np
import time
from array import array

def findTagLastLessThanIdx(data,lessThan):
    #注意！！！timetag 如果有相同的可能掉数据
    lendata=len(data)
    r=-1
    for i in range(lendata):
        if data[i][0]==lessThan:
            r=i
        elif data[i][0]>lessThan:
            r=i-1
            break
    return r

def binRawData(  bgrate, dbname, binMs = 1 ):
    binTag=(binMs*1e-3)/bgrate["SyncResolution"] #每个bin对应的timetag值
    print(binTag)
    span=int(10/binMs)+1
    conn = sqlite3.connect(dbname)
    c = conn.cursor()
    chs=["All"] #暂时只处理All通道
    binData=dict()
    nowpercent=0
    for ch in chs:
        timetag=[]
        dtime=[]
        chl=[]
        fretE=array("d")
        fretS=array("d")
        fretZ=array("d")
        lifetime=array("d")        
        hasData=False
        c.execute("select min(TimeTag) from fretData_"+ch)
        idx= c.fetchone()[0] # Start TimeTag
        if idx!=None:
            hasData=True
        c.execute("select max(TimeTag) from fretData_"+ch)
        TimeLast= c.fetchone()[0]
        TimeStart=idx
        percent=0
        start = time.time()
        timeIdx=0
        while hasData:        
            nowpercent= (idx-TimeStart)/(TimeLast-TimeStart)
            if nowpercent>=percent+0.1:
                now = time.time()
                print(nowpercent,'% speed =',(idx-TimeStart)/binTag/1e3/(now-start),"s/s")
                percent=nowpercent
                                     
            if (idx+binTag*span)>=TimeLast:
                sql="select TimeTag,dtime,ch from fretData_"+ch+" where TimeTag>=? and TimeTag<=? ORDER BY TimeTag" 
                c.execute(sql,(idx,TimeLast))
                hasData=False
            else:
                sql="select TimeTag,dtime,ch from fretData_"+ch+" where TimeTag>=? and TimeTag<? ORDER BY TimeTag" 
                c.execute(sql,(idx,idx+binTag*span))
            data=c.fetchall()
            r0=0
            r1=0
            # r00=0
            for i in range(span):  
                # if i==0:
                #     r00=r0   
                r1=findTagLastLessThanIdx(data,TimeStart+timeIdx*binTag*span+(i+1)*binTag)    
                if r1<0 and i!=span-1:
                    continue   
                elif i==span:
                    r1=0
                tt=BurstSearch.data2Dcol(data,r0,r1,0)
                if len(tt)>0:
                    timetag.append(tt)
                    dtime.append(BurstSearch.data2Dcol(data,r0,r1,1))
                    chl.append(BurstSearch.data2Dcol(data,r0,r1,2))   
                    lifetime.append(0)
                    fretE.append(0)
                    fretS.append(0)
                    fretZ.append(0)             
                r0=r1
            idx=idx+binTag*span
            # print(data[r00][0],data[r0][0])
            # print("=============")
            timeIdx+=1
        binData[ch]=dict({'timetag':timetag,'dtime':dtime,'chl':chl,'binMs':binMs \
                        ,'e':fretE,'s':fretS,'z':fretZ,'lifetime':lifetime})
    if nowpercent<0.95:
        print("!!!!!span的合理范围 >= 7 !!!!!!!!")
    conn.close()
    binData["SyncResolution"]=bgrate["SyncResolution"]
    binData["DelayResolution"]=bgrate["DelayResolution"]    
    return binData
def countBin(binData,chl):
    if chl in binData:
        binDataCh=binData[chl]
        lenbin=len(binDataCh['timetag'])
        print("bin#:",lenbin)
        sumBin=np.empty(lenbin)
        for i in range(lenbin):
            sumBin[i]=len(binDataCh['timetag'][i])
        return sumBin
    else:
        return None
if __name__=='__main__':
    dbname='/home/liuk/proj/data/RSV89C224C.sqlite'
    br=BGrate.calcBGrate(dbname,20,400,chs=["All"],T0=10.0,Tlen=21.0)
    binData=binRawData(br,dbname)
    bin=countBin(binData,"All")
    print(np.sum(bin))
    import matplotlib.pyplot as plt
    plt.hist(bin,100,(0,50))
    plt.show()
    
    