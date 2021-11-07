import datetime
from dateutil.relativedelta import relativedelta

import numpy as np
from numpy.random import randn
from numpy.random import seed
from hmmlearn import hmm
from scipy.stats import pearsonr
import matplotlib.pyplot as plt
from copy import deepcopy
import pandas as pd


class PredictHMM():
    def __init__(self, type, initial_probabilties=None, transition_probabilities=None,
                 emission_probabilities=None, state_space=None, emission_space=None):
        self.temp = None
        self.type = type
        self.initial = initial_probabilties
        self.transition = transition_probabilities
        self.emission = emission_probabilities
        self.state_space = state_space
        self.emission_space = emission_space


    def predict_fed_rate(self, interest_rates, inflation_rates, curr_inflation, training_required=True):
        # States: interest rate (range from 0% to 5% each step by 0.25%) at time T
        # Emission: inflation rate (range from 0% to 5% each step by 0.25%) in one month earlier than state time T
        states = []
        emissions = []
        for i in range(20):
            states.append(i * 0.25)
            emissions.append(i * 0.25)
        states.append(5)
        emissions.append(5)
        interest_lst, inflation_lst, dates = self.get_seqeuences(inflation_rates, interest_rates,
                                                                relativedelta(months=-1))
        # discretize states space
        for i in range(len(interest_lst)):
            int_rate_discretized = float(interest_lst[i]) // 0.25
            if int_rate_discretized >= 20:
                interest_lst[i] = 20
            else:
                interest_lst[i] = int(int_rate_discretized)
            inflation_discretized = float(inflation_lst[i]) // 0.25
            if inflation_discretized <= 0:
                inflation_lst[i] = 0
            elif inflation_discretized >= 20:
                inflation_lst[i] = 20
            else:
                inflation_lst[i] = int(inflation_discretized)
        # training model if training_required(Param) is True. Else, use the model's given attributes
        fed_rate = np.array(interest_lst)
        inflation = np.array(inflation_lst)
        print(f"Correlation R: {pearsonr(fed_rate, inflation)}")
        if training_required: model = self.train_model(fed_rate, inflation, len(states))
        else: model = self
        # get Time t+1 emission state
        if curr_inflation // 0.25 < 0: curr_inflation = 0
        elif curr_inflation // 0.25 >= 20: curr_inflation = 20
        else: curr_inflation = int(curr_inflation // 0.25)
        # make prediction based on Viterbi Algorithm
        if training_required:
            most_probable_state = self.predict_future_state(curr_inflation, fed_rate, model)
        else:
            most_probable_state = predict_with_viterbi(fed_rate[-1], curr_inflation, self.transition, self.emission)
        # add t+1 data into each container
        interest_lst.append(most_probable_state)
        t_plus_one_date = self.get_next_date(dates[-1], '1mo')
        dates.append(t_plus_one_date)
        inflation_lst.append(curr_inflation)
        # translate result data containers into state and emission representation
        hmm_interests, hmm_inflations = self.map_sequence_to_label(states, emissions,
                                                                   interest_lst, inflation_lst, dates)
        most_probable_state = states[most_probable_state]
        hmm_interests.reverse()
        hmm_inflations.reverse()
        return most_probable_state, hmm_interests, hmm_inflations, states, emissions, model

    def get_seqeuences(self, observation_seq, state_seq, time_diff=datetime.timedelta(days=0)):
        '''
        param: observation(emission) sequence and hidden state sequence to be used for model training
        param: time_diff(default=0) is used to get an emission sequence starts from earlier
        or later time than state sequence, but two sequences will have the same length
        return: a tuple of observation sequence, hidden state sequence, and time(date)
        '''
        max_len = len(observation_seq) if len(observation_seq) > len(state_seq) else len(state_seq)
        emission_seq_ind = 0  # observed sequence index
        state_seq_ind = 0  # hidden state sequence index
        emission_seq = []
        new_state_seq = []
        date = []
        while emission_seq_ind < max_len:
            try:
                emission_date = datetime.datetime.strptime(observation_seq[emission_seq_ind][0],
                                                           "%Y-%m-%d")
                state_date = datetime.datetime.strptime(state_seq[state_seq_ind][0],
                                                           "%Y-%m-%d")
                if emission_date > (state_date + time_diff):
                    emission_seq_ind += 1
                elif emission_date < (state_date + time_diff) :
                    state_seq_ind += 1
                else:
                    date.append(state_seq[state_seq_ind][0])
                    emission_seq.append(observation_seq[emission_seq_ind][1])
                    new_state_seq.append(state_seq[state_seq_ind][1])
                    emission_seq_ind += 1
                    state_seq_ind += 1
            except IndexError:
                break
        emission_seq.reverse()
        new_state_seq.reverse()
        date.reverse()
        return new_state_seq, emission_seq, date


    def train_model(self, state_sequence_set, observed_sequence_set, num_states, n_iterations=100):
        # return trained multinomial HMM model. States space should be discrete
        model = hmm.MultinomialHMM(n_components=num_states, n_iter=900, tol=-2)
        x = np.array([observed_sequence_set]).T
        model.fit(x)
        return model

    def predict_future_state(self, t_observation, state_seq, model):
        '''
        :param observation: observation at time t+1
        :param obsevation_seq: E = {e1, e2, e3, .... et}
        :param state_seq: S = {s1, s2, s3, .... st}
        :param model: hmm model theta
        :return: most probable state at time t+1
        '''
        initial_prob = model.startprob_
        transition_prob = model.transmat_
        emission_prob = model.emissionprob_

        # because of conditional independency
        # hidden state at time t is enough to predict hidden state at time t+1
        prev_state = state_seq[-1]
        from_prev_state = transition_prob[prev_state]  # type numpy nd array
        given_t_observation = emission_prob[:, t_observation]  # type numpy nd array
        product = from_prev_state * given_t_observation
        highest_probability = -0.01
        for i in range(len(product)):
            if product[i] > highest_probability:
                most_probable_state = i
                highest_probability = product[i]
        return most_probable_state  # this is the most probable state at time t

    def get_next_date(self, date: str, interval: str):
        # interval: interval between current and next date. Options) 1d(day), 1mo(month)
        # return t+1 date in real time
        date_dt = datetime.datetime.strptime(date, "%Y-%m-%d")
        next_date = None
        if interval == '1d':
            next_date = datetime.datetime.strftime(date_dt + datetime.timedelta(days=1), "%Y-%m-%d")
        if interval == '1mo':
            next_date = datetime.datetime.strftime(date_dt + relativedelta(months=1), "%Y-%m-%d")
        return next_date

    def map_sequence_to_label(self, state_space, emission_space, state_seq,
                                    emission_seq, dates):
        # map emission and hidden state sequences to the corresponding state spaces' labels
        new_state_seq = []
        new_emission_seq = []
        for i in range(len(state_seq)):
            state = state_space[state_seq[i]]
            observed_emission = emission_space[emission_seq[i]]
            new_state_seq.append((dates[i], state))
            new_emission_seq.append((dates[i], observed_emission))
        return new_state_seq, new_emission_seq

    def how_corrleated(self, variable_x, variable_y):
        corr, _ = pearsonr(variable_x, variable_y)
        print(f"Correlation R: {corr}")


def predict_with_viterbi(prev_state, curr_observation, transition_prob, emission_prob):
    '''
    :param transition_prob: 2d list
    :param emission_prob: 2d list
    :return: most probable state at time t+1
    '''
    # because of conditional independency,
    # state at time t is enough to predict hidden state at time t+1
    from_prev_state = transition_prob[prev_state]  # type numpy nd array
    given_t_observation = [array[curr_observation] for array in emission_prob] # type numpy nd array
    product = [from_prev_state[i] * given_t_observation[i] for i in range(len(from_prev_state))]
    highest_probability = max(product)
    most_probable_state = product.index(highest_probability)
    return most_probable_state

