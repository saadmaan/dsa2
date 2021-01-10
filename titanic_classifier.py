# pylint: disable=C0321,C0103,E1221,C0301,E1305,E1121,C0302,C0330
# -*- coding: utf-8 -*-
"""


  python titanic_classifier.py  train    > zlog/log_titanic_train.txt 2>&1
  python titanic_classifier.py  predict  > zlog/log_titanic_predict.txt 2>&1


"""
import warnings, copy, os, sys
warnings.filterwarnings('ignore')

####################################################################################
###### Path ########################################################################
from source.util_feature import save

config_file  = "titanic_classifier.py"
# config_file      = "titanic_classifier.py"   ### name of file which contains data configuration

print( os.getcwd())
root = os.path.abspath(os.getcwd()).replace("\\", "/") + "/"
print(root)

dir_data  = os.path.abspath( root + "/data/" ) + "/"
dir_data  = dir_data.replace("\\", "/")
print(dir_data)


def os_get_function_name():
    import sys
    return sys._getframe(1).f_code.co_name


def global_pars_update(model_dict,  data_name, config_name):
    m                      = {}
    m['config_path']       = root + f"/{config_file}"
    m['config_name']       = config_name

    ##### run_Preoprocess ONLY
    m['path_data_preprocess'] = root + f'/data/input/{data_name}/train/'

    ##### run_Train  ONLY
    m['path_data_train']   = root + f'/data/input/{data_name}/train/'
    m['path_data_test']    = root + f'/data/input/{data_name}/test/'
    #m['path_data_val']    = root + f'/data/input/{data_name}/test/'
    m['path_train_output']    = root + f'/data/output/{data_name}/{config_name}/'
    m['path_train_model']     = root + f'/data/output/{data_name}/{config_name}/model/'
    m['path_features_store']  = root + f'/data/output/{data_name}/{config_name}/features_store/'
    m['path_pipeline']        = root + f'/data/output/{data_name}/{config_name}/pipeline/'


    ##### Prediction
    m['path_pred_data']    = root + f'/data/input/{data_name}/test/'
    m['path_pred_pipeline']= root + f'/data/output/{data_name}/{config_name}/pipeline/'
    m['path_pred_model']   = root + f'/data/output/{data_name}/{config_name}/model/'
    m['path_pred_output']  = root + f'/data/output/{data_name}/pred_{config_name}/'


    #####  Generic
    m['n_sample']             = model_dict['data_pars'].get('n_sample', 5000)

    model_dict[ 'global_pars'] = m
    return model_dict


####################################################################################
##### Params########################################################################
config_default   = 'titanic_lightgbm'          ### name of function which contains data configuration


# data_name    = "titanic"     ### in data/input/
cols_input_type_1 = {
     "coly"   :   "Survived"
    ,"colid"  :   "PassengerId"
    ,"colcat" :   ["Sex", "Embarked" ]
    ,"colnum" :   ["Pclass", "Age","SibSp", "Parch","Fare"]
    ,"coltext" :  []
    ,"coldate" :  []
    ,"colcross" : [ "Name", "Sex", "Ticket","Embarked","Pclass", "Age","SibSp", ]
}


cols_input_type_2 = {
     "coly"   :   "Survived"
    ,"colid"  :   "PassengerId"
    ,"colcat" :   ["Sex", "Embarked" ]
    ,"colnum" :   ["Pclass", "Age","SibSp", "Parch","Fare"]
    ,"coltext" :  ["Name", "Ticket"]
    ,"coldate" :  []
    ,"colcross" : [ "Name", "Sex", "Ticket","Embarked","Pclass", "Age","SibSp", "Parch","Fare" ]
}


