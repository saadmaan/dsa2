# pylint: disable=C0321,C0103,E1221,C0301,E1305,E1121,C0302,C0330
# -*- coding: utf-8 -*-
"""
cd analysis
 run preprocess



"""
import warnings
warnings.filterwarnings('ignore')
import sys
import gc
import os
import pandas as pd
import json, copy

# from tqdm import tqdm_notebook


#### Add path for python import
sys.path.append( os.path.dirname(os.path.abspath(__file__)) + "/")

#### Root folder analysis
root = os.path.abspath(os.getcwd()).replace("\\", "/") + "/"
print(root)


# from diskcache import Cache
# cache = Cache('db.cache')
# cache.reset('size_limit', int(2e9))


####################################################################################################
####################################################################################################
def log(*s, n=0, m=1):
    sspace = "#" * n
    sjump = "\n" * m
    ### Implement pseudo Logging
    print(sjump, sspace, s, sspace, flush=True)


from util_feature import  save, load_function_uri



####################################################################################################
####################################################################################################
from util_feature import  load_dataset



def save_features(df, name, path):
    """

    :param df:
    :param name:
    :param path:
    :return:
    """
    if path is not None :
       os.makedirs( f"{path}/{name}" , exist_ok=True)
       df.to_parquet( f"{path}/{name}/features.parquet")


# @cache.memoize(typed=True,  tag='fib')  ### allow caching results
def preprocess(path_train_X="", path_train_y="", path_pipeline_export="", cols_group=None, n_sample=5000,
               preprocess_pars={}, filter_pars={}, path_features_store=None):
    """

    :param path_train_X:
    :param path_train_y:
    :param path_pipeline_export:
    :param cols_group:
    :param n_sample:
    :param preprocess_pars:
    :param filter_pars:
    :param path_features_store:
    :return:
    """
    from util_feature import (pd_colnum_tocat, pd_col_to_onehot, pd_colcat_mapping, pd_colcat_toint,
                              pd_feature_generate_cross)

    ##### column names for feature generation ###############################################
    log(cols_group)
    coly            = cols_group['coly']  # 'salary'
    colid           = cols_group['colid']  # "jobId"
    colcat          = cols_group['colcat']  # [ 'companyId', 'jobType', 'degree', 'major', 'industry' ]
    colnum          = cols_group['colnum']  # ['yearsExperience', 'milesFromMetropolis']
    
    colcross_single = cols_group.get('colcross', [])   ### List of single columns
    #coltext        = cols_group.get('coltext', [])
    coltext         = cols_group.get('coltext', [])
    coldate         = cols_group.get('coldate', [])
    colall          = colnum + colcat + coltext + coldate
    log(colall)

    #### Pipeline Execution
    pipe_default    = [ 'filter', 'label', 'dfnum_bin', 'dfnum_hot',  'dfcat_bin', 'dfcat_hot', 'dfcross_hot', ]
    pipe_list       = preprocess_pars.get('pipe_list', pipe_default)


    ##### Load data ########################################################################
    df = load_dataset(path_train_X, path_train_y, colid, n_sample= n_sample)


    ##### Filtering / cleaning rows :   ####################################################
    if "filter" in pipe_list :
        ymin, ymax = filter_pars.get('ymin', -9999999999.0), filter_pars.get('ymax', 999999999.0)
        df = df[df[coly] > ymin]
        df = df[df[coly] < ymax]


    ##### Label processing   ##############################################################
    y_norm_fun = None
    if "label" in pipe_list :
        # Target coly processing, Normalization process  , customize by model
        log("y_norm_fun preprocess_pars")
        y_norm_fun = preprocess_pars.get('y_norm_fun', None)
        if y_norm_fun is not None:
            df[coly] = df[coly].apply(lambda x: y_norm_fun(x))
            save(y_norm_fun, f'{path_pipeline_export}/y_norm.pkl' )


    ########### colnum procesing   #########################################################
    for x in colnum:
        df[x] = df[x].astype("float32")
    log(df[colall].dtypes)


    if "dfnum_bin" in pipe_list :
        log("### Map numerics to Category bin  ###########################################")
        dfnum_bin, colnum_binmap = pd_colnum_tocat(df, colname=colnum, colexclude=None, colbinmap=None,
                                                   bins=10, suffix="_bin", method="uniform",
                                                   return_val="dataframe,param")
        log(colnum_binmap)
        ### Renaming colunm_bin with suffix
        colnum_bin = [x + "_bin" for x in list(colnum_binmap.keys())]
        log(colnum_bin)
        save_features(dfnum_bin, 'dfnum_binmap', path_features_store)


    if "dfnum_hot" in pipe_list and "dfnum_bin" in pipe_list  :
        log("### colnum bin to One Hot")
        dfnum_hot, colnum_onehot = pd_col_to_onehot(dfnum_bin[colnum_bin], colname=colnum_bin,
                                                    colonehot=None, return_val="dataframe,param")
        log(colnum_onehot)
        save_features(dfnum_hot, 'dfnum_onehot', path_features_store)


    ##### Colcat processing   ################################################################
    colcat_map = pd_colcat_mapping(df, colcat)
    log(df[colcat].dtypes, colcat_map)

    if "dfcat_hot" in pipe_list :
        log("#### colcat to onehot")
        dfcat_hot, colcat_onehot = pd_col_to_onehot(df[colcat], colname=colcat,
                                                    colonehot=None, return_val="dataframe,param")
        log(dfcat_hot[colcat_onehot].head(5))
        save_features(dfcat_hot, 'dfcat_onehot', path_features_store)


    if "dfcat_bin" in pipe_list :
        #### Colcat to integer encoding
        dfcat_bin, colcat_bin_map = pd_colcat_toint(df[colcat], colname=colcat,
                                                    colcat_map=None, suffix="_int")
        colcat_bin = list(dfcat_bin.columns)
        save_features(dfcat_bin, 'dfcat_bin', path_features_store)


    ####### colcross cross features from Onehot features  #####################################
    if "dfcross_hot" in pipe_list :
        try :
           df_onehot = dfcat_hot.join(dfnum_hot, on=colid, how='left')
        except :
           df_onehot = copy.deepcopy(dfcat_hot)

        colcross_single_onehot_select = []
        for t in list(df_onehot) :
            for c1 in colcross_single :
                if c1 in t :
                   colcross_single_onehot_select.append(t)

        df_onehot = df_onehot[colcross_single_onehot_select ]
        dfcross_hot, colcross_pair = pd_feature_generate_cross(df_onehot, colcross_single_onehot_select,
                                                               pct_threshold=0.02,  m_combination=2)
        log(dfcross_hot.head(2).T)
        colcross_pair_onehot = list(dfcross_hot.columns)
        save_features(dfcross_hot, 'dfcross_onehot', path_features_store)
        del df_onehot ; gc.collect()

    ##### Coltext processing   ################################################################
    if "dftext" in pipe_list :
        from utils import util_text, util_text_embedding
        dftext = pd.DataFrame()
        # dfext = df[coltext]
        save_features(dftext, 'dftext', path_features_store)





    ##### Coldate processing   ################################################################
    if "dfdate" in pipe_list :
        from utils import util_date
        dfdate = pd.DataFrame()
        # dfdate = df[coldate]
        save_features(dfdate, 'dfdate', path_features_store)








    ##################################################################################################
    ##### Save pre-processor meta-parameters
    os.makedirs(path_pipeline_export, exist_ok=True)
    log(path_pipeline_export)
    cols_family = {}

    for t in ['colid',
              "colnum", "colnum_bin", "colnum_onehot", "colnum_binmap",  #### Colnum columns
              "colcat", "colcat_bin", "colcat_onehot", "colcat_bin_map",  #### colcat columns
              'colcross_single_onehot_select', "colcross_pair_onehot",  'colcross_pair',  #### colcross columns

              'coldate',
              'coltext',

              "coly", "y_norm_fun"
              ]:
        tfile = f'{path_pipeline_export}/{t}.pkl'
        log(tfile)
        t_val = locals().get(t, None)
        if t_val is not None :
           save(t_val, tfile)
           cols_family[t] = t_val


    ######  Merge AlL  #############################################################################
    dfXy = df[colnum + colcat + [coly] ]
    for t in [ 'dfnum_bin', 'dfnum_hot', 'dfcat_bin', 'dfcat_hot', 'dfcross_hot',
               'dfdate',  'dftext'  ] :
        if t in locals() :
           dfXy = pd.concat((dfXy, locals()[t] ), axis=1)
    save_features(dfXy, 'dfX', path_features_store)

    colXy = list(dfXy.columns)
    colXy.remove(coly)    ##### Only X columns
    cols_family['colX'] = colXy
    save(colXy, f'{path_pipeline_export}/colsX.pkl' )


    ###### Return values  #########################################################################
    return dfXy, cols_family


