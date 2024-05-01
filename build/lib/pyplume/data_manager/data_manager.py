# -*- coding: utf-8 -*-
"""
Created on Mon Jul 31 11:27:01 2023

@author: anba
"""

from rich import print

import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
import pandas as pd
import warnings
import os
import sys
import time 
import psutil


from rich.console import Console
from rich.text import Text
from rich.style import Style
from rich.theme import Theme


import time


from ..ptools import ptools
from ..plotting.matplotlib_shell import subplots, dhi_colors




from ..pd0.pd0_decoder import DataSet as DataSet_pd0,PT3,Pd0
from ..ctd.seabird_hex_decoder import seabird_ctd, DataSet as DataSet_ctd


np.seterr(divide='ignore', invalid='ignore')

import dill

#%%



class manager_base:
    def __init__(self,parser_name,name,fpaths,min_fsize = 0):
        """
        Parameters
        ----------
        parser_name : str
            parser to use. 'adcp', 'ctd', etc...
        name : str
            name of the dataset.
        fpaths : list
            list of filepaths [f1,f2,f3], or list of tuples containing all 
            filepaths needed for the parser [(f1a,f1b,..),(f2a,f2b,..),...]. 
            In general the main data file should be first.
            
        min_fsize : int, optional
            minimum filesize (in kb) to accept. Files smaller than this will be
            rejected. The default is 0.

        Returns
        -------
        None.

        """
 
        self.name = name # name of the dataset
        self.type = parser_name # name of the parser to use 
        self._filepaths_in = fpaths # list of all input filepaths 
        self._min_fsize = min_fsize # minimum filesize to load 
        
        
        ## check for duplicate input files 
        
        
        # theme = Theme({'screening file': 'gold3 italic',
        #                'loading_file': 'dark_cyan',
        #                'notification': 'yellow'})
        # self.console = Console(tab_size=4,
        #                        log_path = False,
        #                        theme = theme) # create a rich-text console 
        self.create_console()

        self._reason_failed = [] # reason why files could not be imported
        self._filepaths_failed = [] # full path to all files that were unsuccessfully imported
        self.filepaths = [] # full path to all files that were successfully imported
        self.file_start_times = []# start times for all files in the dataset
        self.file_end_times = [] # end times for all files in the dataset
        self.n_files = 0 # number of files in the dataset
        self.dataset_size = 0 # size of the entire data set (in kb)
        self.data = [] # data currently being held in memory 
        self.labels = []
        
        
        ## set parser type 
        if self.type == 'pd0':
            self._parser = self.__pd0_parser
            
        elif self.type == 'ctd':
            self._parser = self.__ctd_parser
            
        # elif self.type == 'pose':
        #     self._parser = self.__pose_parser

        else:
            raise Warning('Unsupported data type')
            
        
        

                

        
        
        
        ### operations ###

        with self.console.status(f'[gold3]screening {self.type} files', spinner_style = 'white') as status:
            
            
            ## check for duplicate files
            status.start()
            status.update(f'[yellow] checking for duplicate files', spinner_style = 'white')
            self.screen_duplicate_files(fpaths)
            
            if self._duplicates_removed>0:
                self.console.log(f'[yellow]({self.name}) {self._duplicates_removed} duplicate files removed', style = 'notification')
                time.sleep(0.25)
            
            
            ## screen elegible input files
            
            status.update(f'[yellow]screening {len(self._filepaths_in)} {self.type} files', spinner_style = 'white')
            self.__screen_files()
            status.stop()
            status.update(f'', spinner_style = 'white')
            self.console.log(f'[light_green]({self.name}) {self.n_files} {self.type} files available for import [yellow]({len(self._filepaths_failed)} rejected)', style = 'notification')
            time.sleep(.25)
        #self.console.log(f'')
            
            
        self.data_active = self.n_files*[False] # list of indicators for whether a file has been pulled into memory
        self.data = self.n_files*[None]
        #self.labels = [f'file{i}'for i in range(self.n_files)] # label for imported files (search handle)
     
        
    def create_console(self):
        theme = Theme({'screening file': 'gold3 italic',
                       'loading_file': 'dark_cyan',
                       'notification': 'yellow'})
        self.console = Console(tab_size=4,
                               log_path = False,
                               theme = theme) # create a rich-text console 
        
        
    def deactivate_all_data(self):
        self.data = self.n_files*[None]
        self.data_active = self.n_files*[False] 
        
    def screen_duplicate_files(self,fpaths):
        """
        check for duplicate files 

        Parameters
        ----------
        fpaths : list
            list of filepaths to check



        """
        filedata = []# store the filepaths and the size of the main data file for each input file 
        for fpath in fpaths:
            filedata.append([i.split(os.sep)[-1] for i in fpath] + [os.path.getsize(fpath[0])] + [fpath])
        fdata_df = pd.DataFrame(data =filedata, columns = ['fname_main','fname_aux','fsize','fpath'])

        n_files_init= len(fdata_df)
        fdata_df.drop_duplicates(inplace = True, subset = ['fname_main','fname_aux','fsize'])
        

        n_removed = n_files_init - len(fdata_df) # number of files removed
        self._duplicates_removed = n_removed
        self._filepaths_in = [i for i in fdata_df['fpath']]        
        
    # def __Pose_parser(self,Pose):
        
    #     #identify data gaps 
    #     t = p.pose.index.to_numpy() 
    #     dt =np.diff(t, prepend = t[0],).astype(float)/1e9 # time delta in seconds
    #     mask = dt>np.percentile(dt,99) # mask to identify data gaps 

    #     t[mask] = np.datetime64("NaT")
    #     def declump(a):
    #         return [a[s] for s in np.ma.clump_unmasked(np.ma.masked_invalid(a))]
    #     t_seg = declump(t)

    #     x1 = []
    #     x2 = []
    #     for seg in t_seg:
    #         print(len(seg))
    #         x1.append(seg[0])
    #         x2.append(seg[-1])
            
    #     file_start_time = x1
    #     file_end_time = x2
        

    #     return Pose,file_start_time,file_end_time
        
        
    def __pd0_parser(self,fpath,import_file = False,start_frac = 0, end_frac = 1):
        """
        parse a pd0 type file

        Parameters
        ----------
        fpath : TYPE
            DESCRIPTION.
        import_file : TYPE, optional
            DESCRIPTION. The default is False.
        start_frac : TYPE, optional
            DESCRIPTION. The default is 0.
        end_frac : TYPE, optional
            DESCRIPTION. The default is 1.

        Returns
        -------
        data : TYPE
            DESCRIPTION.
        file_start_time : TYPE
            DESCRIPTION.
        file_end_time : TYPE
            DESCRIPTION.

        """
        #screen the file
        

        data  = Pd0(fpath[0], import_file = False)
        file_start_time = pd.to_datetime(data.metadata.first_date_in_file)
        file_end_time = pd.to_datetime(data.metadata.last_date_in_file)


        if import_file:
            start_ensemble = int(start_frac*data.metadata.n_ensembles_in_file)+1
            end_ensemble = int(end_frac*data.metadata.n_ensembles_in_file)
            data = DataSet_pd0(fpath[0], 
                               import_file = True, 
                               start = start_ensemble,
                               end = end_ensemble,
                               pt3_filepath = fpath[1],
                               print_progress = False)
            
     
            
            
        return data, file_start_time,file_end_time
    
    def __ctd_parser(self,fpath,import_file = False,start_time = None, end_time = None):
        """
        parse a ctd type file

        Parameters
        ----------
        fpath : TYPE
            DESCRIPTION.
        import_file : TYPE, optional
            DESCRIPTION. The default is False.
        start_time : TYPE, optional
            DESCRIPTION. The default is none.
        end_time : TYPE, optional
            DESCRIPTION. The default is none.

        Returns
        -------
        data : TYPE
            DESCRIPTION.
        file_start_time : TYPE
            DESCRIPTION.
        file_end_time : TYPE
            DESCRIPTION.

        """
        
        ## add internal seabird method to read from entry a to b !!!!
        # for use in the manager base class
        # global data
        
        data = seabird_ctd(filepath_hex = fpath[0], filepath_xml = fpath[1], import_file = False)
        file_start_time = min(data.data['DateTime'])
        file_end_time = max(data.data['DateTime'])
 
        if import_file:
            data = DataSet_ctd(filepath_hex = fpath[0], filepath_xml = fpath[1], import_file = True)
            
            if type(start_time) == type(None):
                start_time = file_start_time
            
                        
            if type(end_time) == type(None):
                end_time = file_end_time


    
            mask = (data.data['DateTime']>=start_time) & (data.data['DateTime']<=end_time)
            
            #delete data outside of start_frac and end_frac #trim the data 
            #start_idx = max(int(data.n_samples*start_frac),0)
            #end_idx = int(data.n_samples*end_frac)
            
            for key in data.data.keys():
                data.data[key] = data.data[key][mask]#[start_idx:end_idx]
                
            data.n_samples = len(data.data['DateTime'])    
        return data, file_start_time,file_end_time
        
    def __screen_files(self):
        """
        Get metadata from files without reading the entire file. 
        file start and end dates. 

        Parameters
        ----------
        None

        Returns
        -------
        None.

        """
        #screen files initially 
        
        fpaths_to_read = [] # list of filepaths that passes the initial screening 

        for i,fpath in enumerate(self._filepaths_in):
            _pass = True
            reason = 'pass'
            ## check filesize requirements 
            if type(fpath) != type(str()):fsize = round(os.path.getsize(fpath[0])/1000,1)
            else: fsize = round(os.path.getsize(fpath)/1000,1)
            
            if fsize< self._min_fsize:
                _pass = False
                reason = f'file smaller than minimum allowed filesize {self._min_fsize} kb'
            
            ## update failed filepaths and reasons 
            if _pass:
                fpaths_to_read.append(fpath)
            
            else:
                self._filepaths_failed.append(fpath) 
                self._reason_failed.append(reason)
            
        
        for i,fpath in enumerate(fpaths_to_read):
            _pass = True
            
            try:
                self.get_file_metadata(fpath)
                message = f'screening {self.type} files from {self.name} {fpath[0].split(os.sep)[-1]} ({i+1}) '
                #print(message.ljust(1500),end = "\r")
            except Exception as e:
                _pass = False
                reason = e
                #status.update(e)
            
            ## update failed filepaths and reasons     
            if not _pass:
                self._reason_failed.append(reason)
                self._filepaths_failed.append(fpath)      
    




                  
        # et = time.time()
        #print(f'\r {150*" "}',end = "\r")
        #print(f'\rCreated dataset "{self.name}" - {self.n_files} {self.type} files ({round(self.dataset_size,1)}kb)')#\n\texecution time: {round(et - st,1)} sec'
        
       
        
    
    
    def get_file_metadata(self,fpath):
        '''
        Get metadata from a file without reading the entire file. 
        
        '''   
        dataset,file_start_time,file_end_time = self._parser(fpath)
        #self.data.append(dataset)
        self.file_start_times.append(file_start_time)
        self.file_end_times.append(file_end_time)
        self.n_files+=1 
        self.filepaths.append(fpath)
        self.dataset_size+=os.path.getsize(fpath[0])
        self.labels.append(dataset.name)
        
            
        
        
 
        
        
        
        
        

            
            
        
    def get_active_data(self):
        """
        Returns a list of objects for all active files.

        Returns
        -------
        active_data : list
            list of data objects for every active file

        """

        
        active_data = []
        
        for i in range(self.n_files):
            if self.data_active[i]:
                active_data.append(self.data[i])
        
        
        return active_data

    def load_data_between(self,start_time, end_time):
        """
        read data from all files between start_time and end_time. if start_time or 
        end_time fall within a file, then only the portion of the file after 
        start_time and before end_time will be loaded. 

        Parameters
        ----------
        start_time : pd.datetime
            start time to load data from. 
        end_time : TYPE
            end time to load data from. 

        Returns
        -------
        None.

        """
        
        ## filepaths, index of file, start_percentage, end_percentage 
        # global start_pcts, end_pcts,dt



        fnames = []
        indicies = []
        start_pcts = []
        end_pcts = []
        if end_time<=min(self.file_start_times) or start_time>=max(self.file_end_times):
            print('No results in selection')
            #warnings.warn('No results in selection')
        else:    
            
            
            indicies = np.arange(0,self.n_files)
            st= np.array(self.file_start_times)
            et= np.array(self.file_end_times)
            indicies = indicies[((st>=start_time) & (st<=end_time)) | ((et>=start_time) & (et<=end_time)) | ((st<=start_time) & (et>=end_time)) ]
    
    
            
            # indicies = np.arange(start_index,end_index+1)
            fnames = [self.filepaths[i] for i in indicies]
            
            start_pcts = [] # approx percentage into the file where the start time is
            end_pcts   = [] # approx percentage into the file where the end time is
            for idx in indicies:
                st = self.file_start_times[idx]
                et = self.file_end_times[idx]

                dt = et-st
                if et == st:
                    start_pct = 0
                    end_pct   = 1
                else:
                    start_pct = max((start_time - st)/dt,0)
                    end_pct = min((end_time-st)/dt,1)
                    
                start_pcts.append(start_pct)
                end_pcts.append(end_pct)
                    
                    
        
        
        ## load the data   
        #print(f'\r\tloaded ({0}/{len(indicies)}) {self.type} files from {self.name} dataset'.ljust(100), end = '\r')
        
        #print(indicies, start_pcts, end_pcts, start_time, end_time)
        for i,file_index in enumerate(indicies):
            
            args = {'file_index': file_index,'start_frac':start_pcts[i], 'end_frac':end_pcts[i], 'start_time':start_time,'end_time' :end_time} 
            self.load_one_file(args)
            
            
            #print(f'\r ... loading ({i+1}/{len(indicies)}) {self.type} files from {self.name} dataset'.ljust(100), end = '\r')
        #print(f'loaded {i+1} {self.type} files from {self.name} dataset'.ljust(100), end = '\n')    
        #print('\n')     
            # else:
            #     print(f'{fnames[i]} already leaded')
                
    def load_files(self,file_inds):
        
        if type(file_inds) != list:
            file_inds = list(file_inds)
         
        
        for file_index in file_inds:
            fname = self.filepaths[file_index][0].split(os.sep)[-1]
            if self.type == 'ctd':
                data,file_start_time,file_end_time = self._parser(self.filepaths[file_index], import_file = True)
            else:
                data,file_start_time,file_end_time = self._parser(self.filepaths[file_index], import_file = True)
                
            self.data[file_index] = data
            self.data_active[file_index] = True    
            self.console.log(f'[green4]({self.name}) loaded {fname} ({self.type})')     

    def load_one_file(self,args):
        '''
        load data from one file
        
        
        input args include the file index, start_fraction (start percentage of the file to read), end_fraction, start time, or end time 
        
        '''
        file_index = args['file_index']
        start_frac = args['start_frac']
        start_time= args['start_time']
        end_time = args['end_time']
        end_frac = args['end_frac']
        ## check if data has already been loaded 
        

        

            
        #try:
        fname = self.filepaths[file_index][0].split(os.sep)[-1]
        if self.type == 'ctd':
            data,file_start_time,file_end_time = self._parser(self.filepaths[file_index], import_file = True, start_time = start_time, end_time = end_time)
        else:
            data,file_start_time,file_end_time = self._parser(self.filepaths[file_index], import_file = True, start_frac = start_frac, end_frac = end_frac)
        
        self.data[file_index] = data
        self.data_active[file_index] = True    
        self.console.log(f'[green4]({self.name}) loaded {fname} ({self.type})')
                #time.sleep(.25)
        # except Exception as e: 
        #     self.console.log(f'[red3]({self.name}) failed to load {fname} ({self.type}) - {e}')
 

                
    def load_all_data(self, parallel = False):

        if parallel:
            args = [{'file_index': i,'start_frac':0, 'end_frac':1, 'start_time' : pd.to_datetime('1/1/1899'),'end_time' : pd.to_datetime('1/1/2100')} for i in range(self.n_files)]
            file_data = ptools.paralell_fcn(self.load_one_file,args)
            
            
        else:
            for i in range(self.n_files):
                #print(f'\rloading ({i+1}/{self.n_files}) {self.type} files from {self.name} dataset'.ljust(100), end = '\r')
                args = {'file_index': i,'start_frac':0, 'end_frac':1, 'start_time' :pd.to_datetime('1/1/1899'),'end_time' : pd.to_datetime('1/1/2100')} 
                self.load_one_file(args)
                
                
                
        

    
    

