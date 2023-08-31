# AUTOGENERATED! DO NOT EDIT! File to edit: 41-generic-framework-for-spacy-training.ipynb (unless otherwise specified).

__all__ = ['load_model', 'train_model', 'save_model', 'test_model']

# Cell
#no_test
#dependencies

#nlp packages
import nltk
import spacy
from spacy.util import minibatch, compounding
from spacy.training import Example

#ssda modules for testing
from .collate import genSpaCyInput

# manipulation of tables/arrays
import pandas as pd
import numpy as np

# helpers
import random
import warnings
from pathlib import Path

# Cell

def load_model(model=None, language="en", verbose=False):
    '''
    Load the Spacy model or create blank model
        model: (default None) directory of any existing model or named Spacy model
        language: (default 'en') two-letter Spacy language code, default is English
        verbose: (default False) boolean reflecting whether to print status of model loading

        returns: Spacy Language object
    '''
    if model is not None:
        nlp = spacy.load(model)  # load existing spaCy model
        if verbose: print("Loaded model '%s'" % model)
    else:
        #Create new model
        nlp = spacy.blank(language)  # create blank Language model

        # defaults to English, unless different language passed to function
        if verbose: print("Created blank '" + language)

    return nlp

# Cell

def train_model(nlp, training_data, n_iter=100, dropout=0.5, compound_params=None, solver_params=None):

    '''
    Train the `ner` component of the provided Language object (model)
        nlp: Language object (model) - blank or pretrained.  Usually created by `load_model`.
        training_data: pre-labelled training data in Spacy format
        n_iter: (default 100)  Integer number of training iterations
        dropout: (default 0.5)  Float value of ratio of dropout to prevent network memorization.
        compound_params: (default None) dictionary of keys `start`, `end`, and `cp_rate` (defaults 4, 32, and 1.001).  Refer to the starting
            number of elements in the batch (start), the maximum number of elements in a batch (end), and the multiplier of `start` to do the
            compounding (cp_rate).  Pass in a dictionary of one or more of these keys to change those specific default parameters.
        solver_params: (default None) dictionary of keys relating to the parameters of the Adam solver.  Allowable parameters include:
            `learn_rate`, `b1`, `b2`, `L2`, `max_grad_norm`, with defaults 0.001, 0.9, 0.999, 1e-6, and 1.0.  See
            https://github.com/explosion/spaCy/blob/master/spacy/_ml.py : `create_default_parameters` for more information.

        returns: trained Language object, pandas Dataframe object with losses per iteration
    '''

    # create the built-in pipeline components and add them to the pipeline
    # use ner_init for blank models whose ner weights will need to be initialized later
    ner_init = False
    if "ner" not in nlp.pipe_names:
        #ner = nlp.create_pipe("ner")
        nlp.add_pipe("ner", last=True)
        ner_init = True
        ner = nlp.get_pipe("ner")
    # otherwise, get it so we can add labels
    else:
        ner = nlp.get_pipe("ner")

    for _, annotations in training_data:
        for ent in annotations.get("entities"):
            ner.add_label(ent[2])

    # get names of other pipes to disable them during training
    pipe_exceptions = ["ner", "trf_wordpiecer", "trf_tok2vec"]
    other_pipes = [pipe for pipe in nlp.pipe_names if pipe not in pipe_exceptions]

    # only train NER
    with nlp.disable_pipes(*other_pipes) and warnings.catch_warnings():
        # show warnings for misaligned entity spans once
        warnings.filterwarnings("once", category=UserWarning, module='spacy')

        # initialize the weights if a blank model was passed in, otherwise, use existing weights.
        if ner_init:
            nlp.begin_training()
        else:
            nlp.resume_training()

        # set optimizer values to be the ones passed in if desired
        allowable_params = ['learn_rate', 'b1', 'b2', 'L2', 'max_grad_norm']
        if solver_params is not None:
            for key, val in solver_params.items():
                if key in allowable_params:
                    setattr(nlp._optimizer, key, val)
                else:
                    raise ValueError('Key "{0}" not supported for solver. Only values {1} allowed'.format(key, allowable_params))

        # set compounding parameters to be passed in and ensure they are floats
        cp_params = {'start': 4.0, 'end': 32.0, 'cp_rate': 1.001}
        if compound_params is not None:
            for key, val in compound_params.items():
                if key in cp_params:
                    cp_params[key] = float(compound_params[key])
                else:
                    raise ValueError('Key "{0}" not supported for compounding.  Only `start`, `end`, `cp_rate` allowed.'.format(key))

        # create dataframe to be returned
        losses_df = pd.DataFrame(np.zeros(shape=(n_iter, 1)), columns=['epoch_loss'])

        # train batches of data for n_iter iterations
        examples = []
        for text, annots in training_data:
            examples.append(Example.from_dict(nlp.make_doc(text), annots))
            #nlp.initialize(lambda: examples)

        for itn in range(n_iter):
            random.shuffle(examples)
            losses = {}

            # Create variable size minibatch
            batches = minibatch(examples, size=compounding(cp_params['start'], cp_params['end'], cp_params['cp_rate']))
            for batch in batches:
                #implement dropout decay?
                nlp.update(
                    batch,
                    drop = dropout,
                    losses = losses,
                )

            # Update df with loss stats
            losses_df.loc[itn, 'epoch_loss'] = losses['ner']

    return nlp, losses_df

