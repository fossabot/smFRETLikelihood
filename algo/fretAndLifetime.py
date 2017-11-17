#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec 22 10:31:42 2016

@author: liuk
"""

import numpy as np
import sys
import BurstSearch
import BGrate
import binRawData
import fretAndS
from array import array

import pickle


#burstD如果是浮点数，则为Donor only的TauD，否则为Donor only的提取的burst
def FretAndLifetime(burst,bins=(25,25),bgrate=None,burstD=4.1,bgrateD=None,T0=6.8695,binLenT=30,S=0):
    #conn = sqlite3.connect(dbname)
    #c = conn.cursor()
    Tau_D=1e-9
    if type(burstD) is float:
        Tau_D=burstD*1e-9
        print('已经制定TauD')
    else:
        lenburstD=len(burstD["All"]['chl'])
        burstTauD = array("d")#np.zeros(lenburst)
        weiD = array("d")#np.zeros(lenburst)
            
        for i in range(lenburstD):
            data=burstD["All"]['chl'][i]
            if bgrateD!=None:
                tt=burstD["All"]['timetag'][i]
                #print(tt)
                backgT=burstD["All"]['burstW'][i]/2+tt[0]*bgrate["SyncResolution"] #中点时刻
                bgAA=BurstSearch.getBGrateAtT(bgrateD,"AexAem",backgT)
                bgDD=BurstSearch.getBGrateAtT(bgrateD,"DexDem",backgT)
                bgDA=BurstSearch.getBGrateAtT(bgrateD,"DexAem",backgT)            
            w=len(data)       
            nda=0#ch1
            ndd=0;#ch2
            naa=0;#ch3
            nad=0#ch4        
            sumdtimed=array("d")
            for idxd in range(w):
                d=data[idxd]
                if d==1:
                    nda+=1
                elif d==2:
                    ndd+=1
                    sumdtimed.append(burstD["All"]['dtime'][i][idxd]*burstD["DelayResolution"]*1e9)
                elif d==3:
                    naa+=1
                elif d==4:
                    nad+=1                
            if bgrateD!=None:
                naa=naa-bgAA*burstD["All"]['burstW'][i]
                ndd=ndd-bgDD*burstD["All"]['burstW'][i]
                nda=nda-bgDA*burstD["All"]['burstW'][i]
                if naa< bgAA*burstD["All"]['burstW'][i] or ndd<0 or nda<0:
                    continue
            weiD.append(w)
            Tau=np.mean(sumdtimed)
            burstTauD.append(Tau)
        [hist,bin]=np.histogram(burstTauD, bins=200)
        x=array("d")
        y=array("d")
        sidx=np.argmax(hist) #只拟合最大值之后的数据
        lenhist=len(hist)
        for vh in range(sidx,lenhist):
            if hist[vh]>0:        
                y.append(np.log(hist[vh]))
                x.append(bin[vh])            
        m = 2  #多项式的次数
        #先随机产生一组多项式分布的参数
        p0 = np.random.randn(m)
        plsq = leastsq(BGrate.residuals, p0, args=(y, x))
        print(plsq)
        # fig = plt.figure()
        # ax = fig.add_subplot(111)
        # n, bins, patches = plt.hist(burstTauD, 200, facecolor='g', alpha=0.75)
        # plt.legend(loc='best')
        # plt.show()
        Tau_D=-1*plsq[0][0]*1e-9#        
        with open('../data/TauD.pickle', 'wb') as f:  # Python 3: open(..., 'wb')
            pickle.dump([burstTauD], f)

    lenburst=len(burst['chs']["All"]['chl'])
    print("lenburst:",lenburst)
    if S>0:
        if burst['chs']['All']['s'][0]==-1:
            fretAndS.FretAndS(burst,bins,bgrate,False)
            print('S calc:',S)
    sumdtimed0=array("d")
    for i in range(lenburst):
        if burst['chs']['All']['s'][i]>=S and burst['chs']['All']['s'][i]<=1:
            w=burst['chs']["All"]['ntag'][i]            
            for idxd in range(w):  
                if burst['chs']["All"]['chl'][i][idxd]==2:
                    detime=burst['chs']["All"]['dtime'][i][idxd]\
                    *burst["DelayResolution"]-T0*1e-9
                    if detime>=0:
                        sumdtimed0.append(detime)   
    print(len(sumdtimed0))
    Tau_D=np.mean(sumdtimed0)
    print('Tau_D:',Tau_D)

    burstFRET = array("d")#np.zeros(lenburst)
    burstSeff = array("d")#np.zeros(lenburst)
    burstTau = array("d")#np.zeros(lenburst)
    wei = array("d")#np.zeros(lenburst)
    #fw = np.zeros(lenburst)

    '''     
    i=1000
    data=burst["All"]['chl'][i]
    w=len(data)
    print(w)
    nda=0#ch1
    ndd=0;#ch2
    naa=0;#ch3
    nad=0#ch4
    histdtime=array("d")
    for idxd in range(w):
        d=data[idxd]
        dtime=burst["All"]['dtime'][i][idxd]*burst["DelayResolution"]
        if d==1:
            nda+=1
        elif d==2:
            ndd+=1
            histdtime.append(dtime)
        elif d==3:
            naa+=1
        elif d==4:
            nad+=1
            #sumdtimed+=dtime
    fig = plt.figure()
    ax = fig.add_subplot(111)
    n, bins, patches = plt.hist(histdtime, 100,  facecolor='g', alpha=0.75)
    print(len(histdtime))
    plt.legend(loc='best')
    plt.show() 
    '''
    isBurst=False
    if 'burstW' in burst['chs']["All"]:
        isBurst=True
    for i in range(lenburst):
#        c.execute("select Dtime,ch from fretData_All where TimeTag>=? and TimeTag<= ?",
#                  (burst["All"].stag[i],burst["All"].etag[i]))
#        data=c.fetchall()
        if burst['chs']['All']['s'][i]>0.83 or burst['chs']['All']['s'][i]<0.11:
            continue
        data=burst['chs']["All"]['chl'][i]
        w=burst['chs']["All"]['ntag'][i]
        if type(w)!=type(1):
            continue
        if len(data)<1:
            continue
        bgAA=0
        bgDD=0
        bgDA=0  
        if bgrate!=None:
            tt=burst['chs']["All"]['timetag'][i]
            
            backgT=0
            if isBurst:
                backgT=burst['chs']["All"]['burstW'][i]/2+tt[0]*bgrate["SyncResolution"] #中点时刻
            else:
                backgT=burst['chs']['All']['binMs']*0.5e-3+tt[0]*bgrate["SyncResolution"]
            bgAA=BurstSearch.getBGrateAtT(bgrate,"AexAem",backgT)
            bgDD=BurstSearch.getBGrateAtT(bgrate,"DexDem",backgT)
            bgDA=BurstSearch.getBGrateAtT(bgrate,"DexAem",backgT)            
        elif not isBurst:
            bgAA= burst['chs']['AexAem']['mean'] + burst['chs']['AexAem']['std']#每个bin中的光子数
            bgDD=burst['chs']['DexDem']['mean']
            bgDA=burst['chs']['DexAem']['mean']

        #print(w)
        nda=0#ch1
        ndd=0;#ch2
        naa=0;#ch3
        nad=0#ch4
        sumdtimed=array("d")
        #sumdtimea=array("d")
        for idxd in range(w):
            d=data[idxd]            
            if d==1:
                nda+=1
                # detime=burst['chs']["All"]['dtime'][i][idxd]*burst["DelayResolution"]-T0*1e-9
                # if detime>=0:
                #     sumdtimea.append(detime)                
            elif d==2:
                ndd+=1
                detime=burst['chs']["All"]['dtime'][i][idxd]*burst["DelayResolution"]-T0*1e-9
                if detime>=0:
                    sumdtimed.append(detime)
            elif d==3:
                naa+=1
            elif d==4:
                nad+=1
                #sumdtimed+=dtime
        if len(sumdtimed)<1:
            continue
        Tau=np.mean(sumdtimed)/(Tau_D)        
        if bgrate!=None:
            if isBurst:
                naa=naa-bgAA*burst['chs']["All"]['burstW'][i]
                ndd=ndd-bgDD*burst['chs']["All"]['burstW'][i]
                nda=nda-bgDA*burst['chs']["All"]['burstW'][i]
                if naa< bgAA*burst['chs']["All"]['burstW'][i] or ndd<0 or nda<0:
                    continue    
            else:
                naa=naa-bgAA*burst['chs']["All"]['binMs']*1e-3
                ndd=ndd-bgDD*burst['chs']["All"]['binMs']*1e-3
                nda=nda-bgDA*burst['chs']["All"]['binMs']*1e-3
                if naa< bgAA*burst['chs']["All"]['binMs']*1e-3 or ndd<0 or nda<0:
                    continue                       
        elif not isBurst:
            naa=naa-bgAA
            ndd=ndd-bgDD
            nda=nda-bgDA
            if naa< bgAA or ndd<0 or nda<0:
                continue            

        if Tau<=1 and w>=binLenT:
            wei.append(w)
            burstTau.append(Tau)
            burst['chs']["All"]['lifetime'][i]=Tau        
            gamma=0.31        
            beta=1.42
            DexDirAem=0.08
            Dch2Ach=0.07            
            if (nda+ndd)==0:
                burstFRET.append(1)
                burst['chs']["All"]['e'][i]=1
            else:
                theFret=(nda*(1-DexDirAem)-Dch2Ach*ndd)/((1-DexDirAem)*nda+(gamma-Dch2Ach)*ndd)
                burstFRET.append(theFret)
                burst['chs']["All"]['e'][i]=theFret
            if (nda+ndd+naa)==0:
                burstSeff.append(1)
                burst['chs']["All"]['s'][i]=1
            else:
                theSeff=((1-DexDirAem)*nda+(gamma-Dch2Ach)*ndd)/ \
                    ((1-DexDirAem)*nda+(gamma-Dch2Ach)*ndd+naa/beta)
                burstSeff.append(theSeff)
                burst['chs']["All"]['s'][i]=theSeff
    if isBurst:
        H, xedges, yedges = np.histogram2d(burstFRET,burstTau, bins=bins, weights=wei)
    else:
        H, xedges, yedges = np.histogram2d(burstFRET,burstTau, bins=bins)
    #print(burstTau[0:100])
    #conn.close()
    # fig, ax = plt.subplots()
    # #plt.subplots_adjust(bottom=0.15)

    # im=plt.imshow(H.transpose()[::-1], interpolation='bessel', \
    #               cmap=cm.jet, \
    #               extent=[min(0,xedges[0]), max(1,xedges[-1]), min(0,yedges[0]), max(1,yedges[-1])])
    #               #extent=[0,1,0,1])
    # plt.colorbar(im)
    # plt.show()


    #rs=RectSect(ax,xedges,yedges)
    #toggle_selector(rs.toggle_selectorRS,plt)
    #RectBuilder(ax,xedges,yedges,rs.toggle_selectorRS)

    #callback = MaxLikehood(ax,burstSeff, burstFRET,burst)
    #axMLH = plt.axes([0.1, 0.02, 0.1, 0.05])

    #bnMLH = Button(axMLH, 'calc ML')
    #bnMLH.on_clicked(callback.calc)
    #import seaborn as sns
    #g = sns.JointGrid(x=burstFRET, y=burstTau)

    #g.plot_marginals(sns.distplot)
    #g.plot_joint(plt.hist2d)
    return burstTau, burstFRET,wei,H,xedges, yedges

if __name__ == '__main__':
    import pickle
    dbname="/home/liuk/proj/data/LS35_RSV86C224C.sqlite"
    dbname="../data/lineardiub/LS9_150pM_poslineardiUb25c101c_alex488cy5_32MHz.sqlite"
    dbTau_D="/home/liuk/proj/data/Tau_D.sqlite"
    br=BGrate.calcBGrate(dbname,20,400)
    if type(br)==type(1):
        exit(-1)
    binTime=2
    sp=1
    if len(sys.argv)>1:
        binTime=float(sys.argv[1])
    if len(sys.argv)>2:
        sp=float(sys.argv[2])        
    # burst=BurstSearch.findBurst(br,dbname,["All"],30,6)
    burst=binRawData.binRawData(br,dbname,binTime)
    binRawData.statsBins(burst)
    binRawData.burstFilter(burst,5.1,4.1,3.1)
    #brD=BGrate.calcBGrate(dbTau_D,20,400)
    #burstD=BurstSearch.findBurst(br,dbTau_D,["All"])

    burstTau, burstFRET,wei,H,xedges, yedges=\
    FretAndLifetime(burst,(30,30),None,4.1,binLenT=sp,S=0.84)
    title= "bin:"+str(binTime)+"ms,photon# threshold:"+str(sp)
    # with open('E:/tmp/objs.pickle', 'wb') as f:  # Python 3: open(..., 'wb')
    #     pickle.dump([burstSeff, burstFRET,wei,H,xedges], f)

    # sys.path.append('./ui')
    # from qtPlot import ControlMainWindow 
    # from PyQt5 import QtWidgets
    # app = QtWidgets.QApplication(sys.argv)
    # mySW = ControlMainWindow(H,xedges, yedges,title)
    # mySW.show()
    # sys.exit(app.exec_())
    
    import matplotlib.cm as cm
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots()
    im=ax.imshow(H.transpose()[::-1], interpolation='sinc', \
                       cmap=cm.jet,extent=[0,1,0,1])
    ax.set_title(title)
    fig.colorbar(im)                       
    plt.show()
    
    # import matplotlib.pyplot as plt
    # plt.hist(burstFRET, bins=50,weights=wei) 
    # plt.title(title)
    # plt.show()
