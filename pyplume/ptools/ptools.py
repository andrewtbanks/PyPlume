# -*- coding: utf-8 -*-
"""
Created on Tue Apr  4 14:56:11 2023

@author: anba
"""

import time
import pathos.multiprocessing as mp
import progressbar
import pickle
import cloudpickle    
import numpy as np
import pandas as pd

#%%



def moving_average(x, window_size):
    """
    Calculate the moving average of a one-dimensional array.

    Parameters:
        x (numpy.ndarray): The input array.
        window_size (int): The size of the moving average window.

    Returns:
        numpy.ndarray: The moving average array.

    Example:
        # Calculate the moving average of an array 'data' with a window size of 3
        result = moving_average(data, window_size=3)
    """
    return np.convolve(x, np.ones(window_size) / window_size, mode='same')

def moving_variance(x, window_size):
    """
    Calculate the moving variance of a one-dimensional array.

    Parameters:
        x (numpy.ndarray): The input array.
        window_size (int): The size of the moving variance window.

    Returns:
        numpy.ndarray: The moving variance array.

    Example:
        # Calculate the moving variance of an array 'data' with a window size of 3
        result = moving_variance(data, window_size=3)
    """
    mean_centered = x - np.mean(x)
    return np.convolve(mean_centered**2, np.ones(window_size) / window_size, mode='same')




def pickle_obj(obj,fname):
    """
    Pickle an object

    Parameters
    ----------
    obj : Object to pickle
    fname : string
        filename for pickled object

    Returns
    -------
    None.

    """

    
    with open(fname,"wb") as f:
        
        try:
            pickle.dump(obj,f)
        except:
            cloudpickle.dump(obj,f)
        
def unpickle_obj(fname):
    """
    Unpickle an object

    Parameters
    ----------
    fname : string
        Path to pickled object.

    Returns
    -------
    out : unpickled object.

    """

    with open(fname,"rb") as f:
        
        try:
            out = pickle.load(f) 
        except:
            out = cloudpickle.load(f) 
    return out

def flatten_list(l): # flatten a list of lists
    """
    Parameters
    ----------
    l : list
        List to flatten

    Returns
    -------
    out : flattened list

    """
    
    out = [item for sublist in l for item in sublist]
    return out

