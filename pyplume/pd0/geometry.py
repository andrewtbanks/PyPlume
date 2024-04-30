# -*- coding: utf-8 -*-
"""
Created on Fri Jul 21 15:51:57 2023

@author: anba
"""
import numpy as np 
import sys
import copy
import rich
import pandas as pd
#if __name__ == '__main__':
# sys.path.insert(1, r'C:\Users\anba\Desktop\Projects\pyplume\pyplume\ptools')
# import ptools


from ..ptools import ptools


class geometry:
    def __init__(self,pd0,**kwargs):
        
        self._pd0 = pd0
        
        self.instrument_depth = 0 # instrument height above bed
        self.instrument_HAB = 0 # intrument height above bed
        
        
    def get_bin_midpoints(self):
        """
        Generate numpy array of bin midpoint distances in meters. 
        Args:
            None
        Returns:
            numpy array with dimensions (n_ensembles)  
        """          
        
        # if self._pd0.config.beam_facing == 'DOWN':
        #     direction = -1
        # else: direction = 1
        
        beam_length = self._pd0.config.number_of_cells*self._pd0.config.depth_cell_length # total length of the beam 
        
        
        bin_distances = np.linspace(self._pd0.config.bin_1_distance,
                                    beam_length+self._pd0.config.bin_1_distance,
                                    self._pd0.config.number_of_cells)/100
        
        
            
        
        
        return bin_distances 
    
    def get_bin_midpoints_depth(self):
        """
        Generate numpy array of bin midpoint depths, based on static instrument depth. 
        Args:
            None
        Returns:
            numpy array with dimensions (n_ensembles)  
        """   
        if self._pd0.config.beam_facing == 'DOWN':
            bin_midpoints_depth = self.instrument_depth + self.get_bin_midpoints() 
        elif self._pd0.config.beam_facing =='UP':
            bin_midpoints_depth = self.instrument_depth - self.get_bin_midpoints() 
        return bin_midpoints_depth
    
    def get_bin_midpoints_HAB(self):
        """
        Generate numpy array of bin midpoint heights, based on static instrument heihgt above bed. 
        Args:
            None
        Returns:
            numpy array with dimensions (n_ensembles)  
        """  
        if self._pd0.config.beam_facing == 'DOWN':
            bin_midpoints_HAB = self.instrument_HAB - self.get_bin_midpoints()
        elif self._pd0.config.beam_facing =='UP':
            bin_midpoints_HAB = self.instrument_HAB + self.get_bin_midpoints()
        return bin_midpoints_HAB         
    
    
    
    # def get_absolute_beam_midpoint_positions(self):
    #     """
    #     Calculate the absolute position of each beam, taking into account the 
    #     position and orientation (pitch,roll,heading) of the platform (e.g., ROV), 
    #     and the relative geometry of the beam (e.g.,beam angle, bin size) 
 
 
    #     Returns
    #     -------
    #     absolute_beam_midpoint_positions: list of numpy arrays
    #         list of beam midpoint positions for each beam and each ensemble.  
    #         Element of the list contains the array for each beam, and each array
    #         has dimensions of (3,n_bins,n_ensembles)
            
 
    #     """
        
    #     ## get position of beam midpoints for every ensemble 
    #     absolute_beam_midpoint_positions = []
    #     X = np.empty((3,self._pd0.config.number_of_beams,self._pd0.config.number_of_cells,self._pd0.n_ensembles))
    #     pose = self.pose.pose[['x','y','z']].to_numpy().T #position  
    #     for b in range(self._pd0.config.number_of_beams):
    #         beam = self.relative_beam_midpoint_positions[b]
    #         #absolute_beam_midpoint_positions.append(np.full((3,self._pd0.config.number_of_cells,self._pd0.n_ensembles),0, dtype = float))
    #         for e in range(self._pd0.n_ensembles):
                
    #             #build rotation matrix
                
         
    #             yaw = self.pose.pose['heading'].to_numpy()[e]
    #             pitch = self.pose.pose['pitch'].to_numpy()[e]
    #             roll = self.pose.pose['roll'].to_numpy()[e]
                
    
                
    #             # yaw   = self.orientation[2][e]
    #             # pitch = self.orientation[0][e]
    #             # roll  = self.orientation[1][e]
    #             R = np.dot(ptools.gen_rot_x(roll),ptools.gen_rot_z(yaw).dot(ptools.gen_rot_y(pitch)))
    #             Xp = np.add(pose[:,e],beam.T.dot(R)).T
    #             X[:,b,:,e] = Xp#np.add(pos[:,e],beam.T).T        
    #     #% apply masks 
    #     # X = np.empty((self-mask(.config.number_of_beams,self.config.number_of_cells,self.n_ensembles))
        
        
    #     X[0] = self._pd0.mask.apply_masks(X[0])
    #     X[1] = self._pd0.mask.apply_masks(X[1])
    #     X[2] = self._pd0.mask.apply_masks(X[2])
        
    #     return X    
    
   
        

        
