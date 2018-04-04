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
import irf_decov
from array import array

import pickle


#burstD如果是浮点数，则为Donor only的TauD，否则为Donor only的提取的burst
def FretAndLifetime(burst,bins=(25,25),bgrate=None,burstD=4.1,bgrateD=None,\
        T0=6.8695,binLenT=30,S=0,ESm='k',byBurst=False,bgfilter=True,histIRF=None,sampleNum=20):

    rESm=0
    if ESm=='K' or ESm=='k':
        rESm=0
    else:
        rESm=1

    Tau_D=1e-9
    if type(burstD) is float:
        Tau_D=burstD*1e-9
        print('已经制定TauD')
    else:
        lenburstD=len(burstD['chs']["All"]['chl'])
        burstTauD = array("d")#np.zeros(lenburst)
        weiD = array("d")#np.zeros(lenburst)
            
        for i in range(lenburstD):
            data=burstD['chs']["All"]['chl'][i]
            if bgrateD!=None:
                tt=burstD['chs']["All"]['timetag'][i]
                #print(tt)
                backgT=burstD['chs']["All"]['burstW'][i]/2+tt[0]*bgrate["SyncResolution"] #中点时刻
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
                    sumdtimed.append(burstD['chs']["All"]['dtime'][i][idxd]*burstD["DelayResolution"]*1e9)
                elif d==3:
                    naa+=1
                elif d==4:
                    nad+=1                
            if bgrateD!=None:
                naa=naa-bgAA*burstD['chs']["All"]['burstW'][i]
                ndd=ndd-bgDD*burstD['chs']["All"]['burstW'][i]
                nda=nda-bgDA*burstD['chs']["All"]['burstW'][i]
                if naa< bgAA*burstD['chs']["All"]['burstW'][i] or ndd<0 or nda<0:
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
            fretAndS.FretAndS(burst,bins,bgrate,False,ESm)
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
    Tau_D=4.2e-9
    print('Tau_D:',Tau_D)

    burstFRET = array("d")#np.zeros(lenburst)
    burstSeff = array("d")#np.zeros(lenburst)
    burstTau = array("d")#np.zeros(lenburst)
    wei = array("d")#np.zeros(lenburst)
    markDel=False
    if 'markDel' in burst['chs']["All"]:
            markDel=True
            print("markDel")
    isBurst=False
    if 'burstW' in burst['chs']["All"]:
        isBurst=True
        print("isBurst")
    if not byBurst:
        print('no byBurst')
        for i in range(lenburst):    
            if markDel:
                if burst['chs']['All']['markDel'][i]:
                    continue
            # if burst['chs']['All']['s'][i]>0.83 or burst['chs']['All']['s'][i]<0.11:
            #     continue
            data=burst['chs']["All"]['chl'][i]
            w=len(data)
            if type(w)!=type(1):
                continue
            if len(data)<1:
                continue
            bgAA=0
            bgDD=0
            bgDA=0  
            if bgfilter:
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
                    bgAA= burst['chs']['All']['AAmean'] + burst['chs']['All']['AAstd']#每个bin中的光子数
                    bgDD=burst['chs']['All']['DDmean']
                    bgDA=burst['chs']['All']['DAmean']

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
                    if True:#detime>=0:
                        sumdtimed.append(detime)
                elif d==3:
                    naa+=1
                elif d==4:
                    nad+=1
                    #sumdtimed+=dtime
            lensumdtimed=len(sumdtimed)                                
            if lensumdtimed<1:
                Tau=0            
            else:            
                Tau=np.mean(sumdtimed)/(Tau_D)  
            goodTau=False
            if lensumdtimed>20 and histIRF!=None:
                cTau,rchi=irf_decov.calcTauOf1Bin(histIRF,burst,i,sampleNum,T0,'leastsq')
                if rchi>=1 and rchi<5000:
                    Tau=cTau*1e-9/(Tau_D)
                    goodTau=True
                    # print("cTau:",cTau,"rchi",rchi)
            if bgfilter:      
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
            if (goodTau or histIRF==None) and Tau<=1 and Tau>=0.0:                                  
                burst['chs']["All"]['lifetime'][i]=Tau        
                gamma=0.34   
                beta=1.42
                DexDirAem=0.08
                Dch2Ach=0.07 
                e=0;s=0           
                if (nda+ndd)==0:
                    burstFRET.append(1)                    
                    e=1
                else:
                    if rESm==0:
                        e=(nda)/(nda+gamma*ndd)
                    else:                
                        e=(nda*(1-DexDirAem)-Dch2Ach*ndd)/((1-DexDirAem)*nda+(gamma-\
                            Dch2Ach)*ndd)                                                        
                if (nda+ndd+naa)==0:
                    s=1
                else:
                    if rESm==0:
                        s=(nda+gamma*ndd)/(nda+gamma*ndd+naa/beta)
                    else:
                        s=((1-DexDirAem)*nda+(gamma-Dch2Ach)*ndd)/ \
                            ((1-DexDirAem)*nda+(gamma-Dch2Ach)*ndd+naa/beta)
                if s>=0 and s<=1 and e>=0 and e<=1:
                    burst['chs']["All"]['s'][i]=s
                    burst['chs']["All"]['e'][i]=e
                    if isBurst:
                        wei.append(w)
                        burstFRET.append(e)
                        burstSeff.append(s)
                        burstTau.append(Tau)                        
                    else:
                        weis=[s]*w;weie=[e]*w
                        wTau=[Tau]*w
                        burstFRET.extend(weie)
                        burstSeff.extend(weis)
                        burstTau.extend(wTau)
                    
    else:  #byBurst
        lenburst=len(burst['chs']['All']['burst'])
        for j in range(lenburst):
            burstNumTh=burst['chs']['All']['burst'][j]
            # print(burstNumTh)
            data=[]
            sumw=array("l")   
            nda=0#ch1
            ndd=0;#ch2
            naa=0;#ch3
            nad=0#ch4
            sumdtimed=array("d")            
            for i in range(burstNumTh[0],burstNumTh[1]+1):
                w=burst['chs']["All"]['ntag'][i]
                sumw.append(w)
                for idxd in range(w):
                    d=burst['chs']["All"]['chl'][idxd]        
                    if d==1:
                        nda+=1            
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
            if True:#Tau<=1 and w>=binLenT:
                wei.append(np.sum(sumw))
                burstTau.append(Tau)
                # burst['chs']["All"]['lifetime'][i]=Tau        
                gamma=0.31        
                beta=1.42
                DexDirAem=0.08
                Dch2Ach=0.07 
                e=0;s=0           
                if (nda+ndd)==0:
                    burstFRET.append(1)             
                else:
                    if rESm==0:
                        e=(nda)/(nda+gamma*ndd)
                    else:                
                        e=(nda*(1-DexDirAem)-Dch2Ach*ndd)/((1-DexDirAem)*nda+(gamma-\
                            Dch2Ach)*ndd)                
                    burstFRET.append(e)
                if (nda+ndd+naa)==0:
                    burstSeff.append(1)                
                else:
                    if rESm==0:
                        s=(nda+gamma*ndd)/(nda+gamma*ndd+naa/beta)
                    else:
                        s=((1-DexDirAem)*nda+(gamma-Dch2Ach)*ndd)/ \
                            ((1-DexDirAem)*nda+(gamma-Dch2Ach)*ndd+naa/beta)
                    burstSeff.append(s)
                                      
    if isBurst:
        H, xedges, yedges = np.histogram2d(burstFRET,burstTau, bins=bins, weights=wei)
    else:
        print("no wei")
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
def usage():  
    print("Usage:%s -i|--sqlite inputfilename.sqlite -o|--pickle outputfilename.pickle -b|--binms bintimeinMs" % sys.argv[0])

