from pickle import load
import numpy as np
import streamlit as st

model_data = load(open('diabetic.pkl', 'rb'))

scaler = load(open('scalerdata.pkl', 'rb'))


def diabeted_prediction(input_data):
    array_input_data = np.asarray(input_data)
    reshaped_data = array_input_data.reshape(1, -1)
    standard_data = scaler.transform(reshaped_data)
    pred = model_data.predict(standard_data)
    if pred[0] == 0:
        return "The Person have not Diabetic"
    else:
        return "The Person have Diabetic"


def main():
    st.title("Diabetes Prediction Web App")
    Pregnancies = st.text_input('Number of Pregnancies')
    Glucose = st.text_input('Glucose Level')
    BloodPressure = st.text_input('Blood Pressure value')
    SkinThickness = st.text_input('Skin Thickness value')
    Insulin = st.text_input('Insulin Level')
    BMI = st.text_input('BMI value')
    DiabetesPedigreeFunction = st.text_input('Diabetes Pedigree Function value')
    Age = st.text_input('Age of the Person')

    # code for prediction
    diagnsis = ''

    if st.button("Diabetes Test Result"):
        diagnsis = diabeted_prediction(
            [Pregnancies, Glucose, BloodPressure, SkinThickness, Insulin, BMI, DiabetesPedigreeFunction, Age])
    st.success(diagnsis)


if __name__ == '__main__':
    main()
