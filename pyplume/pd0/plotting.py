import numpy as np
import os 
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.collections import LineCollection
import matplotlib.ticker as mticker
from matplotlib.ticker import AutoLocator
import sys
import seaborn as sns
import pandas as pd
import cmocean
# #if __name__ == '__main__':
# sys.path.insert(1, r'C:\Users\anba\Desktop\Projects\pyplume\pyplume\ptools')
# import ptools

# sys.path.insert(1, r'C:\Users\anba\Desktop\Projects\pyplume\pyplume\plotting')
# from matplotlib_shell import subplots
    
    
# else:
from ..ptools import ptools
from ..plotting.matplotlib_shell import subplots, dhi_colors



#from ..plotting import plotting





class plotting:
    def __init__(self,pd0):
        
        self._pd0 = pd0
        
        
        
        self._cmaps =  {'PERCENT GOOD': plt.cm.binary,
                     'ECHO INTENSITY': plt.cm.turbo,
                     'FILTERED ECHO INTENSITY': plt.cm.turbo,
                     'CORRELATION MAGNITUDE': plt.cm.nipy_spectral,
                     'ABSOLUTE BACKSCATTER':plt.cm.turbo,
                     'NTU':plt.cm.turbo,
                     'SSC':plt.cm.turbo,
                     'SIGNAL TO NOISE RATIO':plt.cm.bone_r}


    def four_beam_flood_plot(self,**kwargs):#plot_by = 'bin',start_bin = None,end_bin = None,start_ensemble = None,end_ensemble = None,title = None):
        """
        Generate a flooded color plot
    
        Parameters
        ----------
        self._pd0 : object
            WorkhorseADCP object.
        plot_by : str
            y-axes plot method ('bin','depth').
        start_bin : int
            First bin to plot. (use zero based index)
        end_bin : int
            Last bin to plot.(use zero based index)
        start_ensemble : int
            First ensemble to plot.(use zero based index)
        end_ensemble : int
            Last ensemble to plot.(use zero based index)
        title : str
            plot axes title.
        field_name: str
            ensemble data type (string). "ECHO INTENSITY" (default), "CORRELATION MAGNITUDE", "PERCENT GOOD", others in ensemble_fields
    
        Returns
        -------
        fig,ax
            matplotlib figure and axes objects
    
        """
        
        # if self._pd0.ensemble_data[0]['COORDINATE SYSTEM'] != 'BEAM COORDINATES':
        #     print('Plot feature only implemented for BEAM coordinates')
    
    
        plot_by = kwargs.pop('plot_by','bin')  
        start_bin = kwargs.pop('start_bin',0)
        end_bin = kwargs.pop('end_bin',self._pd0.config.number_of_cells-1)    
        start_ensemble = kwargs.pop('start_ensemble',0)
        end_ensemble = kwargs.pop('end_ensemble',self._pd0.n_ensembles)       
        title = kwargs.pop('title',self._pd0.metadata.filepath.split(os.sep)[-1])    
        field_name = kwargs.pop('field_name','ECHO INTENSITY')
        ctd = kwargs.pop('ctd',None)
        
        extra_rows = kwargs.pop('extra_rows',0)
        
        nbins = (end_bin - start_bin)
        X  = self._pd0.get_ensemble_array(field_name = field_name)[:,start_bin:end_bin,start_ensemble:end_ensemble]
        
        x1 = X[0]
        x2 = X[1]
        x3 = X[2]
        x4 = X[3]

        #echo_intensity = self._pd0.get_ensemble_array(beam_number = 0, field_name = 'CORRELATION MAGNITUDE')[start_bin:end_bin,start_ensemble:end_ensemble]
        ensemble_times = self._pd0.get_ensemble_datetimes()[start_ensemble:end_ensemble]
        
        subplot_titles = []
        nrow = self._pd0.config.number_of_beams 
        if ctd:
            fig,ax = subplots(nrow = nrow+1 + extra_rows, ncol = 1, figheight = 8, figwidth = 10.5, width_ratios = [1], sharex = True, sharey = False)
            # Manually link the y-axes of the first four subplots
            base_ax = ax[0]  # Use the first subplot as the base for sharing
            for axes in ax[1:nrow]:  # Link axes 2, 3, 4 to the first
                axes.sharey(base_ax)
            
            # Optionally, you can use the below loop to enforce the linked behavior visually
            # It syncs all linked axes limits after plotting
            #base_ax.get_shared_y_axes().join(*ax[:nrow])
            base_ax.autoscale()
        else:
            fig,ax = subplots(nrow = nrow + extra_rows, ncol = 1, figheight = 8, figwidth = 10.5, width_ratios = [1], sharex = True, sharey = True)
    
        ## format the ADCP data axes (left)
        topax = ax[0].twiny()
        topax.set_xlim(start_ensemble,end_ensemble)
        ax[0].set_zorder(4)
        #topax.set_xticks(np.arange())
        ax[0].set_title(field_name)
        
        fig.suptitle(title, fontsize = 16)
        

            # for i,axes in enumerate(ax[:self._pd0.config.number_of_beams]):
            #     axes.get_shared_y_axes().remove(ax[-1])
            #     ax[-1].get_shared_y_axes().remove(axes)
    
        # set plot params based on instrument configuration 
    
        def set_axes_labels(axs,ylabel):
            # function to set the ylabel on a list of axes objects 
            for ax in axs:
                ax.set_ylabel(ylabel, fontsize = 8)
                
            return axs
                
        
        
        # set plotting extents in vertical direction
        if plot_by == 'bin':
            ylims = [start_bin,end_bin]
            set_axes_labels(ax,'Bin')
        elif plot_by == 'depth':
            bin_depths = self._pd0.geometry.get_bin_midpoints_depth()
            ylims = [bin_depths[start_bin],bin_depths[end_bin]]
            set_axes_labels(ax,'Depth')
        elif plot_by == 'HAB':
            bin_heights = self._pd0.geometry.get_bin_midpoints_HAB()
            ylims = [bin_heights[start_bin],bin_heights[end_bin]]
            set_axes_labels(ax,'Height Above Bed (m)')
            #fig.text(0.02,0.5, 'Height Above Bed (m)', va='center', rotation='vertical',fontsize = 12)
        else: 
            print('Invalid plot_by parameter')
            
            
            
        
        
        def get_plot_extent(X):
            """
            set the image plot extent based on the ADCP beam configuration
    
            Parameters
            ----------
            X : numpy array
                Input array (ensemble data).
    
            Returns
            -------
            X : numpy array
                Possibly rotated input array (ensemble data) - to match the sensor orientation.
                
            extent : list
                bounding box for the plotted image.
    
            """
       
        
            # set plotting extents in horizontal direction
            xlims = mdates.date2num(ensemble_times) # list of elegible xlimits 
            if self._pd0.config.beam_facing == 'UP':
                
                extent = [xlims[0],xlims[-1],ylims[0],ylims[1]]
            else:
                X = np.flipud(X)
                extent = [xlims[0],xlims[-1],ylims[1],ylims[0]]
            return X,extent
            
        
    
        cmap = self._cmaps.pop(field_name,'turbo')
        
        dataset = [x1,x2,x3,x4] # hold all elegible beam datasets 
        dataset = dataset[:self._pd0.config.number_of_beams] # just plot for valid beams
        
        for x in dataset:
            x[x == 32768] = np.nan
        
        
        
        if field_name == 'PERCENT GOOD':
            vmin = 0
            vmax = 100
        elif field_name == 'SIGNAL TO NOISE RATIO':
            vmin = np.nanmin(dataset)
            vmax = 50
        elif field_name == 'ABSOLUTE BACKSCATTER':
            vmin = -95
            vmax = -10
        else:
            vmin = np.nanmin(dataset)
            vmax = np.nanmax(dataset)
        
        ## overwrite with kwargs if provided 
        vmin = kwargs.pop('vmin',vmin) 
        vmax = kwargs.pop('vmax',vmax) 
        
        
        for i,x in enumerate([x1,x2,x3,x4]):
            xi,extent = get_plot_extent(x)
            if self._pd0.config.beam_facing == 'UP': 
                origin = 'lower'
            
            else: origin = 'upper'
            
            im = ax[i].matshow(x, origin = origin, extent = extent, cmap = cmap, aspect = 'auto', resample = False, vmin = vmin, vmax = vmax)
            
        
        
        for i,axes in enumerate(ax[:self._pd0.config.number_of_beams]):# modify subplot apperance 
            # set colorbar 
            
            
            #if i==(len(ax)-1) and ctd: break # dont plot a colorbar if 
            cbar = fig.colorbar(im, ax=axes,orientation="vertical",location = 'right',fraction=0.046)
            cbar.set_label(f'Beam {i+1}', rotation=90,fontsize= 8)
            
            axes.xaxis.set_major_locator(mticker.FixedLocator(axes.get_xticks()))
            axes.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M %d%b%y '))
            axes.grid(alpha = 0.1)
            axes.set_xticklabels(axes.get_xticklabels(), rotation = 0, ha = 'center')
            axes.xaxis.tick_bottom()
            axes.xaxis.set_label_position('bottom') 
            
            axes.yaxis.set_major_locator(AutoLocator())

                        
            
        if ctd:
    
            #ax[-1].autoscale(enable=True, axis='y', tight=False)
            # group = ax[-1].get_shared_y_axes()
            # group.remove(ax[-1])
            df = ctd.to_pandas_df()
            df = df.reindex(ensemble_times, method = 'nearest', tolerance = pd.to_timedelta('60s')).dropna()

            
            
            if field_name == 'SSC':
                #t,ssc = ctd.get_timeseries_data(field_name = 'SSC (mg/L)')
                t = df.index
                ssc = df['SSC (mg/L)']
                sc = ax[-1].scatter(t,ssc,c= ssc,vmax = vmax,vmin = vmin, alpha = 0.9, label = 'SSC (CTD)')
                ax[-1].set_ylabel('SSC (mg/L)', fontsize = 12)
                
                cbar = fig.colorbar(im, ax=ax[-1],orientation="vertical",location = 'right',fraction=0.046)
                cbar.set_label(f'CTD SSC (mg/L)', rotation=90,fontsize= 8)
            else:
                
                #t,turb = ctd.get_timeseries_data(field_name = 'Turbidity (NTU)')
                
                t = df.index
                turb = df['Turbidity (NTU)'].to_numpy()
                sc = ax[-1].scatter(t,turb,c= 'black', alpha = 0.9, s = 0.25, label = 'Turbidity (CTD)')
                ax[-1].plot(t,turb,c= 'black', alpha = 0.9,lw = 1, label = 'Turbidity (CTD)')
                ax[-1].set_ylabel('Turbidity (NTU)', fontsize = 8)
                ax[-1].set_ylim(0,1.1*np.nanmax(turb))
                
                ax[-1].yaxis.set_major_locator(AutoLocator())
                
                cbar = fig.colorbar(im, ax=ax[-1],orientation="vertical",location = 'right',fraction=0.046)
                cbar.set_label(f'CTD Turbidity (NTU)', rotation=90,fontsize= 8)
            #     ax[i].scatter(df.index,df.z,c =df['Turbidity (NTU)'], s = 15, edgecolor = None, cmap = cmap, marker = 'o', alpha = 0.9, label = 'Turbidity (CTD)')
            #ax[-1].xaxis.set_major_locator(AutoLocator())
                        
            locator = mdates.AutoDateLocator(minticks=3, maxticks=7)
            formatter = mdates.ConciseDateFormatter(locator)
            formatter.formats = ['%D',  # ticks are mostly years
                     '%b%y',       # ticks are mostly months
                     '%b%d',       # ticks are mostly days
                     '%H:%M',    # hrs
                     '%H:%M',    # min
                     '%S.%f', ]  # secs
            ax[-1].xaxis.set_major_locator(locator)
            ax[-1].xaxis.set_major_formatter(formatter)
            #ax[-1].xaxis.set_major_locator(mticker.FixedLocator(ax[-1].get_xticks()))
            #ax[-1].xaxis.set_major_formatter(mdates.DateFormatter('%H:%M %d%b%y '))
            ax[-1].grid(alpha = 0.1)
            #ax[-1].set_xticklabels(ax[-1].get_xticklabels(), rotation = 0, ha = 'center')
            ax[-1].xaxis.tick_bottom()
            ax[-1].xaxis.set_label_position('bottom') 

        
        return fig,ax  

        
    
    def four_beam_mesh_plot(self,**kwargs):#plot_by = 'bin',start_bin = None,end_bin = None,start_ensemble = None,end_ensemble = None,title = None):
        """
        Generate a flooded color plots of correlation magnitude
    
        Parameters
        ----------
        self._pd0 : object
            WorkhorseADCP object.
        plot_by : str
            y-axes plot method ('bin','depth').
        start_bin : int
            First bin to plot. (use zero based index)
        end_bin : int
            Last bin to plot.(use zero based index)
        start_ensemble : int
            First ensemble to plot.(use zero based index)
        end_ensemble : int
            Last ensemble to plot.(use zero based index)
        title : str
            plot axes title.
        field_name: str
            ensemble data type (string). "ECHO INTENSITY" (default), "CORRELATION MAGNITUDE", "PERCENT GOOD", others in ensemble_fields
    
        Returns
        -------
        fig,ax
            matplotlib figure and axes objects
    
        """
        
        # if self._pd0.ensemble_data[0]['COORDINATE SYSTEM'] != 'BEAM COORDINATES':
        #     print('Plot feature only implemented for BEAM coordinates')
    
        
        plot_by = kwargs.pop('plot_by','bin')  
        start_bin = kwargs.pop('start_bin',0)
        end_bin = kwargs.pop('end_bin',self._pd0.config.number_of_cells)    
        start_ensemble = kwargs.pop('start_ensemble',0)
        end_ensemble = kwargs.pop('end_ensemble',self._pd0.n_ensembles)       
        title = kwargs.pop('title',self._pd0.metadata.filepath.split(os.sep)[-1])    
        field_name = kwargs.pop('field_name','ECHO INTENSITY')
        ctd = kwargs.pop('ctd',None)
        
        extra_rows = kwargs.pop('extra_rows',0)
        
        nbins = (end_bin - start_bin)
        X  = self._pd0.get_ensemble_array(field_name = field_name)[:,start_bin:end_bin,start_ensemble:end_ensemble]
        
        x1 = X[0]
        x2 = X[1]
        x3 = X[2]
        x4 = X[3]
    
        #echo_intensity = self._pd0.get_ensemble_array(beam_number = 0, field_name = 'CORRELATION MAGNITUDE')[start_bin:end_bin,start_ensemble:end_ensemble]
        ensemble_times = self._pd0.get_ensemble_datetimes()[start_ensemble:end_ensemble]
        
        subplot_titles = []
        nrow = 4 #self._pd0.config.number_of_beams 
    
        fig,ax = subplots(nrow = nrow + extra_rows, ncol = 1, figheight = 8, figwidth = 10.5, width_ratios = [1], sharex = True, sharey = True)
    
        ## format the ADCP data axes (left)
        # topax = ax[0].twiny()
        # topax.set_xlim(start_ensemble,end_ensemble)
        # ax[0].set_zorder(4)
        #topax.set_xticks(np.arange())
        ax[0].set_title(field_name)
        
        fig.suptitle(title, fontsize = 16)
        
    
        # set plot params based on instrument configuration 
    
        def set_axes_labels(axs,ylabel):
            # function to set the ylabel on a list of axes objects 
            for ax in axs:
                ax.set_ylabel(ylabel)
                
            return axs
        
        # set plotting extents in vertical direction
        if plot_by == 'bin':
           # ylims = [start_bin,end_bin]
            set_axes_labels(ax,'Bin Dist. (m)')
            Z = self._pd0.geometry.get_relative_beam_midpoint_positions(mask = False)[2] # z mesh values
            
            z_platform =  (self._pd0.config.bin_1_distance/100) +np.zeros(self._pd0.geometry.get_corrected_bottom_track().shape)
            
            print(z_platform.min())
            ylims = [np.nanmin(Z),np.nanmax(Z)]
            
        elif plot_by == 'depth':
            #bin_depths = self._pd0.get_bin_midpoints_depth()
            #ylims = [bin_depths[start_bin],bin_depths[end_bin]]
            set_axes_labels(ax,'Depth (m)')
            Z = self._pd0.geometry.get_absolute_beam_midpoint_positions(mask = False)[2] # z mesh values
            
            z_platform = np.repeat(self._pd0.geometry.pose.pose['z'].to_numpy()[np.newaxis,:],repeats = self._pd0.config.number_of_beams,axis = 0)
            ylims = [np.nanmin(Z),np.nanmax(Z)]
            
            
            
        elif plot_by == 'HAB':
            #bin_heights = self._pd0.get_bin_midpoints_HAB()
            #ylims = [bin_heights[start_bin],bin_heights[end_bin]]
            set_axes_labels(ax,'HAB (m)')
            Z = self._pd0.geometry.get_absolute_beam_midpoint_positions_HAB(mask = False)[2] # z mesh values
            z_platform = -  self._pd0.geometry.get_corrected_bottom_track()
            
            ylims = [0,1.1*np.nanmax(z_platform[:,start_ensemble:end_ensemble])]
        else: 
            print('Invalid plot_by parameter')
          
        
        z_platform = z_platform[:,start_ensemble:end_ensemble]
        Z = Z[:,start_bin:end_bin,start_ensemble:end_ensemble]
    
        cmap = kwargs.pop('cmap',self._cmaps.pop(field_name,'turbo'))
        
        dataset = [x1,x2,x3,x4] # hold all elegible beam datasets 
        dataset = dataset[:self._pd0.config.number_of_beams] # just plot for valid beams
        
        for x in dataset:
            x[x == 32768] = np.nan
        if field_name == 'PERCENT GOOD':
            vmin = 0
            vmax = 100
            print('pg')
        elif field_name == 'SIGNAL TO NOISE RATIO':
            vmin = np.nanmin(dataset)
            vmax = 50
            print('stn')
        elif field_name == 'ABSOLUTE BACKSCATTER':
            vmin = -95
            vmax = -45
        elif field_name == 'NTU':
            vmin = np.nanmin(dataset)
            vmax = np.nanmax(dataset)
        else:
            vmin = np.nanmin(dataset)
            vmax = np.nanmax(dataset)
        
        ## overwrite with kwargs if provided 
        vmin = kwargs.pop('vmin',vmin) 
        vmax = kwargs.pop('vmax',vmax) 
        
        
        for i,x in enumerate([x1,x2,x3,x4]):
        #     xi,extent = get_plot_extent(x)
        #     if self._pd0.config.beam_facing == 'UP': 
        #         origin = 'lower'
        #     else: origin = 'upper'
            
            #im = ax[i].matshow(x, origin = origin, extent = extent, cmap = cmap, aspect = 'auto', resample = False, vmin = vmin, vmax = vmax)
            
            
            
            #T = np.repeat(self._pd0.get_ensemble_datetimes(),self._pd0.config.number_of_cells).reshape((len(self._pd0.get_ensemble_datetimes()),self._pd0.config.number_of_cells)).T
            T = np.repeat(ensemble_times,self._pd0.config.number_of_cells).reshape((len(ensemble_times),self._pd0.config.number_of_cells)).T[start_bin:end_bin]#,start_ensemble:end_ensemble]
            #Z = X_hab[2,beam_no]
            #print(Z[i].shape,T.shape,x.shape,z_platform[i].shape)
            im = ax[i].pcolor(T,Z[i],x, vmin = vmin, vmax = vmax, cmap = cmap)#,antialiaseds = True)
            
            
            ax[i].plot(ensemble_times,z_platform[i], label = 'ROV (z)', lw = 1, alpha = 0.7)
    
            
            #axp.set_ylabel('Turbidity')
        
        for i,axes in enumerate(ax[:self._pd0.config.number_of_beams]):# modify subplot apperance 
            # set colorbar 
            
            
            #if i==(len(ax)-1) and ctd: break # dont plot a colorbar if 
        
            
            cbar = fig.colorbar(im, ax=axes,orientation="vertical",location = 'right',fraction=0.046, extend = 'max')
            cbar.set_label(f'Beam {i+1}', rotation=90,fontsize= 10)
            axes.grid(alpha = 0.1)
            axes.xaxis.tick_bottom()
            axes.xaxis.set_label_position('bottom') 
            axes.set_ylim(ylims)
            
            
            
        ax[-1].set_xlabel('Time')
    
       
        if ctd:
            for i,axes in enumerate(ax[:self._pd0.config.number_of_beams]):
                t,turb = ctd.get_timeseries_data(field_name = 'Turbidity (NTU)')
                

                
                df = ctd.to_pandas_df()
                df = df.reindex(ensemble_times, method = 'nearest')
                df['z'] = z_platform[i]+0.25
                #df = df.resample('1s').mean()
                
                if field_name == 'NTU':
                    axes.scatter(df.index,df.z,c =df['Turbidity (NTU)'], vmin = vmin,vmax = vmax, s = 10, edgecolor = None, cmap = cmap, marker = 's' , alpha = 0.9)#, label = 'Turbidity (CTD)')
                    #axp.set_ylabel('Turbidity (NTU)', fontsize = 7)
                elif field_name == 'SSC':
                    axes.scatter(df.index,df.z,c =df['SSC (mg/L)'], vmin = vmin,vmax = vmax, s = 10, edgecolor = None, cmap = cmap, marker = 's' , alpha = 0.9)#, label = 'SSC (CTD)')
                   # axp.set_ylabel('SSC (mg/L)', fontsize = 7)
                else:
                    axp = ax[i].twinx()
                    axp.plot(t,turb, lw = 0.25, c = 'black', alpha = 0.6)
                    axp.set_zorder(4)
                    axp.set_ylabel('Turbidity (NTU)', fontsize = 7)
                    
                    
                    
                # else:
                #     ax[i].scatter(df.index,df.z,c =df['Turbidity (NTU)'], s = 15, edgecolor = None, cmap = cmap, marker = 'o', alpha = 0.9, label = 'Turbidity (CTD)')
                    
        for i,axes in enumerate(ax):
            axes.legend(fontsize = 7)
            
        if extra_rows>0:    
            for axes in ax[-1:]  :
                cbar = fig.colorbar(im, ax=axes,orientation="vertical",location = 'right',fraction=0.046, extend = 'max')
                #cbar.set_label( rotation=90,fontsize= 8)
                axes.grid(alpha = 0.1)
                axes.xaxis.tick_bottom()
                axes.xaxis.set_label_position('bottom') 
                axes.set_ylim(ylims)
            
        # unlink the axisd
        # if extra_rows>0:
        #     for i in range(1,extra_rows+1):
        #         axes.get_shared_y_axes().remove(ax[-i])
        #         ax[-i].get_shared_y_axes().remove(axes)
        
        return fig,ax   
         
    def single_beam_flood_plot(self,**kwargs):#plot_by = 'bin',start_bin = None,end_bin = None,start_ensemble = None,end_ensemble = None,title = None):
        """
        Generate a fencegate plot of ensemble data
        
        Parameters
        ----------
        self._pd0 : object
            WorkhorseADCP object.
        plot_by : str
            y-axes plot method ('bin','depth').
        start_bin : int
            First bin to plot. (use zero based index)
        end_bin : int
            Last bin to plot.(use zero based index)
        start_ensemble : int
            First ensemble to plot.(use zero based index)
        end_ensemble : int
            Last ensemble to plot.(use zero based index)
        title : str
            plot axes title.
        field_name: str
            ensemble data type (string). "ECHO INTENSITY" (default), "CORRELATION MAGNITUDE", "PERCENT GOOD", others in ensemble_fields
        beam : int or str. 
            beam number to plot. if 0 or 'average', the beam average is returned. If none, the beam average is returned. 
        
        Returns
        -------
        fig,ax
            matplotlib figure and axes objects
        
        """
        
        plot_by = kwargs.pop('plot_by','bin')  
        start_bin = kwargs.pop('start_bin',0)
        end_bin = kwargs.pop('end_bin',self._pd0.config.number_of_cells)    
        start_ensemble = kwargs.pop('start_ensemble',0)
        end_ensemble = kwargs.pop('end_ensemble',self._pd0.n_ensembles)       
        title = kwargs.pop('title',self._pd0.metadata.filepath.split(os.sep)[-1])    
        field_name = kwargs.pop('field_name','ECHO INTENSITY')
        beam = kwargs.pop('beam',0)
        if beam == 'average': beam = 0 
        
        
        nbins = (end_bin - start_bin)
        x = self._pd0.get_ensemble_array(field_name = field_name)[start_bin:end_bin,start_ensemble:end_ensemble]
        
        if beam == 0:
            x = np.nanmean(x,axis = 0)
        else:
            x = x[beam-1,:,:]
        
        #echo_intensity = self._pd0.get_ensemble_array(beam_number = 0, field_name = 'CORRELATION MAGNITUDE')[start_bin:end_bin,start_ensemble:end_ensemble]
        ensemble_times = self._pd0.get_ensemble_datetimes()[start_ensemble:end_ensemble]
        
        
        subplot_titles = []
        fig,ax = subplots( figheight = 2.5, figwidth = 10.5, width_ratios = [1])
        
        
        ## format the ADCP data axes (left)
        topax = ax.twiny()
        ax.set_title(title)
        
        
        # set plotting extents in vertical direction
        if plot_by == 'bin':
            ylims = [start_bin,end_bin]
            ax.set_ylabel('Bin')
        elif plot_by == 'depth':
            bin_depths = self._pd0.get_bin_midpoints_depth()
            ylims = [bin_depths[start_bin],bin_depths[end_bin]]
            ax.set_ylabel('Depth')
        elif plot_by == 'HAB':
            bin_heights = self._pd0.get_bin_midpoints_HAB()
            ylims = [bin_heights[start_bin],bin_heights[end_bin]]
            ax.set_ylabel('Height Above Bed')
        else: 
            print('Invalid plot_by parameter')
        
        
        # set plotting extents in horizontal direction
        xlims = mdates.date2num(ensemble_times) # list of elegible xlimits 
        if self._pd0.config.beam_facing == 'UP':
            extent = [xlims[0],xlims[-1],ylims[0],ylims[1]]
        else:
            x = np.flipud(x)
            extent = [xlims[0],xlims[-1],ylims[1],ylims[0]]
         
        cmap = self._cmaps[field_name]
        
        
        
        im = ax.matshow(x, origin = 'lower', extent = extent, cmap = cmap, aspect = 'auto',resample = False )
        cbar = fig.colorbar(im, ax=ax,orientation="vertical",location = 'right',fraction=0.046)
        
        if beam == 0:
            cbar_label = f'{field_name}\n BEAM AVERAGE' 
        else:
            cbar_label = f'{field_name}\n BEAM {beam}' 
        cbar.set_label(cbar_label, rotation=90,fontsize= 9)
        
        
        ax.xaxis.set_major_locator(mticker.FixedLocator(ax.get_xticks()))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M %d%b%y '))
        topax.set_xlim(start_ensemble,end_ensemble)
        ax.set_xlabel('Ensemble')
        ax.grid(alpha = 0.1)
        ax.set_xticklabels(ax.get_xticklabels(), rotation = 0, ha = 'left')
        
        return fig,ax
    #%%
    
    def four_beam_histogram(self,**kwargs):
        """
        Generate a histofram for ensemble data for all beams 
    
        Parameters
        ----------
        self._pd0 : object
            WorkhorseADCP object.
        start_bin : int
            First bin to plot. (use zero based index)
        end_bin : int
            Last bin to plot.(use zero based index)
        start_ensemble : int
            First ensemble to plot.(use zero based index)
        end_ensemble : int
            Last ensemble to plot.(use zero based index)
        title : str
            plot axes title.
        field_name: str
            ensemble data type (string). "ECHO INTENSITY" (default), "CORRELATION MAGNITUDE", "PERCENT GOOD", others in ensemble_fields
    
        Returns
        -------
        fig,ax
            matplotlib figure and axes objects
    
        """
        
        # if self._pd0.ensemble_data[0]['COORDINATE SYSTEM'] != 'BEAM COORDINATES':
        #     print('Plot feature only implemented for BEAM coordinates')
    
    
        plot_by = kwargs.pop('plot_by','bin')  
        start_bin = kwargs.pop('start_bin',0)
        end_bin = kwargs.pop('end_bin',self._pd0.config.number_of_cells)    
        start_ensemble = kwargs.pop('start_ensemble',0)
        end_ensemble = kwargs.pop('end_ensemble',self._pd0.n_ensembles)       
        title = kwargs.pop('title',self._pd0.metadata.filepath.split(os.sep)[-1])    
        field_name = kwargs.pop('field_name','ECHO INTENSITY')

        
        nbins = (end_bin - start_bin)
        
        X  = self._pd0.get_ensemble_array(field_name = field_name)[:,start_bin:end_bin,start_ensemble:end_ensemble]
        # four beam histogram 

        
        fig,ax = subplots(xlabel = field_name, figwidth = 7, figheight = 4)
        
        
        colors = [dhi_colors.blue1,
                 'black',
                 dhi_colors.red1,
                 dhi_colors.yellow1,]
        
        
        
        for b in range(self._pd0.config.number_of_beams):
            x = X[b].flatten()
            sns.kdeplot(data = x, ax = ax, color = colors[b%4], label = f'beam {b+1}', alpha = 1)
        ax.legend()    
        ax.set_ylabel('Density')
        
        ax.set_title(title)
    #%%
    def progressive_vector_plot(self,**kwargs):
        """
        
    
        Generate a progressive vector plot from the WorkhorseADCP class object 
    
        Parameters
        ----------
        self : object
            WorkhorseADCP object.
        color_by : str
            Coloring method ('bin','velocity','month').
        start_bin : int
            First bin to plot. (use zero based index)
        end_bin : int
            Last bin to plot.(use zero based index)
        start_ensemble : int
            First ensemble to plot.(use zero based index)
        end_ensemble : int
            Last ensemble to plot.(use zero based index)
        title : str
            plot axes title.
        ax : object,optional 
            axes object to plot to
    
        Returns
        -------
        fig,ax
            matplotlib figure and axes objects
    
        """
        
    
    
        if kwargs.get('color_by'):color_by = kwargs.get('color_by')
        else: color_by = 'bin'
        
        if kwargs.get('start_bin'): start_bin = kwargs.get('start_bin')
        else: start_bin = 0
        
        if kwargs.get('end_bin'): end_bin = kwargs.get('end_bin')
        else: end_bin = self._pd0.config.number_of_cells-1
        
        if kwargs.get('start_ensemble'): start_ensemble = kwargs.get('start_ensemble')
        else: start_ensemble = 0
        
        if kwargs.get('end_ensemble'): end_ensemble= kwargs.get('end_ensemble')
        else: end_ensemble = self._pd0.n_ensembles   
        
        if kwargs.get('title'): title = kwargs.get('title')
        else: title = self._pd0.metadata.filepath.split(os.sep)[-1]     
        
        
      
    
    
        
        #self = self[ID]
        # start_ensemble = 0
        # end_ensemble = self._pd0.n_ensembles
        # start_bin = 0
        # end_bin = self._pd0.config.number_of_cells-1
        #color_by = 'bin' #velocity'  #bin'#'velocity'#'bin'
        
        
        plot = True
        nbins = (end_bin - start_bin)+1
    
        
        
        
        
        u,v,z,du,dv,dz,errv = self._pd0.get_velocity()
        ensemble_times = self._pd0.get_ensemble_datetimes()[start_ensemble:end_ensemble]
        
        # transpose and cut off data
        u = u[start_ensemble:end_ensemble,start_bin:end_bin+1]
        v = v[start_ensemble:end_ensemble,start_bin:end_bin+1]
        z = z[start_ensemble:end_ensemble,start_bin:end_bin+1]
        du = du[start_ensemble:end_ensemble,start_bin:end_bin+1]
        dv = dv[start_ensemble:end_ensemble,start_bin:end_bin+1]
        dz = dz[start_ensemble:end_ensemble,start_bin:end_bin+1]
        
        xy_speed = np.sqrt(u**2 + v**2)
        
        pu = np.nancumsum(du,axis = 0) #,-np.outer(du[0,:],np.ones(self.n_ensembles)).T])
        pv = np.nancumsum(dv,axis = 0) # ,-np.outer(dv[0,:],np.ones(self.n_ensembles)).T])
        pz = np.nancumsum(dz,axis = 0) # ,-np.outer(dz[0,:],np.ones(self.n_ensembles)).T])
        
        
        if plot:
            # fig = plt.figure()
            # ax = plt.gca()
            #fig, ax = plt.subplots(1, 2,gridspec_kw={'width_ratios': [3, 1]})

            fig,ax = subplots( figheight = 5, figwidth =5.5, width_ratios = [1])
     
            #ax.set_aspect('equal')
            ax.grid(alpha = 0.3)
            ax.set_xlabel('East Distance (m)')
            ax.set_ylabel('North Distance (m)')
            ax.set_title(title)
            #ax.set_aspect('equal',adjustable = 'datalim')
            
    
            cbar_shrink = .046#.75
          
            
            if color_by == 'bin':
    
                cmap = plt.cm.Spectral  # define the colormap
                # extract all colors from the .jet map
                cmaplist = [cmap(i) for i in range(cmap.N)]
                # force the first color entry to be grey
                cmaplist[0] = (.5, .5, .5, 1.0)
                
                # create the new map
                cmap = mpl.colors.LinearSegmentedColormap.from_list(
                    'Custom cmap', cmaplist, cmap.N)
                
                # define the bins and normalize
                bounds = np.linspace(start_bin, start_bin + nbins, nbins+1)
                norm = mpl.colors.BoundaryNorm(bounds, cmap.N)
                for b in range(nbins):
                    #ax.plot(pu[:,b],pv[:,b], label = f'Bin {start_bin+b}')#, c = cmap(b), norm = norm)#,color = colors[s],alpha = 0.6)
        
                    points = np.array((pu[:-1,b], pv[:-1,b])).T.reshape(-1, 1, 2)
                    segments = np.concatenate([points[:-1], points[1:]], axis=1)
                    #norm = plt.Normalize(0, self._pd0.config.number_of_cells,1)
                    lines = LineCollection(segments, cmap=cmap, norm=norm)
                    lines.set_array(len(points)*[b+start_bin])
                    lines.set_linewidth(1)
                    line = ax.add_collection(lines)           
                cbar = fig.colorbar(line, ax=ax,orientation="vertical")
                cbar.set_label('Bin Number', rotation=270, labelpad = 10, fontsize = 12)
        
        
            elif color_by == 'velocity':
                cmap = plt.cm.jet
                for b in range(nbins):
                    points = np.array((pu[:-1,b], pv[1:,b])).T.reshape(-1, 1, 2)
                    segments = np.concatenate([points[:-1], points[1:]], axis=1)
                    norm = plt.Normalize(0, np.quantile(xy_speed[~np.isnan(xy_speed)],0.99))
                    lines = LineCollection(segments, cmap=cmap, norm=norm)
                    lines.set_array(xy_speed[:,b])
                    lines.set_linewidth(1)
                    line = ax.add_collection(lines)
                    #break
                cbar = fig.colorbar(line, ax=ax,orientation="vertical")
                cbar.set_label('Velocity (m/s) ', rotation=270, labelpad = 10, fontsize = 12)
                
            elif color_by == 'month':
                cmap = plt.cm.get_cmap('tab20b', 12)
                def gen_interval(x):
                    x = x.isoweekday()
                    return x
                vgen_interval = np.vectorize(gen_interval)
                months = [i.month for i in ensemble_times]
                for b in range(nbins):
                    points = np.array((pu[:-1,b], pv[1:,b])).T.reshape(-1, 1, 2)
                    segments = np.concatenate([points[:-1], points[1:]], axis=1)
                    norm = plt.Normalize(1,12)
                    lines = LineCollection(segments, cmap=cmap, norm=norm)
                    lines.set_array(months)
                    lines.set_linewidth(1)
                    line = ax.add_collection(lines)
                    #break
                cbar = fig.colorbar(line, ax=ax,orientation="vertical")
                cbar.set_label('Month of Year', rotation=270, labelpad = 10, fontsize = 12)        
                
                
            else:
                print(r'Invalid plot mode {color_by}')
        
            #set axes limits 
            xrange = 1.1*(np.nanmax(abs(pu)))
            yrange = 1.1*(np.nanmax(abs(pv)))
            
            rng = max(xrange,yrange)
            #print([np.nanmax(pu),xrange])
            # ax.set_xbound([-xrange,xrange])
            # ax.set_ybound([-yrange,yrange])
            
            ax.set_xlim(-rng,rng)
            ax.set_ylim(-rng,rng)
        
            ax.set_aspect('equal')
    
        return fig,ax
    
    def velocity_flood_plot(self,**kwargs):#plot_by = 'bin',start_bin = None,end_bin = None,start_ensemble = None,end_ensemble = None,title = None):
        """
        Generate a fencegate plot of velocity components
    
        Parameters
        ----------
        self : object
            WorkhorseADCP object.
        plot_by : str
            y-axes plot method ('bin','depth').
        start_bin : int
            First bin to plot. (use zero based index)
        end_bin : int
            Last bin to plot.(use zero based index)
        start_ensemble : int
            First ensemble to plot.(use zero based index)
        end_ensemble : int
            Last ensemble to plot.(use zero based index)
        title : str
            plot axes title.
    
        Returns
        -------
        fig,ax
            matplotlib figure and axes objects
    
        """
    
    
        if kwargs.get('plot_by'):plot_by = kwargs.get('plot_by')
        else: plot_by = 'bin'
        
        if kwargs.get('start_bin'): start_bin = kwargs.get('start_bin')
        else: start_bin = 0
        
        if kwargs.get('end_bin'): end_bin = kwargs.get('end_bin')
        else: end_bin = self._pd0.config.number_of_cells
        
    
        if kwargs.get('start_ensemble'): start_ensemble = kwargs.get('start_ensemble')
        else: start_ensemble = 0
        
        if kwargs.get('end_ensemble'): end_ensemble = kwargs.get('end_ensemble')
        else: end_ensemble = self._pd0.n_ensembles   
        
        if kwargs.get('title'): title = kwargs.get('title')
        else: title = self._pd0.metadata.filepath.split(os.sep)[-1]
        
        
        nbins = (end_bin - start_bin)
        u,v,z,du,dv,dz,errv = self._pd0.get_velocity()
        
        
        x1 = u.T[start_bin:end_bin,start_ensemble:end_ensemble]
        x2 = v.T[start_bin:end_bin,start_ensemble:end_ensemble]
        x3 = z.T[start_bin:end_bin,start_ensemble:end_ensemble]
        x4 = np.sqrt(x1**2 + x2**2 + x3**2)
        x5 = errv.T[start_bin:end_bin,start_ensemble:end_ensemble]
        
        
        
    
        #echo_intensity = self._pd0.get_ensemble_array(beam_number = 0, field_name = 'CORRELATION MAGNITUDE')[start_bin:end_bin,start_ensemble:end_ensemble]
        ensemble_times = self._pd0.get_ensemble_datetimes()[start_ensemble:end_ensemble]
        
    
        subplot_titles = []
        fig,ax = subplots(nrow = 5, ncol = 1, figheight = 8, figwidth = 10.5, width_ratios = [1], sharex = True, sharey = True)
        
    
        ## format the ADCP data axes (left)
        topax = ax[0].twiny()
        topax.set_xlim(start_ensemble,end_ensemble)
        ax[0].set_title('Velocity')
        ax[0].set_zorder(4)
        fig.suptitle(title, fontsize = 16)
        
    
        # set plot params based on instrument configuration 
    
        def set_axes_labels(axs,ylabel):
            # function to set the ylabel on a list of axes objects 
            for ax in axs:
                ax.set_ylabel(ylabel)
                
            return axs
                
        
        
        # set plotting extents in vertical direction
        if plot_by == 'bin':
            ylims = [start_bin,end_bin]
            set_axes_labels(ax,'Bin')
        elif plot_by == 'depth':
            bin_depths = self._pd0.get_bin_midpoints_depth()
            ylims = [bin_depths[start_bin],bin_depths[end_bin]]
            set_axes_labels(ax,'Depth')
        elif plot_by == 'HAB':
            bin_heights = self._pd0.get_bin_midpoints_HAB()
            ylims = [bin_heights[start_bin],bin_heights[end_bin]]
            set_axes_labels(ax,'Height Above Bed')
    
        else: 
            print('Invalid plot_by parameter')
            
            
            
        
        
        def get_plot_extent(X):
            """
            
    
            Parameters
            ----------
            X : numpy array
                Input array (ensemble data).
    
            Returns
            -------
            X : numpy array
                Possibly rotated input array (ensemble data) - to match the sensor orientation.
                
            extent : list
                bounding box for the plotted image.
    
            """
       
        
            # set plotting extents in horizontal direction
            xlims = mdates.date2num(ensemble_times) # list of elegible xlimits 
            if self._pd0.config.beam_facing == 'UP':
                extent = [xlims[0],xlims[-1],ylims[0],ylims[1]]
            else:
                X = np.flipud(X)
                extent = [xlims[0],xlims[-1],ylims[1],ylims[0]]
            return X,extent
            
        
    
        cmap = 'jet'#cmocean.cm.speed
        
        
        for x in [x1,x2,x3,x4,x5]:
            x[x == 32768] = np.nan
        
        
        
    
        # vmin = np.nanmin([x1,x2,x3,x4])
        # vmax = np.nanmax([x1,x2,x3,x4])
        

        
        x1,extent = get_plot_extent(x1)
        im = ax[0].matshow(x1, origin = 'lower', extent = extent, cmap = cmap, aspect = 'auto', resample = False, vmin = np.nanmin(x1), vmax = np.nanmax(x1))
        cbar = fig.colorbar(im, ax=ax[0],orientation="vertical",location = 'right',fraction=0.046)
        cbar.set_label(f'u', rotation=90,fontsize= 8)
        
        x2,extent = get_plot_extent(x2)
        im = ax[1].matshow(x2, origin = 'lower', extent = extent, cmap = cmap, aspect = 'auto', resample = False, vmin = np.nanmin(x2), vmax = np.nanmax(x2))
        cbar = fig.colorbar(im, ax=ax[1],orientation="vertical",location = 'right',fraction=0.046)
        cbar.set_label(f'v', rotation=90,fontsize= 8)
        
        x3,extent = get_plot_extent(x3)
        im = ax[2].matshow(x3, origin = 'lower', extent = extent, cmap = cmap, aspect = 'auto', resample = False, vmin = np.nanmin(x3), vmax = np.nanmax(x3))
        cbar = fig.colorbar(im, ax=ax[2],orientation="vertical",location = 'right',fraction=0.046)
        cbar.set_label(f'z', rotation=90,fontsize= 8)
        
        x4,extent = get_plot_extent(x4)
        im = ax[3].matshow(x4, origin = 'lower', extent = extent, cmap = cmap, aspect = 'auto', resample = False, vmin = np.nanmin(x4), vmax = np.nanmax(x4))
        cbar = fig.colorbar(im, ax=ax[3],orientation="vertical",location = 'right',fraction=0.046)
        cbar.set_label(f'speed', rotation=90,fontsize= 8)
        
        x5,extent = get_plot_extent(x5)
        im = ax[4].matshow(x5, origin = 'lower', extent = extent, cmap = cmap, aspect = 'auto', resample = False, vmin = np.nanmin(x5), vmax = np.nanmax(x5))
        cbar = fig.colorbar(im, ax=ax[4],orientation="vertical",location = 'right',fraction=0.046)
        cbar.set_label(f'errv', rotation=90,fontsize= 8)    
        
        for i,axes in enumerate(ax):# modify subplot apperance 
            # set colorbar 
            # cbar = fig.colorbar(im, ax=axes,orientation="vertical",location = 'right',fraction=0.046)
            # cbar.set_label(f'Beam {i+1}', rotation=90,fontsize= 8)
            
            axes.xaxis.set_major_locator(mticker.FixedLocator(axes.get_xticks()))
            axes.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M %d%b%y '))
            axes.grid(alpha = 0.1)
            axes.set_xticklabels(axes.get_xticklabels(), rotation = 0, ha = 'center')
            axes.xaxis.tick_bottom()
            axes.xaxis.set_label_position('bottom') 
            #axes.text(.5,.5,f'PG{i+1}',transform = ax. transAxes)
            #axes.text(0.5, 0.5, 'matplotlib')#, horizontalalignment='center',verticalalignment='center', transform=ax.transAxes)
            #path_effects=[mpl_path_effects.Stroke(linewidth=.25, foreground="black",alpha = .75)] 
            #axes.text(.025,.8,f'Percent Good {i}',transform = axes.transAxes, fontsize = 8, color = 'white',path_effects = path_effects)
        ax[-1].set_xlabel('Ensemble')
            
        return fig,ax

        
        
    def active_mask_flood_plot(self,**kwargs):#plot_by = 'bin',start_bin = None,end_bin = None,start_ensemble = None,end_ensemble = None,title = None):
        """
        Generate a fencegate plot of velocity components
    
        Parameters
        ----------
        self : object
            WorkhorseADCP object.
        plot_by : str
            y-axes plot method ('bin','depth').
        start_bin : int
            First bin to plot. (use zero based index)
        end_bin : int
            Last bin to plot.(use zero based index)
        start_ensemble : int
            First ensemble to plot.(use zero based index)
        end_ensemble : int
            Last ensemble to plot.(use zero based index)
        title : str
            plot axes title.
    
        Returns
        -------
        fig,ax
            matplotlib figure and axes objects
    
        """
    
    
        if kwargs.get('plot_by'):plot_by = kwargs.get('plot_by')
        else: plot_by = 'bin'
        
        if kwargs.get('start_bin'): start_bin = kwargs.get('start_bin')
        else: start_bin = 0
        
        if kwargs.get('end_bin'): end_bin = kwargs.get('end_bin')
        else: end_bin = self._pd0.config.number_of_cells
        
    
        if kwargs.get('start_ensemble'): start_ensemble = kwargs.get('start_ensemble')
        else: start_ensemble = 0
        
        if kwargs.get('end_ensemble'): end_ensemble = kwargs.get('end_ensemble')
        else: end_ensemble = self._pd0.n_ensembles   
        
        if kwargs.get('title'): title = kwargs.get('title')
        else: title = self._pd0.metadata.filepath.split(os.sep)[-1]
        
        
        nbins = (end_bin - start_bin)
        #u,v,z,du,dv,dz,errv = self._pd0.get_velocity()
        
        
        # global x1,x2,x3,x4
        # x1 = u.T[start_bin:end_bin,start_ensemble:end_ensemble]
        # x2 = v.T[start_bin:end_bin,start_ensemble:end_ensemble]
        # x3 = z.T[start_bin:end_bin,start_ensemble:end_ensemble]
        # x4 = np.sqrt(u**2 + v**2 + z**2).T[start_bin:end_bin,start_ensemble:end_ensemble]
        # x5 = errv.T[start_bin:end_bin,start_ensemble:end_ensemble]
        
        
       
        x = []
        n_active_masks = 0
        active_mask_names = []
        for mask_name in self._pd0.mask.masks.keys():
            if self._pd0.mask.mask_status[mask_name]:
                x.append(self._pd0.mask.masks[mask_name])
                n_active_masks+=1
                active_mask_names.append(mask_name)
        active_mask_names.append('Combined')
    
                
                
            
        
            
            
    
        #echo_intensity = self._pd0.get_ensemble_array(beam_number = 0, field_name = 'CORRELATION MAGNITUDE')[start_bin:end_bin,start_ensemble:end_ensemble]
        ensemble_times = self._pd0.get_ensemble_datetimes()[start_ensemble:end_ensemble]
        
    
        subplot_titles = []
        fig,ax = subplots(nrow = n_active_masks+1, ncol = 1, figheight = 8, figwidth = 10.5, width_ratios = [1])
        
    
        topax = ax[0].twiny()
        topax.set_xlim(start_ensemble,end_ensemble)
        ax[0].set_title('Active Masks')
        fig.suptitle(title, fontsize = 16)
        
    
        # set plot params based on instrument configuration 
    
        def set_axes_labels(axs,ylabel):
            # function to set the ylabel on a list of axes objects 
            for ax in axs:
                ax.set_ylabel(ylabel)
                
            return axs
                
        
        
        # set plotting extents in vertical direction
        if plot_by == 'bin':
            ylims = [start_bin,end_bin]
            set_axes_labels(ax,'Bin')
        elif plot_by == 'depth':
            bin_depths = self._pd0.get_bin_midpoints_depth()
            ylims = [bin_depths[start_bin],bin_depths[end_bin]]
            set_axes_labels(ax,'Depth')
        elif plot_by == 'HAB':
            bin_heights = self._pd0.get_bin_midpoints_HAB()
            ylims = [bin_heights[start_bin],bin_heights[end_bin]]
            set_axes_labels(ax,'Height Above Bed')
    
        else: 
            print('Invalid plot_by parameter')
            
            
            
        
        
        def get_plot_extent(X):
            """
            
    
            Parameters
            ----------
            X : numpy array
                Input array (ensemble data).
    
            Returns
            -------
            X : numpy array
                Possibly rotated input array (ensemble data) - to match the sensor orientation.
                
            extent : list
                bounding box for the plotted image.
    
            """
       
        
            # set plotting extents in horizontal direction
            xlims = mdates.date2num(ensemble_times) # list of elegible xlimits 
            if self._pd0.config.beam_facing == 'UP':
                extent = [xlims[0],xlims[-1],ylims[0],ylims[1]]
            else:
                X = np.flipud(X)
                extent = [xlims[0],xlims[-1],ylims[1],ylims[0]]
            return X,extent
            
        
    
        cmap = 'Greys'#cmocean.cm.speed
        
        
        # for x in [x1,x2,x3,x4,x5]:
        #     x[x == 32768] = np.nan
        
        
        
    
        vmin = 0#np.nanmin([x1,x2,x3,x4])
        vmax = 1#np.nanmax([x1,x2,x3,x4])
        

        combined_mask = np.full(np.shape(x[0]),1.0)
        for i,mask in enumerate(x):
            mask,extent = get_plot_extent(mask[0])
            im = ax[i].matshow(mask, origin = 'lower', extent = extent, cmap = cmap, aspect = 'auto', resample = False, vmin = vmin, vmax = vmax)
            np.putmask(combined_mask,~mask, values = np.nan)
        
        im = ax[-1].matshow(combined_mask, origin = 'lower', extent = extent, cmap = cmap, aspect = 'auto', resample = False, vmin = vmin, vmax = vmax)
        
    
        for i,axes in enumerate(ax):# modify subplot apperance 
            # set colorbar 
            cbar = fig.colorbar(im, ax=axes,orientation="vertical",location = 'right',fraction=0.046)
            cbar.set_label(f'{active_mask_names[i]}', rotation=90,fontsize= 12)
            
            
            locator = mpl.dates.AutoDateLocator()
            axes.xaxis.set_major_locator(locator)
            axes.xaxis.set_major_formatter( mpl.dates.AutoDateFormatter(locator) )  
            #axes.xaxis.set_major_locator(mticker.FixedLocator(axes.get_xticks()))
            axes.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M %d%b%y '))
            axes.grid(alpha = 0.1)
            axes.set_xticklabels(axes.get_xticklabels(), rotation = 0, ha = 'center')
            axes.xaxis.tick_bottom()
            axes.xaxis.set_label_position('bottom') 
    
        ax[-1].set_xlabel('Ensemble')
            
        return fig,ax    
        
        
        
