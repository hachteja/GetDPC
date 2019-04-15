# standard libraries
import gettext
import logging
import numpy as np
import scipy
import threading

# third party libraries
from nion.data import Calibration
from nion.data import DataAndMetadata
from nion.data import xdata_1_0 as xd

# local libraries
#from nion.swift.model import HardwareSource
#from nion.typeshed import API_1_0 as API

_ = gettext.gettext

class DPCExtension(object):
    extension_id = "GetDPC"

    def __init__(self, api_broker):
        api = api_broker.get_api(version="1", ui_version="1")
        self.__panel_ref = api.create_panel(GetDPCDelegate(api))
        print('Running!')

    def close(self):
        print('Closed!')
        self.__panel_ref.close()
        self.__panel_ref = None

class GetDPCDelegate(object):
    def __init__(self,api):  
        self.api = api
        self.panel_id = "DPC-panel"
        self.panel_name = _("Fun with 4D-STEM")
        self.panel_positions = ["left", "right"]
        self.panel_position = "right"
        self.findct=0.3
        self.rcx = 0.
        self.rcy = 0.
        self.ri = 0.
        self.ro = 200.
        self.hpass=0.
        self.lpass=0.
        self.toff = 0.
        self.binN = 1
        self.conv = 32.
        self.pixcal = 1.
        self.centerfound = False
        self.dpccalculated = False
        self.cimcalculated = False
        self.vimcalculated = False
        self.comx = None
        self.comy = None
        self.EIM = None
        self.CIM = None
        self.VIM = None
        self.ptyuuid = None
        self.comxuuid = None
        self.comyuuid = None
        self.EIMuuid = None
        self.CIMuuid = None
        self.VIMuuid = None

    def create_panel_widget(self, ui, document_window):#,document_controller):
        Menu = ui.create_column_widget()
