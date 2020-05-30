"""
NASA NextGen NAS ULI Information Fusion

@organization: Arizona State University
@author: Xinyu Zhao
@date: 2020-05-30
@last updated: 2020-05-30

This Python script is used for simulating aviation accident based on recording in NTSB
Simulation based on NATS beta1.7 standalone version
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import pandas as pd
import numpy as np

class RiskEstimator:
    """

        Estimating the risk of each event in an accident

        Parameters
        ----------
        inputs to Aviation Risk simulation
        isRNN : boolean
            check weather using RNN or not
        data : str
            directory to required reference from NTSB
        model : str
            directory to pre-trained model
        device : str
            'CUDA'/ 'CPU'-- Running the model along GPU or CPU
    """
    def __init__(self, model, isRNN, data, device):
        self.model = model
        self.isRNN = isRNN
        self.data = data
        self.device = device

    def load_model(self):
        """
            Load pre-trained models
        """
        refer = pd.read_pickle(self.data + 'refer.pickle')
        occurrence_code_corpus = refer['occurrence_code_corpus']
        subject_code_corpus = refer['subject_code_corpus']
        phase_code_corpus = refer['phase_code_corpus']
        subj_to_occurrence_dict = refer['subj_to_occurrence_dict']
        occurrence_to_subj_dict = refer['occurrence_to_subj_dict']
        phase_to_occurrence_dict = refer['phase_to_occurrence_dict']
        subject_size = len(subject_code_corpus)
        phase_size = len(phase_code_corpus)
        occurrence_size = len(occurrence_code_corpus)

        batch_size = 1

        if self.isRNN:
            embedding_dim = 30  # Embedding of each word
            hidden_dim = 50  # Final hidden dimension that is used for prediction
            num_layer = 2  # Number of layers
            latent_dim = 30  # Latend dimension

            model = _RNNModel(phase_size, occurrence_size, subject_size, embedding_dim, latent_dim, num_layer,
                             batch_size, hidden_dim, self.device).to(self.device)
            hierarchical_softmax = _HierarchicalSoftmax(hidden_dim, phase_to_occurrence_dict, occurrence_to_subj_dict,
                                                       subj_to_occurrence_dict, self.device).to(self.device)
            hierarchical_softmax.load_state_dict(torch.load(self.model + "hierarchical_softmax_rnn.sav"))
            model.load_state_dict(torch.load(self.model + "model_rnn.sav"))
        else:
            embedding_dim = 100  # Embedding of each word
            hidden_dim = 50  # Final hidden dimension that is used for prediction

            model = _SequentialPrediction(phase_size, occurrence_size, subject_size, embedding_dim, batch_size,
                                         hidden_dim, self.device)
            hierarchical_softmax = _HierarchicalSoftmax(hidden_dim, phase_to_occurrence_dict, occurrence_to_subj_dict,
                                                       subj_to_occurrence_dict, self.device).to(self.device)
            hierarchical_softmax.load_state_dict(torch.load(self.model + "hierarchical_softmax_sequential.sav"))
            model.load_state_dict(torch.load(self.model + "model_sequential.sav"))
        risk_model = pd.read_pickle(self.model + 'risk_model.sav')
        return model, hierarchical_softmax, risk_model

    def _create_risk_estimator(self, pred_phase, pred_occurrence, pred_subject):
        """
            Converting feature vectors into one-hot-encoding format

            Parameters
            ----------
            inputs to Aviation Risk simulation
            pred_phase : str
                the predicted flight phase
            pred_occurrence : str
                the predicted flight occurrence
            pred_subject : str
                the predicted flight subject
        """
        refer = pd.read_pickle(self.data + 'refer.pickle')
        occurrence_code_corpus = refer['occurrence_code_corpus']
        subject_code_corpus = refer['subject_code_corpus']
        phase_code_corpus = refer['phase_code_corpus']
        subject_buffer = np.zeros(len(subject_code_corpus))
        phase_buffer = np.zeros(len(phase_code_corpus))
        occurrence_buffer = np.zeros(len(occurrence_code_corpus))
        for j in pred_subject:
            subject_buffer[int(j)] = 1
        for j in pred_occurrence:
            occurrence_buffer[int(j)] = 1
        for j in pred_phase:
            phase_buffer[int(j)] = 1
        a = np.concatenate((subject_buffer, occurrence_buffer, phase_buffer), axis=0)
        return a

    def risk_estimation(self, case_code, i, device, model, hierarchical_softmax, risk_model, datadict, isRNN, nsample=100):
        """
            Estimating the risk of the event in aviation accident

            Parameters
            ----------
            inputs to Aviation Risk simulation
            case_code : Pandas DataFrame
                Accident recording from NTSB
            i : int
                The time index of sequential events in an accident
            device : str
                'CUDA'/ 'CPU'-- Running the model along GPU or CPU
            model : Pytorch model
                Model for hierarchical sequential modeling for aviation accident
            hierarchical_softmax : Pytorch model
                Model for hierarchical softmax
            risk_model : catboost/ xgboost object
                Model for estimating the risk of a sequential event
            datadict : Pandas DataFrame
                dictionary from NTSB recording
            isRNN : boolean
                check weather using RNN or not
        """
        x_subject_input = torch.LongTensor(case_code['Subj_Code'][0][:i + 1]).to(device)
        x_occurrence_input = torch.LongTensor(case_code['Occurrence_Code'][0][:i + 1]).to(device)
        x_phase_input = torch.LongTensor(case_code['Phase_of_Flight'][0][:i + 1]).to(device)
        refer = pd.read_pickle(self.data + 'refer.pickle')
        occurrence_code_corpus = refer['occurrence_code_corpus']
        subject_code_corpus = refer['subject_code_corpus']
        phase_code_corpus = refer['phase_code_corpus']

        subject = list(datadict[datadict['code_iaids'] == subject_code_corpus[x_subject_input[-1]]]['meaning'])[0]
        phase = list(datadict[datadict['code_iaids'] == phase_code_corpus[x_phase_input[-1]]]['meaning'])[0]
        occurrence = \
        list(datadict[datadict['code_iaids'] == occurrence_code_corpus[x_occurrence_input[-1]]]['meaning'])[0]

        # Predicting the possible future path
        if isRNN:
            hidden = model.init_hidden()
            X, hidden = model(x_phase_input, x_occurrence_input, x_subject_input, len(x_subject_input), hidden)

        else:
            X = model(x_phase_input, x_occurrence_input, x_subject_input, len(x_subject_input))

        phase_proba, occurance_proba, subject_proba = hierarchical_softmax.predict(X, len(x_subject_input))
        pred_phase = np.zeros(phase_proba.shape[0] + 1)
        pred_occurrence = np.zeros(phase_proba.shape[0] + 1)
        pred_subject = np.zeros(phase_proba.shape[0] + 1)
        risk_current = []

        # Sampling according to the predicting probability
        for j in range(nsample):
            for jj in range(phase_proba.shape[0] + 1):

                if jj == phase_proba.shape[0]:
                    pred_phase[jj] = np.random.choice(phase_proba.shape[1], 1,
                                                      phase_proba[jj - 1].cpu().detach().numpy().tolist())
                    pred_occurrence[jj] = np.random.choice(phase_proba.shape[1], 1,
                                                           phase_proba[jj - 1].cpu().detach().numpy().tolist())
                    pred_subject[jj] = np.random.choice(phase_proba.shape[1], 1,
                                                        phase_proba[jj - 1].cpu().detach().numpy().tolist())
                else:
                    pred_phase[jj] = x_phase_input[jj]
                    pred_occurrence[jj] = x_occurrence_input[jj]
                    pred_subject[jj] = x_subject_input[jj]

            # Convert feature vector into one-hot-encoding format
            risk_estimators = self._create_risk_estimator(pred_phase, pred_occurrence, pred_subject)
            # Estimating the risk of a sequential event in aviation accident
            risk = risk_model.predict(risk_estimators.reshape(1, -1))[0, 0]
            risk_current.append(risk)
        return risk_current, phase, occurrence, subject

class _RNNModel(nn.Module):
    def __init__(self, phase_size, occurrence_size, subject_size, embedding_dim, latent_dim, num_layer, batch_size,
                 hidden_dim, device):
        super(_RNNModel, self).__init__()
        self.latent_dim = latent_dim
        self.num_layer = num_layer
        self.batch_size = batch_size
        self.phase_size = phase_size
        self.occurrence_size = occurrence_size
        self.hidden_dim = hidden_dim

        self.subject_size = subject_size
        self.embedding_dim = embedding_dim
        self.device = device

        self.word_embedding_phase = nn.Embedding(
            num_embeddings=self.phase_size,
            embedding_dim=self.embedding_dim,
            padding_idx=self.phase_size - 1,
        ).to(self.device)

        self.word_embedding_occurrence = nn.Embedding(
            num_embeddings=self.occurrence_size,
            embedding_dim=self.embedding_dim,
            padding_idx=self.occurrence_size - 1,
        ).to(self.device)

        self.word_embedding_subject = nn.Embedding(
            num_embeddings=self.subject_size,
            embedding_dim=self.embedding_dim,
            padding_idx=self.subject_size - 1,
        ).to(self.device)

        self.output = nn.Linear(latent_dim, hidden_dim).to(device)

        self.rnn = nn.LSTM(
            input_size=3 * self.embedding_dim,
            hidden_size=self.latent_dim,  # class number
            num_layers=self.num_layer,  # number of RNN layers
            batch_first=True,
            bidirectional=False,
        ).to(self.device)

    def init_hidden(self):
        h0 = torch.zeros(self.num_layer, self.batch_size, self.latent_dim, requires_grad=True).to(self.device)
        c0 = torch.zeros(self.num_layer, self.batch_size, self.latent_dim, requires_grad=True).to(self.device)
        return (h0, c0)

    def forward(self, X_phase, X_occurrence, X_subject, X_lengths, hidden):
        h_phase = self.word_embedding_phase(X_phase)
        h_occurrence = self.word_embedding_occurrence(X_occurrence)
        h_subject = self.word_embedding_subject(X_subject)
        h = torch.cat((h_phase, h_occurrence, h_subject), axis=1).unsqueeze(0)
        X, hidden = self.rnn(h, hidden)
        out = self.output(X[0])
        return out, hidden


class _SequentialPrediction(nn.Module):
    def __init__(self, phase_size, occurrence_size, subject_size, embedding_dim, batch_size, hidden_dim, device):
        super(_SequentialPrediction, self).__init__()
        self.hidden_dim = hidden_dim
        self.batch_size = batch_size

        self.phase_size = phase_size
        self.occurrence_size = occurrence_size
        self.subject_size = subject_size

        self.embedding_dim = embedding_dim
        self.device = device

        self.word_embedding_phase = nn.Embedding(
            num_embeddings=self.phase_size,
            embedding_dim=self.embedding_dim,
            padding_idx=self.phase_size - 1,
        ).to(self.device)

        self.word_embedding_occurrence = nn.Embedding(
            num_embeddings=self.occurrence_size,
            embedding_dim=self.embedding_dim,
            padding_idx=self.occurrence_size - 1,
        ).to(self.device)

        self.word_embedding_subject = nn.Embedding(
            num_embeddings=self.subject_size,
            embedding_dim=self.embedding_dim,
            padding_idx=self.subject_size - 1,
        ).to(self.device)
        self.output = nn.Linear(3 * embedding_dim, hidden_dim).to(device)

    def forward(self, X_phase, X_occurrence, X_subject, X_lengths):
        h_phase = self.word_embedding_phase(X_phase)
        h_occurrence = self.word_embedding_occurrence(X_occurrence)
        h_subject = self.word_embedding_subject(X_subject)
        h = torch.cat((h_phase, h_occurrence, h_subject), axis=1)
        out = F.relu(self.output(F.relu(h)))

        return out


class _HierarchicalSoftmax(nn.Module):
    def __init__(self, hidden_dim, phase_to_occurrence_dict, occurrence_to_subj_dict, subj_to_occurrence_dict, device):
        super(_HierarchicalSoftmax, self).__init__()
        self.hidden_dim = hidden_dim

        self.phase_to_occurrence_dict = phase_to_occurrence_dict

        self.occurrence_to_subj_dict = occurrence_to_subj_dict
        self.subj_to_occurrence_dict = subj_to_occurrence_dict

        self.to_phase = nn.Linear(self.hidden_dim, len(self.phase_to_occurrence_dict))

        self.phase_to_occurrence = nn.ModuleDict(
            {str(key): nn.Linear(hidden_dim, len(self.phase_to_occurrence_dict[key])) for key in
             self.phase_to_occurrence_dict.keys()})

        self.occurrence_to_subj = nn.ModuleDict(
            {str(key): nn.Linear(hidden_dim, len(self.occurrence_to_subj_dict[key])) for key in
             self.occurrence_to_subj_dict.keys()})

        self.softmax1 = nn.Softmax(dim=1)

        self.softmax = nn.Softmax(dim=0)

        self.device = device

    def forward(self, X, X_length, X_subject, X_occurrence, X_phase):
        device = self.device
        phase_logit = self.to_phase(X)
        phase_proba = self.softmax1(phase_logit)
        phase_proba = phase_proba[torch.arange(phase_proba.shape[0]), X_phase].to(device)

        occurrence_proba = torch.zeros(len(X_occurrence)).to(self.device)
        for i in range(len(X_phase)):
            key = X_phase[i].cpu().numpy()
            buffer = self.phase_to_occurrence[str(key)](X[i])
            occurrence_proba[i] = self.softmax(buffer)[self.phase_to_occurrence_dict[int(key)].index(X_occurrence[i])]

        subject_proba = torch.zeros(len(X_subject)).to(self.device)
        for i in range(len(X_subject)):
            key = X_occurrence[i].cpu().numpy()
            buffer = self.occurrence_to_subj[str(key)](X[i])
            subject_proba[i] = self.softmax(buffer)[self.occurrence_to_subj_dict[int(key)].index(X_subject[i])]
        target_proba = phase_proba * occurrence_proba * subject_proba
        return phase_proba, phase_proba * occurrence_proba, target_proba

    def predict(self, X, X_length):
        phase_logit = self.to_phase(X)
        phase_proba = self.softmax1(phase_logit)
        nlength = X.shape[0]

        occurance_proba = torch.zeros(nlength, max(self.occurrence_to_subj_dict.keys()) + 1, requires_grad=True).to(
            self.device)
        subject_proba = torch.zeros(nlength, max(self.subj_to_occurrence_dict.keys()) + 1, requires_grad=True).to(
            self.device)

        for i_time in range(X_length):
            for i_phase in self.phase_to_occurrence_dict.keys():
                phase_to_occurance_prob = self.softmax(self.phase_to_occurrence[str(i_phase)](X[i_time]))
                occurance_proba[i_time, self.phase_to_occurrence_dict[i_phase]] += phase_proba[
                                                                                       i_time, i_phase] * phase_to_occurance_prob
            for i_occurrence in self.occurrence_to_subj_dict.keys():
                occurrence_to_subj_prob = self.softmax(self.occurrence_to_subj[str(i_occurrence)](X[i_time]))
                subject_proba[i_time, self.occurrence_to_subj_dict[i_occurrence]] += occurance_proba[
                                                                                         i_time, i_occurrence] * occurrence_to_subj_prob

        return phase_proba, occurance_proba, subject_proba