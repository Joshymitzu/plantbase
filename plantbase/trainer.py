from data import get_data
from utils import get_test_data
from params import MODEL_VERSION

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import csv
import tensorflow
import os
from PIL import Image
import glob
import joblib
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline, make_pipeline
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.preprocessing.image import load_img
from tensorflow.keras.preprocessing.image import img_to_array
from tensorflow import keras
from tensorflow.keras.models import Sequential
from tensorflow.keras import optimizers
from tensorflow.keras.applications.vgg16 import preprocess_input
from tensorflow.keras import layers
from tensorflow.keras.callbacks import EarlyStopping
import tensorflow.keras.losses


class Trainer():

    ESTIMATOR = 'CNN_basic'
    EXPERIMENT_NAME = 'PlantBaseTrainer'

    def __init__(self, train, val, **kwargs):
        self.train_generator = train_generator
        self.val_generator = val_generator
        self.kwargs = kwargs


    def get_estimator(self):
        estimator = self.kwargs.get('estimator', self.ESTIMATOR)
        if estimator == 'CNN_basic':
            model = Sequential([
                  #layers.experimental.preprocessing.Rescaling(1./255, input_shape=(img_height, img_width, 3)),
                  layers.Conv2D(16, 3, input_shape=(256,256, 3),padding='same', activation='relu'),
                  layers.MaxPooling2D(),
                  layers.Conv2D(32, 3, padding='same', activation='relu'),
                  layers.MaxPooling2D(),
                  layers.Conv2D(64, 3, padding='same', activation='relu'),
                  layers.MaxPooling2D(),
                  layers.Flatten(),
                  layers.Dense(128, activation='relu'),
                  layers.Dense(16)
                ])
            model.compile(optimizer='adam',
                        loss=tensorflow.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
                        metrics=['accuracy'])

        elif estimator == 'vgg16':
            pass

        elif estimator == 'vgg19':
            pass
        else:
            pass

        # add in mlflow stuff
        print(type(model))
        return model


    # def set_pipeline(self):
    #     self.set_pipeline = make_pipeline([self.get_estimator()])

    def train(self):
        self.model= self.get_estimator()
        es = EarlyStopping(monitor='val_loss', patience=5, mode='min')
        self.model.fit(self.train_generator,
                    steps_per_epoch = self.train_generator.samples // 32,
                    validation_data = self.val_generator,
                    validation_steps = self.val_generator.samples // 32,
                    #class_weight=class_weight,
                    epochs = 15,
                    #callbacks = [es]
                    )

    def evaluate(self):
        # get predictions for all species
        X_test, y_true = get_test_data()
        test_df = pd.read_csv("../plantbase/data/test_data.csv").drop(columns = "Unnamed: 0")
        y_pred = self.model.predict(X_test)

        y_pred_df = pd.DataFrame(y_pred, columns=np.sort(test_df.genus.unique()))

        # get species with top prediction and true species
        y_pred_df['pred_genus'] = y_pred_df.idxmax(axis=1)
        y_pred_df['true_genus'] = y_true[:,0]

        # measure success rate
        prediction_review = (y_pred_df['pred_genus'] == y_pred_df['true_genus'])
        accuracy = prediction_review.value_counts()[True] / prediction_review.count()
        print(f'test accuracy: {accuracy}')

    def save_model(self, upload=True, auto_remove=True):
        """Save the model into a .joblib and upload it on Google Storage /models folder
        HINTS : use sklearn.joblib (or jbolib) libraries and google-cloud-storage"""
        joblib.dump(self.model, 'model.joblib')
        print("model.joblib saved locally", "green")

        if not self.local:
            storage_upload(model_version=MODEL_VERSION)


if __name__ == '__main__':
    params = dict()
    train_val = get_data(**params)
    train_generator = train_val[0]
    val_generator = train_val[1]
    t = Trainer(train=train_generator, val=val_generator, **params)
    print("############  Training model   ############")
    t.train()
    print("############  Evaluating model ############")
    t.evaluate()
    # print("############   Saving model    ############", "green")
    # t.save_model()

