# standard libraries
import gettext
import logging
import numpy as np
import scipy
import threading

# local libraries
from getdpc import GetDPC

# third party libraries
from nion.data import Calibration
from nion.data import DataAndMetadata
from nion.data import xdata_1_0 as xd

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
        self.panel_name = _("Get DPC")
        self.panel_positions = ["left", "right"]
        self.panel_position = "right"
        self.findct=0.3
        self.absct=0.
        self.rcx = 0.
        self.rcy = 0.
        self.hpass=0.
        self.lpass=0.
        self.rotation=0.
        self.conv = 32.
        self.ri = 0.
        self.ro = self.conv*1.1
        self.dpcri = self.ri
        self.dpcro = self.ro
        self.pixcal = 1.
        self.centerfound = False
        self.detimgenerated=False
        self.dpccalculated = False
        self.rhocalculated = False
        self.fieldscalculated = False
        self.vimcalculated = False
        self.dpcx = None
        self.dpcy = None
        self.RHO = None
        self.EIM = None
        self.CIM = None
        self.CLEG = None
        self.VIM = None
        self.dat4duuid = None
        self.dpcxuuid = None
        self.dpcyuuid = None
        self.RHOuuid = None
        self.EIMuuid = None
        self.CIMuuid = None
        self.CLEGuuid = None
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
                self.dat4duuid=document_window.target_data_item.uuid
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
        ctedit.text = round(self.findct,2)
        def ct_editing_finished(ct):
            try:
                if float(self.findct)!=float(ct): print('Changed BF Disk Finding Threshold to '+str(ct))
                self.findct=float(ct)
                ctedit.text = round(self.findct,2)
            except ValueError:
                print('ValueError: Not Changing BF Limit')
                ctedit.text = round(self.findct,2)
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
                if float(self.rcx)!=float(x): print('Changed Ronchigram Center X Pixel from '+str(self.rcx)+' to '+str(x))
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
                if float(self.rcy)!=float(y): print('Changed Ronchigram Center Y Pixel from '+str(self.rcy)+' to '+str(y))
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
                if float(self.pixcal)!=float(pixcal): print('Changed Calibration to '+str(self.pixcal)+' pixels per mrad')
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

        ##############################################
        ### Calculate DPC and Reconstructed Images ###
        ##############################################
        
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
        
        ### Calculate Rotation from PLs ### 
        CalculatePLRotationRow = ui.create_row_widget()
        rot_button = ui.create_push_button_widget("Get PL Rotation")
        def rotclicked():
            self.CalculateRotation()
            rotedit.text = int(self.rotation*180./np.pi)
        rot_button.on_clicked = rotclicked
        CalculatePLRotationRow.add(rot_button)
        CalculatePLRotationRow.add_spacing(6)
        CalculatePLRotationRow.add(ui.create_label_widget("Rot. (deg):"))
        rotedit = ui.create_line_edit_widget()
        rotedit.text = int(self.rotation*180./np.pi)
        def rot_editing_finished(rot):
            try:
                if float(round(self.rotation,3))!=round(float(rot)*np.pi/180.,3): 
                    print('Changed PL Rotation Angle to '+str(round(float(rot),1)))
                self.rotation=float(rot)*np.pi/180.
                rotedit.text = round(float(rot),1)
            except ValueError:
                print('ValueError: Not Changing PL Rotation')
                rotedit.text = round(self.rotation*180./np.pi,1)
            self.UpdateBFDisk()
        rotedit.on_editing_finished = rot_editing_finished
        CalculatePLRotationRow.add(rotedit)
        CalculatePLRotationRow.add_spacing(8)

        ### Group and Display ###
        DPC=ui.create_column_widget()
        DPC.add(SetRadiiRow)
        DPC.add(GetDIButtonRow)
        DPC.add(GetCOMShiftRow)
        DPC.add(CalculatePLRotationRow)

        #########################################
        ### Calculate Electrostatics from DPC ###
        #########################################
      
        ### Get Electric Field Magnitudes and Vectors
        GetRhoRow = ui.create_row_widget()
        getrho_button = ui.create_push_button_widget("Get Charge Density")
        def GetRho_clicked():
            self.GetChargeDensity()
        getrho_button.on_clicked = GetRho_clicked
        GetRhoRow.add(getrho_button)

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
        PotParamRow = ui.create_row_widget()
        PotParamRow.add_spacing(8)
        PotParamRow.add(ui.create_label_widget("High Pass:"))
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
        PotParamRow.add(hpedit)
        PotParamRow.add_spacing(8)
        
        ### Set Low Pass Filtering 
        PotParamRow.add(ui.create_label_widget("Low Pass:"))
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
        PotParamRow.add(lpedit)
        
        ### Group and Display ###
        Electro=ui.create_column_widget()
        Electro.add(GetRhoRow)
        Electro.add(GetERow)
        Electro.add(GetPOTRow)
        Electro.add(PotParamRow)
        
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
        Menu.add_spacing(24)
        Menu.add(Electro)
        Menu.add_spacing(8)
        Menu.add(ClearRow)
        Menu.add_stretch()
        return Menu