#%% 

class plotting:
    def __init__(self,dm):
        
        self._dm = dm
        
        # self.dtypes = [i for i in dir(self._dm.data) if not i.endswith('__')]
        

    def timespan(self,interactive = False):  
       
        global legend_items
        # if data == 'adcp':
        #     ds = self._data.adcp
        # if data == 'ctd':
        #     ds = self._data.ctd
        
        
        fig,ax = subplots(figheight = 3,figwidth = 8, for_production = True)
        
        #ax.set_aspect(1/ds.n_files)
 
        
        colors = [dhi_colors.blue2,
                  dhi_colors.green1,
                  dhi_colors.blue3,
                  dhi_colors.green2]
        color = dhi_colors.blue2
        legend_items = []
        for d,dataset in enumerate(self._dm.datasets.keys()):
            ds = self._dm.datasets[dataset]
            x = np.array([ds.file_start_times,ds.file_end_times]).T
            offset = 1
            
            for n in range(ds.n_files):
                if n == 0: label = dataset
                else: label = None
                
                
                #if ds.type == 'ctd':
                gid = '...'+ os.sep + os.sep.join(ds.filepaths[n][0].split(os.sep)[-3:])
  
                
                #print(gid)
                item = ax.plot([x[n,0],x[n,1]],2*[(d)*offset], lw = 20,solid_capstyle='butt', color = color, alpha = 0.7, label = label, gid = gid)

        # Shrink current axis by 20%
        box = ax.get_position()
        ax.set_position([box.x0+.1, box.y0, box.width*0.9, box.height])


        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)   
        ax.spines['left'].set_visible(False) 
        
        #ax.get_yaxis().set_visible(False)
        ax.set_ylim(-offset,(d+1)*offset)    
        locator = mpl.dates.AutoDateLocator()
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter( mpl.dates.AutoDateFormatter(locator) )        
        
        ax.set_xlabel('Time')
    
        ax.set_title(f'Timespan\n{self._dm.name}')
        ax.set_yticks(np.linspace(0,d*offset,d+1))
        ax.minorticks_off()
        

        ax.set_yticklabels([d for d in self._dm.datasets.keys()],fontsize = 10)


        ax.grid(False)
        
        if interactive:
            annot = ax.text(0,0,'TEST')
            def update_annot(text,x,y):
                annot.set_visible(True)
                annot.set_position((x,y))
                annot.set_text(text)
                fig.canvas.draw()
                
            def on_plot_hover(event):
                global curve
                
                
                annot.set_visible(False)
                for curve in ax.get_lines():
                    if curve.contains(event)[0]:
                        x, y = event.xdata, event.ydata
                        text = curve.get_gid()
                        annot.set_visible(True)
                        annot.set_position((x,y))
                        annot.set_text(text)
                        fig.canvas.draw()
                        curve.set_color(dhi_colors.red2)
                    else:
                        curve.set_color(dhi_colors.blue2)
                    
            fig.canvas.mpl_connect('motion_notify_event', on_plot_hover)           
            plt.show()
        
        
        return fig, ax
                
    
