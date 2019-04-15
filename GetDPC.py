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

_ = gettext.gettext

class DPCExtension(object):
    extension_id = "GetDPCThisOne"

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
        self.hpass=0.
        self.lpass=0.
        self.toff = 0.
        self.conv = 32.
        self.ri = 0.
        self.ro = self.conv
        self.dpcri = self.ri
        self.dpcro = self.ro
        self.pixcal = 1.
        self.centerfound = False
        self.dpccalculated = False
        self.fieldscalculated = False
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

        ##############################      
        ### Ronchigram Calibration ###
        ##############################

        ### Button and BF Disk Threshold ### 
        CalibrateRonchiRow = ui.create_row_widget()
        cal_button = ui.create_push_button_widget("Calibrate Ronchigram")
        def calclicked():
            try:
                self.ptyuuid=document_window.target_data_item.uuid
                self.CalibrateRonchigram()
            except AttributeError:
                print('AttributeError: Select the 4D-STEM Dataset')
            rcxedit.text = round(self.rcx,1)
            rcyedit.text = round(self.rcy,1)
            pixcaledit.text = round(self.pixcal,1)
        cal_button.on_clicked = calclicked
        CalibrateRonchiRow.add(cal_button)
        CalibrateRonchiRow.add_spacing(6)
        CalibrateRonchiRow.add(ui.create_label_widget("BF Limit (0-1):"))
        ctedit = ui.create_line_edit_widget()
        ctedit.text = round(self.findct,1)
        def ct_editing_finished(ct):
            try:
                if float(self.findct)!=float(ct): print('Changed BF Disk Finding Threshold to '+str(ct))
                self.findct=float(ct)
                ctedit.text = round(self.findct,1)
            except ValueError:
                print('ValueError: Not Changing BF Limit')
                ctedit.text = round(self.findct,1)
            self.UpdateBFDisk()
        ctedit.on_editing_finished = ct_editing_finished
        CalibrateRonchiRow.add(ctedit)
        CalibrateRonchiRow.add_spacing(8)
      
        ### Center X and Y ###
        CalibratedCenterRow = ui.create_row_widget()
        CalibratedCenterRow.add_spacing(8)
        CalibratedCenterRow.add(ui.create_label_widget("Center of Ronchigram (pixels)   X:"))
        rcxedit = ui.create_line_edit_widget()
        rcxedit.text = round(self.rcx,1) 
        def rcx_editing_finished(x):
            try:
                if float(self.rcx)!=float(x): print('Manually Changed Ronchigram Center X Pixel from '+str(self.rcx)+' to '+str(x))
                self.rcx=float(x)
                rcxedit.text = round(self.rcx,1) 
            except ValueError:
                print('ValueError: Not Changing X-Center Position')
                rcxedit.text = round(self.rcx,1) 
            self.UpdateBFDisk()
        rcxedit.on_editing_finished = rcx_editing_finished
        CalibratedCenterRow.add(rcxedit)
        CalibratedCenterRow.add_spacing(8)
        CalibratedCenterRow.add(ui.create_label_widget("Y: "))
        rcyedit = ui.create_line_edit_widget()
        rcyedit.text = round(self.rcy,1) 
        def rcy_editing_finished(y):
            try:
                if float(self.rcy)!=float(y): print('Manually Changed Ronchigram Center Y Pixel from '+str(self.rcy)+' to '+str(y))
                self.rcy=float(y)
                rcyedit.text = round(self.rcy,1)
            except ValueError:
                print('ValueError: Not Changing Y-Center Position')
                rcyedit.text = round(self.rcy,1)
            self.UpdateBFDisk()
        rcyedit.on_editing_finished = rcy_editing_finished
        CalibratedCenterRow.add(rcyedit)
        CalibratedCenterRow.add_spacing(8)
        
        ### Convergence Angle and Calibration Display ###       
        CalibrationParamsRow=ui.create_row_widget()
        CalibrationParamsRow.add_spacing(8)
        CalibrationParamsRow.add(ui.create_label_widget("Conv. Angle (mrad): "))
        convedit = ui.create_line_edit_widget()
        convedit.text = round(self.conv,1)  
        def conv_editing_finished(conv):
            try:
                if float(self.conv)!=float(conv): print('Set Convergence Angle to '+str(conv)+' mrad')
                self.conv=float(conv)
                convedit.text = round(self.conv,1)  
            except ValueError:
                print('ValueError: Not Changing Convergence Angle')
                convedit.text = round(self.conv,1)  
            self.UpdateBFDisk()
        convedit.on_editing_finished = conv_editing_finished
        CalibrationParamsRow.add(convedit)
        CalibrationParamsRow.add_spacing(8)
        CalibrationParamsRow.add(ui.create_label_widget("Cal. (pixels/mrad): "))
        pixcaledit = ui.create_line_edit_widget()
        pixcaledit.text = round(self.pixcal,1)  
        def pixcal_editing_finished(pixcal):
            try:
                if float(self.pixcal)!=float(pixcal): print('Manually Changed Calibration to '+str(self.pixcal)+' pixels per mrad')
                self.pixcal=float(pixcal)
                pixcaledit.text = round(self.pixcal,1)  
            except ValueError:
                print('ValueError: Not Changing Calibration')
                pixcaledit.text = round(self.pixcal,1)  
            self.UpdateBFDisk()
        pixcaledit.on_editing_finished = pixcal_editing_finished
        CalibrationParamsRow.add(pixcaledit)
        CalibrationParamsRow.add_spacing(8)
        
        ### Group and Display ###
        RonchigramCalibration = ui.create_column_widget()
        RonchigramCalibration.add(CalibrateRonchiRow)
        RonchigramCalibration.add(CalibratedCenterRow)
        RonchigramCalibration.add(CalibrationParamsRow)

        ####################################
        ### Image Reconstruction and DPC ### 
        ####################################
        
        ### Set Inner and Outer Angle ###
        SetRadiiRow = ui.create_row_widget()
        SetRadiiRow.add_spacing(8)
        SetRadiiRow.add(ui.create_label_widget("Set Detector Radii (mrad). Inner: "))
        riedit = ui.create_line_edit_widget()
        riedit.text = round(self.ri,1)  
        def ri_editing_finished(ri):
            try:
                if float(self.ri)!=float(ri): print('Set Inner Radius for Image Reconstruction and DPC to '+str(ri)+' mrad')
                self.ri=float(ri)
                riedit.text = round(self.ri,1)  
            except ValueError:
                print('ValueError: Not Changing Inner Radius')
                riedit.text = round(self.ri,1)  
        riedit.on_editing_finished = ri_editing_finished
        SetRadiiRow.add(riedit)
        SetRadiiRow.add_spacing(8)
        SetRadiiRow.add(ui.create_label_widget("Outer: "))
        roedit = ui.create_line_edit_widget()
        roedit.text = round(self.ro,1)  
        def ro_editing_finished(ro):
            try:
                if float(self.ro)!=float(ro): print('Set Outer Detector Radius for Image Reconstruction and DPC to '+str(ro)+' mrad')
                self.ro=float(ro)
                roedit.text = round(self.ro,1)  
            except ValueError:
                print('ValueError: Not Changing Outer Radius')
                roedit.text = round(self.ro,1)  
        roedit.on_editing_finished = ro_editing_finished
        SetRadiiRow.add(roedit)
        SetRadiiRow.add_spacing(8)
        
        ### Get Detector Image Button ###
        GetDIButtonRow = ui.create_row_widget()
        getdi_button = ui.create_push_button_widget("Get Detector Image")
        def GetDI_clicked():
            self.GetDetectorImage()
        getdi_button.on_clicked = GetDI_clicked
        GetDIButtonRow.add(getdi_button)

        ### Calculate Center of Mass Shifts
        GetCOMShiftRow = ui.create_row_widget()
        getcom_button = ui.create_push_button_widget("Get Center of Mass Shifts")
        def GetCOM_clicked():
            self.GetICOM()
        getcom_button.on_clicked = GetCOM_clicked
        GetCOMShiftRow.add(getcom_button)

        ### Get Electric Field Magnitudes and Vectors
        GetERow = ui.create_row_widget()
        gete_button = ui.create_push_button_widget("Get Electric Field")
        def GetE_clicked():
            self.GetEFields()
        gete_button.on_clicked = GetE_clicked
        GetERow.add(gete_button)
        
        ### Reconstruct Atomic Potential with Inverse Gradient 
        GetPOTRow = ui.create_row_widget()
        getpot_button = ui.create_push_button_widget("Get Atomic Potential")
        def GetPOT_clicked():
            self.GetPotential()
        getpot_button.on_clicked = GetPOT_clicked
        GetPOTRow.add(getpot_button)
 
        ### Set High Pass Filtering 
        GetPOTRow.add(ui.create_label_widget("High Pass:"))
        hpedit = ui.create_line_edit_widget()
        hpedit.text = self.hpass
        def hp_editing_finished(hp):
            try:
                if float(self.hpass)!=float(hp): print('Set High Pass Filter for Potential Reconstruction to '+str(hp))
                self.hpass=float(hp)
                hpedit.text = self.hpass  
            except ValueError:
                print('GotValueError: Did not change High Pass Filter')
                hpedit.text = self.hpass
        hpedit.on_editing_finished = hp_editing_finished
        GetPOTRow.add(hpedit)
        GetPOTRow.add_spacing(8)
        
        ### Set Low Pass Filtering 
        GetPOTRow.add(ui.create_label_widget("Low Pass:"))
        lpedit = ui.create_line_edit_widget()
        lpedit.text = self.lpass
        def lp_editing_finished(lp):
            try:
                if float(self.lpass)!=float(lp): print('Set High Pass Filter for Potential Reconstruction to '+str(lp))
                self.lpass=float(lp)
                lpedit.text = self.lpass  
            except ValueError:
                print('GotValueError: Did not change High Pass Filter')
                lpedit.text = self.lpass
        lpedit.on_editing_finished = lp_editing_finished
        GetPOTRow.add(lpedit)
        
        ### Group and Display ###
        DPC=ui.create_column_widget()
        DPC.add(SetRadiiRow)
        DPC.add(GetDIButtonRow)
        DPC.add(GetCOMShiftRow)
        DPC.add(GetERow)
        DPC.add(GetPOTRow)
        
        #########################
        ### Clear Stored Data ###
        #########################

        ClearRow = ui.create_row_widget()
        clear_button = ui.create_push_button_widget("Clear Stored Data")
        def CLEAR():
            self.cleardpcuuid()
        clear_button.on_clicked = CLEAR
        ClearRow.add(clear_button)

        Menu = ui.create_column_widget()
        Menu.add(RonchigramCalibration) 
        Menu.add_spacing(24)
        Menu.add(DPC)
        Menu.add_spacing(8)
        Menu.add(ClearRow)
        return Menu

