from keras.preprocessing.sequence import pad_sequences
from keras import backend as K
from keras.models import load_model
from keras.models import Model
import keras.optimizers
from sklearn.decomposition import PCA
from visualize_embedding import get_topic_embedding
from visualize_embedding import get_if_embedding
from baseline import generate_feature_label_pair
import matplotlib.pyplot as plt
import getopt
import numpy as np
import pandas as pd
import keras
import pickle
import sys

MAX_SEQ_LENGTH = 500
BATCH_SIZE = 512
MAX_SEQ_LENGTH = 500
EMBEDDING_SIZE = 256

tokenizer = pickle.load(open("data/tokenizer.p", "rb"))
labelEncoder = pickle.load(open("data/label_encoder.p", "rb"))
topic_model = load_model("model/category1.h5")
if_model = load_model("model/impact_factor1.h5")

trainIterator = pd.read_table("data/train_j.txt", delimiter="\t", header = 0, chunksize=BATCH_SIZE)
trainIterator = iter(trainIterator)

def convert2embedding(X):
	topic_embedding = get_topic_embedding(topic_model, X)
	if_embedding = get_if_embedding(if_model, X)
	embedding = np.concatenate((topic_embedding, if_embedding), axis = 1)
	return embedding

def sample_generator():
    global trainIterator
    while True:
        try:
            chunk = next(trainIterator)
        except:
            trainIterator = pd.read_table("data/train_j.txt", delimiter="\t", header = 0, chunksize=BATCH_SIZE)
            trainIterator = iter(trainIterator)
            chunk = next(trainIterator)
        X, Y = generate_feature_label_pair(chunk)
        embedding = convert2embedding(X)
        yield embedding, Y

def create_model():
    model = Sequential()
    model.add(layers.Dense(units=1200, activation='relu', input_shape=(EMBEDDING_SIZE,)))
    model.add(layers.Dense(units=800, activation='relu'))
    model.add(layers.Dense(units=len(labelEncoder.classes_), activation = 'softmax'))
    model.compile(loss = 'categorical_crossentropy',
                 optimizer = keras.optimizers.Adam(lr=0.001), 
                 metrics = ['accuracy'])
    return model

def main():
    # Get number of training samples
    with open("data/train_j.txt") as f:
        nTrain = sum(1 for _ in f)
    dev = pd.read_table("data/dev_j.txt", delimiter="\t", header = 0)
    devX, devY = generate_feature_label_pair(dev)
    devX = convert2embedding(devX)
    nBatches = math.ceil(nTrain / BATCH_SIZE)
    model = create_model()
    model.fit_generator(sample_generator(), steps_per_epoch = nBatches, epochs=2, validation_data=(devX, devY))
    model.save("model/embedding1.h5")

if __name__ == "__main__":
    main()


