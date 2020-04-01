FROM python:3.7
EXPOSE 8501
WORKDIR /app
RUN pip3 install cython
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt
COPY . .
CMD streamlit run corona-calculator.py