####################################################################################
def titanic_lightgbm(path_model_out="") :
    """
       Contains all needed informations for Light GBM Classifier model,
       used for titanic classification task
    """
    config_name  = os_get_function_name()
    data_name    = "titanic"         ### in data/input/
    model_class  = 'LGBMClassifier'  ### ACTUAL Class name for model_sklearn.py
    n_sample     = 1000

    def post_process_fun(y):   ### After prediction is done
        return  int(y)

    def pre_process_fun(y):    ### Before the prediction is done
        return  int(y)


    model_dict = {'model_pars': {
        ### LightGBM API model   #######################################
         'model_class': model_class
        ,'model_pars' : {'objective': 'binary',
                           'n_estimators': 10,
                           'learning_rate':0.001,
                           'boosting_type':'gbdt',     ### Model hyperparameters
                           'early_stopping_rounds': 5
                        }

        , 'post_process_fun' : post_process_fun   ### After prediction  ##########################################
        , 'pre_process_pars' : {'y_norm_fun' :  pre_process_fun ,  ### Before training  ##########################


        ### Pipeline for data processing ##############################
        'pipe_list': [
            {'uri': 'source/preprocessors.py::pd_coly',                 'pars': {}, 'cols_family': 'coly',       'cols_out': 'coly',           'type': 'coly'         },
            {'uri': 'source/preprocessors.py::pd_colnum_bin',           'pars': {}, 'cols_family': 'colnum',     'cols_out': 'colnum_bin',     'type': ''             },
            {'uri': 'source/preprocessors.py::pd_colnum_binto_onehot',  'pars': {}, 'cols_family': 'colnum_bin', 'cols_out': 'colnum_onehot',  'type': ''             },
            {'uri': 'source/preprocessors.py::pd_colcat_bin',           'pars': {}, 'cols_family': 'colcat',     'cols_out': 'colcat_bin',     'type': ''             },
            {'uri': 'source/preprocessors.py::pd_colcat_to_onehot',     'pars': {}, 'cols_family': 'colcat_bin', 'cols_out': 'colcat_onehot',  'type': ''             },
            {'uri': 'source/preprocessors.py::pd_colcross',             'pars': {}, 'cols_family': 'colcross',   'cols_out': 'colcross_pair',  'type': 'cross'},

            #### Example of Custom processor
            {'uri': 'source/preprocessors.py::pd_colnum_quantile_norm',   'pars': {}, 'cols_family': 'colnum',   'cols_out': 'colnum_quantile_norm',  'type': '' },          
          
        ],
               }
        },

      'compute_pars': { 'metric_list': ['accuracy_score','average_precision_score']
                        },

      'data_pars': { 'n_sample' : n_sample,
          'cols_input_type' : cols_input_type_1,
          ### family of columns for MODEL  #########################################################
          #  "colnum", "colnum_bin", "colnum_onehot", "colnum_binmap",  #### Colnum columns
          #  "colcat", "colcat_bin", "colcat_onehot", "colcat_bin_map",  #### colcat columns
          #  'colcross_single_onehot_select', "colcross_pair_onehot",  'colcross_pair',  #### colcross columns
          #  'coldate', 'coltext',
          'cols_model_group': [ 'colnum_bin',
                                'colcat_bin',
                                # 'coltext',
                                # 'coldate',
                                'colcross_pair',
                               
                               ### example of custom
                               'colnum_quantile_norm'
                              ]

          ### Filter data rows   ##################################################################
         ,'filter_pars': { 'ymax' : 2 ,'ymin' : -1 }

         }
      }

    ##### Filling Global parameters    ############################################################
    model_dict        = global_pars_update(model_dict, data_name, config_name )
    return model_dict







#####################################################################################
########## Profile data #############################################################
def data_profile(path_data_train="", path_model="", n_sample= 5000):
   from source.run_feature_profile import run_profile
   a = titanic_lightgbm()
   path_data_train = a['global_pars']['path_data_train']
   run_profile(path_data   = path_data_train,
               path_output = "data/out/ztmp/" + "/profile/",
               n_sample    = n_sample,
              )


###################################################################################
########## Preprocess #############################################################
### def preprocess(config='', nsample=1000):
from core_run import preprocess
aa = 0

def preprocess(config=None, nsample=None):
    config_name  = config  if config is not None else config_default
    mdict        = globals()[config_name]()
    m            = mdict['global_pars']
    #print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>><<<<???????????????????????????????????????????????")
    #print(config_name)
    #print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>><<<" +hj+"<???????????????????????????????????????????????")
    n = nsample if nsample is not None else m['n_sample']
    print(n)
    n = int(float(n))
    from source import run_preprocess
    run_preprocess.run_preprocess(config_name   =  config_name,
                                  config_path   =  m['config_path'],
                                  n_sample      =  n,

                                  ### Optonal
                                  mode          =  'run_preprocess',
                                  model_dict=None)




##################################################################################
########## Train #################################################################
from core_run import train

def train(config=None, nsample=None):

    config_name  = config  if config is not None else config_default
    mdict        = globals()[config_name]()
    m            = mdict['global_pars']
    print(mdict)

    from source import run_train
    run_train.run_train(config_name       =  config_name,
                        config_path       =  m['config_path'],
                        n_sample          =  nsample if nsample is not None else m['n_sample'],
                        )




###################################################################################
######### Check data ##############################################################
def check():
   pass




####################################################################################
####### Inference ##################################################################
# predict(config='', nsample=10000)
from core_run import predict