def preprocess_load(path_train_X="", path_train_y="", path_pipeline_export="", cols_group=None, n_sample=5000,
               preprocess_pars={}, filter_pars={}, path_features_store=None):
  return  None, None


####################################################################################################
############CLI Command ############################################################################
def run_preprocess(model_name, path_data, path_output, path_config_model="source/config_model.py", n_sample=5000,
              mode='run_preprocess',):     #prefix "pre" added, in order to make if loop possible
    """
      Configuration of the model is in config_model.py file

    """
    path_output       = root + path_output
    path_data         = root + path_data
    path_pipeline_out = path_output + "/pipeline/"
    path_model_out    = path_output + "/model/"
    path_check_out    = path_output + "/check/"
    path_train_X      = path_data   + "/features*"    ### Can be a list of zip or parquet files
    path_train_y      = path_data   + "/target*"      ### Can be a list of zip or parquet files
    log(path_output)


    log("#### load input column family  ###################################################")
    cols_group = json.load(open(path_data + "/cols_group.json", mode='r'))
    log(cols_group)


    log("#### Model parameters Dynamic loading  ############################################")
    model_dict_fun = load_function_uri(uri_name= path_config_model + "::" + model_name)
    model_dict     = model_dict_fun(path_model_out)   ### params


    log("#### Preprocess  #################################################################")
    preprocess_pars = model_dict['model_pars']['pre_process_pars']
    filter_pars     = model_dict['data_pars']['filter_pars']

    if mode == "run_preprocess" :
        dfXy, cols      = preprocess(path_train_X, path_train_y, path_pipeline_out, cols_group, n_sample,
                                 preprocess_pars, filter_pars)

    elif mode == "load_preprocess" :
        dfXy, cols      = preprocess_load(path_train_X, path_train_y, path_pipeline_out, cols_group, n_sample,
                                 preprocess_pars, filter_pars)


    model_dict['data_pars']['coly'] = cols['coly']
    
    ### Get actual column names from colum groups : colnum , colcat
    model_dict['data_pars']['cols_model'] = sum([  cols[colgroup] for colgroup in model_dict['data_pars']['cols_model_group'] ]   , [])                
    log(  model_dict['data_pars']['cols_model'] , model_dict['data_pars']['coly'])
    
   
    log("######### finish #################################", )


if __name__ == "__main__":
    import fire
    fire.Fire()




