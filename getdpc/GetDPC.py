import typing
import numpy as np
from matplotlib.colors import hsv_to_rgb


def CalibrateRonchigram(dat4d: np.ndarray, conv: float = 32, t: float = 0.3) -> typing.Tuple[np.ndarray, np.ndarray, np.ndarray, float, float, np.ndarray, np.ndarray]:
    """Find true center of Ronchigram, and pixels/mrad calibration

    :param dat4d: 4D Dataset, 2-spatial, 2-diffraction dimensions
    :param conv: Convergence Angle of Electron Probe in mrad
    :param t: Threshhold for BF Disk (fraction of 1)
    :return: center, calibrations
    """
    R = np.average(dat4d, axis=(0, 1))
    Rn = (R - np.amin(R)) / np.ptp(R)
    BFdisk = np.ones(R.shape) * (Rn > t)
    absct = t * np.ptp(R)
    rxx, ryy = np.meshgrid(np.arange(0, Rn.shape[1]), np.arange(0, Rn.shape[0]))
    rcx, rcy = np.sum(BFdisk * rxx / np.sum(BFdisk)), np.sum(BFdisk * ryy / np.sum(BFdisk))
    edge = (np.sum(np.abs(np.gradient(BFdisk)), axis=0)) > t
    pixcal = np.average(np.sqrt((rxx - rcx) ** 2 + (ryy - rcy) ** 2)[edge]) / conv
    return R, rcx, rcy, pixcal, BFdisk, absct, edge


def GetDetectorImage(dat4d: np.ndarray, RCX: float, RCY: float, RCal: float, RI: float = 0, RO: float = 32) -> np.ndarray:
    """Reconstruct a detector image from the 4D Dataset

    :param dat4d: 4D Dataset, 2-spatial, 2-diffraction dimensions
    :param RCX: X Center of the Ronchigram (pixels)
    :param RCY: Y Center of the Ronchigram (pixels)
    :param RCal: Calibration of the Ronchigram (pixels/mrad)
    :param RI: Inner Radius for CoM Measurement (mrad)
    :param RO: Outer Radius for CoM Measurement (mrad)
    :return detector image as ndarray
    """
    X, Y = np.meshgrid((np.arange(0, dat4d.shape[3]) - RCX) / RCal, (np.arange(0, dat4d.shape[2]) - RCY) / RCal)
    return np.average(dat4d * ((X ** 2 + Y ** 2 >= RI ** 2) & (X ** 2 + Y ** 2 < RO ** 2)), axis=(2, 3))


def GetiCoM(dat4d: np.ndarray, RCX: float, RCY: float, RCal: float, RI: float = 0, RO: float = 32) -> typing.Tuple[np.ndarray, np.ndarray]:
    """Get Ronchigram Center of Mass Shifts from 4D Dataset

    :param dat4d: 4D Dataset, 2-spatial, 2-diffraction dimensions
    :param RCX: X Center of the Ronchigram (pixels)
    :param RCY: Y Center of the Ronchigram (pixels)
    :param RCal: Calibration of the Ronchigram (pixels/mrad)
    :param RI: Inner Radius for CoM Measurement (mrad)
    :param RO: Outer Radius for CoM Measurement (mrad)
    :return iCoM as ndarray
    """
    X, Y = np.meshgrid((np.arange(0, dat4d.shape[3]) - RCX) / RCal, (np.arange(0, dat4d.shape[2]) - RCY) / RCal)
    maskeddat4d = dat4d * ((X ** 2 + Y ** 2 >= RI ** 2) & (X ** 2 + Y ** 2 < RO ** 2))
    return np.average(maskeddat4d * X, axis=(2, 3)), np.average(maskeddat4d * Y, axis=(2, 3))

def GetPLRotation(dpcx: np.ndarray, dpcy: np.ndarray, *,  order: int = 3, outputall: bool = False) -> float:
    """Find Rotation from PL Lenses by minimizing curl/maximizing divergence of DPC data

    :param dpcx: X-Component of DPC Data (2D numpy array)
    :param dpcy: Y-Component of DPC Data (2D numpy array)
    :param order: Number of times to iterated calculation (int)
    :param outputall: Output Curl and Divergence curves for all guesses in separate array (bool)
    :return: The true PL Rotation value (Note: Can potentially be off by 180 degrees, determine by checking signs of charge/field/potential)
    """
    def DPC_ACD(dpcx,dpcy,tlow,thigh):        
        A,C,D=[],[],[]
        for t in np.linspace(tlow,thigh,10,endpoint=False):            
            rdpcx,rdpcy=dpcx*np.cos(t)-dpcy*np.sin(t),dpcx*np.sin(t)+dpcy*np.cos(t)        
            gXY,gXX=np.gradient(rdpcx);gYY,gYX=np.gradient(rdpcy)        
            C.append(np.std(gXY-gYX));D.append(np.std(gXX+gYY));A.append(t)
        R=np.average([A[np.argmin(C)],A[np.argmax(D)]])
        return R,A,C,D
    RotCalcs=[]
    RotCalcs.append(DPC_ACD(dpcx,dpcy,0,np.pi))
    for i in range(1,order): 
        RotCalcs.append(DPC_ACD(dpcx,dpcy,RotCalcs[i-1][0]-np.pi/(10**i),RotCalcs[i-1][0]+np.pi/(10**i)))
    if outputall: return RotCalcs
    else: return RotCalcs[-1][0]

