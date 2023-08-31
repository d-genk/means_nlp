# AUTOGENERATED! DO NOT EDIT! File to edit: 33-split-data.ipynb (unless otherwise specified).

__all__ = ['split_data', 'split_data_grp']

# Cell
#no_test
#dependencies
import pandas as pd
import numpy as np

# Cell
def split_data(df, train_prop = 0.80, validation_prop = None, seed = None):
    '''
        df: data frame to use for splitting
        train: proportion of df for training ; testing set is 1-training proportion
        validation: proportion of df for validation ; if None, testing set is 1-training proportion. If not None, testing set is 1 - (training_prop + validation_prop)
        seed: seed number to use for splitting the data

        returns: 2 or 3 dataframes based on the inputs
    '''

    #Create training frame
    train_df = df.sample(frac=train_prop,random_state = seed)

    #Conditionally create validation and testing frames
    if validation_prop != None:
        validation_pool = df.drop(train_df.index)
        validation_df = validation_pool.sample(n = int(validation_prop * len(df)), random_state = seed)

        #Create testing frame
        test_drop_index = train_df.index.union(validation_df.index)
        test_df = df.drop(test_drop_index)

        #Return frames
        return train_df, validation_df, test_df

    #Return testing w/o validation frame
    else:
        test_df = df.drop(train_df.index)

        return train_df, test_df

# Cell
def split_data_grp(df, prop_train = 0.80, prop_validation = None, grp_var = None, seed = None):
    '''
     df: data frame to use for splitting
        train: proportion of df for training ; testing set is 1-training proportion
        validation: proportion of df for validation ; if None, testing set is 1-training proportion. If not None, testing set is 1 - (training_prop + validation_prop)
        grp_var: variable to split data frames on, passed as a string
        seed: seed number to use for splitting the data for reproducibility

        returns: 2 or 3 dataframes based on the inputs
    '''

    # If grouping variable is supplied
    if grp_var != None:

        #Determine the relevant splits of interest
        if prop_validation is None:
            prop_validation = 0

        prop_test = 1 - prop_train - prop_validation

        #Light error checking
        if prop_test <=0:
            raise ValueError("prop_train + prop_validation + prop_test must be equal to 1.")

        #Select out the unique groups (note: we reset index here because otherwise, the horzconcat below tries to align on the row indices)
        unique_groups = df[grp_var].drop_duplicates().reset_index(drop=True)
        n_grps = len(unique_groups)

        #Generate list with values 1, 2, and 3 in proportion to the train/valid/test splits
        rep_list = [1]*int(n_grps*prop_train) + [2]*int(n_grps*prop_validation) + [3]*int(n_grps*prop_test)

        #For non-even splits, just add these to the test set
        n_leftovers = n_grps - len(rep_list)
        rep_list = rep_list + [3]*n_leftovers

        #Randomly permute these values to get assignments
        grp_assigns = (pd.DataFrame(rep_list, columns=['split'])
                       .sample(frac=1, random_state = seed)
                       .reset_index(drop=True))

        #Concatenate these onto the unique_groups dataframe
        unique_groups = pd.concat([unique_groups, grp_assigns], axis=1)

        #Join the split assignments with the original dataframe (unique row split assignments will be broadcast to the non-unique ones)
        full_df = pd.merge(df, unique_groups, on=grp_var)

        #Split and drop columns
        tr_df = full_df.query('split==1').drop(columns=['split'])
        val_df = full_df.query('split==2').drop(columns=['split'])
        te_df = full_df.query('split==3').drop(columns=['split'])

        #Return the splits
        if prop_validation == 0:
            return tr_df, te_df
        else:
            return tr_df, val_df, te_df

    else:

        #no grouping variable applies original split_data function
        return split_data(df, train_prop = prop_train, validation_prop = prop_validation, seed = seed)
