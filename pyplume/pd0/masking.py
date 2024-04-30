# -*- coding: utf-8 -*-
"""
Created on Sat Jul 22 08:55:44 2023

@author: anba
"""
import numpy as np 

class masking:
    def __init__(self,pd0,**kwargs):
        
        self._pd0 = pd0
        
        self.masks = {} # dict to hold masks for ensemble data
        self.mask_status= {} # dict to hold activation status of defined masks 
        
        
        
    def delete_mask(self,name):
        """
        Define a mask
    
        Parameters
        ----------

        name : str
            name for the mask

        Returns
        -------
        None.
    
        """     
        
        
        try:
            del self.masks[name]
            del self.mask_status[name]
            #print('delete successful')
        except:
            ValueError(f'Invalid mask name')
            
            
        
        
        
            
    def define_mask(self,mask,name, set_active = False):
        """
        Define a boolean mask that can be applied to ensemble data when ensemble
        data is called. The ensemble data corresponding FALSE entries in the mask
        will be converted to np.nan 
    
        Parameters
        ----------
        mask : numpy array
            numpy array with dimensions (n_beams,n_bins,n_ensembles).
        name : str
            name for the mask
        set_active: bool
            if True, the defined mask will be activated. All calls to 
            get_ensemble_array will have this mask applied. Default is False.  
    
        Returns
        -------
        None.
    
        """
        #check that mask has correct dimensions  
        valid_dims = (self._pd0.config.number_of_beams,self._pd0.config.number_of_cells,self._pd0.n_ensembles)
        if not np.shape(mask) == valid_dims:
            ValueError(f'Mask must have dimensions of {valid_dims}')
        
    
        
        self.masks[name] = mask
        
    
        # initalize the mask status 
        if set_active:
            self.mask_status[name] = True
        else:
            self.mask_status[name] = False
      

    def set_mask_status(self,status,name = 'all'):
        """
        Change the status of a mask, or multiple masks.The ensemble data 
        corresponding to FALSE entries in the mask will be converted to np.nan

        Parameters
        ----------
        name : str or list of str, optional
            mask name, or list of mask names. if 'all', all defined masks will be 
            activated. The default is 'all'.
        status : TYPE
            DESCRIPTION.

        Raises
        ------
        ValueError
            Invalid mask name

        Returns
        -------
        None.

        """
        
        
        if name == 'all':
            for key in self.masks.keys():
                self.mask_status[key] = status
                
        elif type(name) == list:
            for n in names:
                # check if mask exists 
                if n in self.masks.keys(): 
                    self.mask_status[name] = status
                else: 
                    raise ValueError(f'{name} is not a defined mask.')
                
        elif type(name) == str:
            if name in self.masks.keys(): 
                self.mask_status[name] = status
            else: 
                raise ValueError(f'{name} is not a defined mask.')
        
        
        
    def apply_masks(self,X):
        """
        apply all of the active masks to the ensemble array X. Masked values 
        will be converted to np.nan
        

        Parameters
        ----------
        X : numpy array
            array of ensemble data with dimensions (n_bins,n_ensembles).

        Returns
        -------
        X : numpy array
            masked array of ensemble data with dimensions (n_bins,n_ensembles).

        """
        #combined_mask = np.full((self._pd0.config.number_of_cells,self.n_ensembles),False)
        if self.masks:
            for mask_name in self.masks.keys():
                if self.mask_status[mask_name]:
                    mask = self.masks[mask_name]
                    
                    #print(np.shape(mask), np.shape(X))
                    np.putmask(X,~mask, values = np.nan)


        return X
        
        