def GetElectricFields(dpcx: np.ndarray, dpcy: np.ndarray, *, rotation: float = 0, LegPix: int = 301, LegRad: float = 0.85) -> typing.Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Convert dpcx and dpcy maps to to a color map where the color corresponds to the angle

    :param dpcx: X-Component of DPC Data (2D numpy array)
    :param dpcy: Y-Component of DPC Data (2D numpy array)
    :param rotation: Optional rotation radians
    :param LegPix: Number of Pixels in Color Wheel Legend
    :param LegRad: Radius of Color Wheel in Legend (0-1)
    :return: The electric fields as a 2D numpy array
    """
    EX = -dpcx
    EY = -dpcy
    rEX = EX * np.cos(rotation) - EY * np.sin(rotation)
    rEY = EX * np.sin(rotation) + EY * np.cos(rotation)

    EMag = np.sqrt(rEX ** 2 + rEY ** 2)

    XY = np.zeros(rEX.shape + (3,), dtype=float)
    M = np.amax(EMag)
    EMagScale = EMag / M
    for i in range(rEX.shape[0]):
        for j in range(rEX.shape[1]):
            XY[i, j] = np.angle(np.complex(rEX[i, j], rEY[i, j])) / (2 * np.pi) % 1, 1, EMagScale[i, j]
    EDir=hsv_to_rgb(XY)
    x, y = np.meshgrid(np.linspace(-1, 1, LegPix, endpoint=True), np.linspace(-1, 1, LegPix, endpoint=True))
    X, Y = x * (x ** 2 + y ** 2 < LegRad ** 2), y * (x ** 2 + y ** 2 < LegRad ** 2)
    XYLeg = np.zeros(X.shape + (3,), dtype=float)
    RI = np.sqrt(X ** 2 + Y ** 2) / np.amax(np.sqrt(X ** 2 + Y ** 2))
    for i in range(X.shape[0]):
        for j in range(X.shape[1]):
            XYLeg[i, j] = np.angle(np.complex(X[i, j], Y[i, j])) / (2 * np.pi) % 1, 1, RI[i, j]
    EDirLeg=hsv_to_rgb(XYLeg)
    return EMag, EDir, EDirLeg

def GetChargeDensity(dpcx: np.ndarray, dpcy: np.ndarray, *, rotation: float = 0) -> np.ndarray:
    """Calculate Charge Density from the Divergence of the Ronchigram Shifts

    :param dpcx: X-Component of DPC Data (2D numpy array)
    :param dpcy: Y-Component of DPC Data (2D numpy array)
    :param rotation: Optional rotation radians
    :return: The charge density as a 2D numpy array
    """

    rdpcx = dpcx * np.cos(rotation) + dpcy * np.sin(rotation)
    rdpcy = -dpcx * np.sin(rotation) + dpcy * np.cos(rotation)
    gxx, gyy = np.gradient(rdpcx)[1], np.gradient(rdpcy)[0]

    return - gxx - gyy


def GetPotential(dpcx: np.ndarray, dpcy: np.ndarray, *, rotation: float = 0, hpass: float = 0, lpass: float = 0) -> np.ndarray:
    """Convert X and Y Shifts (E-Field Vector) Into Atomic Potential By Inverse Gradient

    Note: This method is vulnerable to edge induced artifacts that a small degree of high-pass filtering
    can clear up without significantly affecting the atomic-level contrast

    :param dpcx: X-Component of DPC Data (2D numpy array)
    :param dpcy: Y-Component of DPC Data (2D numpy array)
    :param rotation: Optional rotation radians
    :param hpass: Optional constant to provide variable high-pass filtering
    :param lpass: Optional constant to provide variable low-pass filtering
    :return: The potential as a 2D numpy array
    """

    rdpcx = dpcx * np.cos(rotation) + dpcy * np.sin(rotation)
    rdpcy = -dpcx * np.sin(rotation) + dpcy * np.cos(rotation)
    fCX = np.fft.fftshift(np.fft.fft2(np.fft.fftshift(rdpcx)))
    fCY = np.fft.fftshift(np.fft.fft2(np.fft.fftshift(rdpcy)))
    KX = fCX.shape[1]
    KY = fCY.shape[0]
    kxran = np.linspace(-1, 1, KX, endpoint=True)
    kyran = np.linspace(-1, 1, KY, endpoint=True)
    kx, ky = np.meshgrid(kxran, kyran)
    fCKX = fCX * kx
    fCKY = fCY * ky
    fnum = (fCKX + fCKY)
    fdenom = np.pi * 2 * (0 + 1j) * (hpass + (kx ** 2 + ky ** 2) + lpass * (kx ** 2 + ky ** 2) ** 2)
    fK = np.divide(fnum, fdenom)

    return np.real(np.fft.ifftshift(np.fft.ifft2(np.fft.ifftshift(fK))))