def predict(config=None, nsample=None):
    config_name  = config  if config is not None else config_default
    mdict        = globals()[config_name]()
    m            = mdict['global_pars']


    from source import run_inference
    run_inference.run_predict(config_name = config_name,
                              config_path = m['config_path'],
                              n_sample    = nsample if nsample is not None else m['n_sample'],

                              #### Optional
                              path_data   = m['path_pred_data'],
                              path_output = m['path_pred_output'],
                              model_dict  = None
                              )



###########################################################################################################
###########################################################################################################
"""
python  titanic_classifier.py  data_profile
python  titanic_classifier.py  preprocess  --nsample 100
python  titanic_classifier.py  train       --nsample 200
python  titanic_classifier.py  check
python  titanic_classifier.py  predict


"""
if __name__ == "__main__":
    import fire
    fire.Fire()
    




#######################################################################################
########## Examepl of custom processor ################################################
def pd_colnum_quantile_norm(df, col, pars={}):
  """
     colnum normalization by quantile
  """
  import pandas as pd, numpy as np
  from source.util_feature import  load, save
  prefix  = "colnum_quantile_norm"
  df      = df[col]
  num_col = col

  ##### Grab previous computed params  ################################################
  pars2 = {}
  if  'path_pipeline' in pars :   #### Load existing column list
       colnum_quantile_norm = load( pars['path_pipeline']  +f'/{prefix}.pkl')
       model                = load( pars['path_pipeline']  +f'/{prefix}_model.pkl')
       pars2                = load( pars['path_pipeline']  +f'/{prefix}_pars.pkl')

  ########### Compute #################################################################
  lower_bound_sparse = pars2.get('lower_bound_sparse', None)
  upper_bound_sparse = pars2.get('upper_bound_sparse', None)
  lower_bound        = pars2.get('lower_bound_sparse', None)
  upper_bound        = pars2.get('upper_bound_sparse', None)
  sparse_col         = pars2.get('colsparse', ['capital-gain', 'capital-loss'] )

  ####### Find IQR and implement to numericals and sparse columns seperately ##########
  Q1  = df.quantile(0.25)
  Q3  = df.quantile(0.75)
  IQR = Q3 - Q1

  for col in num_col:
    if col in sparse_col:
      df_nosparse = pd.DataFrame(df[df[col] != df[col].mode()[0]][col])

      if lower_bound_sparse is not None:
        pass

      elif df_nosparse[col].quantile(0.25) < df[col].mode()[0]: #Unexpected case
        lower_bound_sparse = df_nosparse[col].quantile(0.25)

      else:
        lower_bound_sparse = df[col].mode()[0]

      if upper_bound_sparse is not None:
        pass

      elif df_nosparse[col].quantile(0.75) < df[col].mode()[0]: #Unexpected case
        upper_bound_sparse = df[col].mode()[0]

      else:
        upper_bound_sparse = df_nosparse[col].quantile(0.75)

      n_outliers = len(df[(df[col] < lower_bound_sparse) | (df[col] > upper_bound_sparse)][col])

      if n_outliers > 0:
        df.loc[df[col] < lower_bound_sparse, col] = lower_bound_sparse * 0.75 #--> MAIN DF CHANGED
        df.loc[df[col] > upper_bound_sparse, col] = upper_bound_sparse * 1.25 # --> MAIN DF CHANGED

    else:
      if lower_bound is None or upper_bound is None :
         lower_bound = df[col].quantile(0.25) - 1.5 * IQR[col]
         upper_bound = df[col].quantile(0.75) + 1.5 * IQR[col]

      df[col] = np.where(df[col] > upper_bound, 1.25 * upper_bound, df[col])
      df[col] = np.where(df[col] < lower_bound, 0.75 * lower_bound, df[col])

  df.columns = [ t + "_qt_norm" for t in df.columns ]
  pars_new   = {'lower_bound' : lower_bound, 'upper_bound': upper_bound,
                'lower_bound_sparse' : lower_bound_sparse, 'upper_bound_sparse' : upper_bound_sparse  }
  dfnew    = df
  model    = None
  colnew   = list(df.columns)

  ##### Export ##############################################################################
  if 'path_features_store' in pars and 'path_pipeline_export' in pars:
      # save_features(df,  prefix, pars['path_features_store'])
      save(colnew,     pars['path_pipeline_export']  + f"/{prefix}.pkl" )
      save(pars_new,   pars['path_pipeline_export']  + f"/{prefix}_pars.pkl" )
      save(model,      pars['path_pipeline_export']  + f"/{prefix}_model.pkl" )



  col_pars = {'prefix' : prefix, 'path': pars.get('path_pipeline_export', pars.get("path_pipeline", None)) }
  col_pars['cols_new'] = {
    prefix :  colnew  ### list
  }
  return dfnew,  col_pars