#        CalibrationTitleRow = ui.create_row_widget()
#        CalibrationTitleRow.add(ui.create_label_widget('Ronchigram Calibration')
#
        CalibrationTuningRow = ui.create_row_widget()
        CalibrationTuningRow.add(ui.create_label_widget("Convergence Angle (mrad):"))
        convedit = ui.create_line_edit_widget()
        convedit.text = self.conv
        def ct_editing_finished(conv):
            self.conv=float(conv)
            try:
                val = float(conv)
            except ValueError:
                print('GotValueError')
                self.conv=32.
                convedit.text = self.conv
            print('Adjusted Convergence Angle to '+str(ct)+' mrad')
            self.UpdateBFDisk()
        convedit.on_editing_finished = ct_editing_finished
        CalibrationTuningRow.add(convedit)
        CalibrationTuningRow.add_spacing(12)
        
        CalibrationTuningRow.add(ui.create_label_widget("BF Disk Threshold (0-1):"))
        ctedit = ui.create_line_edit_widget()
        ctedit.text = self.findct
        def ct_editing_finished(ct):
            self.findct=float(ct)
            try:
                val = float(ct)
            except ValueError:
                print('GotValueError')
                self.findct=0.3
                ctedit.text = self.findct
            print('Adjusted BF disk calibration threshold to '+str(ct))
            self.UpdateBFDisk()
        ctedit.on_editing_finished = ct_editing_finished
        CalibrationTuningRow.add(ctedit)
        
        CalibrationButtonRow = ui.create_row_widget()
        cal_button = ui.create_push_button_widget("Calibrate!")
        def calclicked():
            self.ptyuuid=document_window.target_data_item.uuid
            self.CalibrateRonchigram()
            rcxedit.text = round(self.rcx,2)
            rcyedit.text = round(self.rcy,2)
        cal_button.on_clicked = calclicked
        CalibrationButtonRow.add(cal_button)
        CalibrationButtonRow.add_spacing(24)
        
        CalibrationParamsRow = ui.create_row_widget()
        CalibrationParamsRow.add(ui.create_label_widget("Calibration (pixels/mrad):"))
        caledit = ui.create_line_edit_widget()
        caledit.text = self.pixcal
        def cal_editing_finished(cal):
            self.pixcal=float(cal)
            try:
                val = float(cal)
            except ValueError:
                print('GotValueError')
                self.pixcal=1
                caledit.text = self.pixcal
            print('MadeItPastTry')
            print(self.pixcal)
            self.UpdateBFDisk()
        caledit.on_editing_finished = cal_editing_finished
        CalibrationParamsRow.add(caledit)
        CalibrationParamsRow.add_spacing(16)
        
        CalibrationParamsRow.add(ui.create_label_widget("Ronchigram Center (pixels)    X:"))
        rcxedit = ui.create_line_edit_widget()
        rcxedit.text = self.rcx 
        def rcx_editing_finished(x):
            if float(self.rcx)!=float(x): print('Manually Changed Ronchigram Center X Pixel from '+str(self.rcx)+' to '+str(x))
            self.rcx=float(x)
            try:
                val = float(x)
            except ValueError:
                print('GotValueError')
                self.rcx=0.
                rcxedit.text = self.rcx
            self.UpdateBFDisk()
        rcxedit.on_editing_finished = rcx_editing_finished
        CalibrationParamsRow.add(rcxedit)
        CalibrationParamsRow.add_spacing(8)
        
        CalibrationParamsRow.add(ui.create_label_widget("Y:"))
        rcyedit = ui.create_line_edit_widget()
        rcyedit.text = self.rcy 
        def rcy_editing_finished(y):
            if float(self.rcy)!=float(y): print('Manually Changed Ronchigram Center Y Pixel from '+str(self.rcy)+' to '+str(y))
            self.rcy=float(y)
            try:
                val = float(y)
            except ValueError:
                print('GotValueError')
                self.rcy=0.
                rcyedit.text = self.rcy
            self.UpdateBFDisk()
        rcyedit.on_editing_finished = rcy_editing_finished
        CalibrationParamsRow.add(rcyedit)
        CalibrationParamsRow.add_spacing(8)
        
        GetDPCRow = ui.create_row_widget()
        getdpc_button = ui.create_push_button_widget("Get DPC from 4D Dataset")
        def GetDPC_clicked():
            self.ComputeDPC()
        getdpc_button.on_clicked = GetDPC_clicked
        GetDPCRow.add(getdpc_button)

        GetCIMRow = ui.create_row_widget()
        getcim_button = ui.create_push_button_widget("Get Field Directions from 4D Dataset")
        def GetCIM_clicked():
            self.GetFieldDirection()
        getcim_button.on_clicked = GetCIM_clicked
        GetCIMRow.add(getcim_button)

        GetDetImRow = ui.create_row_widget()
        getdetim_button = ui.create_push_button_widget("Get Detector Image")
        def GetDETIM_clicked():
            self.GetDetectorImage()
        getdetim_button.on_clicked = GetDETIM_clicked
        GetDetImRow.add(getdetim_button)
        
        GetDIParamsRow = ui.create_row_widget()
        GetDIParamsRow.add(ui.create_label_widget("Inner Radius:"))
        riedit = ui.create_line_edit_widget()
        riedit.text = self.ri
        def ri_editing_finished(ri):
            self.ri=float(ri)
            try:
                val = float(ri)
            except ValueError:
                print('GotValueError')
                self.ri=0.
                riedit.text = self.ri
            print('MadeItPastTry')
            print(self.ri)
           # self.UpdateBFDisk()
        riedit.on_editing_finished = ri_editing_finished
        GetDIParamsRow.add(riedit)
        GetDIParamsRow.add_spacing(8)
        
        GetDIParamsRow.add(ui.create_label_widget("Outer Radius:"))
        roedit = ui.create_line_edit_widget()
        roedit.text = self.ro
        def ro_editing_finished(ro):
            self.ro=float(ro)
            try:
                val = float(ro)
            except ValueError:
                print('GotValueError')
                self.ro=0.
                roedit.text = self.ro
            print('MadeItPastTry')
            print(self.ro)
           # self.UpdateBFDisk()
        roedit.on_editing_finished = ro_editing_finished
        GetDIParamsRow.add(roedit)
        GetDIParamsRow.add_spacing(8)

        GetPOTRow = ui.create_row_widget()
        getpot_button = ui.create_push_button_widget("Get Atomic Potential")
        def GetPOT_clicked():
            self.GetPotential()
        getpot_button.on_clicked = GetPOT_clicked
        GetPOTRow.add(getpot_button)
        
        ClearRow = ui.create_row_widget()
        clear_button = ui.create_push_button_widget("Clear Stored Data")
        def CLEAR():
            self.cleardpcuuid()
        clear_button.on_clicked = CLEAR
        ClearRow.add(clear_button)

        GetPOTRow.add(ui.create_label_widget("High Pass:"))
        hpedit = ui.create_line_edit_widget()
        hpedit.text = self.hpass
        def hp_editing_finished(hp):
            self.hpass=float(hp)
            try:
                val = float(hp)
            except ValueError:
                print('GotValueError')
                self.hp=0.
                hpedit.text = self.hpass
            print('MadeItPastTry')
            print(self.hpass)
           # self.UpdateBFDisk()
        hpedit.on_editing_finished = hp_editing_finished
        GetPOTRow.add(hpedit)
        GetPOTRow.add_spacing(8)

        GetPOTRow.add(ui.create_label_widget("Low Pass:"))
        lpedit = ui.create_line_edit_widget()
        lpedit.text = self.lpass
        def lp_editing_finished(lp):
            self.lpass=float(lp)
            try:
                val = float(lp)
            except ValueError:
                print('GotValueError')
                self.lp=0.
                lpedit.text = self.lpass
            print('MadeItPastTry')
            print(self.lpass)
           # self.UpdateBFDisk()
        lpedit.on_editing_finished = lp_editing_finished
        GetPOTRow.add(lpedit)
        
        Bin4DRow = ui.create_row_widget()
        bin4d_button = ui.create_push_button_widget("Bin Ronchigrams of 4D Dataset")
        def Bin4D_clicked():
            self.ptyuuid=document_window.target_data_item.uuid
            self.GetBinned4D()
        bin4d_button.on_clicked = Bin4D_clicked
        Bin4DRow.add(bin4d_button)

        Bin4DRow.add(ui.create_label_widget("Bin by:"))
        binedit = ui.create_line_edit_widget()
        binedit.text = self.binN
        def bin_editing_finished(n):
            self.binN=int(n)
            try:
                val = int(n)
            except ValueError:
                print('GotValueError')
                self.binN=1
                binedit.text = self.binN
            print('MadeItPastTry')
            print(self.binN)
        binedit.on_editing_finished = bin_editing_finished
        Bin4DRow.add(binedit)
        
