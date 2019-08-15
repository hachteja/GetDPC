GetDPC
======
GetDPC is a Nion Swift plugin designed for streamlined differential phase contrast (DPC) analysis from 4D-STEM datasets. Here, the 4D-STEM dataset is a 2D array of convergent beam electron diffraction patterns or Ronchigrams. The dataset can be analyzed by creating virtual annular detectors and reconstructing images based only off of the intensity corresponding to the angles of the simulated detector, or by measuring the center-of-mass shifts of the Ronchigram intensity to perform DPC. DPC can be used as a highly versatile phase-contrast imaging technique, and for ultrathin samples can be directly connected to the electrostatic fields and potentials experienced by the electron beam within the material. 

The plugin can be implemented on the STEM acquisition computers for fast analysis of data during experiments, and can also be implemented on personal computers allowing for users to analyze and visualize electrostatics and produce image reconstructions without any coding/scripting background.

In addition to the plugin, all functions are included in an external library which can be imported directly into iPython Notebooks for more intensive analyses. A demo notebook is also included to guide users through a successful DPC analysis of a 4D-STEM dataset.

If you found this Plugin to be helpful and it led to a publication please cite our paper: J.A. Hachtel, J.C. Idrobo, and M. Chi, *Adv. Struct. Chem. Imag.* **4** (2018)

Usage Instructions (Nion Swift)
-------------------------------
1. Installation
	a. Download from `GitHub <https://github.com/hachteja/GetDPC>`
        b. Run `python setup.py`

2. Select 4D-STEM Dataset
	a. Open Nion Swift
	b. Move 4D-STEM dataset to active workspace, select such that border turns blue
	c. Go to Window Tab. Select "Get DPC", this should open the GetDPC UI.

3. Calibrate Ronchigram
	a. Enter convergence angle used for DPC experiment.
	b. With 4D-STEM Dataset selected, click 'Calibrate Ronchigram' Button
	c. Function will use BF Threshold value to define BF disk. This is a purely boolean mask, so depending on your acquisition parameters the needed threshold can change. After the calibration, Swift will annotate a circle on the 4D-STEM dataset indicating what it thinks your BF disk is, if this is visibly wrong, try futzing with the BF-Disk threshold.
	d. The calibration will return three important values: The X-Center of the Ronchigram, the Y-Center of the Ronchigram, and the calibration of the Ronchigram in pixels per mrad. If the annotated circle matches the BF disk you are good to continue.

4. Reconstruct Images and Find Ronchigram Center-of-Mass Shfits
	a. Define desired detector range for 4D-STEM Analysis (Note: Image reconstruction and DPC both rely on same detector definitions).
	b. Click 'Get Detector Image' to reconstruct an image from the selected detector range. I recommend doing a 0-(Your Convergence Angle) Image Reconstruction first to check the integrity of the dataset.
	c. Click 'Get CoM Shifts' to calculate the total shift of individual ronchigrams from the true-BF disk center determined from the Ronchigram calibration.
        d. Click 'Get PL Rotation' to get rotation induced by changing the camera length. (Note: Found by rotating CoM shifts until the standard deviation of the curl across the whole 4D dataset is minimized. This method can only find an optimization within 180 degrees of rotation (i.e. if true rotation at 30 degrees, curl minimized at 30 and 210). In order to determine whether true rotation is found value or 180 degrees off from found value you must examine the data and determine whether it is physical (simple for most systems).
	e. Click 'Get CoM Shifts' again to recalculate CoM shifts with correct PL rotation angle. 

5. Calculate Electrostatics
	a. Click 'Get Charge Density' to calculate charge density from the divergence of the CoM Shifts (Note: Here is ideal place to check for needed 180 shift, if atomic nuclei are negative and empty space is positive, the 180 shift is needed).
	b. Click 'Get Electric Field' to calculate electric fields from opposite of CoM Shift. This returns three data items: A 2D Image of the magnitude of the projected electric field as a funciton of position, A 2D RGB image of the field directions where the intensity of color corresponds to the magnitude and the color corresponds to the direction of the field, and a legend for the field direction map. 
	c. Click 'Get Potential' to calculate the atomic potential from the inverse gradient of the CoM shifts. (Note: For most datasets there should be some edge artifacts around the border of the image, this can be solved by adding a small bit of high pass filtering to the inverse gradient operation).

Usage Instructions (Jupyter Notebook)
-------------------------------------
1. Download the package from `GitHub <https://github.com/hachteja/GetDPC>`_ and unzip it.
2. Using Command Prompt or Terminal, `cd /directory/of/GetDPC`.
3. Activate your Python environment `conda activate`
4. Run Jupyter Notebook `jupyter notebook`

More Information
----------------
- `Changelog <https://github.com/hachteja/GetDPC/blob/master/CHANGES.rst>`_