##########################################
##########################################
####### Functions for DPC Analysis #######
##########################################
##########################################

    def UpdateBFDisk(self):
        #Updates Annotation of circle around BF disk
        if self.dat4duuid==None: return
        dat4d=self.api.library.get_data_item_by_uuid(self.dat4duuid)
        daty,datx=dat4d.data.shape[2:]
        frcx=self.rcx/float(datx);frcy=self.rcy/float(daty);fr=self.conv*self.pixcal/float(datx)
        if len(dat4d.graphics)<1.:
            dat4d.add_ellipse_region(center_y=frcy,center_x=frcx,height=2*fr,width=2*fr)
        else: dat4d.graphics[0].bounds=((frcy-fr,frcx-fr),(2*fr,2*fr))

    def CalibrateRonchigram(self):
        dat4d=self.api.library.get_data_item_by_uuid(self.dat4duuid)
        R, rcx, rcy, pixcal, BFdisk, absct, edge = GetDPC.CalibrateRonchigram(dat4d.data, self.conv, self.findct)
        try:
            NY, NX = R.shape[:2]
        except ValueError:
            print('ValueError: Select the 4D-STEM Dataset')
            return
        self.absct = absct
        self.rcx = rcx
        self.rcy = rcy
        self.pixcal=pixcal
        print('Calibrated Ronchigrams. Sub-Pixel Center of BF Disk: X-'+str(round(self.rcx,2))+' Y-'+str(round(self.rcy,2))+'    Calibration: '+str(round(self.pixcal,2))+' pixels/mrad')
        if len(dat4d.graphics)<1:
            daty,datx=R.data.shape
            frcx=self.rcx/float(datx);frcy=self.rcy/float(daty);fr=self.conv*self.pixcal/float(datx)
            dat4d.add_ellipse_region(center_y=frcy,center_x=frcx,height=2*fr,width=2*fr)
        else: self.UpdateBFDisk()

    def CalculateRotation(self):
        def DPC_ACD(DPCX,DPCY,tlow,thigh):        
            A,C,D=[],[],[]
            for t in np.linspace(tlow,thigh,10,endpoint=False):            
                rDPCX,rDPCY=DPCX*np.cos(t)+DPCY*np.sin(t),-DPCX*np.sin(t)+DPCY*np.cos(t)        
                gXY,gXX=np.gradient(rDPCX);gYY,gYX=np.gradient(rDPCY)        
                C.append(np.std(gXY-gYX));D.append(np.std(gXX+gYY));A.append(t)
            G=np.average([A[np.argmin(C)],A[np.argmax(D)]])
            return G
        DPCX,DPCY=self.dpcx,self.dpcy
        G=DPC_ACD(DPCX,DPCY,0,np.pi)
        for i in range(1,3): G=DPC_ACD(DPCX,DPCY,G-np.pi/(10**i),G+np.pi/(10**i))
        self.rotation=GetDPC.GetPLRotation(self.dpcx,self.dpcy)
        print('Calculated PL Rotation Angle as '+str(round(self.rotation*180/np.pi,1))+' degrees`')

    def GetICOM(self):
        dat4d=self.api.library.get_data_item_by_uuid(self.dat4duuid)
        self.dpcx, self.dpcy = GetDPC.GetiCoM(dat4d.data, self.rcx, self.rcy, self.pixcal, self.ri, self.ro)
        rdpcx=self.dpcx*np.cos(self.rotation)-self.dpcy*np.sin(self.rotation)
        rdpcy=self.dpcx*np.sin(self.rotation)+self.dpcy*np.cos(self.rotation)
        print('Calculated DPC from Center of Mass Shifts')
        if not self.dpccalculated:
            self.api.library.create_data_item_from_data(rdpcx)
            self.dpcxuuid=self.api.library.data_items[-1].uuid
            self.api.library.create_data_item_from_data(rdpcy)
            self.dpcyuuid=self.api.library.data_items[-1].uuid
            self.dpccalculated=True
            DPCX = self.api.library.get_data_item_by_uuid(self.dpcxuuid)
            DPCY = self.api.library.get_data_item_by_uuid(self.dpcyuuid)
            DPCX.title=('CoM Shifts X-Component (Rotation='+str(round(self.rotation*180/np.pi,1))+' degrees)')
            DPCY.title=('CoM Shifts Y-Component (Rotation='+str(round(self.rotation*180/np.pi,1))+' degrees)')
        else:
            DPCX = self.api.library.get_data_item_by_uuid(self.dpcxuuid)
            DPCX.data=rdpcx
            DPCY = self.api.library.get_data_item_by_uuid(self.dpcyuuid)
            DPCY.data=rdpcy
            DPCX.title=('CoM Shifts X-Component (Rotation='+str(round(self.rotation*180/np.pi,1))+' degrees)')
            DPCY.title=('CoM Shifts Y-Component (Rotation='+str(round(self.rotation*180/np.pi,1))+' degrees)')

    def GetEFields(self):
        EMag, EDir, EDirLeg = GetDPC.GetElectricFields(self.dpcx, self.dpcy, rotation=self.rotation)
       # self.EIM=EMag  
       # CIMxd=xd.rgb(*np.transpose(EDir,(2,0,1)))
       # CLEGxd=xd.rgb(*np.transpose(EDirLeg,(2,0,1)))
        
        if not self.fieldscalculated:
            self.api.library.create_data_item()
            self.EIMuuid=self.api.library.data_items[-1].uuid
            self.api.library.create_data_item()
            self.CIMuuid=self.api.library.data_items[-1].uuid
            self.api.library.create_data_item()
            self.CLEGuuid=self.api.library.data_items[-1].uuid
            EIM=self.api.library.get_data_item_by_uuid(self.EIMuuid)
            CIM=self.api.library.get_data_item_by_uuid(self.CIMuuid)
            CLEG=self.api.library.get_data_item_by_uuid(self.CLEGuuid)
            EIM.data=EMag
            CIM.xdata=xd.rgb(*np.transpose(EDir,(2,0,1)))
            CLEG.xdata=xd.rgb(*np.transpose(EDirLeg,(2,0,1)))
            EIM.title=('E-Field Magnitude')
            CIM.title=('E-Field Vectors (Rotation='+str(round(self.rotation*180/np.pi,1))+' degrees)')
            CLEG.title=('E-Field Vectors Legend')
            self.fieldscalculated=True
        else:
            EIM = self.api.library.get_data_item_by_uuid(self.EIMuuid)
            CIM=self.api.library.get_data_item_by_uuid(self.CIMuuid)
            CLEG=self.api.library.get_data_item_by_uuid(self.CLEGuuid)
            EIM.data=EMag
            CIM.xdata=xd.rgb(*np.transpose(EDir,(2,0,1)))
            CLEG.xdata=xd.rgb(*np.transpose(EDirLeg,(2,0,1)))
            EIM.title=('E-Field Magnitude')
            CIM.title=('E-Field Vectors (Rotation='+str(round(self.rotation*180/np.pi,1))+' degrees)')
            CLEG.title=('E-Field Vectors Legend')

    def GetPotential(self):
        self.VIM = GetDPC.GetPotential(self.dpcx, self.dpcy, rotation=self.rotation, hpass=self.hpass, lpass=self.lpass)
        if not self.vimcalculated:
            self.api.library.create_data_item_from_data(self.VIM)
            self.VIMuuid=self.api.library.data_items[-1].uuid
            VIM = self.api.library.get_data_item_by_uuid(self.VIMuuid)
            VIM.title=('Atomic Potential: HPass='+str(self.hpass)+' LPass='+str(self.lpass))
            self.vimcalculated=True
        else:
            VIM = self.api.library.get_data_item_by_uuid(self.VIMuuid)
            VIM.title=('Atomic Potential: HPass='+str(self.hpass)+' LPass='+str(self.lpass))
            VIM.data=self.VIM

    def GetChargeDensity(self):
        self.RHO=GetDPC.GetChargeDensity(self.dpcx, self.dpcy, rotation=self.rotation)
        if not self.rhocalculated:
            self.api.library.create_data_item_from_data(self.RHO)
            self.RHOuuid=self.api.library.data_items[-1].uuid
            RHO = self.api.library.get_data_item_by_uuid(self.RHOuuid)
            RHO.title=('Charge Density (Rotation='+str(round(self.rotation*180/np.pi,1))+' degrees)')
            self.rhocalculated=True
        else:
            RHO = self.api.library.get_data_item_by_uuid(self.RHOuuid)
            RHO.title=('Charge Density (Rotation='+str(round(self.rotation*180/np.pi,1))+' degrees)')
            RHO.data=self.RHO

    def GetDetectorImage(self):
        dat4d=self.api.library.get_data_item_by_uuid(self.dat4duuid).data
        detim = GetDPC.GetDetectorImage(dat4d, self.rcx, self.rcy, self.pixcal, self.ri, self.ro)
        if not self.detimgenerated:
            self.api.library.create_data_item_from_data(detim)
            self.detimuuid=self.api.library.data_items[-1].uuid
            self.detimgenerated=True
            DETim = self.api.library.get_data_item_by_uuid(self.detimuuid)
            DETim.title=('Detector Image ('+str(int(self.ri))+'-'+str(int(self.ro))+' mrad)')
        else:
            DETim = self.api.library.get_data_item_by_uuid(self.detimuuid)
            DETim.data=detim
            DETim.title=('Detector Image ('+str(int(self.ri))+'-'+str(int(self.ro))+' mrad)')

    def cleardpcuuid(self):
        dat4duuid=None
        self.dpccalculated=False
        self.fieldscalculated=False
        self.vimcalculated=False
