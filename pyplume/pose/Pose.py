# -*- coding: utf-8 -*-
"""
Created on Fri Sep 15 13:00:08 2023

@author: anba
"""

import numpy as np 
import pandas as pd 
import os, sys
import pyproj
# from pyproj import Transformer
import copy
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.collections import LineCollection
import matplotlib.ticker as mticker
import cmocean
import warnings

import rich
import dill
import copy

#import pyplume as pp
from ..ptools import ptools
from ..plotting.matplotlib_shell import subplots, dhi_colors


class Pose:
    """
    Class for managing monitoring platform pose and orientation ("Pose") data (e.g. ROV, Vessel, AUV, Lander, etc).
    positive z is up, positive x is east, and positive y is north. 
    Features:
    - Importing data (pose and orientation)
    - Regularization/re-sampling
    - Updating pose depth (z)
    - QAQC when possible
    - Reversing z-convention
    - Scaling operations (e.g., vertical exaggeration)
    - managing projections 
    """

    def __init__(self, name='Pose', df=None, z_convention = 'normal', proj = "EPSG:32611"):
        """
        Initialize the Pose class.

        Parameters
        ----------
        name : str, optional
            Name of the pose data. Default is 'Pose'.
        df : pd.DataFrame, optional
            Input pandas DataFrame. Default is None.
        z_convention : str, optional
            Specify the z-convention of the data as 'normal' (positive z is up) or 'reverse' (positive z is down). Default is 'normal'.
        proj: str, optional
            data projection. Use pyproj projection keys. 
        """
        self.pose = None
        self.name = name
        self.plot = self.__plotting(self)
        
        self.resample_method = 'nearest'
        self.resample_tolerance = None #second
        
        
            
        self.proj = proj
        


        if df is not None:
            self.import_from_pandas_df(df)
            
        # set z convention
        # doesnt work with the funciton call on init for some reason 
        if z_convention in ['normal','reverse']:
            self.z_convention = z_convention # positive z is up, negative z is down
        else:
            print(f'invalid z_convention. Choose from {z_convention}')    

        
    def set_resample_method(self,method): 
        self.resample_method = method
        
    def set_resample_tolerance(self,tolerance):
        # if method is nearest this is the tolerance for matchingh
        # if ffill of bfill its the consecutive numberto propageate
        self.resample_tolerance = tolerance
        
    def to_csv(self, fname=None):
        """
        Write pose data to a CSV file.

        Parameters
        ----------
        fname : str, optional
            The file name to save the CSV. If not provided, the default filename
            will be based on the 'name' attribute of the pose instance.
        """
        if not fname:
            fname = f'{self.name}_pose_export.csv'
        self.pose.to_csv(fname)

    def import_from_pandas_df(self, df):
        """
        Import data from a pandas DataFrame and transform column names.

        DataFrame column names must include 'Easting', 'Northing', 'Depth',
        'Pitch', 'Roll', and 'Heading'.

        Parameters
        ----------
        df : pd.DataFrame
            The input pandas DataFrame.
        flip_z : bool, optional
            Whether to flip the z-values. Default is False.

        Returns
        -------
        pd.DataFrame
            Transformed DataFrame with updated column names.
        """
        self.pose = df[['Easting', 'Northing', 'Depth', 'Pitch', 'Roll', 'Heading']].copy()
        self.pose.columns = ['x', 'y', 'z', 'pitch', 'roll', 'heading']
        self.pose['z'] = -self.pose['z']
        
        # if flip_z:
        #     self.pose['z'] = -self.pose['z']  # Flip z direction so that down is negative
    #@z_convention.setter    
    def set_z_convention(self,z_convention = 'normal', update_z = False):
        """
        set the z-coordinate convention of the pose data.

        This method multiplies the z-coordinates by -1 to flip the convention,
        ensuring that down is negative.
        
        Parameters
        ----------
        z_convention : str, optional
            Specify the z-convention of the data as 'normal' (positive z is up) or 'reverse' (positive z is down). Default is 'normal'.
            
        update_z: bool, optional
            if true the z-coordinate will be multiplied by -1. Default is False. 
        Notes
        -----
        This method modifies the 'z' column of the 'pos' DataFrame in place.
        """
        
        if z_convention in ['normal','reverse']:
            self.z_convention = z_convention # positive z is up, negative z is down
        else:
            print(f'invalid z_convention. Choose from {z_convention}')
            
            #raise Warning(f'invalid z_convention. Choose from {z_convention}')
           
        if update_z:
            self.pose['z'] = -self.pose['z']

    def get_between(self, start_date, end_date):
        """
        Retrieve pose data between two dates.

        Parameters
        ----------
        start_date : datetime-like
            The start date for filtering the pose data.
        end_date : datetime-like
            The end date for filtering the pose data.

        Returns
        -------
        pandas.DataFrame
            pose data within the specified date range.

        Notes
        -----
        The 'pose' DataFrame must have a DatetimeIndex for this method to work correctly.
        """
        mask = (self.pose.index >= start_date) & (self.pose.index <= end_date)
        return self.pose.loc[mask]
    
    

            

            
            # for i,etime in enumerate(et):
            #     index = orient_in.index.get_indexer([etime], method='ffill')[0] # index of nearest input positon to the ensemble timestamp
            #     self.orientation[0,i] = orient_in.iloc[index].pitch
            #     self.orientation[1,i] = orient_in.iloc[index].roll
            #     self.orientation[2,i] = orient_in.iloc[index].heading 
    def add_lat_lon(self):
        """
        Convert from input easting northing to lat/lon.
        
        Input projection code comes from pyproj.
        Lat and lon columns are added to the pose data.
        """
    
        transformer = pyproj.Transformer.from_crs(self.proj, "EPSG:4326")
        lat, lon = transformer.transform(self.pose['x'].to_numpy(), self.pose['y'].to_numpy())
        
        self.pose['latitude'] = lat
        self.pose['longitude'] = lon

        
        
        
            
    class __plotting:
        def __init__(self, pose):
            self._pose = pose

        def trajectory(self, **kwargs):
            """
            Create a trajectory plot.

            Parameters
            ----------
            **kwargs : dict, optional
                Additional keyword arguments.

            Notes
            -----
            This method uses the 'pos' DataFrame stored in the pose class.
            """
            pose = self._pose.pose

            start_date = kwargs.pop('start_date', pose.index.min())
            end_date = kwargs.pop('end_date', pose.index.max())

            mask = (pose.index >= start_date) & (pose.index <= end_date)
            pose = pose.loc[mask]

            fig, ax = subplots(nrow = 3, figheight = 8, figwidth = 10)
            
            
            

            
            s = ax[0].scatter(pose['x'], pose['y'],s = 5, c = pose['z'], cmap = 'jet')
            ax[0].set_ylabel('Distance (m)')
            ax[0].set_aspect('equal')
            ax[0].grid(alpha = 0.3, color = 'white')
            ax[0].set_title('Position')
            fig.colorbar(s,ax = ax[0],label = 'Depth (m)')
            
            
            ax[1].scatter(pose.index, pose['z'],s = 5,c = pose['z'], cmap = 'jet')
            ax[1].set_ylabel('Depth (m)')
            ax[1].grid(alpha = 0.3, color = 'white')

            ax[2].plot(pose.index, pose['pitch'],lw = 1,ls = '--',c ='black',alpha = 0.9,label = 'Pitch')
            ax[2].plot(pose.index, pose['roll'] ,lw = 2,ls = '-',c ='black',alpha = 0.9,label = 'Roll')
            ax[2].set_ylabel('degrees')
            ax[2].grid(alpha = 0.3, color = 'white')
            ax[2].legend()
            
            ax[0].set_facecolor('lightgray')
            ax[1].set_facecolor('lightgray')
            ax[2].set_facecolor('lightgray')
            title = f'{self._pose.name}'
            fig.suptitle(title)  
            
            
            return fig,ax
            
            
    def resample_to(self, t_in,kwargs):
        """
        Resample the pose data to match the input timeseries.

        This method resamples the pose data to align with the provided input timeseries (`t_in`).
        The `tolerance` parameter specifies the maximum allowable time difference in seconds for a match to be considered acceptable.
        Input timesteps that could not be matched will be filled in with nan values. 
        It uses nearest neighbor search to find the closest matching timestamps in the input timeseries.
        
        Warning - all data in the pose data outside the bounds of the input 
        timeseries will be deleted. 

        Args:
            t_in (list or numpy array, pandas datatime index): A list-like object containing pandas datetimes representing the target timeseries.
            
            tolerance (int, optional): The maximum time difference in seconds allowed for matching. only true if method = nearest
            Default is 1 second. if tolerance is None, then the nearest value 
            will be used, regardless of distance. this is useful for static 
            sensors without regular pose measurements. 




        """
        

        self.pose = self.pose.reindex(t_in, method=self.resample_method, tolerance = self.resample_tolerance)
        
        # method = kwargs.pop('method','nearest')
        # tolerance = kwargs.pop('tolerance','auto')

        # if tolerance:
        #     if tolerance == 'auto': # calculate the right tolerance 
        #         if len(t_in)>1 and len(self.pose.index)>1:
        #             # calculate timestep for input timeseries
                   
        #             dt = np.diff(t_in).astype(float)/1e9 # time delta in seconds
                    
        #             dt = np.append(dt,dt[-1])
        #             dt_99_in = np.percentile(dt,99) # mask to identify data gaps 
                    
        #             # calculate timestep for existing timeseries
        #             t = self.pose.index.to_numpy()
        #             dt = np.diff(t,prepend = t[0],).astype(float)/1e9 # time delta in seconds
        #             dt_99 = np.percentile(dt,99) # mask to identify data gaps 
                    
        #             tolerance = 1.1*max(dt_99,dt_99_in)
        #         else:
        #             tolerance = 1e6 # set to 30 :)
                    
                    
                

            
        #     print(tolerance)
        #     self.pose = self.pose.reindex(t_in, tolerance=pd.to_timedelta(f'{tolerance} s'), method='nearest')
        # else:
        #     self.pose = self.pose.reindex(t_in, method='nearest')
            
        #rich.print(f"[light_green]({self.name}) successfully resampled on interval")
                
        #rich.print(f"[bold cyan]({self.name})[white] pose data successfully resampled\n{(len(self.name)+3)*' '}[white bold]interval:[white] {t_in[0].strftime('%D %H:%M')}-{t_in[-1].strftime('%D %H:%M')}\n{(len(self.name)+3)*' '}[white bold]% valid:[white] {(self.pose.isnull().sum()/(~self.pose.isnull()).sum()).mean()*100} ")
        
        
        #return p_out
        
        
    def resample_from(self,tser,field_name, tolerance = 'auto', z_convention = 'normal'):
        """
        set field in the pose data ('x','y','z','pitch','roll','heading') 
        from an external timeseries. 
        
        This method resamples the input timeseries data to align with the pose timesteps
        
        Input timesteps that could not be matched will be filled in with nan values. 
        It uses nearest neighbor search to find the closest matching timestamps in the input timeseries.
 
        
        input timeseries must be a pandas series object 
        
        z_convention: str, optional
           z convention for the input timeseries. 'normal' (positive z in up) or 'reverse' (negative z is up). 
        """
        
        if tolerance == 'auto': # calculate the right tolerance 
        
        
            
            # calculate timestep for input timeseries
            t = tser.index.to_numpy()
            dt = np.diff(t,prepend = t[0],).astype(float)/1e9 # time delta in seconds
            dt_99_in = np.percentile(dt,99) # mask to identify data gaps 
            
            # calculate timestep for existing timeseries
            t = self.pose.index.to_numpy()
            dt = np.diff(t,prepend = t[0],).astype(float)/1e9 # time delta in seconds
            dt_99 = np.percentile(dt,99) # mask to identify data gaps 
            
            tolerance = max(dt_99,dt_99_in)
            

            
        
        tser = tser.reindex(self.pose.index,tolerance=pd.to_timedelta(f'{tolerance} s'), method='nearest')
        if field_name in self.pose.columns: # check if input field_name is valid
        
            self.pose[field_name] = tser.to_numpy()
            # if z_convention == self.z_convention:
            #     self.pose[field_name] = tser.to_numpy()
            # else:
            #     self.pose[field_name] = -1*tser.to_numpy()
                
        
        else:
            raise SyntaxWarning(f'{field_name} is not a valid field \nField options: {", ".join(self.pose.columns)}')
            
            
    def save(self, fpath = None):
        # serialize a Pose robject 
        if fpath == None:
            fpath = '.' + os.sep + self.name + '.pose'
        else:
            fpath = fpath + '.pose'
            
            
        with open(fpath, "wb") as dill_file:
            # serialize the data manager object and save to file
            dill.dump(self, dill_file)
            
            
    def copy(self, name, deep = False):
        """
        Make a copy of the pose object.

        Parameters
        ----------
        deep : bool, optional
            If True, perform a deep copy. If False, perform a shallow copy.
            The default is False.
            
        name: str
            name of the copied Pose object (updates self.name)
            

        Returns
        -------
        Pose
            A copy of the pose object.
        """
        
        
        if deep:
            pout = copy.deepcopy(self)
        else:
            pout = copy.copy(self)
            
            pout.name = name
        return pout
    
    def merge(self,pose_in):
        None