#        CalibrateRonchiRow = ui.create_row_widget()
#        cal_button = ui.create_push_button_widget("Calibrate Ronchigrams")
#        def calclicked():
#            self.ptyuuid=document_window.target_data_item.uuid
#            self.CalibrateRonchigram()
#            rcxedit.text = round(self.rcx,2)
#            rcyedit.text = round(self.rcy,2)
#        cal_button.on_clicked = calclicked
#        CalibrateRonchiRow.add(cal_button)
#        CalibrateRonchiRow.add_spacing(24)
        
        FindcParamsrow = ui.create_row_widget()
        FindcParamsrow.add(ui.create_label_widget("Cal. (pix/mrad):"))
        caledit = ui.create_line_edit_widget()
        caledit.text = self.pixcal
        def cal_editing_finished(cal):
            self.pixcal=float(cal)
            try:
                val = float(cal)
            except ValueError:
                print('GotValueError')
                self.pixcal=1
                caledit.text = self.pixcal
            print('MadeItPastTry')
            print(self.pixcal)
            self.UpdateBFDisk()
        caledit.on_editing_finished = cal_editing_finished
        FindcParamsrow.add(caledit)
        FindcParamsrow.add_spacing(16)
        FindcParamsrow.add(ui.create_label_widget("BF Disk Threshold (0-1):"))
        ctedit = ui.create_line_edit_widget()
        ctedit.text = self.findct
        def ct_editing_finished(ct):
            self.findct=float(ct)
            try:
                val = float(ct)
            except ValueError:
                print('GotValueError')
                self.findct=0.3
                ctedit.text = self.findct
            print('MadeItPastTry')
            print(self.findct)
            self.UpdateBFDisk()
        ctedit.on_editing_finished = ct_editing_finished
        FindcParamsrow.add(ctedit)
      
 #       Menu.add(CalibrationTitleRow)
        Menu.add(CalibrationTuningRow)
        Menu.add(CalibrationButtonRow)
        Menu.add(CalibrationParamsRow)
       # Menu.add(CalibrateRonchiRow)
       # Menu.add(rcxcyrow)
        Menu.add(GetDIParamsRow)
        Menu.add(GetDetImRow)
        Menu.add(GetDPCRow)
        Menu.add(GetCIMRow)
        Menu.add(GetPOTRow)
        Menu.add(Bin4DRow)
        Menu.add(ClearRow)
        return Menu

    def CalibrateRonchigram(self):
        #from scipy import ndimage
        pty=self.api.library.get_data_item_by_uuid(self.ptyuuid)
        t=self.findct#;sig=self.findblur
        R=np.sum(pty.data,axis=(0,1))
        NV,NU=R.shape[:2]
        Rn=((R-np.amin(R))/np.ptp(R))
        BFdisk=np.ones(R.shape)*(Rn>t)
        uu,vv = np.meshgrid(np.arange(0,NV), np.arange(0,NU))
        self.rcx = np.sum(BFdisk*uu/np.sum(BFdisk))
        self.rcy = np.sum(BFdisk*vv/np.sum(BFdisk))
	#NY,NX=Rn.shape[:2]
        
        #BFdisk=np.ones(Rn.shape)*(ndimage.gaussian_filter(Rn,sig)>t)
        #xx,yy = np.meshgrid(np.arange(0,NY), np.arange(0,NX))
        #self.rcx = np.sum(BFdisk*xx/np.sum(BFdisk))
        #self.cy = np.sum(BFdisk*yy/np.sum(BFdisk)) + NY/128.###DON'T LEAVE THIS!!!
        print(NV/128.)
        if len(pty.graphics)<1:
            daty,datx=R.data.shape
            frcx=self.rcx/float(datx);frcy=self.rcy/float(daty);fr=self.conv*self.pixcal/float(datx)
            pty.add_ellipse_region(center_y=frcy,center_x=frcx,height=2*fr,width=2*fr)
        else: self.UpdateBFDisk()

    def cleardpcuuid(self):
        ptyuuid=None
        self.dpccalculated=False
        self.cimcalculated=False
        self.vimcalculated=False

    def UpdateBFDisk(self):
        if self.ptyuuid==None: return
        pty=self.api.library.get_data_item_by_uuid(self.ptyuuid)
        daty,datx=pty.data.shape[2:]
        frcx=self.rcx/float(datx);frcy=self.rcy/float(daty);fr=self.conv*self.pixcal/float(datx)
        if len(pty.graphics)<1.:
            pty.add_ellipse_region(center_y=frcy,center_x=frcx,height=2*fr,width=2*fr)
        else: pty.graphics[0].bounds=((frcy-fr,frcx-fr),(2*fr,2*fr))
        
    def ComputeDPC(self):
        pty=self.api.library.get_data_item_by_uuid(self.ptyuuid)
        daty,datx=pty.data.shape[2:]
        fx=2*float(self.rcx+0.5)/datx
        fy=2*float(self.rcy+0.5)/daty
        xran=np.linspace(-fx,2-fx,datx)
        yran=np.linspace(-fy,2-fy,daty)
        xx,yy = np.meshgrid(xran,yran)
        icomx,icomy=np.sum(pty.data*xx,axis=(2,3)),np.sum(pty.data*yy,axis=(2,3))
        self.comx=icomx*np.cos(self.toff)+icomy*np.sin(self.toff)
        self.comy=-icomx*np.sin(self.toff)+icomy*np.cos(self.toff)
        self.EIM=np.sqrt(icomx**2+icomy**2)
        if not self.dpccalculated:
            self.api.library.create_data_item_from_data(self.comx)
            self.comxuuid=self.api.library.data_items[-1].uuid
            self.api.library.create_data_item_from_data(self.comy)
            self.comyuuid=self.api.library.data_items[-1].uuid
            self.api.library.create_data_item_from_data(self.EIM)
            self.EIMuuid=self.api.library.data_items[-1].uuid
            self.dpccalculated=True
        else:
            COMX = self.api.library.get_data_item_by_uuid(self.comxuuid)
            COMX.data=self.comx
            COMY = self.api.library.get_data_item_by_uuid(self.comyuuid)
            COMY.data=self.comy
            eim = self.api.library.get_data_item_by_uuid(self.EIMuuid)
            eim.data=self.EIM

    def GetFieldDirection(self):
        print("Getting Here")
        import matplotlib.colors
        X=self.comx;Y=self.comy
        XY=np.zeros(X.shape+(3,),dtype=float)
        Eint=np.sqrt(X**2+Y**2)
        M=np.amax(Eint)
        for i in range(X.shape[0]):
            for j in range(X.shape[1]):
                XY[i,j]=np.angle(np.complex(X[i,j],Y[i,j]))/(2*np.pi)%1,1,Eint[i,j]/M
        self.CIMxd=xd.rgb(*np.transpose(matplotlib.colors.hsv_to_rgb(XY),(2,0,1)))
        if not self.cimcalculated:
            self.api.library.create_data_item()
            self.CIMuuid=self.api.library.data_items[-1].uuid
            cimdataitem=self.api.library.get_data_item_by_uuid(self.CIMuuid)
            cimdataitem.xdata=self.CIMxd
            self.cimcalculated=True
        else:
            cimdataitem=self.api.library.get_data_item_by_uuid(self.CIMuuid)
            cimdataitem.xdata=self.CIMxd

    def GetPotential(self):
        print("Getting Here")
        X=-self.comx;Y=-self.comy
        fCX=np.fft.fftshift(np.fft.fft2(np.fft.fftshift(X)))   
        fCY=np.fft.fftshift(np.fft.fft2(np.fft.fftshift(Y)))
        KX=fCX.shape[1];KY=fCY.shape[0]
        kxran=np.linspace(-1,1,KX,endpoint=True)
        kyran=np.linspace(-1,1,KY,endpoint=True)
        kx,ky=np.meshgrid(kxran,kyran)
        fCKX=fCX*kx;fCKY=fCY*ky;fnum=(fCKX+fCKY)
        fdenom=np.pi*2*(0+1j)*(self.hpass+(kx**2+ky**2)+self.lpass*(kx**2+ky**2)**2)
        fK=np.divide(fnum,fdenom)
        self.VIM=np.real(np.fft.ifftshift(np.fft.ifft2(np.fft.ifftshift(fK))))
        if not self.vimcalculated:
            self.api.library.create_data_item_from_data(self.VIM)
            self.VIMuuid=self.api.library.data_items[-1].uuid
            self.vimcalculated=True
        else:
            vim = self.api.library.get_data_item_by_uuid(self.VIMuuid)
            vim.data=self.VIM

    def GetDetectorImage(self):
        pty=self.api.library.get_data_item_by_uuid(self.ptyuuid).data
        X=pty.shape[3];Y=pty.shape[2]
        fx=self.rcx+0.5;fy=self.rcy+.05
        xran=np.linspace(-fx,X-fx,X)
        yran=np.linspace(-fy,Y-fy,Y)
        xx,yy = np.meshgrid(xran*self.pixcal,yran*self.pixcal) 
        detim=np.sum(pty*((xx**2+yy**2>=self.ri**2) & (xx**2+yy**2<self.ro**2)),axis=(2,3))
        self.api.library.create_data_item_from_data(detim)

    def GetBinned4D(self):
        N=self.binN
        pty=self.api.library.get_data_item_by_uuid(self.ptyuuid).data
        NY,NX=int(pty.shape[2]/N),int(pty.shape[3]/N)
        ptybin=np.zeros((pty.shape[0],pty.shape[1],NY,NX))
        for i in range(NY):
            for j in range(NX):
                ptybin[:,:,i,j]=np.sum(pty[:,:,N*i:N*(i+1),N*j:N*(j+1)],axis=(2,3))
        self.api.library.create_data_item_from_data(ptybin)