# Cell

def save_model(nlp_model, output_dir):

    '''
    Save the Language object model to directory specified by `output_dir`
       nlp_model: Language (pipeline) object
       output_dir: output directory string - relative or absolute
       returns: none - saves model to directory and prints directory
    '''

    if output_dir is not None:
        output_dir = Path(output_dir)
        if not output_dir.exists():
            output_dir.mkdir(parents=True)
        nlp_model.to_disk(output_dir)  # nlp.to_disk('/data/p_dsi/ssda/models/model_name')
        print("Saved model to", output_dir)

    return

# Cell
def _test_model(row, nlp_model, id_colname, text_colname):
    '''
    Internal helper function which uses the nlp model to predict the `text` rows of the dataframe and match with their ID.
        *shouldn't be used directly; is used with an `apply` statement for a pandas DF
        row: row of dataframe which contains at least columns `ID` and `text`
        nlp_model: Spacy Language object (model) to perform predictions
        id_colname: String name of the column where the ID is stored
        text_colname: String name of the column where the text is stored
        returns: Long pandas dataframe with columns reflecting entities recognized, entity types, and spans
    '''

    doc = nlp_model(row[text_colname])
    doc_ents = [(ents.text, ents.label_, ents.start_char, ents.end_char) for ents in doc.ents]

    # Make sure that actual entities were extracted or else, return None for everything
    if doc_ents != []:
        pred_ent_names, pred_ent_types, pred_ent_start, pred_ent_end = zip(*doc_ents)
        res_sz = len(pred_ent_names)
    else:
        pred_ent_names, pred_ent_types, pred_ent_start, pred_ent_end = None, None, None, None
        res_sz = 1

    df_res = pd.DataFrame({id_colname: [row[id_colname]]* res_sz, #to fix when doc_ents is None
                           'pred_entity': pred_ent_names,
                           'pred_label': pred_ent_types,
                           'pred_start': pred_ent_start,
                           'pred_end': pred_ent_end})
    return df_res

# Cell

# test the trained model
def test_model(nlp_model, testing_df, id_colname, text_colname, score_model=True):
    '''
    Use the model to predict the entities and labels of the testing data using the model specified; optionally return precision/recall metrics
        nlp_model: nlp object to be evaluated
        testing_df: original dataframe with columns `ID`, `text`, `entity*`, `label*`, `start*`, and `end*`.
            `ID`: identifier for each entry/text
            `text: the text of each text
            `entity`: the person, place, etc within the text to be identified (note: this data frame will be long since there can be
                multiple entities for the same entry)
            `label`: the entity type (e.g., PER, LOC)
            `start`: starting character of the entity in the entry
            `end`: one past the ending character of the entity in the entry
            `*` indicates columns that are required only if score_model=True
        id_colname: String name of the column where the entry ID is stored
        text_colname: String name of the column where the text is stored
        score_model: (default True) boolean indicating whether to return precision/recall metrics associated with the model predictions.  Must pass
            *'ed columns in the dataframe.

        returns: dataframe of prediction results,
                 dataframe of overall precision, recall, and fscore (None if score_model is False)
                 dataframe of per-entity precision, recall, and fscore (None if score_model is False)
    '''

    # get unique entries/texts from the dataframe as a dataframe
    # using id_colname and text_colname both here should be OK as they are 1:1
    unique_entries_df = testing_df[[id_colname, text_colname]].drop_duplicates()

    # Get predicted entities
    preds = unique_entries_df.apply(_test_model, axis=1, args=[nlp_model, id_colname, text_colname]).tolist()
    preds_df = pd.concat(preds, ignore_index=True)

    # Get model performance
    pred_metrics = None
    per_ent_metrics = None

    if score_model:
        spacy_test_data = genSpaCyInput(testing_df)

        examples = []
        for text, annots in spacy_test_data:
            examples.append(Example.from_dict(nlp_model.make_doc(text), annots))

        nlp_scorer = nlp_model.evaluate(examples)

        # Build dataframe of results
        pred_metrics = pd.DataFrame({'precision': [nlp_scorer['ents_p'] * 100],
                                     'recall': [nlp_scorer['ents_r'] * 100],
                                     'f_score': [nlp_scorer['ents_f'] * 100],
                                    })

        per_ent_metrics = pd.DataFrame({**nlp_scorer['ents_per_type']})

    return preds_df, pred_metrics, per_ent_metrics