#%%
###############################################################################
def concatenate(pose_in, name, z_convention='automatic'):
    """
    Concatenate multiple pose objects.

    This function concatenates multiple pose objects into a single pose object. It checks the z-convention of all
    input data and adjusts it as necessary.

    Parameters:
        pose_in (list): A list of pose objects to concatenate.
        name (str): The name of the concatenated pose object.
        z_convention (str, optional): The z-convention for the input data. If set to 'automatic' (default), the function
            will determine the most frequent z-convention among the input pose objects.

    Returns:
        Pose.Pose: A concatenated pose object.

    Example:
        # Create a list of pose objects
        pose_objects = [pose1, pose2, pose3]

        # Concatenate the pose objects into a new pose object named 'concatenated_pose'
        concatenated_pose = concatenate(pose_objects, name='concatenated_pose')
    """
    def most_frequent(List):
        return max(set(List), key=List.count)

    # Determine the most frequent z-convention if 'automatic' is selected
    if z_convention == 'automatic':
        z_convention = most_frequent([p.z_convention for p in pose_in])

    pose_dfs = []
    for pose in pose_in:
        if pose.z_convention == z_convention:
            pose_dfs.append(pose.pose)
        else:
            pose.set_z_convention(z_convention, update_z=True)
            pose_dfs.append(pose.pose)

    pose = pd.concat(pose_dfs)
    pose = pose[~pose.index.duplicated(keep='first')].copy()
    pose.sort_index(inplace=True)
    pose = pose.dropna()

    p = Pose(name=name, z_convention=z_convention)
    p.pose = pose

    return p

def load(fpath):
    # deserialize a Pose object 
    with open(fpath, "rb") as dill_file:
        # deserialize data manager object and reinitilize the print consoles
         p = dill.load(dill_file)    

             
    return p