##########################################
##########################################
####### Functions for DPC Analysis #######
##########################################
##########################################

    def UpdateBFDisk(self):
        #Updates Annotation of circle around BF disk
        if self.ptyuuid==None: return
        pty=self.api.library.get_data_item_by_uuid(self.ptyuuid)
        daty,datx=pty.data.shape[2:]
        frcx=self.rcx/float(datx);frcy=self.rcy/float(daty);fr=self.conv*self.pixcal/float(datx)
        if len(pty.graphics)<1.:
            pty.add_ellipse_region(center_y=frcy,center_x=frcx,height=2*fr,width=2*fr)
        else: pty.graphics[0].bounds=((frcy-fr,frcx-fr),(2*fr,2*fr))

    def CalibrateRonchigram(self):
        pty=self.api.library.get_data_item_by_uuid(self.ptyuuid)
        R=np.sum(pty.data,axis=(0,1))
        try: NY,NX=R.shape[:2]
        except ValueError: print('ValueError: Select the 4D-STEM Dataset');return
        Rn=((R-np.amin(R))/np.ptp(R))
        BFdisk=np.ones(R.shape)*(Rn>self.findct)
        xx,yy = np.meshgrid(np.arange(0,NY), np.arange(0,NX))
        self.rcx = np.sum(BFdisk*xx/np.sum(BFdisk))
        self.rcy = np.sum(BFdisk*yy/np.sum(BFdisk))
        edge=(np.sum(np.abs(np.gradient(BFdisk)),axis=0))>self.findct
        self.pixcal=np.average(np.sqrt((xx-self.rcx)**2+(yy-self.rcy)**2)[edge])/self.conv
        print('Calibrated Ronchigrams. Sub-Pixel Center of BF Disk: X-'+str(round(self.rcx,2))+' Y-'+str(round(self.rcy,2))+'    Calibration: '+str(round(self.pixcal,2))+' pixels/mrad')
        if len(pty.graphics)<1:
            daty,datx=R.data.shape
            frcx=self.rcx/float(datx);frcy=self.rcy/float(daty);fr=self.conv*self.pixcal/float(datx)
            pty.add_ellipse_region(center_y=frcy,center_x=frcx,height=2*fr,width=2*fr)
        else: self.UpdateBFDisk()

    def GetICOM(self):
        pty=self.api.library.get_data_item_by_uuid(self.ptyuuid)
        dims=pty.data.shape
        xx,yy = np.meshgrid((np.arange(0,dims[3])-self.rcx)*self.pixcal,(np.arange(0,dims[2])-self.rcy)*self.pixcal)
        maskdat=pty.data*((xx**2+yy**2<self.dpcro**2)&(xx**2+yy**2>=self.dpcri**2))
        icomx,icomy=np.average(maskdat*xx,axis=(2,3)),np.average(maskdat*yy,axis=(2,3))
        self.comx=icomx*np.cos(self.toff)+icomy*np.sin(self.toff)
        self.comy=-icomx*np.sin(self.toff)+icomy*np.cos(self.toff)
        print('Calculated Center of Mass Shifts Based on Camera/Scan Angle Offset of '+str(round(self.toff,1))+' radians`')
        if not self.dpccalculated:
            self.api.library.create_data_item_from_data(self.comx)
            self.comxuuid=self.api.library.data_items[-1].uuid
            self.api.library.create_data_item_from_data(self.comy)
            self.comyuuid=self.api.library.data_items[-1].uuid
            self.dpccalculated=True
        else:
            COMX = self.api.library.get_data_item_by_uuid(self.comxuuid)
            COMX.data=self.comx
            COMY = self.api.library.get_data_item_by_uuid(self.comyuuid)
            COMY.data=self.comy

    def GetEFields(self):
        import matplotlib.colors
        EX=-self.comx;EY=-self.comy
        EMAG=np.sqrt(EX**2+EY**2)
        XY=np.zeros(EX.shape+(3,),dtype=float)
        M=np.amax(EMAG)
        for i in range(EX.shape[0]):
            for j in range(EX.shape[1]):
                XY[i,j]=np.angle(np.complex(EX[i,j],EY[i,j]))/(2*np.pi)%1,1,EMAG[i,j]/M
        self.EIM=EMAG
        self.CIMxd=xd.rgb(*np.transpose(matplotlib.colors.hsv_to_rgb(XY),(2,0,1)))
        if not self.fieldscalculated:
            self.api.library.create_data_item_from_data(self.EIM)
            self.EIMuuid=self.api.library.data_items[-1].uuid
            self.api.library.create_data_item()
            self.CIMuuid=self.api.library.data_items[-1].uuid
            cimdataitem=self.api.library.get_data_item_by_uuid(self.CIMuuid)
            cimdataitem.xdata=self.CIMxd
            self.fieldscalculated=True
        else:
            eim = self.api.library.get_data_item_by_uuid(self.EIMuuid)
            eim.data=self.EIM
            cimdataitem=self.api.library.get_data_item_by_uuid(self.CIMuuid)
            cimdataitem.xdata=self.CIMxd

    def GetPotential(self):
        print("Getting Here")
        X=self.comx;Y=self.comy
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
        dims=pty.shape
        xx,yy = np.meshgrid((np.arange(0,dims[3])-self.rcx)*self.pixcal,(np.arange(0,dims[2])-self.rcy)*self.pixcal) 
        detim=np.sum(pty*((xx**2+yy**2>=self.ri**2) & (xx**2+yy**2<self.ro**2)),axis=(2,3))
        self.api.library.create_data_item_from_data(detim)

    def cleardpcuuid(self):
        ptyuuid=None
        self.dpccalculated=False
        self.fieldscalculated=False
        self.vimcalculated=False
