import sqlite3
from array import array
from pandas import DataFrame
import numpy as np

class rawPhotonData:
    chs=["DexAem","DexDem","AexAem","All"]
    blockNum=16000
    def __init__(self,dbname=''):
        self.dbname=dbname
        self.conn = sqlite3.connect(dbname)
        self.c = self.conn.cursor()
        self.c.execute("SELECT value FROM fretData_Var where varName='MeasDesc_GlobalResolution'")
        self.MeasDesc_GlobalResolution= self.c.fetchone()[0] #6.2497500099996e-08
        self.c.execute("SELECT value FROM fretData_Var where varName='MeasDesc_Resolution'")
        self.DelayResolution= self.c.fetchone()[0] #2.50000003337858e-11
    def __del__( self ): 
        self.conn.close()
    def photonIn1Chl(self,chl,dbname=''):
        if len(dbname)>0:
            __del__()
            __init__(dbname)       
        return self.fetchPhoton(chl) 
    def fetchPhoton(self,ch):
        photons=dict()
        if ch not in self.chs:
            return photons
        self.c.execute("select TimeTag from fretData_"+ch+" ORDER BY TimeTag limit 1")
        #c.execute('SELECT * FROM stocks WHERE symbol=?', t)
        t1= self.c.fetchone()[0]-1
        hasData=False
        if t1>=0:
            hasData=True
        buf = array("d")        
        dtime=[]
        chl=[]
        #idxbuf=0
        sql="select TimeTag,Dtime from fretData_"+ch+" where TimeTag > ? ORDER BY TimeTag limit ?"
        while hasData:            
            self.c.execute(sql,(t1,self.blockNum))
            data=self.c.fetchall()
            lendata=len(data)
            if lendata<10:
                hasData=False
                break;
            df=DataFrame(data=data)          
            dtime.append(df[0:lendata][1])
            t1=data[-1][0]
        photons=dict({'dtime':dtime,\
                    })
        return photons

def func(x, a, b):
    return a * np.exp(-x /b )

if __name__ == '__main__':
    from scipy.optimize import curve_fit
    import matplotlib.pyplot as plt
    import pickle    
    try:        
        import algo.BGrate as BGrate
    except ImportError:
        import BGrate

    r=rawPhotonData('/home/liuk/proj/data/Tau_D.sqlite')
    d=r.photonIn1Chl("DexDem")
    ad=array('d')
    for dd in d['dtime']:
        for ddd in dd:            
            ad.append(ddd*r.DelayResolution*1e9)
    print(len(ad))
    with open('../data/TauDraw.pickle', 'wb') as f:  # Python 3: open(..., 'wb')
        pickle.dump([ad], f)
    thebin=200
    [hist,bin]=np.histogram(ad, bins=thebin)
    x=array("d")
    y=array("d")
    sidx=np.argmax(hist) #只拟合最大值之后的数据    
    lenhist=len(hist)
    for vh in range(sidx,lenhist):
        if hist[vh]>0 and bin[vh]>bin[sidx]+1:        
            y.append(hist[vh])
            x.append(bin[vh]-bin[sidx]-1)     
            #print(bin[vh])           
    xx=np.array(x)
    yy=np.array(y)
    p0 = [np.min(ad),np.max(ad)]
    #plsq = least_squares(fun, p0, jac=jac, gtol=0,bounds=([0, p0[0]], [9999,p0[1]]), args=(xx,yy), verbose=1)
    popt, pcov = curve_fit(func, xx, yy, \
                    verbose=1,method='trf',loss='cauchy')
                    #,bounds=([0, p0[0]/2.0,-np.inf], [np.inf,p0[1]*2.0,np.inf]),\
    print(popt)
            
    fig = plt.figure()
    ax = fig.add_subplot(111)
    n, bins, patches = plt.hist(ad, thebin, facecolor='g', alpha=0.75)

    #fy=model(plsq.x,xx)
    l = plt.plot(xx+bin[sidx]+1, func(xx,*popt), 'b--', linewidth=2)
    #lr = plt.plot(x, np.exp(y), 'bo', linewidth=2)
    plt.legend(loc='best')
    plt.show()    
                        