if __name__ == '__main__':
    import pickle,sys,getopt
    irfdbname="data/alexa488_IRF_32MHz_PIE_3KCPS.sqlite"
    dbname="/dataB/smfretData/21c_224c.sqlite"
    dbTau_D="/home/liuk/proj/data/Tau_D.sqlite"
    dbname="data/21c_224c.sqlite"
    binTime=1    
    sp=0
    savefn=''
    try:  
        opts, args = getopt.getopt(sys.argv[1:], "i:o:b:", ["sqlite=", "pickle=", "binms="])  
        for o, v in opts: 
            if o in ("-i", "--sqlite"):
                dbname=v
            if o in ("-o", "--pickle"):
                savefn = v
            if o in ("-b", "--binms"):
                binMs = float(v)
    except getopt.GetoptError:  
        # print help information and exit:  
        print("getopt error!")    
        usage()    
        sys.exit(1)

    br=BGrate.calcBGrate(dbname,20,400)#,30,500)
    if type(br)==type(1):
        exit(-1)        
    burst=BurstSearch.findBurst(br,dbname,["All"],30,6)
    # burst=binRawData.binRawData(br,dbname,binTime)
    # binRawData.statsBins(burst)
    # bgAA= burst['chs']['All']['AAmean'] + burst['chs']['All']['AAstd']#每个bin中的光子数
    # bgDD=burst['chs']['All']['DDmean']    
    # bgDA=burst['chs']['All']['DAmean']
    # print("bgDD",bgDD,"bgDA",bgDA,"e",bgDA/(bgDA+bgDD))
    # dddaaaT=[bgDD,bgDA,bgAA,bgDD+bgDA]
    # binRawData.burstFilterByBin(burst,dddaaaT)
    # binRawData.statsBins(burst)
    #brD=BGrate.calcBGrate(dbTau_D,20,400)
    #burstD=BurstSearch.findBurst(br,dbTau_D,["All"])
    sampleNum=20
    # irfbr=BGrate.calcBGrate(irfdbname,20,400)#,T0=0.0,Tlen=600)
    # irfbinData=binRawData.binRawData(irfbr,irfdbname,binTime)        
    # hi,bi=binRawData.statsDelayTime(irfbinData,sampleNum,"D")#,bin0=100,binLen=2)

    burstTau, burstFRET,wei,H,xedges, yedges=\
    FretAndLifetime(burst,(27,27),None,4.1,binLenT=sp,S=0.86,ESm='z',byBurst=False\
            ,bgfilter=False,sampleNum=sampleNum) #,histIRF=hi
    # title= "bin:"+str(binTime)+"ms,E-Lifetime"
    # savefn='data/rawRes/rsv/'+\
    #     dbname.split('/')[-1].split('.')[-2]+'_'+str(binTime)+'_'+\
    #     str(dddaaaT)+".pickle"
    if len(savefn)>0:
        with open(savefn, 'wb') as f:  # Python 3: open(..., 'wb')
            pickle.dump([burstTau, burstFRET,burst], f,protocol=-1)
    # sys.path.append('./ui')
    # from qtPlot import ControlMainWindow 
    # from PyQt5 import QtWidgets
    # app = QtWidgets.QApplication(sys.argv)
    # mySW = ControlMainWindow(H,xedges, yedges,title)
    # mySW.show()
    # sys.exit(app.exec_())
    
    import matplotlib.cm as cm
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(2,1)
    im=ax[1].imshow(H.transpose()[::-1], interpolation='sinc', \
                       cmap=cm.jet,extent=[xedges[0],xedges[-1],yedges[0],yedges[-1]])
    # ax[1].set_title(title)
    fig.colorbar(im)                       
    
    # import matplotlib.pyplot as plt
    ax[0].hist(burstFRET, bins=40) 
    # plt.title(title)
    plt.show()