def printProgressBar (iteration, total,taskname = '', prefix = 'Progress', decimals = 1, length = 25, fill = '█', printEnd = "\r"):
    """
    Terminal progress bar
    Args:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        taskname    - Optional  : task description (Str)
        prefix      - Optional  : prefix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
   
    
    taskname = taskname.ljust(100)
    print(f'\r{prefix} |{bar}|{taskname}', end = printEnd)
    # # Print New Line on Complete
    # if iteration == total: 
    #     print()  
        
        
def paralell_fcn(f,iterable,taskname = 'Processing'):
    
    
    """
    Run a function in paralell

    Parameters
    ----------
    f : function to run 
    iterable: inpute argument to interate over
    taskname: task label on progress bar
    Returns
    -------
    list of task results

    """

    st = time.time()
    cpu_count = min(mp.cpu_count(),len(iterable))
    varname = 'Task'# '_'.join(taskname.split(' '))
    widgets = [progressbar.GranularBar(markers=" ░▒▓█", left='', right='|'),
                progressbar.widgets.Variable(varname)]
    bar = progressbar.ProgressBar(widgets = widgets, max_value = len(iterable))
    bar.variables[varname] = str(taskname) 
    bar.update(1)
    results = []
    
    #printProgressBar(0, len(iterable),prefix = f'Filtering', taskname= f'Filtering 0%')
        
    with mp.Pool(cpu_count) as pool:
        
        
        #results= pool.map(f,iterable)
        tasks = pool.imap_unordered(f,iterable) 
        
        for r,result in enumerate(tasks):
            bar.update(r+1)
            
            
            
            results.append(result)
            time.sleep(0.1)
            
            #print(r)
    bar.update(r+1)
    #bar.update(len(iterable)) # force bar to 100%
            
    # print('\r','\n')
    # print(f'Execution Time: {round((time.time() - st)/60,2)} min')
    # print('\r','\n')
    return results


def gen_rot_y(theta):
    """
    Generate a 3*3 matrix that rotates a vector by angle theta about the y-axis

    Parameters
    ----------
    theta : float
        angle to rotate by.

    Returns
    -------
    numpy array
        Rotation matrix (Ry).

    """
    theta = theta*np.pi/180
    return np.array([(np.cos(theta),0,np.sin(theta)),
                     (0,1,0),
                     (-np.sin(theta),0,np.cos(theta))])

def gen_rot_z(theta):
    """
    Generate a 3*3 matrix that rotates a vector by angle theta about the z-axis

    Parameters
    ----------
    theta : float
        angle to rotate by.

    Returns
    -------
    numpy array
        Rotation matrix (Rz).

    """
    theta = theta*np.pi/180
    return np.array([(np.cos(theta),-np.sin(theta),0),
                     (np.sin(theta),np.cos(theta),0),
                     (0,0,1)])
                     
def gen_rot_x(theta):
    """
    Generate a 3*3 matrix that rotates a vector by angle theta about the x-axis

    Parameters
    ----------
    theta : float
        angle to rotate by.

    Returns
    -------
    numpy array
        Rotation matrix (Rx).

    """
    theta = theta*np.pi/180
    return np.array([(1,0,0),
                     (0,np.cos(theta),-np.sin(theta)),
                     (0,np.sin(theta),np.cos(theta))])


###########################################################################################################
##########################################################################################################

def configure_ADCP(adcp, pose, **kwargs):
    """
    Configure the ADCP parameters, perform processing, and apply masking.

    Parameters
    ----------
    adcp : ADCP object
        An instance of the ADCP class.
    pose : Pose object
        Pose information of the ADCP.
    adcp_offset : ndarray, optional
        Offset of the ADCP from the ROV center of mass.
    adcp_rotation : float, optional
        Rotation of the ADCP in its housing.
    adcp_dr : float, optional
        Distance between transducer faces for the ADCP.
    stn_thresh : int, optional
        Threshold for Signal-to-Noise Ratio masking.
    cmag_thresh : int, optional
        Threshold for Correlation Magnitude masking.
    abs_thresh : int, optional
        Threshold for Absolute Backscatter masking.
    reject_first_bins : list, optional
        List of first n bins to reject (bin 1 - reject_first_bins).

    Returns
    -------
    None

    Notes
    -----
    - The ADCP geometry is updated based on the provided pose and optional parameters.
    - Absolute backscatter is calculated.
    - Various masks (stn, cmag, abs_bs, bins, bottom track) are defined and applied.

    Example
    -------
    configure_ADCP(adcp_instance, pose_instance, adcp_offset=my_offset, adcp_rotation=my_rotation,
                   adcp_dr=my_distance_range, stn_thresh=my_stn_threshold, cmag_thresh=my_cmag_threshold,
                   abs_thresh=my_abs_threshold, reject_first_bins=my_reject_bins)

    """
    ips_offset = np.array([-0.36, -1.45, -0.31])  # Offset of the ips from the ROV center of mass
    adcp_offset = np.array([0.23, -1.38, -0.19])  # Offset of the ADCP from the ROV center of mass
    adcp_offset -= ips_offset
    adcp_length = 0.3949
    adcp_offset[2] += adcp_length
    adcp_offset[2] = -adcp_offset[2]

    offset = kwargs.pop('adcp_offset', adcp_offset)
    adcp_rotation = kwargs.pop('adcp_rotation', 0)
    adcp_dr = kwargs.pop('adcp_dr', 0.1)
    stn_thresh = kwargs.pop('stn_thresh', None)
    cmag_thresh = kwargs.pop('cmag_thresh', None)
    abs_thresh = kwargs.pop('abs_thresh', None)
    reject_first_bins = kwargs.pop('reject_first_bins', None)

    adcp.mask.set_mask_status(False)
    adcp.geometry.set_pose(pose, update_orientation=True)
    adcp.geometry.calculate_beam_geometry(rotation=adcp_rotation, offset=offset, dr=adcp_dr)

    # Processing
    adcp.processing.calculate_absolute_backscatter()

    # Masking (common masking operations)

    if stn_thresh:
        stn = adcp.get_ensemble_array(field_name='SIGNAL TO NOISE RATIO')
        mask1 = (stn > stn_thresh)
        adcp.mask.define_mask(mask=mask1, name='stn', set_active=True)

    if cmag_thresh:
        cmag = adcp.get_ensemble_array(field_name='CORRELATION MAGNITUDE')
        mask2 = cmag > cmag_thresh
        adcp.mask.define_mask(mask=mask2, name='cmag', set_active=True)

    if abs_thresh:
        abs_bs = adcp.get_ensemble_array(field_name='ABSOLUTE BACKSCATTER')
        mask3 = abs_bs > abs_thresh
        adcp.mask.define_mask(mask=mask3, name='abs_bs', set_active=True)

    if reject_first_bins:
        mask4 = np.full(np.shape(mask3), True)
        for i, b in enumerate(reject_first_bins):
            mask4[:, :b, :] = False
            adcp.mask.define_mask(mask=mask4, name='bins', set_active=True)

    # Mask bottom track
    bt_range = adcp.get_bottom_track()
    if any(~np.isnan(bt_range).flatten()):
        bt_range = np.repeat(bt_range[:, np.newaxis, :], adcp.config.number_of_cells, axis=1)
        bt_range[bt_range == 0] = 32675
        bin_centers = np.outer(adcp.geometry.get_bin_midpoints(), np.ones(adcp.n_ensembles))
        bin_centers = np.repeat(bin_centers[np.newaxis, :, :], adcp.config.number_of_beams, axis=0)
        mask = (bt_range - adcp.config.depth_cell_length / 100) > bin_centers
        adcp.mask.define_mask(mask=mask, name='bottom track', set_active=True)
        
        



def configure_CTD(ctd,pose,min_turb = -1,ssc_coeff = 1.5,**kwargs):
    """
    configure a ctd sensor 

    Parameters
    ----------
    ctd : TYPE
        DESCRIPTION.
    Pose : Pose object
        pre-configured Pose object containing position and orientation data 
        for the sensor. 
    orient_in : TYPE
        DESCRIPTION.
    min_turbidity: float, optional
        minimium allowed turbidity value in masking 
        
    ssc_coeff: float, optional
        coefficient for converting Turbidity (NTU) to ssuspended solids concentration (SSC). SSC = ssc_coeff*NTU
    Returns
    -------
    None.

    """

    #min_turb = kwargs.pop('min_turb',0) # minimim allowed turbidity 
    offset = kwargs.pop('ctd_offset',(0,0,0))
    ctd_rotation = kwargs.pop('ctd_rotation',0)
    

    ## configure geometry
    ips_offset = np.array([	-0.36,-1.45,	-0.31]) # offset of the ips from the ROV center of mass - note x and y coordinates interchanged, and z direction reversed to match the ADCP reference frame, 
    ctd_offset = np.array([.80,1.05,	-0.52]) #np.array([0.23,-1.38,	-0.19]) # offset of the wetlabs ntu face from the ROV center of mass - note x and y coordinates interchanged, and z direction reversed to match the ADCP reference frame, 
    ctd_offset -= ips_offset 
    ctd_length = 0
    ctd_offset[2] += ctd_length # add the offset to the face of the transducers
    ctd_offset[2] = -ctd_offset[2] # flip z coordinate direction    



    ctd.geometry.set_pose(pose)
    ctd.geometry.set_sensor_relative_geometry(rotation = ctd_rotation,offset = ctd_offset)
    ctd.processing.calculate_density()
    ctd.processing.calculate_depth(environment = 'SALTWATER')
    ctd.processing.calculate_SSC(A =ssc_coeff)
    
    t,turb = ctd.get_timeseries_data(mask = False)
    mask = turb >= min_turb
    ctd.mask.define_mask(mask,name = 'turbidity',set_active = True)
    
def select_adcp_data(adcp, t_select='time', d_select='HAB', field_name='ECHO INTENSITY', **kwargs):
    """
    Selects data from an ADCP transect based on time or ensemble index and depth (HAB or bin).

    Parameters:
    - adcp (ADCP): ADCP DataSet object 
    - t_select (str): Selection method for time ('time' or 'ensemble').
    - d_select (str): Selection method for depth ('HAB' or 'bin').
    - field_name (str): Name of the field to select (e.g., 'ECHO INTENSITY').
    - **kwargs: Additional keyword arguments based on the selection criteria.

    Returns:
    - t (ndarray): Array of selected time or ensemble values.
    - X (ndarray): Selected data array based on the specified criteria.
    - Z (ndarray): z-values of selected ADCP ensemble array data 
    """
    if t_select == 'time':
        st = kwargs.pop('start_time', min(adcp.get_ensemble_datetimes()))
        et = kwargs.pop('end_time', max(adcp.get_ensemble_datetimes()))
    elif t_select == 'ensemble':
        se = kwargs.pop('start_ensemble', 0)
        ee = kwargs.pop('end_ensemble', adcp.n_ensembles)

    if d_select == 'HAB':
        sh = kwargs.pop('start_HAB', 0)
        eh = kwargs.pop('end_HAB', np.nanmax(adcp.geometry.get_absolute_beam_midpoint_positions_HAB()[2]))

    if d_select == 'bin':
        sb = kwargs.pop('start_bin', 0)
        eb = kwargs.pop('end_bin', adcp.config.number_of_cells)
    mask = kwargs.pop('mask', True)



    if d_select == 'HAB':
        # define a mask to nan out out of range data
        Z = adcp.geometry.get_absolute_beam_midpoint_positions_HAB()[2].copy()
        hab_mask = ((Z >= sh) & (Z <= eh))
        Z[~hab_mask] = np.nan

        adcp.mask.set_mask_status(mask)  # deactivate all existing masks if mask is set to false, otherwise keep existing masks
        adcp.mask.define_mask(mask=hab_mask, name='HAB', set_active=True)
        X = adcp.get_ensemble_array(field_name=field_name, mask=mask)
        # delete the HAB mask
        adcp.mask.delete_mask('HAB')

    if t_select == 'time':
        # find starting ensemble and ending ensemble based on time
        t = adcp.get_ensemble_datetimes()

        se = np.argmin(abs(st - t))  # starting ensemble index
        ee = np.argmin(abs(et - t))  # ending ensemble index
        X = X[:,:,se:ee]
        Z = Z[:,:,se:ee]
        t = t[se:ee]
    
        
    
    return t, X,Z

def select_ctd_data(ctd, field_name='Turbidity (NTU)', **kwargs):
    """
    Selects data from a CTD profile based on time.

    Parameters:
    - ctd (CTD): CTD DataSet object containing the data.
    - field_name (str): Name of the field to select (e.g., 'Turbidity (NTU)').
    
    - **kwargs: Additional keyword arguments based on the selection criteria.

    Returns:
    - t (ndarray): Array of selected time values.
    - turb (ndarray): Selected turbidity data array based on the specified criteria.
    """
    turb, t = ctd.get_timeseries_data(field_name=field_name)
    st = kwargs.pop('start_time', min(t))
    et = kwargs.pop('end_time', max(t))
    sidx = np.argmin(abs(st - t))  # starting ensemble index
    eidx = np.argmin(abs(et - t))  # ending ensemble index
    t = t[sidx:eidx]
    turb = turb[sidx:eidx]
    return t, turb



def calculate_time_overlap(start_time1, end_time1, start_time2, end_time2):
    """
    Calculate the overlap duration between two time intervals.

    Parameters:
    - start_time1: Start time of the first interval. Accepts pandas, numpy, or datetime datetimes.
    - end_time1: End time of the first interval. Accepts pandas, numpy, or datetime datetimes.
    - start_time2: Start time of the second interval. Accepts pandas, numpy, or datetime datetimes.
    - end_time2: End time of the second interval. Accepts pandas, numpy, or datetime datetimes.

    Returns:
    - overlap_duration (timedelta): Duration of the overlap between the two intervals.

    Example:
    >>> start_time1 = "2023-01-01 08:00:00"
    >>> end_time1 = "2023-01-01 12:00:00"
    >>> start_time2 = "2023-01-01 10:00:00"
    >>> end_time2 = "2023-01-01 14:00:00"
    >>> overlap_duration = calculate_time_overlap(start_time1, end_time1, start_time2, end_time2)
    >>> print(f"Overlap duration: {overlap_duration}")
    """
    # Convert inputs to datetime objects if they are not already
    start1 = pd.to_datetime(start_time1)
    end1 = pd.to_datetime(end_time1)
    start2 = pd.to_datetime(start_time2)
    end2 = pd.to_datetime(end_time2)

    overlap_start = max(start1, start2)
    overlap_end = min(end1, end2)

    if overlap_start < overlap_end:
        overlap_duration = overlap_end - overlap_start
        return overlap_duration
    else:
        return pd.Timedelta('0s')
    

def find_ADCP_CTD_pairs(dm, min_overlap=300, plot=True):
    """
    Find matched ADCP and CTD pairs based on overlapping date ranges.

    Parameters:
    - dm: DataManager object containing datasets named 'ADCP' and 'CTD' with ADCP and CTD DataSet objects, respectively.
    - min_overlap: Minimum number of seconds two files must overlap to be considered a match.
    - plot: bool - if True, plot the matched pairs.

    Returns:
    - list: List of tuples containing matched ADCP and CTD pairs (adcp, ctd).
    """
    pairs = []

    for ctd in dm.datasets['CTD'].get_active_data():
        for adcp in dm.datasets['ADCP'].get_active_data():
            
            # Check for valid file lengths and dates
            fail_conds = []  # Boolean fail indicators - for rejecting a CTD or ADCP dataset
            fail_conds.append(ctd.data['DateTime'].min() < pd.to_datetime('September 01 2022'))
            fail_conds.append((ctd.data['DateTime'].max() - ctd.data['DateTime'].min()) < pd.Timedelta('5 min'))
            fail_conds.append((adcp.get_ensemble_datetimes().max() - adcp.get_ensemble_datetimes().min()) < pd.Timedelta('5 min'))

            if not any(fail_conds): 
                
                overlap = calculate_time_overlap(ctd.data['DateTime'].min(), ctd.data['DateTime'].max(), adcp.get_ensemble_datetimes().min(), adcp.get_ensemble_datetimes().max())
                if overlap.total_seconds() > min_overlap:
                    pairs.append((adcp, ctd))
                    # You can perform additional actions here for matched pairs, such as plotting
                    
                    if plot:
                        adcp.plot.four_beam_flood_plot(plot_by='bin', ctd=ctd)

    return pairs


def ABS_to_NTU(ABS, A, B):
    '''
    Convert ABS to NTU using the equation 10log(SSC) = A*Backscatter + B.

    Parameters
    ----------
    ABS : numpy.ndarray
        Absolute backscatter values
    A : float
        Coefficient A in the equation.
    B : float
        Coefficient B in the equation.

    Returns
    -------
    numpy.ndarray
        Nephelometric Turbidity Units (NTU) calculated from ABS.
    '''

    ABS[ABS >= 32768] = np.nan
    return (1 / 10) * 10**(A * ABS + B) 

def NTU_to_SSC(NTU,A):
    '''
    Convert NTU to SSC using equation SCC = A*NTU

    Parameters
    ----------
    NTU : numpy.ndarray
        Absorption values.
    A : float
        Coefficient A in the equation.


    Returns
    -------
    numpy.ndarray
        Suspended solids concentration (SSC) calcualted from NTU
    '''
    return A*NTU  

def random_sample(array, n):
    """
    Randomly sample n elements from the given array.

    Parameters:
    - array: Input array.
    - n: Number of elements to sample.

    Returns:
    - np.ndarray: Array containing n randomly sampled elements.
    """
    if n > len(array):
        raise ValueError("Sample size cannot be greater than the array size.")
    
    return np.random.choice(array, size=n, replace=False)