############ Set Functions ####################################################



    def set_pose(self,Pose,update_orientation = False,**kwargs):
        """
        Define the instrument pose (position and orientation) with a 
        Pose object. Makes a cope of the pose object and stores it under 
        ctd.geometry.Pose
        
        Parameters
        ----------
        Pose : Pose
            Pose object containing position and orientation information.
        update_orientation : bool, optional 
            If True, the adcp orientation (from internal gyroscope) will be 
            used as the pose orientation (pitch, roll, and heading/yaw)
    
        method : 'nearest', 'ffill','bfill'
        
        **kwargs to send to pd.DataFrame.reindex
        Returns
        -------
        None
        """
        # copy input object and Resample the input timeseries to the ADCP ensemble timesteps
        self.pose = copy.deepcopy(Pose)
        self.pose.resample_to(self._pd0.get_ensemble_datetimes(),kwargs)
        
        if update_orientation:
            self.pose.pose['pitch'] = self._pd0.get_sensor_pitch()
            self.pose.pose['roll'] = self._pd0.get_sensor_roll()
            self.pose.pose['heading'] = self._pd0.get_sensor_heading()
            
            
        
            
        
        
        
        
        
        
        
        
        
        
    # def set_sensor_orientation(self,**kwargs):
    #     """
    #     Set the orientation data for the sensor. Accepts input orientation
    #     timeseries, and assigns instrument position based on the closest position 
    #     timestamp to each ensemble timestamp. All orientations are in degrees, 
    #     with pitch and roll ranging[-180,179.99],and heading ranging from [0,359.99] 
        
        
    
    #     Parameters
    #     ----------
    #     orient_in : (optional) pandas dataframe containing a timeseries of roll,pitch,heading 
    #             data corresponding to the orientation of the instrument. Must have 
    #             columns named 'pitch', 'roll' and 'heading'. Index must be a pandas 
    #             timestamp. If not specified, then the onboard gyroscope and compass data 
    #             (from the variable headers) will be used. 
    
    #     Returns
    #     -------
    #     None.
    
    #     """
        
    #     self.orientation = np.full((3,self._pd0.n_ensembles),np.nan)
        
        
    #     orient_in = kwargs.pop('orient_in',None)
        
    #     #if kwargs.get('orient_in'):
    #     if type(orient_in) == type(None):
    #         print('using sensor data')
    #         self.orientation[0,:] = self._pd0.get_sensor_pitch()
    #         self.orientation[1,:] = self._pd0.get_sensor_roll()
    #         self.orientation[2,:] = self._pd0.get_sensor_heading()
    #     else:
    #         et = self._pd0.get_ensemble_datetimes() # ensemble times
    #         for i,etime in enumerate(et):
    #             index = orient_in.index.get_indexer([etime], method='ffill')[0] # index of nearest input positon to the ensemble timestamp
    #             self.orientation[0,i] = orient_in.iloc[index].pitch
    #             self.orientation[1,i] = orient_in.iloc[index].roll
    #             self.orientation[2,i] = orient_in.iloc[index].heading 

            
        
    # def set_sensor_position(self,pos_in):
    #     """
    #     Set the position data for the sensor. Accepts input position timeseries,
    #     and assigns instrument position based on the closest position timestamp to
    #     each ensemble timestamp. 
    
    #     Parameters
    #     ----------
    #     pos_in : pandas dataframe
    #         containing a timeseries of x,y,z data corresponding to the position of 
    #         the instrument. Must have columns named 'x', 'y' and 'z'. Index must be
    #         a pandas timestamp. 
            
    
    #     Returns
    #     -------
    #     None.
    
    #     """
    #     et = self._pd0.get_ensemble_datetimes() # ensemble times
    #     self.position  = np.full((3,self._pd0.n_ensembles),np.nan)
    #     for i,etime in enumerate(et):
    #         index = pos_in.index.get_indexer([etime], method='ffill')[0] # index of nearest input positon to the ensembel timestamp

    #         self.position[0,i] = pos_in.iloc[index].x
    #         self.position[1,i] = pos_in.iloc[index].y
    #         self.position[2,i] = pos_in.iloc[index].z     
        
                    
    def calculate_beam_geometry(self,rotation = 0,offset = (0,0,0), dr = 0.1):
        """
    
        calculate the relative beam midpoint position for every ensemble (accounting for sensor orientation and platform orientation)
        calculate the true bottom track distance (accounting for orientation). 
        calculate the absolute position of each bin/ensemble in depth and relative to bottom track
        
        ----------
        rotation : float, optional
            Orientation of the self._pd0. This is the number of degrees clockwise 
            from the forward direction of the mounting platform. (E.g., the bow
            of the vessel). The default is 0.
        offset : numpy array, optional
            x,y,z offsets for the instrument. This offset 
            should be the relative distance between the position measuremet
            (e.g., from the vessel GPS) and the center of the ADCP transducer 
            face.The default is (0,0,0).
        dr : float, optional
            radial distance from the center of the face of the ADCP to the center 
            of the transdecer faces. The default is 0.1.
    
        Returns
        -------
        None.
    
        """
        
        # offset = (0,0,0)
        # dr = 0.1
        # rotation = 0
        ## calculate the orientation of the beam origins (e.g., orientation on face of ADCP) including the rotation of the insttuymet. (rotation of 0 means beam 3 is pointing "forwards" - in the positive x direction)
        R = ptools.gen_rot_z(theta = rotation)
        if self._pd0.config.beam_facing == 'DOWN':
            relative_beam_origin = np.array([(dr,0,0),(-dr,0,0),(0,dr,0),(0,-dr,0)])# position of each beam relative to the center of the face of the instrument
        if self._pd0.config.beam_facing == 'UP':
            relative_beam_origin = np.array([(-dr,0,0),(dr,0,0),(0,dr,0),(0,-dr,0)])# position of each beam relative to the center of the face of the instrument
        
        relative_beam_origin = np.add(offset,relative_beam_origin)  # offset origin to be relative to the center of mass of the position measurement
        relative_beam_origin = relative_beam_origin.dot(R).T # rotate the origin points - assums that positive y direction is forward (beam 3) 
        
        #%
        #% build an array containing the unrotated beam vectors (at this point they will all be pointing directly downward)
        relative_beam_midpoint_positions = np.full((3,self._pd0.config.number_of_beams,self._pd0.config.number_of_cells,self._pd0.n_ensembles),0, dtype = float)
        
        
        #X = np.empty((3,self._pd0.config.number_of_beams,self._pd0.config.number_of_cells,self._pd0.n_ensembles))
        X = np.repeat(self.pose.pose[['x','y','z']].to_numpy().T[:,np.newaxis,:],self._pd0.config.number_of_cells, axis = 1)
        X = np.repeat(X[:,np.newaxis,:,:], self._pd0.config.number_of_beams,axis = 1)
        X_hab = X.copy()
        
        
        
       
        bt_vec = np.full((3,self._pd0.config.number_of_beams,self._pd0.n_ensembles),0, dtype = float)
        
        bt_range = self._pd0.get_bottom_track()
        if any(~np.isnan(bt_range).flatten()):
            # bottom track range for each beam and ensemble 
            bt_vec[2] = -bt_range
    
        for b in range(self._pd0.config.number_of_beams):
            
            
            # array holding beam midpoints coordinates 
            beam_midpoints = np.repeat(np.outer((0,0,0),np.ones(self._pd0.config.number_of_cells))[:, :, np.newaxis], self._pd0.n_ensembles, axis=2)
            
            ## overwrite z-offset coordiate with HAB(measurement doesnt care about sensor z-offset at origin)
            #beam_midpoints[2] = Z[beam_no]
            
            if self._pd0.config.beam_facing == 'DOWN':
                beam_midpoints[2] += -np.repeat(self.get_bin_midpoints()[:, np.newaxis], self._pd0.n_ensembles, axis=1) #+ 1.18
            else: 
                beam_midpoints[2] += np.repeat(self.get_bin_midpoints()[:, np.newaxis], self._pd0.n_ensembles, axis=1)
            
            # #% rotation matricies for 
            theta_beam = self._pd0.config.beam_angle
            Ry_cw = ptools.gen_rot_y(-theta_beam)
            Rx_cw = ptools.gen_rot_x(-theta_beam)
            Ry_ccw = ptools.gen_rot_y(theta_beam)
            Rx_ccw = ptools.gen_rot_x(theta_beam)   
            
            #% rotate the bottom track vectors 
            
            #% account for beam geometry
            for e in range(self._pd0.n_ensembles):
                if b == 0:
                    relative_beam_midpoint_positions[:,0,:,e] = Ry_cw.dot(beam_midpoints[:,:,e])
                    bt_vec[:,b,e] = Ry_cw.dot(bt_vec[:,b,e])
                elif b == 1:
                    relative_beam_midpoint_positions[:,1,:,e] = Ry_ccw.dot(beam_midpoints[:,:,e])
                    bt_vec[:,b,e] = Ry_ccw.dot(bt_vec[:,b,e])
                elif b == 2:
                    relative_beam_midpoint_positions[:,2,:,e] = Rx_ccw.dot(beam_midpoints[:,:,e])
                    bt_vec[:,b,e] = Rx_ccw.dot(bt_vec[:,b,e])
                elif b == 3: 
                    relative_beam_midpoint_positions[:,3,:,e] = Rx_cw.dot(beam_midpoints[:,:,e])  
                    bt_vec[:,b,e] = Rx_cw.dot(bt_vec[:,b,e])
                   
                yaw = self.pose.pose['heading'].to_numpy()[e]
                pitch = self.pose.pose['pitch'].to_numpy()[e]
                roll = self.pose.pose['roll'].to_numpy()[e]
                
                R = np.dot(ptools.gen_rot_x(roll),ptools.gen_rot_z(yaw).dot(ptools.gen_rot_y(pitch)))
                relative_beam_midpoint_positions[:,b,:,e] = relative_beam_midpoint_positions[:,b,:,e].T.dot(R).T
 
                bt_vec[:,b,e] = bt_vec[:,b,e].dot(R).T
                
                
                #Xp =np.repeat(self.pose.pose[['x','y','z']].to_numpy().T[:,e])[:, np.newaxis], self._pd0.n_ensembles, axis=1) relative_beam_midpoint_positions[:,b,:,e]
                
                X[:,b,:,e] +=relative_beam_midpoint_positions[:,b,:,e]
                  
                X_hab[:,b,:,e] += relative_beam_midpoint_positions[:,b,:,e]
                X_hab[2,b,:,e] = relative_beam_midpoint_positions[2,b,:,e] - bt_vec[2,b,e] 
                
                
        self.relative_beam_midpoint_positions = relative_beam_midpoint_positions
        self.corrected_bottom_track = bt_vec[2]
        
        instrument_range = (self._pd0.config.bin_1_distance + self._pd0.config.depth_cell_length*self._pd0.config.number_of_cells)/100
        #self.corrected_bottom_track[self.corrected_bottom_track>instrument_range] = np.nan #reject bad data, replace with unrotated values 
        
        self.corrected_bottom_track[self.corrected_bottom_track>instrument_range] = bt_range[self.corrected_bottom_track>instrument_range]
        
        
        self.absolute_beam_midpoint_positions = X
        self.absolute_beam_midpoint_positions_HAB = X_hab
        #return X,X_hab,bt_vec[2]
        
    def get_relative_beam_midpoint_positions(self, mask = True):
        """
        retrieve absolute x,y,z position of each bin and ensemble with masks applied. 
 
 
        Returns
        -------
        absolute_beam_midpoint_positions: list of numpy arrays
            list of beam midpoint positions for each beam and each ensemble.  
            Element of the list contains the array for each beam, and each array
            has dimensions of (3,n_bins,n_ensembles)
            
 
        """
        X = self.relative_beam_midpoint_positions
        if mask:
            X[0] = self._pd0.mask.apply_masks(X[0])
            X[1] = self._pd0.mask.apply_masks(X[1])
            X[2] = self._pd0.mask.apply_masks(X[2])
            
        return X 
        
    def get_absolute_beam_midpoint_positions(self, mask = True):
        """
        retrieve absolute x,y,z position of each bin and ensemble with masks applied. 
 
 
        Returns
        -------
        absolute_beam_midpoint_positions: list of numpy arrays
            list of beam midpoint positions for each beam and each ensemble.  
            Element of the list contains the array for each beam, and each array
            has dimensions of (3,n_bins,n_ensembles)
            
 
        """
        X = self.absolute_beam_midpoint_positions
        if mask:
            X[0] = self._pd0.mask.apply_masks(X[0])
            X[1] = self._pd0.mask.apply_masks(X[1])
            X[2] = self._pd0.mask.apply_masks(X[2])
            
        return X 
    
    def get_absolute_beam_midpoint_positions_HAB(self, mask = True):
        """
        retrieve absolute x,y,z position of each bin and ensemble with masks applied. 
 
 
        Returns
        -------
        absolute_beam_midpoint_positions: list of numpy arrays
            list of beam midpoint positions for each beam and each ensemble.  
            Element of the list contains the array for each beam, and each array
            has dimensions of (3,n_bins,n_ensembles)
            
 
        """
        X = self.absolute_beam_midpoint_positions_HAB
        if mask:
            X[0] = self._pd0.mask.apply_masks(X[0])
            X[1] = self._pd0.mask.apply_masks(X[1])
            X[2] = self._pd0.mask.apply_masks(X[2])
            
        return X 
    def get_corrected_bottom_track(self):
        """
        retrieve absolute x,y,z position of each bin and ensemble with masks applied. 
 
 
        Returns
        -------
        absolute_beam_midpoint_positions: list of numpy arrays
            list of beam midpoint positions for each beam and each ensemble.  
            Element of the list contains the array for each beam, and each array
            has dimensions of (3,n_bins,n_ensembles)
            
 
        """
        X = self.corrected_bottom_track
            
        return X 
    
    def set_beam_relative_geometry(self,rotation = 0,offset = (0,0,0), dr = 0.1):
        """
        Calculate the x,y,z position of each bin in the coordinate reference 
        frame of either the the position measurement for the instrument. Accounts 
        for instrument beam angle (e.g., 20 deg) in x-z and y-z planes. Positions are in the reference
        frame of the instrument position measurement.
        Parameters
        ----------
        rotation : float, optional
            Orientation of the ADCP. This is the number of degrees clockwise 
            from the forward direction of the mounting platform. (E.g., the bow
            of the vessel). The default is 0.
        offset : numpy array, optional
            x,y,z offsets for the instrument. This offset 
            should be the relative distance between the position measuremet
            (e.g., from the vessel GPS) and the center of the ADCP transducer 
            face.The default is (0,0,0).
        dr : float, optional
            radial distance from the center of the face of the ADCP to the center 
            of the transdecer faces. The default is 0.1.

        Returns
        -------
        None.

        """

    
        # See WorkHorseCommands and Ouput Data Format page 53
        # rotation = 45
        # offset = adcp_offset
        
        # dr = 0.1 # distance from center of the unit to the center of each transducer face
        
        
        ## calculate the orientation of the beam origins (e.g., orientation on face of ADCP) including the rotation of the insttuymet. (rotation of 0 means beam 3 is pointing "forwards" - in the positive x direction)
        R = ptools.gen_rot_z(theta = rotation)
        if self._pd0.config.beam_facing == 'DOWN':
            self.relative_beam_origin = np.array([(dr,0,0),(-dr,0,0),(0,dr,0),(0,-dr,0)])# position of each beam relative to the center of the face of the instrument
        if self._pd0.config.beam_facing == 'UP':
            self.relative_beam_origin = np.array([(-dr,0,0),(dr,0,0),(0,dr,0),(0,-dr,0)])# position of each beam relative to the center of the face of the instrument
            
        self.relative_beam_origin = np.add(offset,self.relative_beam_origin)  # offset origin to be relative to the center of mass of the position measurement
        self.relative_beam_origin = self.relative_beam_origin.dot(R).T # rotate the origin points - assums that positive y direction is forward (beam 3) 
        
        
        
        #% build an array containing the unrotated beam vectors (at this point they will all be pointing directly downward)
        self.relative_beam_midpoint_positions = []
        for b in range(self._pd0.config.number_of_beams):
            origin = self.relative_beam_origin[:,b]
            beam_midpoints = np.outer(origin,np.ones(self._pd0.config.number_of_cells))
            if self._pd0.config.beam_facing == 'DOWN':
                beam_midpoints[2] += -self.get_bin_midpoints()
            else: 
                beam_midpoints[2] += self.get_bin_midpoints()
            self.relative_beam_midpoint_positions.append(beam_midpoints)
        
        
        # rotate each beam about its origin point by theta_beam. 
        
        #theta_beam = self._pd0.ensemble_data[0]['FIXED LEADER']['BEAM ANGLE']
        theta_beam = self.config.beam_angle
 
        Ry_cw = ptools.gen_rot_y(-theta_beam) # rotate clockwise about the y-axis
        Rx_cw = ptools.gen_rot_x(-theta_beam) # rotate clockwise about the x-axis
        Ry_ccw = ptools.gen_rot_y(theta_beam) # rotate counter-clockwise about the y-axis
        Rx_ccw = ptools.gen_rot_x(theta_beam) # rotate counter-clockwise about the y-axis
        
        # self.relative_beam_midpoint_positions[0] = Rx_cw.dot(Ry_cw.dot(self.relative_beam_midpoint_positions[0]))
        # self.relative_beam_midpoint_positions[1] = Rx_ccw.dot(Ry_ccw.dot(self.relative_beam_midpoint_positions[1]))
        # self.relative_beam_midpoint_positions[2] = Rx_ccw.dot(Ry_cw.dot(self.relative_beam_midpoint_positions[2]))
        # self.relative_beam_midpoint_positions[3] = Rx_cw.dot(Ry_ccw.dot(self.relative_beam_midpoint_positions[3]))     
        
        self.relative_beam_midpoint_positions[0] = Ry_cw.dot(self.relative_beam_midpoint_positions[0])
        self.relative_beam_midpoint_positions[1] = Ry_ccw.dot(self.relative_beam_midpoint_positions[1])
        self.relative_beam_midpoint_positions[2] = Rx_ccw.dot(self.relative_beam_midpoint_positions[2])
        self.relative_beam_midpoint_positions[3] = Rx_cw.dot(self.relative_beam_midpoint_positions[3])  
        
        
        
        