#%%

class DataManager:
    def __init__(self, name = 'Data Manager'):
        self.name = name
        self.datasets = {}
        self.n_datasets = 0
        self.plot = plotting(self)
        
        self.create_console()

        #
        text = Text(f'Data Manager ({name})')

        self.console.print(f'Data Manager ({name})', style = 'header')
        
        
        
    def create_console(self):
        
        theme = Theme({'header': 'bold cyan underline',
                       'new_dataset': 'dark_cyan'})
        self.console = Console(tab_size=4,
                               theme = theme,
                               log_path = False,
                               color_system = 'standard') # create a rich-text console         
    def deactivate_all_data(self):
        for  key in self.datasets.keys():
            self.datasets[key].deactivate_all_data()
            
            
            
    def add_dataset(self,file_type,fpaths,name,min_fsize = 0):
        self.console.log(f'({name}) dataset registered', style = 'new_dataset')
        time.sleep(0.25)
        
        if file_type =='pd0':
            self.datasets[name] = manager_base(parser_name = 'pd0',name = name, fpaths = fpaths,min_fsize = min_fsize)
        elif file_type == 'ctd':
            self.datasets[name] = manager_base(parser_name = 'ctd',name = name, fpaths = fpaths,min_fsize = min_fsize)
        self.n_datasets+=1
        
        

        

        
    
    
    def load_all_data_between(self,start_time,end_time):
        """
        read data from all files between start_time and end_time for every 
        registered dataset. see data_manager.load_data_between for more info

        Parameters
        ----------
        start_time : pd.datetime
            start time to load data from. 
        end_time : TYPE
            end time to load data from. 

        Returns
        -------
        None.
        
        """

        #with self.console.status(f'[yellow] loading all data between {start_time.strftime("%d%b%y %H:%M")} and {end_time.strftime("%d%b%y %H:%M")}', spinner_style = 'white') as status:
        for key in self.datasets.keys():
            self.datasets[key].load_data_between(start_time = start_time, end_time = end_time)
            
            
            
    def load_all_data(self):
        """
        read all files in all datasets.

        """

        #with self.console.status(f'[yellow] loading all data between {start_time.strftime("%d%b%y %H:%M")} and {end_time.strftime("%d%b%y %H:%M")}', spinner_style = 'white') as status:
        for key in self.datasets.keys():
            self.datasets[key].load_all_data()
            
            
    def save(self, fpath = None):
        # serialize a data manage robject 
        if fpath == None:
            fpath = '.' + os.sep + self.name + '.dm'
        else:
            fpath = fpath + '.dm'
            
            
        with open(fpath, "wb") as dill_file:
            # deactivate all loaded data and all print consoles for serilization
            self.deactivate_all_data()
            self.console = None
            for dataset in self.datasets:
                self.datasets[dataset].console = None
            
            # serialize the data manager object and save to file
            dill.dump(self, dill_file)
            
            
            # recreate consoles 
            self.create_console()
            for dataset in self.datasets:
                self.datasets[dataset].create_console()
            
        
            
            

        
        
        

        

#%%   load save and merge functions (serialization)
import copy


def concatenate(dms,name):
    # concatenate a list of DataManager objects. 
    # new DataManager will be given name (name)
    dm = DataManager(name = name)    
    for dm_c in dms:
        # get all datasets in each data manager object to combine 
        for name,dataset in dm_c.datasets.items():
            dataset.console = None
            dm.datasets[name] = copy.deepcopy(dataset)
        dm.n_datasets = len(dm.datasets)
    return dm
    

        
        
        
def load(fpath):
    # deserialize a data manager object 
    with open(fpath, "rb") as dill_file:
        # deserialize data manager object and reinitilize the print consoles
         dm = dill.load(dill_file)    
         dm.create_console()
         for dataset in dm.datasets:
             dm.datasets[dataset].create_console()
             
    return dm



